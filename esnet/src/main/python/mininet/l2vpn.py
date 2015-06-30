from array import array
import binascii

from common.intent import ProvisioningRenderer, ProvisioningIntent
from common.api import Site, Properties
from common.openflow import ScopeOwner,PacketInEvent, FlowMod, Match, Action, L2SwitchScope, PacketOut, SimpleController
from odl.client import ODLClient

from mininet.enos import TestbedTopology, TestbedHost, TestbedNode, TestbedPort, TestbedLink

from net.es.netshell.api import GenericGraph, GenericHost
from mininet.mac import MACAddress
from common.utils import Logger, dump

broadcastAddress = array('B',[0xFF,0xFF,0xFF,0xFF,0xFF,0xFF])
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
        self.topo = intent.topo
        self.pops = intent.pops

        self.macs = {}
        self.active = False
        self.activePorts = {}
        self.flowmods = []
        self.links = self.intent.links
        self.linkByPort = {}
        self.vidIndex = {}
        SDNPopsRenderer.instance = self
        self.scopeIndex = {}

        vid = self.vpn.props['vid']
        for participant in self.vpn.props['participants']:
            (site, hosts, wanVlan) = participant
            pop = site.props['pop']
            coreRouter = pop.props['coreRouter'].props['enosNode']
            hwSwitch = pop.props['hwSwitch'].props['enosNode']
            hwSwitchScope = L2SwitchScope(name='%s.%s' % (self.vpn.name, hwSwitch.name), switch=hwSwitch, owner=self)
            self.scopeIndex[hwSwitch.name] = hwSwitchScope

            hwSwitch.props['siteVlanIndex'][vid] = wanVlan
            controller = hwSwitch.props['controller']
            for port in hwSwitch.getPorts():
                if port.props['type'] == 'ToSite':
                    hwSwitchScope.addEndpoint(port, wanVlan)
            # swSwitch = pop.props['swSwitch'].props['enosNode']
            # swSwitchScope = L2SwitchScope(name='%s.%s' % (self.vpn.name, swSwitch.name),switch=swSwitch,owner=self)
            # self.scopeIndex[swSwitch.name] = swSwitchScope

        for i in range(len(self.pops)):
            pop1 = self.pops[i]
            hwSwitch1 = pop1.props['hwSwitch']
            scope1 = self.scopeIndex[hwSwitch1.name]
            for j in range(i+1, len(self.pops)):
                pop2 = self.pops[j]
                hwSwitch2 = pop2.props['hwSwitch']
                scope2 = self.scopeIndex[hwSwitch2.name]

                link1 = hwSwitch1.props['nextHop'][pop2.name]
                port1 = link1.props['portIndex'][hwSwitch1.name]
                scope1.addEndpoint(port1, vid)
                port1.props['scopeIndex'][vid] = scope1
                link2 = hwSwitch2.props['nextHop'][pop1.name]
                port2 = link2.props['portIndex'][hwSwitch2.name]
                scope2.addEndpoint(port2, vid)
                port2.props['scopeIndex'][vid] = scope2

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
            mac = MACAddress(dl_src)
            in_port = event.props['in_port'].props['enosPort']
            switch = in_port.props['enosNode']
            vlan = event.props['vlan']
            scope = switch.props['controller'].getScope(in_port, vlan, mac)
            etherType = event.props['ethertype']
            success = True
            #if not mac in self.macs:
            if True:
                self.macs[mac.str()] = (dl_src,in_port)
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
            transMac = self.translate(srcMac)
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
                packet = PacketOut(port=port, dl_src=transMac, dl_dst=dstMac,etherType=etherType,vlan=vlan,scope=scope,payload=payload)
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
            transMac = self.reverse(srcMac)
            dstMac = self.reverse(dstMac) # 0xFF{vid}FFFF => 0xFFFFFFFFFFFF
            vpn = self.vpn
            port = switch.props['toSitePorts'][0]
            packet = PacketOut(port=port,dl_src=transMac,dl_dst=dstMac,etherType=etherType,vlan=vlan,scope=scope,payload=payload)
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
            # set the flowmod that if match(dst == trans_mac)
            # then act(mod dst to mac, mod vlan to vlan, output = port)
            trans_mac = self.translate(mac)
        elif port.get('type') == 'ToWAN':
            # from coreRouter i.e. mac = translated VPN mac
            # set the flowmod that if match(dst == mac)
            # then act(mod dst = restoreMac)
            trans_mac = self.reverse(mac)
        else:
            Logger().error('setMAC fail for the packet is from the port with unknown type')
            return
        match.props['dl_dst'] = trans_mac
        action = Action(name=scope.name)
        action.props['out_port'] = port
        action.props['vlan'] = vlan
        action.props['dl_dst'] = mac
        mod.match = match
        mod.actions = [action]
        self.flowmods.append(mod)
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
    def __init__(self, name, vpn, topo):
        """
        Creates a provisioning intent providing a GenericGraph of the logical view of the
        topology that is intended to be created.
        :param topology: TestbedTopology
        :param site: Site
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
        
        links = filter(lambda link : link.props['endpoints'][0].props['node'] in hosts and link.props['endpoints'][1].props['node'] in hosts, topo.links)
        enosHosts = map(lambda host : host.props['enosNode'], hosts)
        enosLinks = map(lambda host : host.props['enosLink'], links)
        self.vpn = vpn
        self.topo = topo
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
            if node1 in self.hosts and node2 in self.hosts:
                graph.addEdge(node1,node2,link)
        return graph


