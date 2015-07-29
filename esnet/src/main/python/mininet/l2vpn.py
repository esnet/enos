from array import array
import binascii

from common.intent import ProvisioningRenderer, ProvisioningIntent
from common.api import Site, Properties
from common.openflow import ScopeOwner,PacketInEvent, FlowMod, Match, Action, L2SwitchScope, PacketOut, SimpleController
from common.openflow import FlowEntry
from odl.client import ODLClient

from mininet.enos import TestbedTopology, TestbedHost, TestbedNode, TestbedPort, TestbedLink

from net.es.netshell.api import GenericGraph, GenericHost
from common.mac import MACAddress
from common.utils import Logger
import threading
import copy

class FlowStatus(Properties):
    """
    TappedBroadcast:
        flowmods[0:N]: forwarding from swSwitch to coreRouter in hwSwitch
        flowmods[N]: copying to serviceVm and dispatching in swSwitch (multicast)
        flowmods[N+1]: forwarding from coreRouter to swSwitch in hwSwitch
    UntappedBroadcast:
        flowmods[0:N]: forwarding from swSwitch to coreRouter in hwSwitch
        flowmods[N]: dispatching in swSwitch (multicast)
        flowmods[N+1]: forwarding from coreRouter to swSwitch in hwSwitch
    """
    def __init__(self, flowEntry, status, flowmods):
        super(FlowStatus, self).__init__(flowEntry.key())
        self.props['flowEntry'] = flowEntry
        self.props['status'] = status # str: 'Tapped', 'TappedWithSrcMac', 'Untapped', 'TappedBroadcast', 'UntappedBroadcast'
        self.props['flowmods'] = flowmods

class SDNPopsRenderer(ProvisioningRenderer,ScopeOwner):
    debug = False
    lastEvent = None
    instance = None
    logger = Logger('SDNPopsRenderer')

    def __init__(self, intent):
        """
        Generic constructor. Translate the intent
        :param intent: SiteIntent
        :return:
        """
        ScopeOwner.__init__(self,name=intent.name)
        self.intent = intent
        self.vpn = intent.vpn
        self.wan = intent.wan
        self.pops = intent.pops

        self.lock = threading.Lock() # protection for tapping/untapping
        self.active = False
        self.activePorts = {}
        self.props['tappedMacs'] = [] # list of tapped MAC
        self.props['tappedSites'] = [] # list of tapped Site
        self.props['tappedSitesWithSrcMac'] = [] # list of Site containing tapped MAC
        self.props['siteIndex'] = {} # [str(mac)] = site
        self.props['tappedMacsIndex'] = {} # [Site.name] = list of MACAddress
        self.props['scopeIndex'] = {} # [hwSwitch.name or swSwitch.name] = scope
        self.props['statusIndex'] = {} # [FlowEntry.key()] = FlowStatus
            # status: Untapped, UntappedHosts, Tapped, TappedBroadcast, UntappedBroadcast
        self.props['flowEntriesIndex'] = {} # [Site.name] = list of FlowEntry related to the site
            # flowEntries in a flowEntriesIndex would be in 3 categories:
            # 1. singlecast from local site: tap if site in tappedSites; tapWithSrcMac if site in tappedSitesWithSrcMac; untap otherwise
            # 2. singlecast to local site: tap if mac in tappedMacs; untap otherwise
            # 3. broadcast from local site: tap if site in tappedSites or site in tappedSitesWithSrcMac; untap otherwise
            # Note: There is at most one flow entry in category 3
        self.links = self.intent.links
        SDNPopsRenderer.instance = self
    def getSrcSite(self, vlan, port):
        k = "%s.%d" % (port.name, vlan)
        if not k in self.vpn.props['siteIndex']:
            SDNPopsRenderer.logger.debug("%r not in %r" % (k, self.name))
            return None
        return self.vpn.props['siteIndex'][k]
    def getDstSite(self, mac):
        if not str(mac) in self.props['siteIndex']:
            SDNPopsRenderer.logger.debug("%r not in %r" % (mac, self))
            return None
        return self.props['siteIndex'][str(mac)]

    def check(self, site, vlan, port):
        sitePort = site.props['pop'].props['hwSwitch'].props['sitePortIndex'][site.name]
        siteVlan = self.vpn.props['participantIndex'][site.name][2]
        return siteVlan == vlan and sitePort.name == port.name

    def getOutput(self, flowEntry):
        (mac, vlan, port) = flowEntry.get()
        switch = port.props['node']
        myPop = switch.props['pop']
        if port.props['type'].endswith('.WAN'):
            transMac = mac
            originalMac = self.reverse(transMac)
        else:
            originalMac = mac
            transMac = self.translate(originalMac)
        site = self.getDstSite(originalMac)
        pop = site.props['pop']
        if pop.name == myPop.name:
            outPort = switch.props['sitePortIndex'][site.name]
            outVlan = self.vpn.props['participantIndex'][site.name][2]
            outMac = originalMac
        else:
            outPort = switch.props['wanPortIndex'][pop.name]
            outVlan = outPort.props['links'][0].props['vlan']
            outMac = transMac
        return FlowEntry(outMac, outVlan, outPort)

    def addFlowEntry(self, site, flowEntry):
        if not site.name in self.props['flowEntriesIndex']:
            self.props['flowEntriesIndex'][site.name] = []
        self.props['flowEntriesIndex'][site.name].append(flowEntry)

    def updateFlowEntry(self, flowEntry):
        k = flowEntry.key()
        if not k in self.props['statusIndex']:
            self.props['statusIndex'][k] = FlowStatus(flowEntry, "Init", [])
            (inMac, inVlan, inPort) = flowEntry.get()
            if not inPort.props['type'].endswith('.WAN'): # from local site
                inSite = self.getSrcSite(inVlan, inPort)
                self.addFlowEntry(inSite, flowEntry)
            else: # from WAN
                # only care singlecast flow to the site
                toSite = self.getDstSite(self.reverse(inMac))
                if toSite:
                    self.addFlowEntry(toSite, flowEntry)
                # else might be broadcast, should have been managed by other pop

    def tapEntry(self, flowEntry):
        """
        flowStatus.props['flowmods'] in result:
         [0]: forwarding from swSwitch to coreRouter in hwSwitch
         [1]: copying to serviceVm and dispatching in swSwitch
         [2]: forwarding from coreRouter to swSwitch in hwSwitch
        """
        self.updateFlowEntry(flowEntry)
        (inMac, inVlan, inPort) = flowEntry.get()
        inSite = self.getSrcSite(inVlan, inPort)
        outFlowEntry = self.getOutput(flowEntry)
        (outMac, outVlan, outPort) = outFlowEntry.get()
        hwSwitch = inPort.props['node']
        hwScope = self.props['scopeIndex'][hwSwitch.name]
        swSwitch = hwSwitch.props['pop'].props['swSwitch']
        swScope = self.props['scopeIndex'][swSwitch.name]

        flowStatus = self.props['statusIndex'][flowEntry.key()]
        if flowStatus.props['status'] == 'Tapped': # tapped already
            return flowStatus.props['flowmods'][-1].getOutFlowEntry()

        SDNPopsRenderer.logger.info("%s.tapEntry(%r)" % (self.name, flowEntry))

        stitchedInPort = hwSwitch.props['stitchedPortIndex'][inPort.name]
        stitchedOutPort = hwSwitch.props['stitchedPortIndex'][outPort.name]

        if flowStatus.props['status'] == "Untapped" or flowStatus.props['status'] == "Init":
            # no need to preserve oldFlowmods
            flowmods = []

            # forward from swSwitch to coreRouter
            mod = hwScope.forward(hwSwitch, outMac, outVlan, stitchedOutPort, outMac, outVlan, outPort)
            flowmods.append(mod)

            # copy to serviceVm and dispatch in swSwitch
            outputs = []
            swInPort = stitchedInPort.props['links'][0].props['portIndex'][swSwitch.name]
            swOutPort = stitchedOutPort.props['links'][0].props['portIndex'][swSwitch.name]
            swScope.forward(swSwitch, inMac, inVlan, swInPort, outMac, outVlan, swOutPort)
            outputs.append((outMac, outVlan, swOutPort))
            vmPort = swSwitch.props['vmPortIndex'][self.vpn.name]
            outputs.append((inMac, inVlan, vmPort))
            mod = swScope.multicast(swSwitch, inMac, inVlan, swInPort, outputs)
            flowmods.append(mod)

            # forward from coreRouter to swSwitch
            mod = hwScope.forward(hwSwitch, inMac, inVlan, inPort, inMac, inVlan, stitchedInPort)
            flowmods.append(mod)
            flowStatus.props['flowmods'] = flowmods
        elif flowStatus.props['status'] == 'TappedWithSrcMac':
            # copy to serviceVm in addition to dispatch in swSwitch
            flowmodSw = flowStatus.props['flowmods'][-2]
            vmPort = flowmodSw.switch.props['vmPortIndex'][self.vpn.name]
            flowmodSw.scope.copy(flowmodSw, vmPort)

            # tear down other flowmods with src
            for flowmodWithSrcMac in flowStatus.props['flowmods'][1:-2]:
                swScope.delFlowMod(flowmodWithSrcMac)

            flowmods = []
            flowmods.append(flowStatus.props['flowmods'][0]) # forwarding from sw to core in hw
            flowmods.append(flowStatus.props['flowmods'][-2]) # copying to vm and dispatching in sw
            flowmods.append(flowStatus.props['flowmods'][-1]) # forwarding from core to sw in hw
            flowStatus.props['flowmods'] = flowmods
        flowStatus.props['status'] = "Tapped"
        return flowStatus.props['flowmods'][-1].getOutFlowEntry()

    def untapEntry(self, flowEntry):
        """
        flowStatus.props['flowmods'] in result:
         [0]: dispatching in hwSwitch
        """
        self.updateFlowEntry(flowEntry)
        (inMac, inVlan, inPort) = flowEntry.get()
        outFlowEntry = self.getOutput(flowEntry)
        (outMac, outVlan, outPort) = outFlowEntry.get()
        hwSwitch = inPort.props['node']
        hwScope = self.props['scopeIndex'][hwSwitch.name]
        swSwitch = hwSwitch.props['pop'].props['swSwitch']
        swScope = self.props['scopeIndex'][swSwitch.name]

        flowStatus = self.props['statusIndex'][flowEntry.key()]
        if flowStatus.props['status'] == "Untapped":
            return flowStatus.props['flowmods'][-1].getOutFlowEntry()

        SDNPopsRenderer.logger.info("%s.untapEntry(%r)" % (self.name, flowEntry))

        flowmods = []
        # dispatch in hwSwitch
        mod = hwScope.forward(hwSwitch, inMac, inVlan, inPort, outMac, outVlan, outPort)
        flowmods.append(mod)

        # tear down flowmods excluding last one (forwarding from core to sw in hw in Tapped)
        for flowmod in flowStatus.props['flowmods'][0:-1]:
            flowmod.scope.delFlowMod(flowmod)

        flowStatus.props['flowmods'] = flowmods
        flowStatus.props['status'] = "Untapped"
        return mod.getOutFlowEntry()

    def tapEntryWithSrcMac(self, flowEntry):
        """
        flowStatus.props['flowmods'] in result:
         [0]: forwarding from swSwitch to coreRouter in hwSwitch
         [1:N]: copying to serviceVm and dispatching in swSwitch with srcMac (with higher priority)
         [-2]: dispatching in swSwitch (without tapping) (with lower priority)
         [-1]: forwarding from coreRouter to swSwitch in hwSwitch
        """
        self.updateFlowEntry(flowEntry)
        (inMac, inVlan, inPort) = flowEntry.get()
        inSite = self.getSrcSite(inVlan, inPort)
        outFlowEntry = self.getOutput(flowEntry)
        (outMac, outVlan, outPort) = outFlowEntry.get()
        hwSwitch = inPort.props['node']
        hwScope = self.props['scopeIndex'][hwSwitch.name]
        swSwitch = hwSwitch.props['pop'].props['swSwitch']
        swScope = self.props['scopeIndex'][swSwitch.name]

        flowStatus = self.props['statusIndex'][flowEntry.key()]
        if flowStatus.props['status'] == 'TappedWithSrcMac':
            return flowStatus.props['flowmods'][-1].getOutFlowEntry()

        SDNPopsRenderer.logger.info("%s.tapEntryWithSrcMac(%r)" % (self.name, flowEntry))
        if flowStatus.props['status'] == "Untapped" or flowStatus.props['status'] == "Init":
            # no need to preserve oldFlowmods
            flowmods = []

            stitchedOutPort = hwSwitch.props['stitchedPortIndex'][outPort.name] 
            stitchedInPort = hwSwitch.props['stitchedPortIndex'][inPort.name]
            swInPort = stitchedInPort.props['links'][0].props['portIndex'][swSwitch.name]
            swOutPort = stitchedOutPort.props['links'][0].props['portIndex'][swSwitch.name]

            # forward from swSwitch to coreRouter
            mod = hwScope.forward(hwSwitch, outMac, outVlan, stitchedOutPort, outMac, outVlan, outPort)
            flowmods.append(mod)

            # copy to serviceVm and dispatch in swSwitch if src is matched (higher priority)
            vmPort = swSwitch.props['vmPortIndex'][self.vpn.name]
            if inSite and inSite.name in self.props['tappedMacsIndex']:
                for srcMac in self.props['tappedMacsIndex'][inSite.name]:
                    mod = swScope.tapWithSrcMac(swSwitch, inMac, inVlan, swInPort, outMac, outVlan, swOutPort, srcMac, vmPort)
                    flowmods.append(mod)

            # dispatch in swSwitch if no src is matched (lower priority)
            mod = swScope.forward(swSwitch, inMac, inVlan, swInPort, outMac, outVlan, swOutPort)
            flowmods.append(mod)

            # forward from coreRouter to swSwitch
            mod = hwScope.forward(hwSwitch, inMac, inVlan, inPort, inMac, inVlan, stitchedInPort)
            flowmods.append(mod)
            flowStatus.props['flowmods'] = flowmods
        elif flowStatus.props['status'] == "Tapped":
            flowmods = []
            flowmods.append(flowStatus.props['flowmods'][0]) # forwarding from sw to core in hw
            # copy to serviceVm and dispatch in swSwitch if src is matched
            (outMac, outVlan, outPort) = self.getOutput(flowEntry).get()
            stitchedOutPort = hwSwitch.props['stitchedPortIndex'][outPort.name] 
            swOutPort = stitchedOutPort.props['links'][0].props['portIndex'][swSwitch.name]
            stitchedInPort = hwSwitch.props['stitchedPortIndex'][inPort.name]
            swInPort = stitchedInPort.props['links'][0].props['portIndex'][swSwitch.name]
            vmPort = swSwitch.props['vmPortIndex'][self.vpn.name]
            if inSite and inSite.name in self.props['tappedMacsIndex']:
                for srcMac in self.props['tappedMacsIndex'][inSite.name]:
                    mod = swScope.tapWithSrcMac(swSwitch, inMac, inVlan, swInPort, outMac, outVlan, swOutPort, srcMac, vmPort)
                    flowmods.append(mod)

            # stop copy to serviceVm
            flowmodSw = flowStatus.props['flowmods'][-2]
            flowmodSw.scope.restore(flowmodSw)
            flowmods.append(flowmodSw)

            flowmods.append(flowStatus.props['flowmods'][-1]) # forwarding from core to sw in hw
            flowStatus.props['flowmods'] = flowmods

        flowStatus.props['status'] = 'TappedWithSrcMac'
        return flowStatus.props['flowmods'][-1].getOutFlowEntry()

    def createBroadcastEntry(self, flowEntry, tapped):
        SDNPopsRenderer.logger.info("%r.createBroadcastEntry(%r,%r)" % (self.name, flowEntry, tapped))
        self.updateFlowEntry(flowEntry)
        (inMac, inVlan, inPort) = flowEntry.get()
        hwSwitch = inPort.props['node']
        hwScope = self.props['scopeIndex'][hwSwitch.name]
        swSwitch = hwSwitch.props['pop'].props['swSwitch']
        swScope = self.props['scopeIndex'][swSwitch.name]

        flowmods = []
        myPop = hwSwitch.props['pop']
        flowEntries = []
        if inPort.props['type'].endswith('.WAN'): # from WAN
            transMac = inMac
            originalMac = self.reverse(transMac)
            for (site, hosts, siteVlan) in self.vpn.props['participants']:
                pop = site.props['pop']
                if pop.name == myPop.name: # to site
                    outPort = hwSwitch.props['sitePortIndex'][site.name]
                    outVlan = siteVlan
                    outMac = originalMac
                    flowEntries.append(FlowEntry(outMac, outVlan, outPort))
                else: # to WAN
                    continue # no need to broadcast from WAN to WAN
        else: # from site
            originalMac = inMac
            transMac = self.translate(originalMac)
            for (site, hosts, siteVlan) in self.vpn.props['participants']:
                pop = site.props['pop']
                if pop.name == myPop.name: # to site
                    outPort = hwSwitch.props['sitePortIndex'][site.name]
                    if siteVlan == inVlan and outPort.name == inPort.name:
                        continue # exclude self
                    outVlan = siteVlan
                    outMac = originalMac
                    flowEntries.append(FlowEntry(outMac, outVlan, outPort))
                else: # to WAN
                    outPort = hwSwitch.props['wanPortIndex'][pop.name]
                    outVlan = outPort.props['links'][0].props['vlan']
                    outMac = transMac
                    flowEntries.append(FlowEntry(outMac, outVlan, outPort))
        outputs = []
        for entry in flowEntries:
            (outMac, outVlan, outPort) = entry.get()
            stitchedOutPort = hwSwitch.props['stitchedPortIndex'][outPort.name]
            # forward to coreRouter
            mod = hwScope.forward(hwSwitch, outMac, outVlan, stitchedOutPort, outMac, outVlan, outPort)
            flowmods.append(mod)
            swOutPort = stitchedOutPort.props['links'][0].props['portIndex'][swSwitch.name]
            outputs.append((outMac, outVlan, swOutPort))

        # broadcast in swSwitch (and copy to serviceVm optionally)
        stitchedInPort = hwSwitch.props['stitchedPortIndex'][inPort.name]
        swInPort = stitchedInPort.props['links'][0].props['portIndex'][swSwitch.name]
        if tapped:
            vmPort = swSwitch.props['vmPortIndex'][self.vpn.name]
            outputs.append((inMac, inVlan, vmPort))
        mod = swScope.multicast(swSwitch, inMac, inVlan, swInPort, outputs)
        flowmods.append(mod)

        # forward to swSwitch
        mod = hwScope.forward(hwSwitch, inMac, inVlan, inPort, inMac, inVlan, stitchedInPort)
        flowmods.append(mod)

        if tapped:
            status = 'TappedBroadcast'
        else:
            status = 'UntappedBroadcast'
        self.props['statusIndex'][flowEntry.key()] = FlowStatus(flowEntry, status, flowmods)
        return FlowEntry(inMac, inVlan, stitchedInPort)

    def tapBroadcastEntry(self, flowEntry):
        """
        flowStatus.props['flowmods'][-2]: dispatching in swSwitch
        flowStatus.props['flowmods'][-1]: forwarding from coreRouter to swSwitch in hwSwitch
        """
        k = flowEntry.key()
        if not k in self.props['statusIndex']:
            return self.createBroadcastEntry(flowEntry, True)

        flowStatus = self.props['statusIndex'][k]
        result = flowStatus.props['flowmods'][-1].getOutFlowEntry()
        if flowStatus.props['status'] == "TappedBroadcast":
            return result

        SDNPopsRenderer.logger.info("%r.tapBroadcastEntry(%r)" % (self.name, flowEntry))

        # copy to serviceVm
        flowmodSw = flowStatus.props['flowmods'][-2]
        vmPort = flowmodSw.switch.props['vmPortIndex'][self.vpn.name]
        flowmodSw.scope.copy(flowmodSw, vmPort)

        flowStatus.props['status'] = "TappedBroadcast"
        return result

    def untapBroadcastEntry(self, flowEntry):
        """
        flowStatus.props['flowmods'][-2]: dispatching in swSwitch
        flowStatus.props['flowmods'][-1]: forwarding from coreRouter to swSwitch in hwSwitch
        """
        k = flowEntry.key()
        if not k in self.props['statusIndex']:
            return self.createBroadcastEntry(flowEntry, False)

        flowStatus = self.props['statusIndex'][k]
        result = flowStatus.props['flowmods'][-1].getOutFlowEntry()
        if flowStatus.props['status'] == "UntappedBroadcast":
            return result

        SDNPopsRenderer.logger.info("%r.untapBroadcastEntry(%r)" % (self.name, flowEntry))

        # stop copying to serviceVm
        flowmodSw = flowStatus.props['flowmods'][-2]
        flowmodSw.scope.restore(flowmodSw)

        flowStatus.props['status'] = "UntappedBroadcast"
        return result

    def tapHost(self, host):
        self.tapMac(host.props['mac'])
    def untapHost(self, host):
        self.untapMac(host.props['mac'])

    def tapMac(self, mac):
        with self.lock:
            if mac in self.props['tappedMacs']:
                SDNPopsRenderer.logger.warning("The mac %r on VPN %s has been tapped" % (mac, self.vpn.name))
                return
            # update tappedMacs, tappedMacsIndex, and tappedSitesWithSrcMac
            self.props['tappedMacs'].append(mac)
            site = self.getDstSite(mac)
            if not site.name in self.props['tappedMacsIndex']:
                self.props['tappedMacsIndex'][site.name] = []
            self.props['tappedMacsIndex'][site.name].append(mac)
            if not site in self.props['tappedSitesWithSrcMac']:
                self.props['tappedSitesWithSrcMac'].append(site)

            if site in self.props['tappedSites']:
                SDNPopsRenderer.logger.debug("The site has been tapped, tap a mac won't change anything")
                return

            if site.name in self.props['flowEntriesIndex']:
                for flowEntry in self.props['flowEntriesIndex'][site.name]:
                    if flowEntry.isBroadcast(): # category 3
                        self.tapBroadcastEntry(flowEntry)
                    else:
                        (inMac, inVlan, inPort) = flowEntry.get()
                        if inPort.props['type'].endswith('.WAN'): # category 2
                            originalMac = self.reverse(inMac)
                            if originalMac == mac:
                                self.tapEntry(flowEntry)
                        else: # category 1
                            self.tapEntryWithSrcMac(flowEntry)

    def untapMac(self, mac):
        with self.lock:
            if not mac in self.props['tappedMacs']:
                SDNPopsRenderer.logger.warning("The mac %r on VPN %s is not tapped yet" % (mac, self.vpn.name))
                return
            # update tappedMacs and tappedSitesWithSrcMac
            self.props['tappedMacs'].remove(mac)
            site = self.getDstSite(mac)
            self.props['tappedMacsIndex'][site.name].remove(mac)
            if not self.props['tappedMacsIndex'][site.name]:
                self.props['tappedSitesWithSrcMac'].remove(site)

            if site in self.props['tappedSites']:
                SDNPopsRenderer.logger.debug("The site is still tapped, untap a mac won't change anything")
                return

            if site.name in self.props['flowEntriesIndex']:
                for flowEntry in self.props['flowEntriesIndex'][site.name]:
                    if flowEntry.isBroadcast(): # category 3
                        if not site in self.props['tappedSitesWithSrcMac']:
                            self.untapBroadcastEntry(flowEntry)
                    else:
                        (inMac, inVlan, inPort) = flowEntry.get()
                        if inPort.props['type'].endswith('.WAN'): # category 2
                            originalMac = self.reverse(inMac)
                            if originalMac == mac:
                                self.untapEntry(flowEntry)
                        else: # category 1
                            if not site in self.props['tappedSitesWithSrcMac']:
                                self.untapEntry(flowEntry)

    def tapSite(self, site):
        with self.lock:
            if site in self.props['tappedSites']:
                SDNPopsRenderer.logger.warning("The site %s on VPN %s has been tapped" % (site.name, self.vpn.name))
                return
            # update tappedSites
            self.props['tappedSites'].append(site)

            if site.name in self.props['flowEntriesIndex']:
                for flowEntry in self.props['flowEntriesIndex'][site.name]:
                    if flowEntry.isBroadcast():
                        self.tapBroadcastEntry(flowEntry)
                    else:
                        self.tapEntry(flowEntry)

    def untapSite(self, site):
        with self.lock:
            if not site in self.props['tappedSites']:
                SDNPopsRenderer.logger.warning("The site %s on VPN %s is not tapped yet" % (site.name, self.vpn.name))
                return
            # update tappedSites
            self.props['tappedSites'].remove(site)

            if site.name in self.props['flowEntriesIndex']:
                for flowEntry in self.props['flowEntriesIndex'][site.name]:
                    if flowEntry.isBroadcast(): # category 3
                        if not site in self.props['tappedSitesWithSrcMac']:
                            self.untapBroadcastEntry(flowEntry)
                    else:
                        (inMac, inVlan, inPort) = flowEntry.get()
                        if inPort.props['type'].endswith('.WAN'): # category 2
                            originalMac = self.reverse(inMac)
                            if not originalMac in self.props['tappedMacs']:
                                self.untapEntry(flowEntry)
                        else: # category 1
                            if site in self.props['tappedSitesWithSrcMac']:
                                self.tapEntryWithSrcMac(flowEntry)
                            else:
                                self.untapEntry(flowEntry)

    def addHost(self, host):
        # cheating here to avoid any possible missed packet from controller
        self.props['siteIndex'][str(host.props['mac'])] = host.props['site']

    def addSite(self, site, siteVlan):
        # could be invoked in CLI
        vid = self.vpn.props['vid']
        pop = site.props['pop']
        coreRouter = pop.props['coreRouter'].props['enosNode']
        hwSwitch = pop.props['hwSwitch'].props['enosNode']
        hwSwitchScope = L2SwitchScope(name='%s.%s' % (self.vpn.name, hwSwitch.name), switch=hwSwitch, owner=self)
        self.props['scopeIndex'][hwSwitch.name] = hwSwitchScope
        sitePort = hwSwitch.props['sitePortIndex'][site.name]
        hwSwitchScope.addEndpoint(sitePort, siteVlan)
        swPort = hwSwitch.props['stitchedPortIndex'][sitePort.name]
        hwSwitchScope.addEndpoint(swPort, siteVlan)

        swSwitch = pop.props['swSwitch'].props['enosNode']
        swSwitchScope = L2SwitchScope(name='%s.%s' % (self.vpn.name, swSwitch.name),switch=swSwitch,owner=self)
        self.props['scopeIndex'][swSwitch.name] = swSwitchScope
        swSwitchScope.addEndpoint(swSwitch.props['sitePortIndex'][site.name], siteVlan)
        swSwitchScope.addEndpoint(swSwitch.props['vmPortIndex'][self.vpn.name])

        hwSwitch.props['siteVlanIndex'][vid] = siteVlan
        controller = hwSwitch.props['controller']
        controller.addScope(hwSwitchScope)
        controller.addScope(swSwitchScope)

        pop = hwSwitch.props['pop']
        for other_pop in self.pops:
            self.connectPop(pop, other_pop)
            self.connectPop(other_pop, pop)
        self.pops.append(pop)

    def connectPop(self, pop1, pop2):
        """
        Connect pop1 to pop2 (one way only)
        Here we use (port, vid) instead of (port, vlan) as the index.
        The reason is that VPNs all share the same port and vlan on the
        'HwToCore.WAN' ports of HwSwitch, so we couldn't dispatch packets
        to the scope based on vlan. The solution is temporary only.
        """
        # swSwitch[tohw_port]-[tosw_port]hwSwitch[tocore_port]-coreRouter
        vid = self.vpn.props['vid']
        hwSwitch = pop1.props['hwSwitch']
        swSwitch = pop1.props['swSwitch']
        hwSwitchScope = self.props['scopeIndex'][hwSwitch.name]
        swSwitchScope = self.props['scopeIndex'][swSwitch.name]

        tocore_port = hwSwitch.props['wanPortIndex'][pop2.name]
        hwSwitchScope.addEndpoint(tocore_port, vid)
        tocore_port.props['scopeIndex'][vid] = hwSwitchScope

        tosw_port = hwSwitch.props['stitchedPortIndex'][tocore_port.name]
        hwSwitchScope.addEndpoint(tosw_port, vid)
        tosw_port.props['scopeIndex'][vid] = hwSwitchScope

        tohw_port = swSwitch.props['wanPortIndex'][pop2.name]
        swSwitchScope.addEndpoint(tohw_port, vid)
        tohw_port.props['scopeIndex'][vid] = swSwitchScope

    def __str__(self):
        return "SDNPopsRenderer(name=%r,scopeIndex=%r)" % (self.name, self.props['scopeIndex'])

    def __repr__(self):
        return self.__str__()

    def eventListener(self,event):
        """
        The implementation of this class is expected to overwrite this method if it desires
        to receive events from the controller such as PACKET_IN
        :param event: ScopeEvent
        """
        if event.__class__ != PacketInEvent:
            SDNPopsRenderer.logger.info("unknown %r, reject by %r" % (event, self))
            return
        if not 'vlan' in event.props:
            SDNPopsRenderer.logger.info("%r has no vlan, reject by %r" % (event, self))
            return

        with self.lock:
            srcMac = event.props['dl_src']
            dstMac = event.props['dl_dst']
            inPort = event.props['in_port'].props['enosPort']
            inVlan = event.props['vlan']
            flowEntry = FlowEntry(dstMac, inVlan, inPort)
            inSite = self.getSrcSite(inVlan, inPort)
            switch = inPort.props['node'].props['enosNode'] # must be hwSwitch
            myPop = switch.props['pop']
            controller = switch.props['controller']
            scope = controller.getScope(inPort, inVlan, dstMac)
            etherType = event.props['ethertype']
            payload = event.props['payload']
            if inPort.props['type'].endswith('.WAN'): # from WAN
                transMac = dstMac
                originalMac = self.reverse(transMac)
            else: # from Site
                originalMac = dstMac
                transMac = self.translate(originalMac)

            if not inPort.props['type'].startswith('HwToCore'):
                SDNPopsRenderer.logger.warning("Unknown packet should come from coreRouter only")
                return

            # update the information of which site the srcMac belongs
            if not inPort.props['type'].endswith('.WAN'): # from site
                if not self.getDstSite(srcMac):
                    self.props['siteIndex'][str(srcMac)] = inSite

            if dstMac.isBroadcast():
                # check if any site or any mac in the same pop is tapped
                involved = False
                for site in myPop.props['sites']:
                    if site in self.props['tappedSites'] or site in self.props['tappedSitesWithSrcMac']:
                        involved = True
                        break
                if involved:
                    outFlowEntry = self.tapBroadcastEntry(flowEntry)
                else:
                    outFlowEntry = self.untapBroadcastEntry(flowEntry)
            else:
                toSite = self.getDstSite(originalMac)
                if inPort.props['type'].endswith('.WAN'):
                    if dstMac in self.props['tappedMacs']:
                        outFlowEntry = self.tapEntry(flowEntry)
                    elif toSite in self.props['tappedSites']:
                        outFlowEntry = self.tapEntry(flowEntry)
                    else:
                        outFlowEntry = self.untapEntry(flowEntry)
                else: # from site
                    if toSite.props['pop'].name == myPop.name:
                        # from site to site: might not support yet
                        if toSite in self.props['tappedSites'] or originalMac in self.props['tappedMacs']:
                            outFlowEntry = self.tapEntry(flowEntry)
                    elif inSite in self.props['tappedSites']:
                        outFlowEntry = self.tapEntry(flowEntry)
                    elif inSite in self.props['tappedSitesWithSrcMac']:
                        outFlowEntry = self.tapEntryWithSrcMac(flowEntry)
                    else:
                        outFlowEntry = self.untapEntry(flowEntry)
            (outMac, outVlan, outPort) = outFlowEntry.get()
            scope.send(switch, outPort, srcMac, outMac, etherType, outVlan, payload)

    def translate(self, mac):
        return self.vpn.props['mat'].translate(mac)
    def reverse(self, trans_mac):
        hid = trans_mac.getHid()
        return self.vpn.props['mat'].reverse(hid)

    def broadcast(self,inPort,inVlan,srcMac,dstMac,etherType,payload,switch,scope) :
        pass
    def setMAC(self,port,vlan,dl_src,dl_dst,switch,scope):
        pass

    def execute(self):
        """
        This function might be useless since a VPN is built in the runtime

        Renders the intent.
        :return: Expectation when succcessful, None otherwise
        """
        # update graph
        self.intent.updateGraph()
        return
        # Add scopes to the controller
        for scope in self.props['scopeIndex'].values():
            if not scope.switch.props['controller'].addScope(scope):
                print "Cannot add", scope
                return False
        self.active = True
        return True


    def destroy(self):
        """
        Destroys or stop the rendering of the intent.
        :return: True if successful
        """
        self.active = False
        return

class SDNPopsIntent(ProvisioningIntent):
    def __init__(self, name, vpn, wan):
        super(SDNPopsIntent, self).__init__(name=name, graph=None)
        self.vpn = vpn
        self.wan = wan
        self.updateGraph()
    def updateGraph(self):
        """
        Creates a provisioning intent providing a GenericGraph of the logical view of the
        topology that is intended to be created.
        :param vpn: VPN which contains information of participants (site and hosts)
        :param wan: Wan which contains information of all links in WAN
        """
        pops = []
        nodes = []
        links = []
        for participant in self.vpn.props['participants']:
            (site, hosts_in_site, wanVlan) = participant
            pop = site.props['pop']
            if not pop in pops:
                pops.append(pop)
            # note: nodes and links will be translated to enosNode later
            hwSwitch = pop.props['hwSwitch']
            coreRouter = pop.props['coreRouter']
            nodes.append(site.props['siteRouter'])
            nodes.extend(hosts_in_site)
            nodes.append(coreRouter)
            nodes.append(hwSwitch)
            nodes.append(pop.props['swSwitch'])
            nodes.extend(self.vpn.props['serviceVms'])
            # links between serviceVms and swSwitch
            links.extend(map(lambda vm:vm.props['ports'][1].props['links'][0], self.vpn.props['serviceVms']))
            # links between host and site
            links.extend(map(lambda host:host.props['ports'][1].props['links'][0], hosts_in_site))
            # link between site and border
            links.append(site.props['siteRouter'].props['toWanPort'].props['links'][0])
            # link between core and hw
            sitePortInCore = coreRouter.props['sitePortIndex'][site.name]
            linkBetweenCoreAndHw = coreRouter.props['stitchedPortIndex'][sitePortInCore.name].props['links'][0]
            links.append(linkBetweenCoreAndHw)
            # link between hw and sw
            toSitePortInHw = linkBetweenCoreAndHw.props['portIndex'][hwSwitch.name]
            links.append(hwSwitch.props['stitchedPortIndex'][toSitePortInHw.name].props['links'][0])
        links.extend(self.wan.subsetLinks(pops))

        enosNodes = map(lambda host : host.props['enosNode'], nodes)
        enosLinks = map(lambda host : host.props['enosLink'], links)
        self.pops = pops
        self.nodes = enosNodes
        self.links = enosLinks
        self.graph = self.getGraph()
        self.props['topology'] = self.graph

    def getGraph(self):
        graph = GenericGraph()

        for node in self.nodes:
            graph.addVertex(node)

        for link in self.links:
            node1 = link.getSrcNode()
            node2 = link.getDstNode()
            graph.addEdge(node1,node2,link)
        return graph


