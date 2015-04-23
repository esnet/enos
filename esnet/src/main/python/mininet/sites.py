from array import array
import binascii

from common.intent import ProvisioningRenderer, ProvisioningIntent
from common.api import Site, Properties
from common.openflow import ScopeOwner,PacketInEvent, FlowMod, Match, Action, L2SwitchScope, PacketOut, SimpleController
from odl.client import ODLClient

from mininet.enos import TestbedTopology

from net.es.netshell.api import GenericGraph, GenericHost

broadcastAddress = array('B',[0xFF,0xFF,0xFF,0xFF,0xFF,0xFF])

class SiteRenderer(ProvisioningRenderer,ScopeOwner):
    """
    Implements the rendering of provisioning intents on the Site. This class is responsible for pushing the proper
    flowMods that will forward packets between the hosts and the ESnet border router. Typically the topology is

         host(s) <-> siteRouter <-> borderRouter

         Simple vlan/port mach and outport /vlan on siteRouter needs to be set
    """

    def __init__(self, intent):
        """
        Generic constructor. Translate the intent
        :param intent: SiteIntent
        :return:
        """
        ScopeOwner.__init__(self,name=intent.name)
        self.intent = intent
        graph = intent.graph
        self.siteRouter = self.intent.siteRouter
        self.borderRouter = self.intent.borderRouter
        self.macs = {}
        self.active = False
        self.activePorts = {}
        self.flowmods = []

        ports = siteRouter.getPorts()
        wanLink = None
        scope = L2SwitchScope(name=intent.name,switch=siteRouter,owner=self)
        scope.props['endpoints'] = []
        scope.props['intent'] = self.intent
        siteRouter.props['controller'].addScope(scope)
        for port in ports:
            port.props['scope'] = scope
            links = port.getLinks()
            self.activePorts[siteRouter.name + ":" + port.name] = port
            port.props['macs'] = []
            for link in links:
                port.props['switch'] = siteRouter
                vlan = link.props['vlan']
                port.props['vlan'] = vlan
                dstNode = link.getDstNode()
                srcNode = link.getSrcNode()
                scope.props['endpoints'].append( (port.name,[vlan]))
                if borderRouter in [dstNode,srcNode]:
                    # this is the link to the WAN border router
                    wanLink = link
                    port.props['type'] = "TOWAN"
                else:
                    port.props['type'] = "LAN"

        scope2 = L2SwitchScope(name=intent.name,switch=borderRouter,owner=self)
        scope2.props['endpoints'] = []
        scope2.props['intent'] = self.intent
        borderRouter.props['controller'].addScope(scope2)
        ports = borderRouter.getPorts()
        for port in ports:
            port.props['scope'] = scope2
            links = port.getLinks()
            for link in links:
                if link == wanLink:
                    # this is the port connected to the site router
                    self.activePorts[borderRouter.name + ":" + port.name] = port
                    vlan = link.props['vlan']
                    port.props['switch'] = borderRouter
                    port.props['vlan'] = vlan
                    port.props['type'] = "WAN"
                    scope2.props['endpoints'].append( (port.name,[vlan]))


    def eventListener(self,event):
        """
        The implementation of this class is expected to overwrite this method if it desires
        to receive events from the controller such as PACKET_IN
        :param event: ScopeEvent
        """
        if event.__class__ == PacketInEvent:
            # This is a PACKET_IN. Learn the source MAC address
            port = event.props['in_port']
            switch = port.props['switch']
            in_port = self.activePorts[switch.name + ":" + port.name]
            dl_dst = event.props['dl_dst']
            dl_src = event.props['dl_src']
            vlan = event.props['vlan']
            etherType = event.props['ethertype']
            self.macs[dl_src] = in_port
            in_port.props['macs'].append(dl_src)
            # set the flow entry to forward packet to that MAC to this port
            success = self.setMAC(port=in_port,vlan=vlan,mac=dl_src)
            if not success:
                print "Cannot set MAC",binascii.hexlify(dl_src),"on",in_port.props['switch'].name + ":" +in_port.name + "." + str(vlan)

            global broadcastAddress
            if dl_dst == broadcastAddress:
                success = self.broadcast(inPort=in_port,srcMac=dl_src,etherType=etherType,payload=event.props['payload'])
                if not success:
                    print  "Cannot send broadcast packet"

    def broadcast(self,inPort,srcMac,etherType,payload) :
        switchController = self.siteRouter.props['controller']

        for (x,port) in self.activePorts.items():
            if port.props['type'] != "WAN":
                if port == inPort:
                    continue
                scope = port.props['scope']
                vlan = port.props['vlan']
                packet = PacketOut(port=port,dl_src=srcMac,dl_dst=broadcastAddress,etherType=etherType,vlan=vlan,scope=scope,payload=payload)
                return switchController.send(packet)



    def setMAC(self,port,vlan, mac):
        switch = port.props['switch']
        controller = switch.props['controller']
        name = port.name + "." + str(vlan) + ":" + str(mac)
        mod = FlowMod(name=name,scope=port.props['scope'],switch=switch)
        mod.props['renderer'] = self
        match = Match(name=name)
        match.props['dl_dst'] = mac
        match.props['in_port'] = port
        match.props['vlan'] = vlan
        action = Action(name=name)
        action.props['out_port'] = port
        action.props['vlan'] = vlan
        mod.match = match
        mod.actions = [action]
        self.flowmods.append(mod)
        return controller.addFlowMod(mod)

    def setBorderRouterBroadcast(self):
        inPort = None
        inVlan = None
        for (x,port) in self.activePorts.items():
            if port.props['type'] == "WAN":
                inPort = port
                inVlan = port.props['vlan']
                break
        if inPort == None:
            return False
        # chose a link to the hwSwitch of the SDNPop
        toHwSwitch = borderRouter.props['toHwSwitch']
        # always get the first link in the list
        link = toHwSwitch[0]
        outPort = None
        outVlan = link.props['vlan']
        endpoints = link.props['endpoints']
        if endpoints[0].props['switch'] == borderRouter:
            outPort = endpoints[0]
        else:
            outPort = endpoints[1]
        # add outPort into the scope
        scope = port.props['scope']
        endpoints = scope.props['endpoints']
        endpoints.append([outPort.name,[outVlan]])
        controller = borderRouter.props['controller']
        name = ""
        mod = FlowMod(name=name,scope=scope,switch=borderRouter)
        mod.props['renderer'] = self
        match = Match(name=name)
        match.props['dl_dst'] = broadcastAddress
        match.props['in_port'] = inPort
        match.props['vlan'] = inVlan
        action = Action(name=name)
        action.props['out_port'] = outPort
        action.props['vlan'] = outVlan
        mod.match = match
        mod.actions = [action]
        self.flowmods.append(mod)
        return controller.addFlowMod(mod)

    def removeFlowEntries(self):
        return False


    def execute(self):
        """
        Renders the intent.
        :return: Expectation when succcessful, None otherwise
        """
        # Request the scope to the controller
        self.active = True
        # set broadcast flow entry
        success = self.setBorderRouterBroadcast()

        return success


    def destroy(self):
        """
        Destroys or stop the rendering of the intent.
        :return: True if successful
        """
        self.active = False
        return self.removeFlowEntries()

class SiteIntent(ProvisioningIntent):
    def __init__(self,name,hosts,siteRouter,borderRouter,links):
        """
        Creates a provisioning intent providing a GenericGraph of the logical view of the
        topology that is intended to be created.
        :param topology: TestbedTopology
        :param site: Site
        """
        self.hosts = hosts
        self.siteRouter = siteRouter
        self.borderRouter = borderRouter
        self.links = links
        self.graph = self.buildGraph()
        ProvisioningIntent.__init__(self,name=name,graph=self.graph)


    def buildGraph(self):
        graph = GenericGraph()

        for (x,host) in hosts.items():
            graph.addVertex(host.props['enosNode'])

        graph.addVertex(self.siteRouter)
        graph.addVertex(self.borderRouter)
        for link in self.links:
            node1 = link.getSrcNode()
            node2 = link.getDstNode()
            graph.addEdge(node1,node2,link)

        return graph




if __name__ == '__main__':
    # todo: real argument parsing.
    configFileName = None
    net=None
    intent=None
    if len(sys.argv) > 1:
        configFileName = sys.argv[1]
        net = TestbedTopology(fileName=configFileName)
    else:
        net = TestbedTopology()

    # clean up the Controller's scope
    SimpleController.scopes = {}

    enosHosts = []
    for (x,vpn) in net.builder.vpns.items():
        sites = vpn.props['sites']
        for (y,site) in sites.items():
            hosts = site.props['hosts']
            siteNodes=[]
            for(z,h) in hosts.items():
                host = h.props['enosNode']
                enosHosts.append(host)
                siteNodes.append(host)
            siteRouter = site.props['siteRouter'].props['enosNode']
            borderRouter = net.nodes[site.props['connectedTo']]
            serviceVm = site.props['serviceVm'].props['enosNode']
            siteNodes.append(siteRouter)
            siteNodes.append(borderRouter)
            links = site.props['links'].copy()
            enosLinks=[]
            for (z,l) in links.items():
                link = l.props['enosLink']
                node1 = link.getSrcNode()
                node2 = link.getDstNode()
                srcNode = link.getSrcNode()
                dstNode = link.getDstNode()
                if srcNode in siteNodes and dstNode in siteNodes:
                    enosLinks.append(link)
            intent = SiteIntent(name=site.name,hosts=enosHosts,borderRouter=borderRouter,siteRouter=siteRouter,links=enosLinks)

    renderer = SiteRenderer(intent)
    err = renderer.execute()
    # Simulates a PacketIn from a host
    # payload = array('B',"ARP REQUEST")
    # packetIn = PacketInEvent(inPort = "eth2",srcMac=array('B',[0,0,0,0,0,1]),dstMac=broadcastAddress,vlan=11,payload=payload)
    # packetIn.props['ethertype'] = 0x0806
    # renderer.eventListener(packetIn)



