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
        self.flowmods = []
        self.links = self.intent.links
        self.linkByPort = {}
        SDNPopsRenderer.instance = self
        self.scopeIndex = {} # [hwSwitch.name or swSwitch.name] = scope

    def addSite(self, site, wanVlan):
        vid = self.vpn.props['vid']
        pop = site.props['pop']
        coreRouter = pop.props['coreRouter'].props['enosNode']
        hwSwitch = pop.props['hwSwitch'].props['enosNode']
        hwSwitchScope = L2SwitchScope(name='%s.%s' % (self.vpn.name, hwSwitch.name), switch=hwSwitch, owner=self)
        self.scopeIndex[hwSwitch.name] = hwSwitchScope

        hwSwitch.props['siteVlanIndex'][vid] = wanVlan
        controller = hwSwitch.props['controller']
        for port in hwSwitch.getPorts():
            if port.props['type'] == 'ToSite': # should have only one (or nbOfLinks) port
                hwSwitchScope.addEndpoint(port, wanVlan)
                break
        swSwitch = pop.props['swSwitch'].props['enosNode']
        swSwitchScope = L2SwitchScope(name='%s.%s' % (self.vpn.name, swSwitch.name),switch=swSwitch,owner=self)
        self.scopeIndex[swSwitch.name] = swSwitchScope
        # A scope with an empty endpoints indicates it covers everything.
        # Therefore, though swSwitchScope has no function for now, we still
        # need to add an endpoint to avoid the failure of scope.overlaps()
        serviceVm = self.vpn.props['serviceVmIndex'][site.name]
        vm_port = serviceVm.props['ports'][1] # assume only one port on ServiceVm
        link = vm_port.props['links'][0] # assume only one link on the port
        sw_port = link.props['portIndex'][swSwitch.name]
        swSwitchScope.addEndpoint(sw_port)

        pop1 = hwSwitch.props['pop']
        hwSwitch1 = hwSwitch
        scope1 = hwSwitchScope
        for pop2 in self.pops:
            hwSwitch2 = pop2.props['hwSwitch']
            scope2 = self.scopeIndex[hwSwitch2.name]

            link1 = hwSwitch1.props['nextHop'][pop2.name]
            port1 = link1.props['portIndex'][hwSwitch1.name]
            # Here we use (port, vid) instead of (port, vlan) as the index.
            # The reason is that VPNs all share the same port and vlan on
            # the 'ToWAN' ports of HwSwitch, so we couldn't dispatch
            # packets to the scope based on vlan. The solution is temporary
            # only.
            scope1.addEndpoint(port1, vid)
            port1.props['scopeIndex'][vid] = scope1
            link2 = hwSwitch2.props['nextHop'][pop1.name]
            port2 = link2.props['portIndex'][hwSwitch2.name]
            # Similar to the comment above
            scope2.addEndpoint(port2, vid)
            port2.props['scopeIndex'][vid] = scope2
        self.pops.append(pop1)

    def __str__(self):
        desc = "SDNPopsRenderer: " + self.name + "\n"
        desc += "\tPorts:\n"
        for (x,port) in self.activePorts.items():
            desc +=  str(port)
        desc += "\n"
        return desc

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
                if SDNPopsRenderer.debug:
                    print "no VLAN, reject",event
                return
            if SDNPopsRenderer.debug:
                print self.name
                print event

            dl_src = event.props['dl_src']
            dl_dst = event.props['dl_dst']
            mac = dl_src
            in_port = event.props['in_port'].props['enosPort']
            switch = in_port.props['enosNode']
            vlan = event.props['vlan']
            scope = switch.props['controller'].getScope(in_port, vlan, dl_dst)
            etherType = event.props['ethertype']
            success = True
            #if not mac in self.macs:
            if True:
                # self.macs[mac.str()] = (dl_src,in_port)
                # set the flow entry to forward packet to that MAC to this port
                success = self.setMAC(port=in_port,switch=switch,scope=scope,vlan=vlan,mac=mac)
                if not success:
                    print 'Cannot set MAC %r on %s.%d' % (mac, in_port.name, vlan)
            if not 'node' in in_port.props:
                print "L2VPN no swict",in_port,in_port.props
                #in_port.props['switch'] = switch
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
        if inPort.get('type') == 'ToSite':
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
                    Logger().warning('switchController.send(%r) fail' % packet)
                    success = False
        elif inPort.props['type'] == 'ToWAN':
            # from WAN, broadcast to site
            assert(dstMac.getVid() == self.vpn.props['vid'])
            vid = self.vpn.props['vid']
            if not vid in switch.props['siteVlanIndex']:
                Logger().warning('get unknown vid %r' % vid)
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
                Logger().warning('switchController.send(%r) fail' % packet)
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
        if port.get('type') == 'ToSite':
            # set the flowmod = {match:{dst:trans_mac}, action:{dst:mac}}
            match_mac = self.translate(mac)
            action_mac = mac
        elif port.get('type') == 'ToWAN':
            # set the flowmod = {match:{dst:mac}, action:{dst:trans_mac}}
            match.props['vlan'] = switch.props['siteVlanIndex'][self.vpn.props['vid']]
            match_mac = mac
            action_mac = self.translate(mac)
        else:
            Logger().warning('setMAC fail for the packet is from the port with unknown type')
            return
        match.props['dl_dst'] = match_mac
        action = Action(name=scope.name)
        action.props['out_port'] = port
        action.props['vlan'] = vlan
        action.props['dl_dst'] = action_mac
        mod.match = match
        mod.actions = [action]
        # self.flowmods.append(mod)
        if SDNPopsRenderer.debug:
            print "add flowMod",mod
        success = controller.addFlowMod(mod)
        if not success:
            print "Cannot push flowmod:\n",mod

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
            links.extend(hwSwitch.props['toSwSwitch'])

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


