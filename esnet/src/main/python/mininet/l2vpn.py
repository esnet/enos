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
        self.pops = intent.pops

        self.macs = {}
        self.active = False
        self.activePorts = {}
        self.flowmods = []
        self.links = self.intent.links
        self.linkByPort = {}
        self.vidIndex = {}
        self.vpnIndex = {}
        SDNPopsRenderer.instance = self
        self.scopes = {}
        self.scopeIndex = {}

        for pop in self.pops:
            coreRouter = pop.props['coreRouter'].props['enosNode']
            hwSwitch = pop.props['hwSwitch'].props['enosNode']
            hwSwitchScope = L2SwitchScope(name=self.name,switch=hwSwitch,owner=self)
            for port in hwSwitch.getPorts():
                port.props['scope'] = hwSwitchScope
                if port.get('type') == 'ToWAN':
                    vlans = []
                    for link in port.getLinks():
                        vlans.append(link.props['vlan'])
                    hwSwitchScope.addEndpoint(port, vlans)
            self.scopeIndex[hwSwitch.name] = hwSwitchScope
            self.scopes[hwSwitch.name] = hwSwitchScope
            swSwitch = pop.props['swSwitch'].props['enosNode']
            swSwitchScope = L2SwitchScope(name=self.name,switch=swSwitch,owner=self,endpoints=[])
            for port in swSwitch.getPorts():
                port.props['scope'] = swSwitchScope
            self.scopeIndex[swSwitch.name] = swSwitchScope
            self.scopes[swSwitch.name] = swSwitchScope

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
            scope = switch.props['controller'].getScope(in_port, vlan)
            etherType = event.props['ethertype']
            success = True
            #if not mac in self.macs:
            if True:
                self.macs[mac.str()] = (dl_src,in_port)
                # set the flow entry to forward packet to that MAC to this port
                success = self.setMAC(port=in_port,switch=switch,scope=scope,vlan=vlan,mac=mac)
                if not success:
                    print "Cannot set MAC", mac, "on", + ":" +in_port.name + "." + str(vlan)
            if not 'node' in in_port.props:
                print "L2VPN no swict",in_port,in_port.props
                #in_port.props['switch'] = switch
            if dl_dst.isBroadcast():
                success = self.broadcast(inPort=in_port,switch=switch,scope=scope,inVlan=vlan,srcMac=mac,dstMac=dl_dst,etherType=etherType,payload=event.props['payload'])
                if not success:
                    print  "Cannot send broadcast packet"

    def addVpn(self, vpn):
        vid = vpn.props['vid']
        self.vpnIndex[vid] = vpn
        for participant in vpn.props['participants']:
            (site, hosts, wanVlan) = participant
            pop = site.props['pop']
            hwSwitch = pop.props['hwSwitch'].props['enosNode']
            hwSwitch.props['siteVlanIndex'][vid] = wanVlan
            controller = hwSwitch.props['controller']
            for port in hwSwitch.getPorts():
                if port.props['type'] == 'ToSite':
                    self.vidIndex['%s.%d' % (port.name, wanVlan)] = vid
                    scope = port.props['scope']
                    scope.addEndpoint(port, [wanVlan])

    def getVid(self, port, vlan):
        key = '%s.%d' % (port, vlan)
        if not key in self.vidIndex:
            Logger().error('%s not found in %r.vidIndex' % (key, self) )
            return None
        return self.vidIndex[key]
    def translate(self, port, vlan, mac):
        vid = self.getVid(port, vlan)
        vpn = self.vpnIndex[vid]
        return vpn.props['mat'].translate(mac)
    def reverse(self, trans_mac):
        vid = trans_mac.getVid()
        vpn = self.vpnIndex[vid]
        hid = trans_mac.getHid()
        return vpn.props['mat'].reverse(hid)

    def broadcast(self,inPort,inVlan,srcMac,dstMac,etherType,payload,switch,scope) :

        switchController = switch.props['controller']
        switch = inPort.props['enosNode']
        scope = inPort.props['scope']
        success = True
        endpoints = scope.props['endpoints']
        if inPort.get('type') == 'ToSite':
            # from site, broadcast to WANs
            vid = self.getVid(inPort, inVlan)
            transMac = self.translate(inPort, inVlan, srcMac)
            vpn = self.vpnIndex[vid]
            lanVlan = vpn.props['lanVlan']
            dstMac = MACAddress.createBroadcast(vid)
            for port in switch.getPorts():
                if port.props['type'] == 'ToWAN':
                    vlan = port.props['vlan']
                    packet = PacketOut(port=port, dl_src=transMac, dl_dst=dstMac,etherType=etherType,vlan=vlan,scope=scope,payload=payload)
                    if SDNPopsRenderer.debug:
                        print packet
                    res = switchController.send(packet)
                    if not res:
                        Logger().warning('switchController.send(%r) fail' % packet)
                        success = False
        elif inPort.get('type') == 'ToWAN':
            # from WAN, broadcast to site
            transMac = self.reverse(srcMac)
            vid = dstMac.getVid()
            dstMac = MACAddress.createBroadcast() # 0xFF{vid}FFFF => 0xFFFFFFFFFFFF
            vpn = self.vpnIndex[vid]
            port = switch.props['toSitePorts'][0]
            vlan = switch.props['siteVlanIndex'][vid]
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
            trans_mac = self.translate(port, vlan, mac)
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
        for scope in self.scopes.values():
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
    def __init__(self, name, pops, hosts, links):
        """
        Creates a provisioning intent providing a GenericGraph of the logical view of the
        topology that is intended to be created.
        :param topology: TestbedTopology
        :param site: Site
        """
        self.pops = pops
        self.hosts = hosts
        self.links = links
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


