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
        self.flowmodIndex = {} # [FlowMod.key()] = FlowMod
        self.backupFlowmodIndex = {} # [FlowMod.key()] = FlowMod
        self.links = self.intent.links
        self.linkByPort = {}
        SDNPopsRenderer.instance = self
        self.scopeIndex = {} # [hwSwitch.name or swSwitch.name] = scope
        self.tapsOnHwSwitch = set() # hwSwitch.name

    def tapFlowMod(self, flowmod):
        """
        Create two types of flowmods: one is to redirect the flow to swSwitch;
        the other is to dispatch the flow from swSwitch.
        For example:
        If the flowmod = {match:{dst:tm1},action:{vlan:11,dst:hm1,port:1}},
        then add a set of flowmods = {match:{tm1,port:3*},action={port:4}} to
        forwarding interested flow to swSwitch,
        and add a new flowmod = {match:{tm1},action={vlan:11,dst:hm1,port:1}}
        to handle flows from swSwitch.
        (hm1: mac address of host 1)
        (tm1: translated mac address of host 1)

        Another example:
        If the flowmod = {match:{dst:hm2,vlan:12},action:{dst:tm2,vlan:1000,port:3}},
        then add a new flowmod = {match:{dst:hm2,vlan:12,port:1},action:{port:2}} to swSwitch,
        and add a new flowmod = {match:{dst:hm2,vlan:12,port:2},action:{dst:tm2,vlan:1000,port:3}}
        """
        success = True
        scope = flowmod.scope
        hwSwitch = scope.switch
        controller = scope.switch.props['controller']

        wanToSite = flowmod.actions[0].props['out_port'].props['type'] == 'HwToCore'
        # create a set of flowmod with match = original match, action = forwarding to swSwitch
        in_ports = []
        if wanToSite:
            for in_port in hwSwitch.getPorts():
                if in_port.props['type'] == 'HwToCore.WAN':
                    in_ports.append(in_port)
            sw_port = hwSwitch.props['toSwSwitchPort.WAN'].props['enosPort']
        else:
            for in_port in hwSwitch.getPorts():
                if in_port.props['type'] == 'HwToCore':
                    in_ports.append(in_port)
            sw_port = hwSwitch.props['toSwSwitchPort'].props['enosPort']

        for port in in_ports:
            name = "%s.toSwSwitch" % flowmod.name
            mod = FlowMod(name=name, scope=scope, switch=flowmod.switch)
            mod.props['renderer'] = self
            match = Match(name=name)
            match.update(flowmod.match.props)
            match.props['in_port'] = port
            action = Action(name=name)
            action.props['out_port'] = sw_port
            mod.match = match
            mod.actions = [action]
            if scope.checkFlowMod(mod):
                SDNPopsRenderer.logger.debug("%r existed already" % mod)
                return
            scope.addFlowMod(mod)
            if not controller.addFlowMod(mod):
                success = False

        # create a new flowmod to dispatch packets from swSwitch
        name = "%s.fromSwSwitch" % flowmod.name
        mod = FlowMod(name=name, scope=scope, switch=flowmod.switch)
        mod.props['renderer'] = self
        match = Match(name=name)
        match.update(flowmod.match.props)
        match.props['in_port'] = sw_port
        action = Action(name=name)
        action.update(flowmod.actions[0].props)
        mod.match = match
        mod.actions = [action]
        if scope.checkFlowMod(mod):
            SDNPopsRenderer.logger.debug("%r existed already" % mod)
            return
        scope.addFlowMod(mod)
        if not controller.addFlowMod(mod):
            success = False
        return success

    def tap(self, site):
        pop = site.props['pop']
        hwSwitch = pop.props['hwSwitch'].props['enosNode']
        if hwSwitch.name in self.tapsOnHwSwitch:
            SDNPopsRenderer.logger.warning("The site %s on VPN %s has been tapped" % (site.name, self.vpn.name))
            return
        self.tapsOnHwSwitch.add(hwSwitch.name)
        scope = self.scopeIndex[hwSwitch.name]
        controller = scope.switch.props['controller']
        # reset all flowmods on hwSwitch
        self.backupFlowmodIndex = {}
        for flowmod in scope.props['flowmodIndex'].values():
            scope.delFlowMod(flowmod)
            controller.delFlowMod(flowmod)
            self.backupFlowmodIndex[flowmod.key()] = flowmod
        for flowmod in self.backupFlowmodIndex.values():
            self.tapFlowMod(flowmod)

    def untap(self, site):
        pop = site.props['pop']
        hwSwitch = pop.props['hwSwitch'].props['enosNode']
        if not hwSwitch.name in self.tapsOnHwSwitch:
            SDNPopsRenderer.logger.warning("The site %s on VPN %s has been untapped" % (site.name, self.vpn.name))
            return
        self.tapsOnHwSwitch.remove(hwSwitch.name)
        scope = self.scopeIndex[hwSwitch.name]
        controller = scope.switch.props['controller']
        # reset all flowmods on hwSwitch
        for flowmod in scope.props['flowmodIndex'].values():
            scope.delFlowMod(flowmod)
            controller.delFlowMod(flowmod)
        for flowmod in self.backupFlowmodIndex.values():
            scope.addFlowMod(flowmod)
            controller.addFlowMod(flowmod)
        self.backupFlowmodIndex = {}

    def addSite(self, site, wanVlan):
        vid = self.vpn.props['vid']
        pop = site.props['pop']
        coreRouter = pop.props['coreRouter'].props['enosNode']
        hwSwitch = pop.props['hwSwitch'].props['enosNode']
        hwSwitchScope = L2SwitchScope(name='%s.%s' % (self.vpn.name, hwSwitch.name), switch=hwSwitch, owner=self)
        self.scopeIndex[hwSwitch.name] = hwSwitchScope
        sitePort = hwSwitch.props['sitePortIndex'][site.name]
        hwSwitchScope.addEndpoint(sitePort, wanVlan)
        hwSwitchScope.addEndpoint(hwSwitch.props['toSwSwitchPort'], wanVlan)
        hwSwitchScope.addEndpoint(hwSwitch.props['toSwSwitchPort.WAN'], vid)

        swSwitch = pop.props['swSwitch'].props['enosNode']
        swSwitchScope = L2SwitchScope(name='%s.%s' % (self.vpn.name, swSwitch.name),switch=swSwitch,owner=self)
        self.scopeIndex[swSwitch.name] = swSwitchScope
        swSwitchScope.addEndpoint(swSwitch.props['toHwSwitchPort'], wanVlan)
        swSwitchScope.addEndpoint(swSwitch.props['toHwSwitchPort.WAN'], vid)

        hwSwitch.props['siteVlanIndex'][vid] = wanVlan
        controller = hwSwitch.props['controller']

        pop = hwSwitch.props['pop']
        for other_pop in self.pops:
            """
            Here we use (port, vid) instead of (port, vlan) as the index.
            The reason is that VPNs all share the same port and vlan on the
            'HwToCore.WAN' ports of HwSwitch, so we couldn't dispatch packets
            to the scope based on vlan. The solution is temporary only.
            """
            link1 = hwSwitch.props['nextHop'][other_pop.name]
            port1 = link1.props['portIndex'][hwSwitch.name]
            hwSwitchScope.addEndpoint(port1, vid)
            port1.props['scopeIndex'][vid] = hwSwitchScope

            hwSwitch2 = other_pop.props['hwSwitch']
            hwScope2 = self.scopeIndex[hwSwitch2.name]
            link2 = hwSwitch2.props['nextHop'][pop.name]
            port2 = link2.props['portIndex'][hwSwitch2.name]
            hwScope2.addEndpoint(port2, vid)
            port2.props['scopeIndex'][vid] = hwScope2
        self.pops.append(pop)

    def __str__(self):
        return "SDNPopsRenderer(name=%r,scopeIndex=%r,flowmodIndex=%r)" % (self.name, self.scopeIndex, self.flowmodIndex.keys())

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
            mac = dl_src
            in_port = event.props['in_port'].props['enosPort']
            switch = in_port.props['enosNode']
            vlan = event.props['vlan']
            controller = switch.props['controller']
            scope = controller.getScope(in_port, vlan, dl_dst)
            etherType = event.props['ethertype']
            success = True

            if switch.props['role'] == 'SwSwitch':
                """
                Here we can filter interested flow in upper layer (eg. HTTPS
                packets) based on the packet, and send to serviceVm

                Note: We didn't add any flowmod to swSwitch so that it could
                monitor all flows. This hack should be fixed by complying
                OpenFlow 1.3 (use group, table, ...etc to tap a flow)
                """
                interested = False
                if interested:
                    pass

                # sendback to hwSwitch
                packet = PacketOut(port=in_port,dl_src=dl_src,dl_dst=dl_dst,etherType=etherType,vlan=vlan,scope=scope,payload=event.props['payload'])
                res = controller.send(packet)
                if not res:
                    SDNPopsRenderer.logger.warning("Cannot send packet %r" % packet)
                return

            #if not mac in self.macs:
            if True:
                # self.macs[mac.str()] = (dl_src,in_port)
                # set the flow entry to forward packet to that MAC to this port
                success = self.setMAC(port=in_port,switch=switch,scope=scope,vlan=vlan,mac=mac)
                if not success:
                    SDNPopsRenderer.logger.warning("Cannot set MAC %r on %s.%d" % (mac, in_port.name, vlan))
            if dl_dst.isBroadcast():
                success = self.broadcast(inPort=in_port,switch=switch,scope=scope,inVlan=vlan,srcMac=mac,dstMac=dl_dst,etherType=etherType,payload=event.props['payload'])
                if not success:
                    print  "Cannot send broadcast packet"

    def translate(self, mac):
        return self.vpn.props['mat'].translate(mac)
    def reverse(self, trans_mac):
        hid = trans_mac.getHid()
        return self.vpn.props['mat'].reverse(hid)

    def broadcast(self,inPort,inVlan,srcMac,dstMac,etherType,payload,switch,scope) :

        switchController = switch.props['controller']
        switch = inPort.props['enosNode']
        scope = switchController.getScope(inPort, inVlan, dstMac)
        success = True
        endpoints = scope.props['endpoints']
        if inPort.props['type'] == 'HwToCore':
            # from site, broadcast to WANs
            vid = self.vpn.props['vid']
            lanVlan = self.vpn.props['lanVlan']
            dstMac = MACAddress.createBroadcast(vid)
            in_pop = switch.props['pop']
            hwSwitch = in_pop.props['hwSwitch']
            for participant in self.vpn.props['participants']:
                (site, hosts, wanVlan) = participant
                pop = site.props['pop']
                if pop == in_pop:
                    continue
                link = hwSwitch.props['nextHop'][pop.name]
                port = link.props['portIndex'][hwSwitch.name]
                vlan = port.props['vlan']
                packet = PacketOut(port=port, dl_src=srcMac, dl_dst=dstMac,etherType=etherType,vlan=vlan,scope=scope,payload=payload)
                if SDNPopsRenderer.debug:
                    print packet
                res = switchController.send(packet)
                if not res:
                    SDNPopsRenderer.logger.warning('switchController.send(%r) fail' % packet)
                    success = False
        elif inPort.props['type'] == 'HwToCore.WAN':
            # from WAN, broadcast to site
            assert(dstMac.getVid() == self.vpn.props['vid'])
            vid = self.vpn.props['vid']
            if not vid in switch.props['siteVlanIndex']:
                SDNPopsRenderer.logger.warning('get unknown vid %r' % vid)
                return False
            vlan = switch.props['siteVlanIndex'][vid]
            dstMac = self.reverse(dstMac) # 0xFF{vid}FFFF => 0xFFFFFFFFFFFF
            vpn = self.vpn
            link = switch.props['toCoreRouter'][0] # always choose the first link
            port = link.props['portIndex'][switch.name]
            packet = PacketOut(port=port,dl_src=srcMac,dl_dst=dstMac,etherType=etherType,vlan=vlan,scope=scope,payload=payload)
            if SDNPopsRenderer.debug:
                print packet
            res = switchController.send(packet)
            if not res:
                SDNPopsRenderer.logger.warning('switchController.send(%r) fail' % packet)
                success = False
        return success


    def setMAC(self,port,vlan, mac,switch,scope):
        if SDNPopsRenderer.debug:
            print "SDNPopsRenderer: Set flow entries for MAC= " + mac.str() + " switch=" + switch.name + " port= " + port.name + " vlan= " + str(vlan)

        controller = switch.props['controller']
        success = True

        mod = FlowMod(name=scope.name,scope=scope,switch=switch)
        mod.props['renderer'] = self
        match = Match(name=scope.name)
        # check if the packet is from the site or the core
        if port.props['type'] == 'HwToCore':
            # set the flowmod = {match:{dst:trans_mac}, action:{dst:mac}}
            match_mac = self.translate(mac)
            action_mac = mac
        elif port.get('type') == 'HwToCore.WAN':
            # set the flowmod = {match:{dst:mac}, action:{dst:trans_mac}}
            match.props['vlan'] = switch.props['siteVlanIndex'][self.vpn.props['vid']]
            match_mac = mac
            action_mac = self.translate(mac)
        else:
            SDNPopsRenderer.logger.warning('setMAC fail for the packet is from the port with unknown type')
            return False
        match.props['dl_dst'] = match_mac
        action = Action(name=scope.name)
        action.props['out_port'] = port
        action.props['vlan'] = vlan
        action.props['dl_dst'] = action_mac
        mod.match = match
        mod.actions = [action]
        key = mod.key()
        if key in self.flowmodIndex or key in self.backupFlowmodIndex:
            SDNPopsRenderer.logger.debug("flowmod %r exists already", mod.key())
            return True
        if not switch.name in self.tapsOnHwSwitch:
            scope.addFlowMod(mod)
            if not controller.addFlowMod(mod):
                success = False
        else:
            # the switch is tapped, should add flowmod in tap form
            self.backupFlowmodIndex[key] = mod
            success = self.tapFlowMod(mod)
        if not success:
            SDNPopsRenderer.logger.warning("Cannot push flowmod:" % mod)
        return success

    def execute(self):
        """
        Renders the intent.
        :return: Expectation when succcessful, None otherwise
        """
        # Add scopes to the controller
        for scope in self.scopeIndex.values():
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
            links.extend(hwSwitch.props['toCoreRouter'])
            links.extend(hwSwitch.props['toSwSwitchLink'])
            links.extend(hwSwitch.props['toSwSwitchLink.WAN'])

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


