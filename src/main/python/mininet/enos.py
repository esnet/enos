#!/usr/bin/python
import sys

from testbed import TopoBuilder
from net.es.netshell.api import GenericGraph, GenericTopologyProvider, TopologyProvider, GenericHost, GenericNode, GenericPort, GenericLink

testbedNodes = {}

def configureVpns(topology):
    graph = topology.getGraph(TopologyProvider.WeightType.TrafficEngineering)

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


class TestbedNode(GenericNode):
    def __init__(self,name):
        GenericPort.__init__(self,name)
        global testbedNodes
        testbedNodes[name] = self

class TestbedTopology (GenericTopologyProvider):
    #
    # Creates nodes and links of a location
    #
    def buildLocation(self,location):
        locationName = location['name']
        router = self.builder.mininetNameToRealName[location['coreRouter']['name']]
        switch = self.builder.mininetNameToRealName[location['hwSwitch']['name']]
        ovs = self.builder.mininetNameToRealName[location['swSwitch']['name']]
        nbOfLinks = location['nbOfLinks']

        # creates nodes
        routerNode = TestbedNode(router)
        switchNode = TestbedNode(switch)
        ovsNode = TestbedNode(ovs)

        self.addNode(routerNode)
        self.addNode(switchNode)
        self.addNode(ovsNode)

        # creates links between router and switch and between switch and ovs. Assume same number
        # of links
        while nbOfLinks > 0:
            # Creates ports
            srcPort = GenericPort(location['coreRouter']['name'] + "-eth" + str(100 + nbOfLinks))
            dstPort = GenericPort(location['hwSwitch']['name'] + "-eth" + str(100 + nbOfLinks))
            self.addPort(routerNode,srcPort)
            self.addPort(switchNode,dstPort)
            link = GenericLink(routerNode,srcPort,switchNode,dstPort)
            self.addLink (link)
            srcPort = GenericPort(location['hwSwitch']['name'] + "-eth" + str(200 + nbOfLinks))
            dstPort = GenericPort(location['swSwitch']['name'] + "-eth" + str(200 + nbOfLinks))
            self.addPort(switchNode,srcPort)
            self.addPort(ovsNode,dstPort)
            link = GenericLink(switchNode,srcPort,ovsNode,dstPort)
            self.addLink(link)
            nbOfLinks = nbOfLinks - 1
        self.displayDot()

    def buildRoutersLinks(self):
        # two links are created between any core router, each of them with a different QoS (TBD)
        # one best effort no cap, the other bandwidth limited to low.
        locations = self.builder.config['topology']
        for fromLoc in locations:
            fromNode = fromLoc['coreRouter']
            for toLoc in locations:
                toNode = toLoc['coreRouter']
                if toNode['name'] == fromNode['name']:
                    continue
                srcNode = TestbedNode(self.builder.mininetNameToRealName[fromNode['name']])
                dstNode = TestbedNode(self.builder.mininetNameToRealName[toNode['name']])
                srcPort = GenericPort(fromNode['name'] + "-eth" + str(501))
                dstPort = GenericPort(toNode['name'] + "-eth" + str(502))
                self.addPort(srcNode,srcPort)
                self.addPort(dstNode,dstPort)
                link = GenericLink(srcNode,srcPort,dstNode,dstPort)
                self.addLink(link)
            self.displayDot()

    def displayDot(self):
        sys.stdout.write('.')
        sys.stdout.flush()

    def getLocation(self, location):
        for loc in self.builder.config['topology']:
            if loc['name'] == location:
                return loc
        return None

    def buildSite(self,site):
        siteName = site['name']
        hosts = site['hosts']
        siteRouter = self.builder.mininetNameToRealName[site['siteRouter']['name']]
        serviceVm = site['serviceVm']
        borderRouter = self.builder.mininetNameToRealName[self.getLocation(site['connectedTo'])['coreRouter']['name']]
        swSwitch =  self.builder.mininetNameToRealName[self.getLocation(site['connectedTo'])['swSwitch']['name']]
        # find the hardware switch associated to this router
        vlan = site['vlan']
        # Create the site border router/switch
        siteRouterNode = TestbedNode(siteRouter)
        switch = TestbedNode(siteRouter)
        self.addNode (switch)
        global testbedNodes
        router = testbedNodes[borderRouter]
        srcPort = GenericPort(site['siteRouter']['name']  + "-eth" + str(300))
        dstPort = GenericPort(self.getLocation(site['connectedTo'])['coreRouter']['name'] + "-eth" + str(300))
        self.addPort(swSwitch,srcPort)
        self.addPort(router,dstPort)
        link = GenericLink(switch,srcPort,router,dstPort)
        self.addLink(link)
        siteHosts=[]
        hostIndex = 1
        for host in hosts:
            h = TestbedNode(self.builder.mininetNameToRealName[host['name']])
            self.addNode(h)
            siteHosts.append(h)
            dstPort = GenericPort(site['siteRouter']['name']  + "-eth" + str(hostIndex))
            srcPort = GenericPort(host['name'] + "-eth" + str(hostIndex))
            self.addPort(h,srcPort)
            self.addPort(switch,dstPort)
            link = GenericLink(h,srcPort,switch,dstPort)
            hostIndex = hostIndex + 1

        # create VPN for the VPN instance and for that site
        vm = TestbedNode(self.builder.mininetNameToRealName[serviceVm['name']])
        self.addNode(vm)
        siteHosts.append(h)
        dstPort = GenericPort(site['siteRouter']['name']  + "-eth400")
        srcPort = GenericHost(serviceVm['name'] + "-eth400")
        self.addPort(vm,srcPort)
        self.addPort(switch,dstPort)
        link = GenericLink(vm,srcPort,switch,dstPort)
        self.displayDot()


    def buildVpns(self):
        for vpn in self.builder.config['vpns']:
            vpnName = vpn['name']
            sites = vpn['sites']
            allSiteNodes = {};
            print "building VPN " + vpnName
            for site in sites:
                siteNodes = self.buildSite(site=site)
            print

    def __init__(self, fileName = None):
        # Build topology
        self.builder = TopoBuilder(fileName)
        self.vpnInstances = {}
        print("building SDN locations")
        locations=self.builder.config['topology']
        for loc in locations:
            self.buildLocation(location=loc)
        self.buildVpns()
        print"building network"
        self.buildRoutersLinks()
        print


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

    configureVpns(net)

