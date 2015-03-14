#!/usr/bin/python
import sys

from testbed import TopoBuilder
from net.es.netshell.api import GenericTopologyProvider, TopologyProvider, GenericHost, GenericNode, GenericPort, GenericLink

testbedNodes = {}

def configureVpn(topology):
    graph = topology.getGraph(TopologyProvider.WeightType.TrafficEngineering)


    for vpn in topology.builder.config['vpns']:
        vpnName = vpn['name']
        sites = vpn['sites']
        for site in sites:
            siteName = site['name']
            hosts = site['hosts']
            siteRouter = site['siteRouter']['name']
            serviceVm = site['serviceVm']
            borderRouter = topology.getLocation(site['connectedTo'])['coreRouter']['name']
            swSwitch =  topology.getLocation(site['connectedTo'])['swSwitch']['name']
            vlan = site['vlan']



class TestbedNode (GenericNode):
    def __init__(self, name):
        self.setResourceName(name)
        self.portIndex = 1
        global testbedNodes
        testbedNodes[name] = self

    def newPort(self):
        portName = "p" + str(self.portIndex)
        port = GenericPort()
        port.setResourceName(portName)
        self.portIndex = self.portIndex + 1
        return port



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
            srcPort = routerNode.newPort()
            dstPort = switchNode.newPort()
            link = GenericLink(routerNode,srcPort,switchNode,dstPort)
            self.addLink (link)
            srcPort = switchNode.newPort()
            dstPort = ovsNode.newPort()
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
                srcPort = srcNode.newPort()
                dstPort = dstNode.newPort()
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
        global testbedoNodes
        router = testbedNodes[borderRouter]
        srcPort = switch.newPort()
        dstPort = router.newPort()
        link = GenericLink(switch,srcPort,router,dstPort)
        self.addLink(link)
        siteHosts=[]
        for host in hosts:
            h = TestbedNode(host['name'])
            self.addNode(h)
            siteHosts.append(h)
            dstPort = switch.newPort()
            srcPort = h.newPort()
            link = GenericLink(h,srcPort,switch,dstPort)

        # create VPN for the VPN instance and for that site
        vm = TestbedNode(serviceVm['name'])
        self.addNode(vm)
        siteHosts.append(h)
        dstPort = switch.newPort()
        srcPort = vm.newPort()
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

    configureVpn(net)

