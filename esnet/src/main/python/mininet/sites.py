from common.intent import ProvisioningRenderer, ProvisioningIntent
from common.api import Site, Properties
from common.openflow import ScopeOwner,PacketInEvent, FlowMod, Match, Action, L2SwitchScope

from mininet.enos import TestbedTopology

from net.es.netshell.api import GenericGraph, GenericHost

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

        for port in ports:
            endpoints = []
            scope = L2SwitchScope(name=intent.name,switch=siteRouter,owner=self)
            scope.endpoints = endpoints
            scope.props['intent'] = self.intent
            port.props['scope'] = scope
            links = port.getLinks()
            self.activePorts[port.name] = port
            port.props['macs'] = []
            for link in links:
                port.props['switch'] = siteRouter
                vlan = link.props['vlan']
                port.props['vlan'] = vlan
                dstNode = link.getDstNode()
                srcNode = link.getSrcNode()
                endpoints.append( (port.name,[vlan]))
                if borderRouter in [dstNode,srcNode]:
                    # this is the link to the WAN border router
                    wanLink = link
                    port.props['type'] = "WAN"
                else:
                    port.props['type'] = "LAN"

        ports = borderRouter.getPorts()
        for port in ports:
            endpoints = []
            scope = L2SwitchScope(name=intent.name,switch=borderRouter,owner=self)
            scope.endpoints = endpoints
            scope.props['intent'] = self.intent
            port.props['scope'] = scope
            links = port.getLinks()
            for link in links:
                if link == wanLink:
                    # this is the port connected to the site router
                    self.activePorts[port.name] = port
                    port.props['switch'] = borderRouter
                    port.props['vlan'] = vlan = link.props['vlan']
                    endpoints.append( (port.name,[vlan]))



    def eventListener(self,event):
        """
        The implementation of this class is expected to overwrite this method if it desires
        to receive events from the controller such as PACKET_IN
        :param event: ScopeEvent
        """
        if event.__class__ == PacketInEvent:
            # This is a PACKET_IN. Learn the source MAC address
            in_port = self.activePorts[event.props['in_port']]
            dl_dst = event.props['dl_dst'].upper()
            dl_src = event.props['dl_src'].upper()
            vlan = event.props['vlan']
            self.macs[dl_src] = in_port
            in_port.props['macs'].append(dl_src)
            # set the flow entry to forward packet to that MAC to this port
            success = self.setMAC(port=in_port,vlan=vlan,mac=dl_src)
            if not success:
                print "Cannot set",dl_src,"on",in_port,".",vlan

            if dl_dst == "FF:FF:FF:FF:FF:FF":
                success = self.broadcast(event)
                if not success:
                    print  "Cannot send packet"

    def broadcast(self,event) :
        return



    def setMAC(self,port,vlan, mac):
        switch = port.props['switch']
        controller = switch.props['controller']
        name = port.name + "." + str(vlan) + ":" + mac
        mod = FlowMod(name=name,scope=port.props['scope'],switch=switch)
        print mod.props
        mod.props['renderer'] = self
        match = Match(name=name)
        match.props['dl_dst'] = mac
        action = Action(name=name)
        action.props['out_port'] = port.name
        action.props['vlan'] = vlan
        mod.match = match
        mod.actions = [action]
        scope = port.props['scope']
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
        return True


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
    packetIn = PacketInEvent(inPort = "eth2",srcMac="00:00:00:00:00:01",dstMac="FF:FF:FF:FF:FF:FF",vlan=11,payload="ARP REQUEST")
    renderer.eventListener(packetIn)



