#!/usr/bin/python
import sys

from testbed import TopoBuilder
from net.es.netshell.api import GenericGraph, GenericTopologyProvider, TopologyProvider, GenericHost, GenericNode, GenericPort, GenericLink

testbedNodes = {}

def configureVpns(topology):
    graph = topology.getGraph(TopologyProvider.WeightType.TrafficEngineering)
    """
    for vpn in topology.builder.config['vpns']:
        vpnName = vpn['name']
        sites = vpn['sites']
        for site in sites:
            siteName = site['name']
            hosts = site['hosts']
            siteRouter = topology.builder.mininetNameToRealName[site['siteRouter']['name']]
            serviceVm = topology.builder.mininetNameToRealName[site['serviceVm']['name']]
            borderRouter = topology.builder.mininetNameToRealName[topology.getLocation(site['connectedTo'])['coreRouter']['name']]
            swSwitch =  topology.builder.mininetNameToRealName[topology.getLocation(site['connectedTo'])['swSwitch']['name']]
            vlan = site['vlan']
            # Create a graph of the site topology
            siteRouterNode = TestbedNode(siteRouter)
            serviceVmHost = TestbedNode(serviceVm)
            borderRouterNode = TestbedNode(borderRouter)
            swSwitchNode = TestbedNode(swSwitch)
            graph = GenericGraph()
            srcPort = GenericPort("p1")
            dstPort = GenericPort("p1")
            link = GenericLink(siteRouterNode,srcPort,borderRouterNode,dstPort)
            graph.addVertex(siteRouterNode)
            graph.addVertex(borderRouterNode)
            graph.addEdge(siteRouterNode,borderRouterNode,link)
            srcPort = GenericPort("p-" + vpnName)
            dstPort = GenericPort("eth0")
            link = GenericLink(swSwitchNode,srcPort,serviceVmHost,dstPort)
            graph.addVertex(swSwitchNode)
            graph.addVertex(serviceVmHost)
            graph.addEdge(swSwitchNode,serviceVmHost,link)
            portIndex = 2
            for host in hosts:
                hostNode = GenericHost(topology.builder.mininetNameToRealName[host['name']])
                srcPort = GenericPort("p" + str(portIndex))
                portIndex = portIndex + 1
                link = GenericLink(siteRouterNode,srcPort,hostNode,dstPort)
                graph.addVertex(hostNode)
                graph.addEdge(siteRouterNode,hostNode,link)
    """


class TestbedNode(GenericNode):
    def __init__(self,name):
        GenericPort.__init__(self,name)
        global testbedNodes
        testbedNodes[name] = self

class TestbedTopology (GenericTopologyProvider):

    def displayDot(self):
        sys.stdout.write('.')
        sys.stdout.flush()

    def buildSwitch(self,switch):
        sw = TestbedNode(switch.name)
        self.addNode(sw)
        switch.props['enosNode'] = sw

    def buildHost(self,host):
        h = GenericHost(host.name)
        self.addNode(h)
        host.props['enosNode'] = h

    def buildLink(self,link):
        p1 = link.props['endpoints'][0]
        p2 = link.props['endpoints'][1]
        port1 = GenericPort(p1.name)
        p1.props['enosPort'] = port1
        port2 = GenericPort(p2.name)
        p2.props['enosPort'] = port2
        node1 = self.builder.nodes[p1.props['node']].props['enosNode']
        node2 = self.builder.nodes[p2.props['node']].props['enosNode']
        self.addPort (node1,port1)
        self.addPort (node2,port2)
        link = GenericLink(node1,port1,node2,port2)
        self.addLink(link)

    def buildCore(self):
        for coreRouter in self.builder.coreRouters.items():
            self.buildSwitch(coreRouter[1])
        for hwSwitch in self.builder.hwSwitches.items():
            self.buildSwitch(hwSwitch[1])
        for swSwitch in self.builder.swSwitches.items():
            self.buildSwitch(swSwitch[1])
        for link in self.builder.coreLinks.items():
            self.buildLink(link[1])

    def buildVpn(self,vpn):
        """

        :param vpn: TopoVPN
        :return:
        """
        for s in vpn.props['sites']:
            site = vpn.props['sites'][s]
            siteRouter = site.props['siteRouter']
            self.buildSwitch(siteRouter)
            for h in site.props['hosts']:
                host = site.props['hosts'][h]
                self.buildHost(host)
            self.buildHost(site.props['serviceVm'])

            for l in site.props['links']:
                link = site.props['links'][l]
                self.buildLink(link)

    def buildVpns(self):
        for vpnName in self.builder.vpns:
            vpn = self.builder.vpns[vpnName]
            self.buildVpn(vpn)

    def __init__(self, fileName = None):
        # Build topology
        self.builder = TopoBuilder(fileName)
        self.buildCore()
        self.buildVpns()

if __name__ == '__main__':
    # todo: real argument parsing.
    configFileName = None
    net=None
    if len(sys.argv) > 1:
        configFileName = sys.argv[1]
        net = TestbedTopology(fileName=configFileName)
    else:
        net = TestbedTopology()
    # viewer = net.getGraphViewer(TopologyProvider.WeightType.TrafficEngineering)
    graph = net.getGraph(TopologyProvider.WeightType.TrafficEngineering)

