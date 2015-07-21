from array import array
import binascii

from common.intent import ProvisioningRenderer, ProvisioningIntent
from common.api import Site, Properties
from common.openflow import ScopeOwner,PacketInEvent, FlowMod, Match, Action, L2SwitchScope, PacketOut, SimpleController
from odl.client import ODLClient

from mininet.enos import TestbedTopology, TestbedHost, TestbedNode, TestbedPort, TestbedLink

from net.es.netshell.api import GenericGraph, GenericHost
from common.mac import MACAddress
from common.utils import Logger
import threading

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

        self.macs = {}
        self.active = False
        self.activePorts = {}
        self.siteEvents = {} # [site.name] = list of dl_src
        self.popEvents = {} # [pop.name] = list of dl_src
        self.flowmodByEvent = [] # list of flowmods
        self.flowmodIndex = {} # [FlowMod.key()] = FlowMod
        self.siteIndex = {} # [str(mac)] = site
        self.links = self.intent.links
        SDNPopsRenderer.instance = self
        self.props['scopeIndex'] = {} # [hwSwitch.name or swSwitch.name] = scope

    def tap(self, site):
        pop = site.props['pop']
        hwSwitch = pop.props['hwSwitch'].props['enosNode']
        scope = self.props['scopeIndex'][hwSwitch.name]
        with scope.props['lock']:
            if scope.props['tap']:
                SDNPopsRenderer.logger.warning("The site %s on VPN %s has been tapped" % (site.name, self.vpn.name))
                return
            scope.props['tap'] = True
            controller = scope.switch.props['controller']
            # reset all flowmods on hwSwitch
            for flowmod in scope.props['flowmodIndex'].values():
                if 'dl_src' in flowmod.match.props:
                    # broadcast related
                    continue
                if len(flowmod.actions) == 1 and 'out_port' in flowmod.actions[0].props:
                    outPort = flowmod.actions[0].props['out_port']
                    if outPort.props['type'] == 'HwToCore' or outPort.props['type'] == 'HwToCore.WAN':
                        # replace dispatching flowmods with forwarding ones (to swSwitch)
                        scope.delFlowMod(flowmod)
                        controller.delFlowMod(flowmod)
                        if 'in_port' in flowmod.match.props:
                            inPort = flowmod.match.props['in_port']
                            if inPort.props['type'].endswith('.WAN'):
                                outPort = flowmod.switch.props['stitchedPortIndex.WAN'][inPort.name]
                            else:
                                outPort = flowmod.switch.props['stitchedPortIndex'][inPort.name]
                            flowmod.actions = [Action(props={'out_port':outPort})]
                            scope.addFlowMod(flowmod)
                            controller.addFlowMod(flowmod)

    def untap(self, site):
        pop = site.props['pop']
        hwSwitch = pop.props['hwSwitch'].props['enosNode']
        scope = self.props['scopeIndex'][hwSwitch.name]
        with scope.props['lock']:
            if not scope.props['tap']:
                SDNPopsRenderer.logger.warning("The site %s on VPN %s is not tapped yet" % (site.name, self.vpn.name))
                return
            scope.props['tap'] = False
            controller = scope.switch.props['controller']
            # reset all flowmods on hwSwitch
            for flowmod in scope.props['flowmodIndex'].values():
                if len(flowmod.actions) == 1 and 'out_port' in flowmod.actions[0].props and not 'dl_src' in flowmod.match.props:
                    outPort = flowmod.actions[0].props['out_port']
                    if outPort.props['type'] == 'HwToSw' or outPort.props['type'] == 'HwToSw.WAN':
                        # replace forwarding flowmods (to swSwitch) with dispatching flowmods
                        scope.delFlowMod(flowmod)
                        controller.delFlowMod(flowmod)
                        dl_dst = flowmod.match.props['dl_dst']
                        vlan = flowmod.match.props['vlan']
                        inPort = flowmod.match.props['in_port']
                        # mac: original MAC address
                        if inPort.props['type'].endswith('.WAN'):
                            trans_mac = dl_dst
                            mac = self.reverse(trans_mac)
                        else:
                            mac = dl_dst
                            trans_mac = self.translate(mac)
                        if not str(mac) in self.siteIndex:
                            SDNPopsRenderer.logger.Warning("Unknown mac %r" % mac)
                        site = self.siteIndex[str(mac)]
                        pop = site.props['pop']
                        myPop = hwSwitch.props['pop']
                        if pop.name == myPop.name:
                            outPort = hwSwitch.props['sitePortIndex'][site.name]
                            outVlan = self.vpn.props['participantIndex'][site.name][2]
                            outDst = mac
                        else:
                            outPort = hwSwitch.props['wanPortIndex'][pop.name]
                            outVlan = outPort.props['links'][0].props['vlan']
                            outDst = trans_mac
                        flowmod.actions = [Action(props={'dl_dst': outDst, 'vlan':outVlan, 'out_port':outPort})]
                        scope.addFlowMod(flowmod)
                        controller.addFlowMod(flowmod)

    def addSite(self, site, wanVlan):
        # could be invoked in CLI
        vid = self.vpn.props['vid']
        pop = site.props['pop']
        coreRouter = pop.props['coreRouter'].props['enosNode']
        hwSwitch = pop.props['hwSwitch'].props['enosNode']
        hwSwitchScope = L2SwitchScope(name='%s.%s' % (self.vpn.name, hwSwitch.name), switch=hwSwitch, owner=self)
        hwSwitchScope.props['tap'] = False
        hwSwitchScope.props['lock'] = threading.Lock()
        self.props['scopeIndex'][hwSwitch.name] = hwSwitchScope
        sitePort = hwSwitch.props['sitePortIndex'][site.name]
        hwSwitchScope.addEndpoint(sitePort, wanVlan)
        swPort = hwSwitch.props['stitchedPortIndex'][sitePort.name]
        hwSwitchScope.addEndpoint(swPort, wanVlan)

        swSwitch = pop.props['swSwitch'].props['enosNode']
        swSwitchScope = L2SwitchScope(name='%s.%s' % (self.vpn.name, swSwitch.name),switch=swSwitch,owner=self)
        self.props['scopeIndex'][swSwitch.name] = swSwitchScope
        swSwitchScope.addEndpoint(swSwitch.props['sitePortIndex'][site.name], wanVlan)
        swSwitchScope.addEndpoint(swSwitch.props['vmPortIndex'][self.vpn.name])

        hwSwitch.props['siteVlanIndex'][vid] = wanVlan
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

        tosw_port = hwSwitch.props['stitchedPortIndex.WAN'][tocore_port.name]
        hwSwitchScope.addEndpoint(tosw_port, vid)
        tosw_port.props['scopeIndex'][vid] = hwSwitchScope

        tohw_port = swSwitch.props['wanPortIndex'][pop2.name]
        swSwitchScope.addEndpoint(tohw_port, vid)
        tohw_port.props['scopeIndex'][vid] = swSwitchScope

    def __str__(self):
        return "SDNPopsRenderer(name=%r,scopeIndex=%r,flowmodIndex=%r)" % (self.name, self.props['scopeIndex'], self.flowmodIndex.keys())

    def __repr__(self):
        return self.__str__()

    def eventListener(self,event):
        """
        The implementation of this class is expected to overwrite this method if it desires
        to receive events from the controller such as PACKET_IN
        :param event: ScopeEvent
        """
        if event.__class__ == PacketInEvent:
            # This is a PACKET_IN. Learn the source MAC address
            if not 'vlan' in event.props:
                # no VLAN, reject
                SDNPopsRenderer.logger.info("%r has no vlan, reject by %r" % (event, self))
                return

            dl_src = event.props['dl_src']
            dl_dst = event.props['dl_dst']
            inPort = event.props['in_port'].props['enosPort']
            switch = inPort.props['enosNode']
            vlan = event.props['vlan']
            controller = switch.props['controller']
            scope = controller.getScope(inPort, vlan, dl_dst)
            etherType = event.props['ethertype']
            payload = event.props['payload']
            success = True

            # check if dl_src a new MAC address
            if not inPort.props['type'].endswith('.WAN'):
                if not str(dl_src) in self.siteIndex:
                    # find the site where dl_src comes
                    for participant in self.vpn.props['participants']:
                        (site, hosts, siteVlan) = participant
                        if siteVlan == vlan:
                            self.siteIndex[str(dl_src)] = site
                            break

            if dl_dst.isBroadcast():
                if switch.props['role'] == 'HwSwitch':
                    # forward to swSwitch
                    if inPort.props['type'].endswith('.WAN'):
                        outPort = switch.props['stitchedPortIndex.WAN'][inPort.name]
                    else:
                        outPort = switch.props['stitchedPortIndex'][inPort.name]
                    mod = FlowMod.create(scope, switch, {'dl_src':dl_src,'vlan':vlan,'in_port':inPort,'dl_dst':dl_dst}, {'out_port':outPort})
                    scope.addFlowMod(mod)
                    if not controller.addFlowMod(mod):
                        success = False
                    packet = PacketOut(port=outPort,dl_src=dl_src,dl_dst=dl_dst,etherType=etherType,vlan=vlan,scope=scope,payload=payload)
                    if not controller.send(packet):
                        success = False
                    return success
                elif switch.props['role'] == 'SwSwitch':
                    # broadcast to all participants plus serviceVm
                    mod = FlowMod.create(scope, switch, {'dl_src':dl_src,'vlan':vlan,'in_port':inPort,'dl_dst':dl_dst}, {})
                    actions = []
                    # forward to serviceVm
                    outPort = switch.props['vmPortIndex'][self.vpn.name]
                    actions.append(Action(props={'out_port':outPort}))
                    packet = PacketOut(port=outPort,dl_src=dl_src,dl_dst=dl_dst,etherType=etherType,vlan=vlan,scope=scope,payload=payload)
                    if not controller.send(packet):
                        success = False
                    # forward to all participants
                    myPop = switch.props['pop']
                    if inPort.props['type'].endswith('.WAN'):
                        trans_mac = dl_dst
                        mac = self.reverse(trans_mac)
                    else:
                        mac = dl_dst
                        trans_mac = self.translate(mac)
                    for participant in self.vpn.props['participants']:
                        (site, hosts, siteVlan) = participant
                        pop = site.props['pop']
                        if pop.name == myPop.name:
                            # site and swSwitch are in the same pop
                            outPort = switch.props['sitePortIndex'][site.name]
                            outVlan = siteVlan
                            outDst = mac
                        else:
                            # site is in the other pop
                            outPort = switch.props['wanPortIndex'][pop.name]
                            outVlan = outPort.props['links'][0].props['vlan']
                            outDst = trans_mac
                        if outVlan == vlan and outPort.name == inPort.name:
                            continue
                        actions.append(Action(props={'vlan':outVlan, 'out_port':outPort, 'dl_dst':outDst}))
                        packet = PacketOut(port=outPort,dl_src=dl_src,dl_dst=outDst,etherType=etherType,vlan=outVlan,scope=scope,payload=payload)
                        if not controller.send(packet):
                            success = False
                    mod.actions = actions
                    scope.addFlowMod(mod)
                    if not controller.addFlowMod(mod):
                        success = False
                return success
            # else not broadcast

            if switch.props['role'] == 'HwSwitch':
                with scope.props['lock']:
                    if scope.props['tap']:
                        # forward to swSwitch (from coreRouter) or to coreRouter (from swSwitch)
                        if inPort.props['type'].endswith('.WAN'):
                            outPort = switch.props['stitchedPortIndex.WAN'][inPort.name]
                        else:
                            outPort = switch.props['stitchedPortIndex'][inPort.name]
                        mod = FlowMod.create(scope, switch, {'dl_dst':dl_dst,'vlan':vlan,'in_port':inPort}, {'out_port':outPort})
                        scope.addFlowMod(mod)
                        if not controller.addFlowMod(mod):
                            success = False
                        packet = PacketOut(port=outPort,dl_src=dl_src,dl_dst=dl_dst,etherType=etherType,vlan=vlan,scope=scope,payload=payload)
                        if not controller.send(packet):
                            success = False
                        return
            # else not tap or swSwitch: try to dispatch to the right port

            # mac = original (untranslated) mac address
            site_to_site = True
            if inPort.props['type'].endswith('.WAN'): # from WAN
                mac = self.reverse(dl_dst)
                site_to_site = False
            else: # from Site
                mac = dl_dst
            if not str(mac) in self.siteIndex:
                SDNPopsRenderer.logger.warning("unknown dl_dst %r" % dl_dst)
                return
            site = self.siteIndex[str(mac)]
            pop = site.props['pop']
            myPop = switch.props['pop']
            if pop.name == myPop.name: # to Site
                outPort = switch.props['sitePortIndex'][site.name]
                outVlan = self.vpn.props['participantIndex'][site.name][2] # siteVlan
                outDst = mac
            else: # to WAN
                outPort = switch.props['wanPortIndex'][pop.name]
                outVlan = outPort.props['links'][0].props['vlan']
                outDst = self.translate(mac)
                site_to_site = False
            mod = FlowMod.create(scope, switch, {'dl_dst':dl_dst,'vlan':vlan,'in_port':inPort})
            actions = []
            if switch.props['role'] == 'SwSwitch':
                # forward to serviceVm
                vmPort = switch.props['vmPortIndex'][self.vpn.name]
                action = Action(props={'out_port':vmPort})
                actions.append(action)
                packet = PacketOut(port=vmPort,dl_src=dl_src,dl_dst=outDst,etherType=etherType,vlan=outVlan,scope=scope,payload=payload)
                if not controller.send(packet):
                    success = False
            # dispatch to responding port
            action = Action(props={'vlan':outVlan, 'out_port':outPort})
            if not site_to_site:
                # Note: wan_to_wan should be a impossible case; 
                # Therefore, only site_to_site case would remain dl_dst.
                action.update({'dl_dst':outDst})
            packet = PacketOut(port=outPort,dl_src=dl_src,dl_dst=outDst,etherType=etherType,vlan=outVlan,scope=scope,payload=payload)
            if not controller.send(packet):
                success = False
            actions.append(action)
            mod.actions = actions
            scope.addFlowMod(mod)
            if not controller.addFlowMod(mod):
                success = False
            return success

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
        """
        Creates a provisioning intent providing a GenericGraph of the logical view of the
        topology that is intended to be created.
        :param vpn: VPN which contains information of participants (site and hosts)
        :param wan: Wan which contains information of all links in WAN
        """
        pops = []
        hosts = []
        for participant in vpn.props['participants']:
            (site, hosts_in_site, wanVlan) = participant
            pop = site.props['pop']
            pops.append(pop)
            # note: hosts will be translated to enosNode later
            hosts.append(site.props['siteRouter'])
            hosts.extend(hosts_in_site)
            hosts.append(pop.props['coreRouter'])
            hosts.append(pop.props['hwSwitch'])
            hosts.append(pop.props['swSwitch'])
            hosts.extend(vpn.props['serviceVms'])

        # filter links between pops in this VPN
        coreRouters = map(lambda pop : pop.props['coreRouter'], pops)
        links = filter(lambda link : link.props['endpoints'][0].props['node'] in coreRouters and link.props['endpoints'][1].props['node'] in coreRouters, wan.props['links'])
        vlans = map(lambda link : link.props['vlan'], links)
        # only keep those whose vlan is interested by the VPN
        links = filter(lambda link : link.props['vlan'] in vlans, wan.props['links'])

        links.extend(vpn.props['links']) # vm - sw
        for participant in vpn.props['participants']:
            (site, hosts_in_site, wanVlan) = participant
            siteRouter = site.props['siteRouter']
            for host in hosts_in_site:
                port = host.props['ports'][1] # assume only one port in the host
                link = port.props['links'][0] # assume only one link in the port
                links.append(link)
            # find the link between siteRouter and borderRouter
            port = siteRouter.props['toWanPort']
            link = port.props['links'][0] # assume only one link in the port
            links.append(link)
            # find the link stitched with the site
            hwSwitch = site.props['pop'].props['hwSwitch']
            links.append(hwSwitch.props['toSwSwitchLink'])
            links.append(hwSwitch.props['toSwSwitchLink.WAN'])
        links.extend(wan.subsetLinks(pops))

        enosHosts = map(lambda host : host.props['enosNode'], hosts)
        enosLinks = map(lambda host : host.props['enosLink'], links)
        self.vpn = vpn
        self.wan = wan
        self.pops = pops
        self.hosts = enosHosts
        self.links = enosLinks
        self.graph = self.getGraph()
        ProvisioningIntent.__init__(self,name=name,graph=self.graph)

    def getGraph(self):
        graph = GenericGraph()

        for host in self.hosts:
            graph.addVertex(host)

        for link in self.links:
            node1 = link.getSrcNode()
            node2 = link.getDstNode()
            graph.addEdge(node1,node2,link)
        return graph


