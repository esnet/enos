from common.intent import ProvisioningRenderer, ProvisioningIntent
from common.api import Site, Properties
from common.openflow import ScopeOwner,PacketInEvent

from mininet.enos import TestbedTopology

from net.es.netshell.api import GenericGraph, GenericHost

class VirtualPort(Properties):
    def __init__(self,port,props={}):
        Properties.__init__(self,port.getResourceName(),props)
        self.props['enosPort'] = port

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
        ports = siteRouter.getPorts()
        self.wanPort=None
        self.hostPorts = {}
        self.hosts = {}
        self.macTable = {}
        self.virtualPorts = {}

        for port in ports:
            self.virtualPorts[port.name] = VirtualPort(port)
            links = port.getLinks()

            for link in links:
                print link.name + "  ID= " + str(id(link)) + " " + link.__class__.__name__
                vlan = link.props['vlan']
                dstNode = link.getDstNode()
                srcNode = link.getSrcNode()
                if borderRouter in [dstNode,srcNode]:
                    # this is the link to the WAN border router
                    self.wanPort = VirtualPort(port)
                else:
                    if siteRouter == dstNode:
                        self.hostPorts[port.getResourceName()] = srcNode
                    else:
                        self.hostPorts[port.getResourceName()] = dstNode

    def eventListener(self,event):
        """
        The implementation of this class is expected to overwrite this method if it desires
        to receive events from the controller such as PACKET_IN
        :param event: ScopeEvent
        """
        if event.__class__ == PacketInEvent:
            # This is a PACKET_IN. Learn the source MAC address
            in_port = event.props['in_port']
            port = self.ports[in_port]
            dl_src = event.props['dl_src']
            self.macTable[dl_src] = port
            # set the flow entry to forward packet to that MAC to this port


    def setDestination(self,port,mac):
        vlan = port.props['vlan']
        controller = port.props['controller']
        print controller





    def executeHost(self,host,link):
        print "HOST " + host.getResourceName()

    def executeNode(self,node,link):
        print  "SWITCH " + node.getResourceName()
        ports = node.getPorts()
        for port in ports:
            links = port.getLinks()
            if link in links:
                  print "."

    def execute(self):
        """
        Renders the intent.
        :return: Expectation when succcessful, None otherwise
        """
        return None


    def destroy(self):
        """
        Destroys or stop the rendering of the intent.
        """

class SiteIntent(ProvisioningIntent):
    def __init__(self,hosts,siteRouter,borderRouter,links):
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
        ProvisioningIntent.__init__(self,self.graph)


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
            intent = SiteIntent(hosts=enosHosts,borderRouter=borderRouter,siteRouter=siteRouter,links=enosLinks)



    renderer = SiteRenderer(intent)
    renderer.execute()

