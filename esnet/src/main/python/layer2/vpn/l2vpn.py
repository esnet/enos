#
# ENOS, Copyright (c) 2015, The Regents of the University of California,
# through Lawrence Berkeley National Laboratory (subject to receipt of any
# required approvals from the U.S. Dept. of Energy).  All rights reserved.
#
# If you have questions about your rights to use or distribute this software,
# please contact Berkeley Lab's Technology Transfer Department at TTD@lbl.gov.
#
# NOTICE.  This software is owned by the U.S. Department of Energy.  As such,
# the U.S. Government has been granted for itself and others acting on its
# behalf a paid-up, nonexclusive, irrevocable, worldwide license in the Software
# to reproduce, prepare derivative works, and perform publicly and display
# publicly.  Beginning five (5) years after the date permission to assert
# copyright is obtained from the U.S. Department of Energy, and subject to
# any subsequent five (5) year renewals, the U.S. Government is granted for
# itself and others acting on its behalf a paid-up, nonexclusive, irrevocable,
# worldwide license in the Software to reproduce, prepare derivative works,
# distribute copies to the public, perform publicly and display publicly, and
# to permit others to do so.
#
from array import array
import binascii

from layer2.common.intent import ProvisioningRenderer, ProvisioningIntent
from layer2.common.api import Site, Properties
from layer2.common.openflow import ScopeOwner,PacketInEvent, FlowMod, Match, Action, L2SwitchScope, PacketOut, SimpleController
from layer2.common.openflow import FlowEntry

from layer2.testbed.topology import TestbedTopology, TestbedHost, TestbedNode, TestbedPort, TestbedLink

from net.es.netshell.api import GenericGraph, GenericHost
from layer2.common.mac import MACAddress
from layer2.common.utils import Logger
import threading
import time
import copy
import sys
import inspect

class FlowStatus(Properties):
    """
    Untapped:
        flowmods[0]: dispatching in hwSwitch
    Tapped:
        flowmods[2]: forwarding from coreRouter to swSwitch in hwSwitch
        flowmods[1]: copying to serviceVm and dispatching in swSwitch
        flowmods[0]: forwarding from swSwitch to coreRouter in hwSwitch
    TappedWithSrcMac:
        flowmods[-1]: forwarding from coreRouter to swSwitch in hwSwitch
        flowmods[-2]: dispatching in swSwitch
        flowmods[1:N+1]: N copying to serviceVm and dispatching in swSwitch with dl_src in match and higher priority
        flowmods[0]: forwarding from swSwitch to coreRouter in hwSwitch
    UntappedBroadcast:
        flowmods[N]: forwarding from coreRouter to swSwitch in hwSwitch
        flowmods[0:N]: N forwarding from swSwitch to coreRouter in hwSwitch
        sampleFlowmod & srcMacs: M dispatching in swSwitch (multicast) with dl_src in match
    TappedBroadcast:
        flowmods[N]: forwarding from coreRouter to swSwitch in hwSwitch
        flowmods[0:N]: N forwarding from swSwitch to coreRouter in hwSwitch
        sampleFlowmod & srcMacs: M copying to serviceVm and dispatching in swSwitch (multicast) with dl_src in match
    """
    def __init__(self, flowEntry, status, flowmods):
        super(FlowStatus, self).__init__(flowEntry.key())
        self.props['flowEntry'] = flowEntry
        self.props['status'] = status # str: 'Init', 'Tapped', 'TappedWithSrcMac', 'Untapped', 'TappedBroadcast', 'UntappedBroadcast'
        self.props['flowmods'] = flowmods
        # for broadcast only
        self.props['sampleFlowmod'] = None # used as a sample in swSwitch
        self.props['broadcastFlowmods'] = []
        self.props['srcMacs'] = []
    def addMac(self, mac, vmPort):
        self.props['srcMacs'].append(mac)
        mod = copy.copy(self.props['sampleFlowmod'])
        mod.match.props['dl_src'] = mac
        if self.props['status'].startswith('Tapped'):
            mod.actions.append(Action(props={'dl_dst':mod.match.props['dl_dst'], 'vlan':mod.match.props['vlan'], 'out_port':vmPort}))
        self.props['broadcastFlowmods'].append(mod)
        return mod

class SDNPopsRenderer(ProvisioningRenderer,ScopeOwner):
    VERSION = 1
    logger = Logger('SDNPopsRenderer')
    index = {}
    def __init__(self, intent):
        """
        Generic constructor. Translate the intent
        :param intent: SDNpopsIntent
        :return:
        """
        ScopeOwner.__init__(self,name=intent.name)
        self.intent = intent
        self.vpn = intent.vpn
        self.wan = intent.wan

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
            # status: Untapped, TappedWithSrcMac, Tapped, TappedBroadcast, UntappedBroadcast
        self.props['flowEntriesIndex'] = {} # [Site.name] = list of FlowEntry related to the site
        """
        flowEntries in a site would be in one of these four categories:
        1. single-cast from local site to WAN: tap if the site in tappedSites; tapWithSrcMac if the site in tappedSitesWithSrcMac; untap otherwise
        2. single-cast from WAN to local site: tap if the site in tappedSites or mac in tappedMacs; untap otherwise
        3. single-cast from local site A to another local site B: tap if A or B in tappedSites, or mac in tappedMacs; tapWithSrcMac if A or B in tappedSitesWithSrcMac; untap otherwise
        4. broadcast from local site: tap if any site in the same pop in tappedSites or in tappedSitesWithSrcMac; untap otherwise
        """
        self.props['popIndex'] = {} # [SDNPop.name] = SDNPop
        self.props['timeout'] = 0 # timeout (seconds) for tapping a new src MAC; 0 means disable
        self.links = self.intent.links
        SDNPopsRenderer.index[self.vpn.name] = self
    def serialize(self):
        obj = {}
        obj['version'] = SDNPopsRenderer.VERSION
        obj['siteIndex'] = {}
        for (mac, site) in self.props['siteIndex'].items():
            obj['siteIndex'][mac] = site.name
        obj['tappedMacs'] = map(lambda mac:str(mac), self.props['tappedMacs'])
        obj['tappedSites'] = map(lambda site:site.name, self.props['tappedSites'])
        obj['flowEntries'] = map(lambda status:status.props['flowEntry'].serialize(), self.props['statusIndex'].values())
        return obj

    @staticmethod
    def deserialize(obj, vpn, net):
        if obj['version'] != SDNPopsRenderer.VERSION:
            SDNPopsRenderer.logger.warning("version is not matched while deserializing")
            return
        intent = SDNPopsIntent(name=vpn.name, vpn=vpn, wan=net.builder.wan)
        renderer = SDNPopsRenderer(intent)
        for (mac, sitename) in obj['siteIndex'].items():
            renderer.props['siteIndex'][mac] = net.builder.siteIndex[sitename]
        for (site, hosts, siteVlan) in vpn.props['participants']:
            pop = site.props['pop']
            if not pop.name in renderer.props['popIndex']:
                renderer.addPop(pop)
            renderer.addSite(site, siteVlan)
            # Here we don't use hosts.props['mac'] to update siteIndex because
            # mac might come from unknown hosts in the future
            # for host in hosts:
            #   renderer.props['siteIndex'][str(host.props['mac'])] = host.props['site']

        for sitename in obj['tappedSites']:
            renderer.props['tappedSites'].append(net.builder.siteIndex[sitename])
        for mac in obj['tappedMacs']:
            renderer.addTappedMac(MACAddress(mac))
        for flowEntry in obj['flowEntries']:
            flow = FlowEntry.deserialize(flowEntry, net)
            renderer.parseFlowEntry(flow)
        return renderer

    def setTimeout(self, timeout):
        self.props['timeout'] = timeout

    def addTappedMac(self, mac):
        # update tappedMacs, tappedMacsIndex, and tappedSitesWithSrcMac
        self.props['tappedMacs'].append(mac)
        site = self.getDstSite(mac)
        if not site.name in self.props['tappedMacsIndex']:
            self.props['tappedMacsIndex'][site.name] = []
        self.props['tappedMacsIndex'][site.name].append(mac)
        if not site in self.props['tappedSitesWithSrcMac']:
            self.props['tappedSitesWithSrcMac'].append(site)

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
        """
        Get the output where the flowEntry should go.
        :param flowEntry: a tuple of (mac, vlan, port). mac should be NOT broadcast, and port should be on hwSwitch.
        :return: the output based on flowEntry
        """
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

    def delFlowEntry(self, flowEntry):
        if not flowEntry.key() in self.props['statusIndex']:
            SDNPopsRenderer.logger.warning("flowEntry %s is not found in %s.statusIndex" % (flowEntry, self))
            return
        status = self.props['statusIndex'][flowEntry.key()]
        for flowmod in status.props['flowmods']:
            flowmod.scope.delFlowMod(flowmod)
        for flowmod in status.props['broadcastFlowmods']:
            flowmod.scope.delFlowMod(flowmod)
        self.props['statusIndex'].pop(flowEntry.key())
        for category in self.getCategories(flowEntry):
            category.append(flowEntry)

    def getFlowEntries(self, site):
        if not site.name in self.props['flowEntriesIndex']:
            self.props['flowEntriesIndex'][site.name] = []
        return self.props['flowEntriesIndex'][site.name]

    def getCategories(self, flowEntry):
        categories = []
        (inMac, inVlan, inPort) = flowEntry.get()
        if inMac.isBroadcast():
            if inPort.props['type'].endswith('.WAN'):
                # from WAN: no interested at all
                # We'll never tap this flowEntry (since we could tap it in the source pop)
                pass
            else:
                inSite = self.getSrcSite(inVlan, inPort)
                categories.append(self.getFlowEntries(inSite))
        else: # single-cast to local site
            if inPort.props['type'].endswith('.WAN'): # from WAN
                toSite = self.getDstSite(self.reverse(inMac))
                categories.append(self.getFlowEntries(toSite))
            else: # from local site
                inSite = self.getSrcSite(inVlan, inPort)
                toSite = self.getDstSite(inMac)
                if toSite.props['pop'].name == inSite.props['pop'].name:
                    categories.append(self.getFlowEntries(inSite))
                    categories.append(self.getFlowEntries(toSite))
                else:
                    categories.append(self.getFlowEntries(inSite))
        return categories

    def updateFlowEntry(self, flowEntry):
        """
        Create a FlowStatus if the flowEntry is new
        """
        k = flowEntry.key()
        if not k in self.props['statusIndex']:
            self.props['statusIndex'][k] = FlowStatus(flowEntry, 'Init', [])
            for category in self.getCategories(flowEntry):
                category.append(flowEntry)

    def tapEntry(self, flowEntry):
        """
        This method might be invoked when tapsite, tapmac, or taphost happens.
        An entry would be tapped if:
            1. the src site (based on vlan, inport) in tappedSites, or
            2. the dst site (based on mac) is local and in tappedSites, or
            3. the dst mac is local and in tappedMacs
        Some scenarios might be:
        When we receive an single-cast entry (mac, vlan, port) satisfying the
        criteria listed above, it is tapped.
        When we tap a site, all local single-cast entries from this site and to
        this site would be tapped.
        When we tap a mac, all local single-cast entries toward to the mac
        would be tapped.

        flowStatus.props['flowmods'] in result:
         [2]: forwarding from coreRouter to swSwitch in hwSwitch
         [1]: copying to serviceVm and dispatching in swSwitch
         [0]: forwarding from swSwitch to coreRouter in hwSwitch
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
        if inPort.props['type'].endswith('.WAN'):
            vmPort = swSwitch.props['vmPort.WAN']
        else:
            vmPort = swSwitch.props['vmPort']

        flowStatus = self.props['statusIndex'][flowEntry.key()]
        if flowStatus.props['status'] == 'Tapped': # tapped already
            return flowStatus.props['flowmods'][-1].getOutFlowEntry()

        SDNPopsRenderer.logger.info("%s.tapEntry(%r)" % (self.name, flowEntry))

        stitchedInPort = hwSwitch.props['stitchedPortIndex'][inPort.name]
        stitchedOutPort = hwSwitch.props['stitchedPortIndex'][outPort.name]

        if flowStatus.props['status'] == "Untapped" or flowStatus.props['status'] == "Init":
            # no need to preserve oldFlowmods since they'll be replaced by new one
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
        This method might be invoked when untapsite, untapmac/host happens.
        An entry would be untapped if:
            1. not satisfied the condition of being tapped, and
            2. not satisfied the condition of being tapped with src mac.
        Some scenarios might be:
        When we receive an single-cast entry (mac, vlan, port) satisfying the
        criteria listed above, it is untapped.
        When we untap a site, we check if the site in tappedSitesWithSrcMac.
        If yes, we untap those local single-cast entries to this site but mac
        is not in tappedMacs.
        If not, we untap all local single-cast entries from this site and to
        the site.
        When we untap a mac belonging to a specific site, if the site is not in
        tappedSites, and if the mac is the only tapped mac in the site, then
        the site would be popped from the tappedSitesWithSrcMac, then we untap
        all local single-cast entries from this site and to the site. Otherwise,
        if the mac is not the only tapped mac in the site, then we just untap
        the local single-cast entry to the mac.

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
        This method might be invoked when untapsite or tapmac/host happens.
        An entry would be tapped with src mac if:
            1. not satisfied the condition of being tapped, and
            2. the src site (based on vlan, inport) is in tappedSitesWithSrcMac
        Some scenarios might be:
        When we receive an single-cast entry (mac, vlan, port) satisfying the
        criteria listed above, it is tapped with src mac.
        When we untap a site, we check if the site in tappedSitesWithSrcMac.
        If yes, we tap all local single-cast entries with src mac from this
        site.
        When we tap a mac belonging to a specific site, if the site is not in
        tappedSites, and if the mac is the first tapped mac in the site, then
        the site would be added into the tappedSitesWithSrcMac, then we tap all
        local single-cast entries from this site with src mac excluding the
        entry to the specific mac.

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
            vmPort = swSwitch.props['vmPort']
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
            if swInPort.props['type'].endswith('.WAN'):
                vmPort = swSwitch.props['vmPort.WAN']
            else:
                vmPort = swSwitch.props['vmPort']
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
        # print "SDNPopsRenderer.createBroadcastEntry for %r (%r,%r)" % (self.name, flowEntry, tapped)
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

                    # Find the correct link to use on this port.  "Correct" is the one
                    # that is associated with a trunk port to the remote pop we need.
                    # From this, derive the correct VLAN tag to use.
                    outVlan = 0 # If it's still 0 after the loop there could be a problem.
                                # In the mininet world, this was fine.
                    for l in outPort.props['links']:
                        if 'pops' in l.props:
                            if l.props['pops'][0].name == pop.name or l.props['pops'][1].name == pop.name:
                                outVlan = l.props['vlan']
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

        sampleFlowmod = FlowMod.create(swScope, swSwitch, {'dl_dst':inMac, 'vlan':inVlan, 'in_port':swInPort}, {})
        sampleFlowmod.props['renderer'] = self
        sampleFlowmod.actions = []
        for (outMac, outVlan, outPort) in outputs:
            sampleFlowmod.actions.append(Action(props={'dl_dst':outMac, 'vlan':outVlan, 'out_port':outPort}))

        # forward to swSwitch
        mod = hwScope.forward(hwSwitch, inMac, inVlan, inPort, inMac, inVlan, stitchedInPort)
        flowmods.append(mod)

        if tapped:
            status = 'TappedBroadcast'
        else:
            status = 'UntappedBroadcast'
        flowStatus = FlowStatus(flowEntry, status, flowmods)
        flowStatus.props['sampleFlowmod'] = sampleFlowmod
        self.props['statusIndex'][flowEntry.key()] = flowStatus
        return FlowEntry(inMac, inVlan, stitchedInPort)

    def tapBroadcastEntry(self, flowEntry):
        """
        This method might be invoked when tapsite or tapmac/host happens.
        An broadcast entry would be tapped if:
            1. any local site is in tappedSites, or
            2. any local mac is in tappedMacs
        Some scenarios might be:
        When we receive an broadcast entry (mac, vlan, port) satisfying the
        criteria listed above, it is tapped.
        When we tap a local site, we tap all local broadcast entries.
        When we tap a local mac, we tap all local broadcast entries.

        flowStatus.props['flowmods'] in result:
         [0:N]: N forwarding from swSwitch to coreRouter in hwSwitch
         [-M:-2]: M copying to serviceVm and dispatching in swSwitch (multicast)
         [-1]: forwarding from coreRouter to swSwitch in hwSwitch
        """
        k = flowEntry.key()
        print "tapBroadcastEntry with k " + k
        if not k in self.props['statusIndex']:
            return self.createBroadcastEntry(flowEntry, True)

        flowStatus = self.props['statusIndex'][k]
        result = flowStatus.props['flowmods'][-1].getOutFlowEntry()
        if flowStatus.props['status'] == "TappedBroadcast":
            return result

        SDNPopsRenderer.logger.info("%r.tapBroadcastEntry(%r)" % (self.name, flowEntry))
        inPort = flowEntry.port
        outPort = result.port
        swSwitch = outPort.props['node'].props['pop'].props['swSwitch']
        swScope = self.props['scopeIndex'][swSwitch.name]
        if inPort.props['type'].endswith('.WAN'):
            vmPort = swSwitch.props['vmPort.WAN']
        else:
            vmPort = swSwitch.props['vmPort']
        # copy to serviceVm
        for flowmod in flowStatus.props['broadcastFlowmods']:
            swScope.copy(flowmod, vmPort)

        flowStatus.props['status'] = "TappedBroadcast"
        return result

    def untapBroadcastEntry(self, flowEntry):
        """
        This method might be invoked when untapsite or untapmac/host happens.
        An broadcast entry would be untapped if:
            1. no local site in tappedSites, or
            2. no local mac is in tappedMacs
        Some scenarios might be:
        When we receive an broadcast entry (mac, vlan, port) satisfying the
        criteria listed above, it is tapped.
        When we untap a site, if it's the last local site in tappedSites and no
        local mac is in tappedMacs, we untap all local broadcast entries.
        When we untap a mac, if it's the last local mac in tappedMacs and no
        local site is in tappedSites, we untap all local broadcast entries.

        flowStatus.props['flowmods'] in result:
         [0:N]: forwarding from swSwitch to coreRouter in hwSwitch
         [-2]: dispatching in swSwitch (multicast)
         [-1]: forwarding from coreRouter to swSwitch in hwSwitch
        """
        k = flowEntry.key()
        print "untapBroadcastEntry with k " + k
        if not k in self.props['statusIndex']:
            print "  not in index"
            return self.createBroadcastEntry(flowEntry, False)

        flowStatus = self.props['statusIndex'][k]
        result = flowStatus.props['flowmods'][-1].getOutFlowEntry()
        if flowStatus.props['status'] == "UntappedBroadcast":
            return result

        SDNPopsRenderer.logger.info("%s.untapBroadcastEntry(%s)" % (self.name, flowEntry))

        inPort = flowEntry.port
        outPort = result.port
        swSwitch = outPort.props['node'].props['pop'].props['swSwitch']
        swScope = self.props['scopeIndex'][swSwitch.name]
        if inPort.props['type'].endswith('.WAN'):
            vmPort = swSwitch.props['vmPort.WAN']
        else:
            vmPort = swSwitch.props['vmPort']

        # stop copying to serviceVm
        for flowmod in flowStatus.props['broadcastFlowmods']:
            flowmod.scope.restore(flowmod)

        flowStatus.props['status'] = "UntappedBroadcast"
        return result

    def tapSiteCLI(self, site):
        # Invoked from CLI.
        with self.lock:
            self.tapSite(site)
    def untapSiteCLI(self, site):
        # Invoked from CLI.
        with self.lock:
            self.untapSite(site)
    def tapHostCLI(self, host):
        # Invoked from CLI.
        with self.lock:
            self.tapMac(host.props['mac'])
    def untapHostCLI(self, host):
        # Invoked from CLI.
        with self.lock:
            self.untapMac(host.props['mac'])

    def tapMacCLI(self, mac):
        # Invoked from CLI.
        with self.lock:
            self.tapMac(mac)

    def untapMacCLI(self, mac):
        # Invoked from CLI.
        with self.lock:
            self.untapMac(mac)

    @staticmethod
    def untapMacTimer(vpnname, mac):
        try:
            """
            Note: During the period before timeout, anything could happen including the SDNPopsRender might be outdated.
            If you want to get rid of error messages, you might have to:
              1. make sure self (SDNPopsRenderer) is still alive
              2. make sure mac is still in siteIndex
              ...etc
            """
            SDNPopsRenderer.logger.info("time's up to untap the mac %s in %s" % (mac, vpnname))
            if not vpnname in SDNPopsRenderer.index:
                SDNPopsRenderer.logger.warning("vpn %s no longer exists" % vpnname)
                return
            SDNPopsRenderer.index[vpnname].untapMacCLI(mac)
        except:
            exc = sys.exc_info()
            SDNPopsRenderer.logger.error("%r %r" % (exc[0], exc[1]))
            tb = exc[2]
            while tb:
                SDNPopsRenderer.logger.error("%r %r" % (tb.tb_frame.f_code, tb.tb_lineno))
                tb = tb.tb_next

    def tapMac(self, mac):
        if not str(mac) in self.props['siteIndex']:
            SDNPopsRenderer.logger.warning("The mac %r on VPN %s not exists" % (mac, self.vpn.name))
            return
        if mac in self.props['tappedMacs']:
            SDNPopsRenderer.logger.warning("The mac %r on VPN %s has been tapped" % (mac, self.vpn.name))
            return

        # update tappedMacs, tappedSites, and tappedSitesWithSrcMac
        self.addTappedMac(mac)

        site = self.getDstSite(mac)
        for flowEntry in self.getFlowEntries(site):
            self.parseFlowEntry(flowEntry)

    def untapMac(self, mac):
        if not mac in self.props['tappedMacs']:
            SDNPopsRenderer.logger.warning("The mac %r on VPN %s is not tapped yet" % (mac, self.vpn.name))
            return

        # update tappedMacs and tappedSitesWithSrcMac
        self.props['tappedMacs'].remove(mac)
        site = self.getDstSite(mac)
        self.props['tappedMacsIndex'][site.name].remove(mac)
        if not self.props['tappedMacsIndex'][site.name]:
            self.props['tappedSitesWithSrcMac'].remove(site)

        site = self.getDstSite(mac)
        for flowEntry in self.getFlowEntries(site):
            self.parseFlowEntry(flowEntry)

    def tapSite(self, site):
        if site in self.props['tappedSites']:
            SDNPopsRenderer.logger.warning("The site %s on VPN %s has been tapped" % (site.name, self.vpn.name))
            return
        # update tappedSites
        self.props['tappedSites'].append(site)

        for flowEntry in self.getFlowEntries(site):
            self.parseFlowEntry(flowEntry)

    def untapSite(self, site):
        if not site in self.props['tappedSites']:
            SDNPopsRenderer.logger.warning("The site %s on VPN %s is not tapped yet" % (site.name, self.vpn.name))
            return
        # update tappedSites
        self.props['tappedSites'].remove(site)

        for flowEntry in self.getFlowEntries(site):
            self.parseFlowEntry(flowEntry)

    def addSite(self, site, link):
        """
        This function could be invoked in CLI.
        Add endpoints related to the site including: HwToCore ports, HwToSw
        ports, SwToHw ports, and the SwToVm port.
        """
        with self.lock:
            pop = site.props['pop']
            if not pop.name in self.props['popIndex']:
                SDNPopsRenderer.logger.warning("The SDNPop of the site is not added yet")
                return False
            siteVlan = link.props['vlan']
            hwSwitch = pop.props['hwSwitch'].props['enosNode']
            hwSwitchScope = self.props['scopeIndex'][hwSwitch.name]
            sitePort = hwSwitch.props['sitePortIndex'][site.name]
            hwSwitchScope.addEndpoint(sitePort, siteVlan)
            swPort = hwSwitch.props['stitchedPortIndex'][sitePort.name]
            hwSwitchScope.addEndpoint(swPort, siteVlan)
            swSwitch = pop.props['swSwitch'].props['enosNode']
            swSwitchScope = self.props['scopeIndex'][swSwitch.name]
            swSwitchScope.addEndpoint(swSwitch.props['sitePortIndex'][site.name], siteVlan)
            # TODO swSwitchScope.addEndpoint(swSwitch.props['vmPort'], siteVlan)
            # XXX Send broadcast packets on hwSwitch, sitePort, siteVlan to controller
            # Where to save the FlowRef?  Maybe put it in the hwSwitchScope, index on port, vlan.
            mac = MACAddress.createBroadcast()
            fe = FlowEntry(mac, siteVlan, sitePort) # mac, vlan, port
            flowRef = hwSwitch.props['controller'].initControllerFlow(hwSwitch, fe)
            bcastKey = sitePort.name + "." + str(siteVlan)
            hwSwitchScope.props['toControllerFlowRefs'][bcastKey] = flowRef
            return True

    def delSite(self, site):
        """
        This function could be invoked in CLI.
        Del endpoints related to the site including: HwToCore ports, HwToSw
        ports, SwToHw ports, and the SwToVm port.
        """
        with self.lock:
            if not site.name in self.vpn.props['participantIndex']:
                SDNPopsRenderer.logger.warning("The site did not participate in the VPN")
                return False
            # clean up all flowEntries related to the site
            for status in self.props['statusIndex'].values():
                flowEntry = status.props['flowEntry']
                related = False
                (inMac, inVlan, inPort) = flowEntry.get()
                if not related:
                    related = inMac.isBroadcast()
                if not related:
                    if inPort.props['type'].endswith('.WAN'):
                        related = (self.getDstSite(self.reverse(inMac)).name == site.name)
                    else:
                        related = (self.getSrcSite(inVlan, inPort).name == site.name) or (self.getDstSite(inMac).name == site.name)
                if not related:
                    continue
                self.delFlowEntry(flowEntry)

            (_, hosts, siteVlan) = self.vpn.props['participantIndex'][site.name]
            pop = site.props['pop']
            hwSwitch = pop.props['hwSwitch'].props['enosNode']
            hwSwitchScope = self.props['scopeIndex'][hwSwitch.name]
            sitePort = hwSwitch.props['sitePortIndex'][site.name]
            hwSwitchScope.delEndpoint(sitePort, siteVlan)
            swPort = hwSwitch.props['stitchedPortIndex'][sitePort.name]
            hwSwitchScope.delEndpoint(swPort, siteVlan)
            # Clean up broadcast flow entry
            bcastKey = sitePort.name + "." + str(siteVlan)
            if bcastKey in hwSwitchScope.props['toControllerFlowRefs']:
                flowRef = hwSwitchScope.props['toControllerFlowRefs'].pop(bcastKey)
                cont = hwSwitch.props['controller']
                cont.deleteFlow(cont.javaByteArray(hwSwitch.props['dpid']), flowRef)


            swSwitch = pop.props['swSwitch'].props['enosNode']
            swSwitchScope = self.props['scopeIndex'][swSwitch.name]
            swSwitchScope.delEndpoint(swSwitch.props['sitePortIndex'][site.name], siteVlan)
            swSwitchScope.delEndpoint(swSwitch.props['vmPort'], siteVlan)
            return True

    def addPop(self, pop):
        """
        This function could be invoked in CLI.
        Add endpoints related to the pop including: HwToCore.WAN ports,
        HwToSw ports, and SwToHw ports, and the SwToVm.WAN port.
        """
        with self.lock:
            if pop.name in self.props['popIndex']:
                SDNPopsRenderer.logger.warning("The SDNPop is already in the VPN")
                return False
            vid = self.vpn.props['vid']
            hwSwitch = pop.props['hwSwitch'].props['enosNode']
            hwSwitchScope = L2SwitchScope(name='%s.%s' % (self.vpn.name, hwSwitch.name), switch=hwSwitch, owner=self)
            self.props['scopeIndex'][hwSwitch.name] = hwSwitchScope
            hwSwitch.props['controller'].addScope(hwSwitchScope)
            swSwitch = pop.props['swSwitch'].props['enosNode']
            swSwitchScope = L2SwitchScope(name='%s.%s' % (self.vpn.name, swSwitch.name),switch=swSwitch,owner=self)
            # ServiceVM Not yet implemented
            # swSwitchScope.addEndpoint(swSwitch.props['vmPort.WAN'], vid)
            self.props['scopeIndex'][swSwitch.name] = swSwitchScope
            swSwitch.props['controller'].addScope(swSwitchScope)
            for other_pop in self.props['popIndex'].values():
                self.connectPop(pop, other_pop)
                self.connectPop(other_pop, pop)
            self.props['popIndex'][pop.name] = pop

            # Per-switch QOS setup on hardware switch
            # If it's a Corsa we need to push two (or three) meters to the switch.
            # We need to do this every time we start using the switch.  The Corsa driver
            # barfs when trying to push a flow to a meter it doesn't know, even if the
            # meter is already configured, so we're pretty aggressive about setting the
            # meter.  Setting it multiple times doesn't hurt.
            hwSwitch.props['controller'].initQos(hwSwitch)

            # Per-switch QOS setup on software switch
            # This should be a no-op, but put the hooks in here anyway
            swSwitch.props['controller'].initQos(swSwitch)

            return True

    def delPop(self, pop):
        with self.lock:
            if not pop.name in self.props['popIndex']:
                SDNPopsRenderer.logger.warning("The SDNPop did not participate in the VPN yet")
                return False
            for (site, hosts, siteVlan) in self.vpn.props['participants']:
                if site.props['pop'].name == pop.name:
                    SDNPopsRenderer.logger.warning("Some sites in the SDNPop is still in the VPNs, must delete them first")
                    return False
            # XXX Undo per-switch QOS setup on software switch
            # XXX Undo per-switch QOS setup on hardware switch
            # Note this actually a bit challenging because the QOS setup is, right now, per-switch not
            # per VPN/switch.  So we can't get rid of a QOS configuration (i.e. Corsa meter) until
            # the last VPN is done using it.  We need to manage this a bit better, either by putting a
            # refcount on each switch or by assigning meters to be per VPN/switch (i.e. so each meter
            # only used by a single VPN).
            for other_pop in self.props['popIndex'].values():
                if other_pop.name == pop.name:
                    continue
                self.disconnectPop(pop, other_pop)
                self.disconnectPop(other_pop, pop)
            hwSwitch = pop.props['hwSwitch'].props['enosNode']
            hwSwitchScope = self.props['scopeIndex'][hwSwitch.name]
            swSwitch = pop.props['swSwitch'].props['enosNode']
            swSwitchScope = self.props['scopeIndex'][swSwitch.name]
            self.props['popIndex'].pop(pop.name)
            self.props['scopeIndex'].pop(hwSwitch.name)
            self.props['scopeIndex'].pop(swSwitch.name)
            hwSwitch.props['controller'].delScope(hwSwitchScope)
            swSwitch.props['controller'].delScope(swSwitchScope)
            return True

    def connectPop(self, pop1, pop2):
        """
        Connect pop1 to pop2 (one way only)
        Here we use (port, vid) instead of (port, vlan) as the index.
        The reason is that VPNs all share the same port and vlan on the
        'HwToCore.WAN' ports of HwSwitch, so we couldn't dispatch packets
        to the scope based on vlan. The solution is temporary only.
        """
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

    def disconnectPop(self, pop1, pop2):
        """
        Disonnect pop1 to pop2 (one way only)
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
        hwSwitchScope.delEndpoint(tocore_port, vid)
        tocore_port.props['scopeIndex'][vid] = hwSwitchScope

        tosw_port = hwSwitch.props['stitchedPortIndex'][tocore_port.name]
        hwSwitchScope.delEndpoint(tosw_port, vid)
        tosw_port.props['scopeIndex'][vid] = hwSwitchScope

        tohw_port = swSwitch.props['wanPortIndex'][pop2.name]
        swSwitchScope.delEndpoint(tohw_port, vid)
        tohw_port.props['scopeIndex'][vid] = swSwitchScope

    def __str__(self):
        return "SDNPopsRenderer(name=%r,scopeIndex=%r)" % (self.name, self.props['scopeIndex'])

    def __repr__(self):
        return self.__str__()

    def updateSrcMac(self, srcMac, inVlan, inPort):
        # update the information of which site the mac belongs
        if not inPort.props['type'].endswith('.WAN'): # from site
            if not self.getDstSite(srcMac):
                self.props['siteIndex'][str(srcMac)] = self.getSrcSite(inVlan, inPort)
                # a new srcMac is detected, try to tap it for a while
                SDNPopsRenderer.logger.info("New mac %s is detected" % srcMac)
                if self.props['timeout'] > 0:
                    self.tapMac(srcMac)
                    threading.Timer(self.props['timeout'], SDNPopsRenderer.untapMacTimer, [self.vpn.name, srcMac]).start()

    def swSwitchEventListener(self, event):
        # no lock because it's locked in eventListener already
        # find the matched inPort in hwSwitch
        srcMac = event.props['dl_src']
        dstMac = event.props['dl_dst']
        inVlan = event.props['vlan']
        swInPort = event.props['in_port'].props['enosPort']
        swSwitch = swInPort.props['node'].props['enosNode']
        if swInPort.props['type'].endswith('.WAN'):
            vmPort = swSwitch.props['vmPort.WAN']
        else:
            vmPort = swSwitch.props['vmPort']
        myPop = swSwitch.props['pop']
        hwSwitch = myPop.props['hwSwitch']
        link = swInPort.props['links'][0]
        hwPort = link.props['portIndex'][hwSwitch.name]
        hwInPort = hwSwitch.props['stitchedPortIndex'][hwPort.name]
        self.updateSrcMac(srcMac, inVlan, hwInPort)

        controller = swSwitch.props['controller']
        swScope = controller.getScope(swInPort, inVlan, dstMac)
        etherType = event.props['ethertype']
        payload = event.props['payload']
        flowEntry = FlowEntry(dstMac, inVlan, hwInPort)
        if not flowEntry.key() in self.props['statusIndex']:
            SDNPopsRenderer.logger.warning("Unknown packet %s received by swSwitch %s" % (event, swSwitch.name))
            return
        flowStatus = self.props['statusIndex'][flowEntry.key()]
        mod = flowStatus.addMac(srcMac, vmPort)
        swScope.addFlowMod(mod)
        sampleFlowmod = flowStatus.props['sampleFlowmod']
        for action in sampleFlowmod.actions:
            outMac = action.props['dl_dst']
            outVlan = action.props['vlan']
            outPort = action.props['out_port']
            swScope.send(swSwitch, outPort, srcMac, outMac, etherType, outVlan, payload)

    def eventListener(self,event):
        """
        The implementation of this class is expected to overwrite this method if it desires
        to receive events from the controller such as PACKET_IN
        :param event: ScopeEvent

        When receiving an event:
        1. check if the src exists already; if not, update the information which site the src belongs.
        2. add flow entry and flow status corespondingly
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
            if not inPort.props['type'].startswith('HwToCore'):
                # Then this should be a broadcast packet received by swSwitch
                # a special case to handle broadcast issues
                self.swSwitchEventListener(event)
                return

            inVlan = event.props['vlan']
            flowEntry = FlowEntry(dstMac, inVlan, inPort)
            inSite = self.getSrcSite(inVlan, inPort)
            switch = inPort.props['node'].props['enosNode']
            myPop = switch.props['pop']
            controller = switch.props['controller']
            scope = controller.getScope(inPort, inVlan, dstMac)
            etherType = event.props['ethertype']
            payload = event.props['payload']

            self.updateSrcMac(srcMac, inVlan, inPort)

            outFlowEntry = self.parseFlowEntry(flowEntry)
            if not outFlowEntry:
                # unknown destination
                return
            (outMac, outVlan, outPort) = outFlowEntry.get()
            scope.send(switch, outPort, srcMac, outMac, etherType, outVlan, payload)

    def parseFlowEntry(self, flowEntry):
        (inMac, inVlan, inPort) = flowEntry.get()
        switch = inPort.props['node'].props['enosNode'] # must be hwSwitch
        myPop = switch.props['pop']
        if inPort.props['type'].endswith('.WAN'): # from WAN
            transMac = inMac
            originalMac = self.reverse(transMac)
        else: # from Site
            originalMac = inMac
            transMac = self.translate(originalMac)
        if inMac.isBroadcast():
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
        else: # single-cast to local site
            toSite = self.getDstSite(originalMac)
            if not toSite:
                SDNPopsRenderer.logger.warning("unknown destination %s" % originalMac)
                return None
            if inPort.props['type'].endswith('.WAN'): # from WAN
                if originalMac in self.props['tappedMacs']:
                    outFlowEntry = self.tapEntry(flowEntry)
                elif toSite in self.props['tappedSites']:
                    outFlowEntry = self.tapEntry(flowEntry)
                else:
                    outFlowEntry = self.untapEntry(flowEntry)
            else: # from site
                inSite = self.getSrcSite(inVlan, inPort)
                if toSite.props['pop'].name == myPop.name:
                    # from site to site
                    if inSite in self.props['tappedSites'] or toSite in self.props['tappedSites'] or originalMac in self.props['tappedMacs']:
                        outFlowEntry = self.tapEntry(flowEntry)
                    elif inSite in self.props['tappedSitesWithSrcMac'] or toSite in self.props['tappedSitesWithSrcMac']:
                        outFlowEntry = self.tapEntryWithSrcMac(flowEntry)
                    else:
                        outFlowEntry = self.untapEntry(flowEntry)
                else:
                    # from site to WAN
                    if inSite in self.props['tappedSites']:
                        outFlowEntry = self.tapEntry(flowEntry)
                    elif inSite in self.props['tappedSitesWithSrcMac']:
                        outFlowEntry = self.tapEntryWithSrcMac(flowEntry)
                    else:
                        outFlowEntry = self.untapEntry(flowEntry)
        return outFlowEntry

    def translate(self, mac):
        return self.vpn.props['mat'].translate(mac)
    def reverse(self, trans_mac):
        hid = trans_mac.getHid()
        return self.vpn.props['mat'].reverse(hid)

    def execute(self):
        """
        Renders the intent.
        :return: Expectation when succcessful, None otherwise
        """
        # update graph
        self.intent.updateGraph()
        return True

        """
        The code is commented out because the scope has been added into the
        controller already while 'vpn addsite'.
        """
        # # Add scopes to the controller
        # for scope in self.props['scopeIndex'].values():
        #     if not scope.switch.props['controller'].addScope(scope):
        #         print "Cannot add", scope
        #         return False
        # self.active = True
        # return True

    def clean(self):
        if len(self.props['popIndex']) != 0:
            SDNPopsRenderer.logger.warning("There are some Pops still in the VPN")
            return False
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
        """
        :param vpn: VPN which contains information of participants (site and hosts)
        :param wan: Wan which contains information of all links in WAN
        """
        super(SDNPopsIntent, self).__init__(name=name, graph=None)
        self.vpn = vpn
        self.wan = wan
        self.updateGraph() # pops, nodes, links, graph, props['topology']
    def updateGraph(self):
        """
        Creates a provisioning intent providing a GenericGraph of the logical view of the
        topology that is intended to be created.
        """
        pops = []
        nodes = []
        links = []
        for participant in self.vpn.props['participants']:
            (site, hosts_in_site, siteVlan) = participant
            pop = site.props['pop']
            hwSwitch = pop.props['hwSwitch']
            coreRouter = pop.props['coreRouter']
            serviceVm = pop.props['serviceVm']
            if not pop in pops:
                pops.append(pop)
                nodes.append(coreRouter)
                nodes.append(hwSwitch)
                nodes.append(pop.props['swSwitch'])
                nodes.append(serviceVm)
            # note: nodes and links will be translated to enosNode later
            nodes.append(site.props['siteRouter'])
            nodes.extend(hosts_in_site)
            # links (siteLink and wanLink) between serviceVm and swSwitch
            links.extend(map(lambda vmPort:vmPort.props['links'][0], serviceVm.props['ports'].values()))
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


