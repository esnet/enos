#!/usr/bin/python
import sys

from testbed import TopoBuilder
from net.es.netshell.api import GenericTopologyProvider, GenericHost, GenericNode, GenericPort, GenericLink

testbedNodes = {}

class TestbedNode (GenericNode):
    def __init__(self):
        self.portIndex = 1
        global testbedNodes
        testbedNodes[self.getResourceName] = self

    def newPort(self):
        portName = "p" + str(self.portIndex)
        return GenericPort(portName)



class TestbedTopology (GenericTopologyProvider):

    #
    # Creates nodes and links of a location
    #
    def buildLocation(self,location):
        locationName = location['name']
        router = self.builder.mininetNameToRealName(location['coreRouter'])
        switch = self.builder.mininetNameToRealName(location['hwSwitch'])
        ovs = self.builder.mininetNameToRealName(location['swSwitch'])
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
            srcPort = router.newPort()
            dstPort = switchNode.newPort()
            link = GenericLink(srcNode=routerNode,srcPort=srcPort,dstNode=switchNode,dstPort=dstPort)
            self.addLink (link)
            srcPort = switchNode.newPort()
            dstPort = ovsNode.newPort()
            link = GenericLink(srcNode=switchNode,srcPort=srcPort,dstNode=ovsNode,dstPort=dstPort)
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
                srcNode = TestbedNode(self.builder.mininetNameToRealName(fromNode))
                dstNode = TestbedNode(self.builder.mininetNameToRealName(toNode))
                srcPort = srcNode.newPort()
                dstPort = dstNode.newPort()
                link = GenericLink(srcNode=srcNode,srcPort=srcPort,dstNode=dstNode,dstPort=dstPort)
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
        siteRouter = self.builder.mininetNameToRealName(site['siteRouter'])
        serviceVm = site['serviceVm']
        borderRouter = self.builder.mininetNameToRealName(self.getLocation(site['connectedTo'])['coreRouter'])
        swSwitch =  self.builder.mininetNameToRealName(self.getLocation(site['connectedTo'])['swSwitch'])
        # find the hardware switch associated to this router
        vlan = site['vlan']
        # Create the site border router/switch
        siteRouterNode = TestbedNode(siteRouter)
        switch = TestbedNode(siteRouter)
        self.addNode (switch)
        global testbedNodes
        router = testbedNodes[borderRouter]
        srcPort = switch.newPort()
        dstPort = router.newPort()
        link = GenericLink(srcNode=switch,srcPort=srcPort,dstNode=router,dstPort=dstPort)
        self.addLink(link)
        siteHosts=[]
        for host in hosts:
            h = TestbedHost(host['name'])
            self.addHost(h)
            siteHosts.append(h)
            dstPort = switch.newPort()
            srcPort = h.newPort()
            link = GenericLink(srcNode=h,srcPort=srcPort,dstNode=switch,dstPort=dstPort)

        # create VPN for the VPN instance and for that site
        vm = TestbedNode(serviceVm['name'])
        self.addHost(vm)
        siteHosts.append(h)
        dstPort = switch.newPort()
        srcPort = vm.newPort()
        link = GenericLink(srcNode=vm,srcPort=srcPort,dstNode=switch,dstPort=dstPort)
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
        Topo.__init__(self)
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
    setLogLevel( 'info' )
    # todo: real argument parsing.
    configFileName = None
    if len(sys.argv) > 1:
        configFileName = sys.argv[1]
        net = TestbedTopology(fileName=configFileName)
    else:
        net = TestbedTopology()

