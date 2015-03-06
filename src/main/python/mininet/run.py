#!/usr/bin/python
import sys

from mininet.net import Mininet
from mininet.node import Controller, OVSKernelSwitch, RemoteController
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.topo import Topo

from testbed import TopoBuilder

#
# OpenFlow controller IP and ports
#
controllerIp='192.168.56.1'
controllerPort=6633


class TestbedTopo(Topo):

    #
    # Creates nodes and links of a location
    #
    def buildLocation(self,location):
        locationName = location['name']
        router = location['coreRouter']
        switch = location['hwSwitch']
        ovs = location['swSwitch']
        nbOfLinks = location['nbOfLinks']

        # creates nodes
        routerNode = self.addSwitch(router['name'],listenPort=6634,dpid=router['dpid'])
        switchNode = self.addSwitch(switch['name'],listenPort=6634,dpid=switch['dpid'])
        ovsNode = self.addSwitch(ovs['name'],listenPort=6634,dpid=ovs['dpid'])

        # creates links between router and switch and between switch and ovs. Assume same number
        # of links
        while nbOfLinks > 0:
            self.addLink(routerNode,switchNode)
            self.addLink(switchNode,ovsNode)
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
                self.addLink(fromNode['name'],toNode['name'])
            self.displayDot()

    def setOpenFlow(self,net):
        global locations, viewAll

        locations = self.builder.config['topology']
        for loc in locations:
            net.getNodeByName(loc['coreRouter']['name']).start([net.ctrl])
            self.displayDot()

            net.getNodeByName(loc['hwSwitch']['name']).start([net.ctrl])
            self.displayDot()
            net.getNodeByName(loc['swSwitch']['name']).start([net.ctrl])
            self.displayDot()

            vpnInstances = self.builder.config['vpns']
            for vpn in self.vpnInstances:
                for site in vpn['sites']:
                    switch = net.getNodeByName(site['siteRouter']['name'])
                    switch.start([net.ctrl])
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
        siteRouter = site['siteRouter']
        serviceVm = site['serviceVm']
        borderRouter = self.getLocation(site['connectedTo'])['coreRouter']
        swSwitch =  self.getLocation(site['connectedTo'])['swSwitch']
        # find the hardware switch associated to this router
        vlan = site['vlan']
        # Create the site border router/switch
        switch = self.addSwitch(siteRouter['name'],listenPort=6634,dpid=siteRouter['dpid'])
        self.addLink(switch, borderRouter['name'])
        siteHosts=[]
        for host in hosts:
            h = self.addHost(host['name'])
            siteHosts.append(h)
            self.addLink(h,switch)
        # create VPN for the VPN instance and for that site
        vm = self.addHost(serviceVm['name'])
        # create a link to the software switch
        self.addLink(swSwitch['name'],vm)
        self.displayDot()

    def start(self,net):
        print "Set OpenFlow controller"
        self.setOpenFlow(net)
        print

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
        self.testbedNodes = {}
        self.vpnInstances = {}
        print("building SDN locations")
        locations=self.builder.config['topology']
        for loc in locations:
            self.buildLocation(location=loc)
        self.buildVpns()
        print"building network"
        self.buildRoutersLinks()
        print

class ESnetMininet(Mininet):

    def __init__(self, **args):
        global controllerIp, controllerPort
        self.topo = TestbedTopo()
        args['topo'] = self.topo
        args['switch'] = OVSKernelSwitch
        args['controller'] = RemoteController
        args['build'] = False
        Mininet.__init__(self, **args)
        self.ctrl = self.addController( 'c0', controller=RemoteController, ip=controllerIp, port=controllerPort)

    def start(self):
        "Start controller and switches."
        if not self.built:
            self.build()
 
        self.topo.start(self)

if __name__ == '__main__':
    setLogLevel( 'info' )
    # todo: real argument parsing.
    configFileName = None
    if len(sys.argv) > 1:
        configFileName = sys.argv[1]
        net = ESnetMininet(fileName=configFileName)
    else:
        net = ESnetMininet()
    print "Starts network"
    net.start()
    CLI(net)
    net.stop()
