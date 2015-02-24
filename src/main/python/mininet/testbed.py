#!/usr/bin/python
import sys

from mininet.net import Mininet
from mininet.node import Controller, OVSKernelSwitch, RemoteController
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.topo import Topo

#
# VPN instances
# Each VPN instance is made of an array containing its name and an array of sites
# Each site  is an array of [hostnames,border router, VLAN] where hostnames is
# an array of hostnames of the site.
#

vpn1=["vpn1",[
    ["s1_1",["h1_1","h1_2"],"lbl",1,11],
    ["s1_2",["h1_3"],"star",1,12]
  ]
]

vpns=[vpn1]
# Locations with hardware openflow switch
# name,rt,nb of links
#
lbl=["lbl","mr2",2]
atla=["atla","cr5",4]
denv=["denv","cr5",2]
wash=["wash","cr5",2]
aofa=["aofa","cr5",2]
star=["star","cr5",8]
cern=["cern","cr5",5]
amst=["amst","cr5",8]


locations=[atla,lbl,denv,wash,aofa,star,cern,amst]
#
# OpenFlow controller IP and ports
#
controllerIp='192.168.56.1'
controllerPort=6633

#
# if viewAll is set to True, router will be made openflow and then will appear in the controller's topology.
#
viewAll = True

class ESnetTestbedTopo(Topo):

    #
    # Returns node name that will be acceptable for Mininet. Binding between real name and mininet name is added in nodeMap
    # Mininet's name are made by appending a - and the index
    #
    def makeMininetName(self,realName,host=False):
        index = 0
        if (host):
            index = self.hostIndex
            self.hostIndex = self.hostIndex + 1
        else:
            index = self.mininetIndex
            self.mininetIndex = self.mininetIndex + 1

        mininetName = realName + "_" + str(index)
        self.nodeMap[realName] = mininetName
        return mininetName
    #
    # Returns the real name of Mininet name
    #
    def makeRealName(self,mininetName):
        realName = "_".join(mininetName.split("_")[0:-1])
        return realName


    #
    # Creates nodes and links of a location
    #
    def buildLocation(self,location):
        locationName = location[0]
        routerName = locationName + "_R"
        switchName = locationName + "_S"
        ovsName = locationName + "_O"

        nbOfLinks = location[2]

        # creates nodes
        routerNode = self.addSwitch(self.makeMininetName(routerName))
        switchNode = self.addSwitch(self.makeMininetName(switchName), listenPort=6634)
        ovsNode = self.addSwitch(self.makeMininetName(ovsName), listenPort=6634)

        # creates links between router and switch and between switch and ovs. Assume same number
        # of links
        while nbOfLinks > 0:
            self.addLink(routerNode,switchNode)
            self.addLink(switchNode,ovsNode)
            nbOfLinks = nbOfLinks - 1
        self.displayDot()
        return [routerNode,switchNode,ovsNode]

    def buildRoutersLinks(self):
            global locations
            index = 0
            for fromLoc in locations:
                    fromNode = self.testbedNodes[fromLoc[0]][0] # router
                    if (index + 1) == len(locations):
                            break
                    for toLoc in locations[index+1:]:
                            toNode = self.testbedNodes[toLoc[0]][0]
                            # two links between routers. one best effort no cap, the other bandwidth limited to low.
                            self.addLink(fromNode,toNode)
                            self.addLink(fromNode,toNode)
                    index = index + 1
            self.displayDot()

    def setOpenFlow(self,net):
        global locations, viewAll

        for loc in locations:
            if viewAll:
                net.getNodeByName(self.testbedNodes[loc[0]][0]).start([net.ctrl])
		self.displayDot()
                for vpnName in self.vpnInstances:
                    vpn = self.vpnInstances[vpnName]
                    for siteName in vpn:
                        site = vpn[siteName]
                        switch = site[0]
                        net.getNodeByName(switch).start([net.ctrl])
			self.displayDot()

            net.getNodeByName(self.testbedNodes[loc[0]][1]).start([net.ctrl])
	    self.displayDot()
            net.getNodeByName(self.testbedNodes[loc[0]][2]).start([net.ctrl])
            self.displayDot()


    def displayNodes(self):
        global locations
        print "Mininet nodes:"
        for loc in locations:
            name = loc[0]
            router = self.testbedNodes[name][0]
            switch = self.testbedNodes[name][1]
            ovs = self.testbedNodes[name][2]
            print name + " router= " + str(router) + " switch= " + str(switch) + " ovs= " + str(ovs)
        print

    def displayDot(self):
        sys.stdout.write('.')
        sys.stdout.flush()

    def buildSite(self,site):
        siteName = site[0]
        hostNames = site[1]
        borderRouter = self.testbedNodes[site[2]][0]
	swSwitch =  self.testbedNodes[site[2]][1]
	# find the hardware switch associated to this router
        vlan = site[3]
        switchName = self.makeMininetName(siteName)
	# Create the site border router/switch
        switch = self.addSwitch(switchName)
        self.addLink(switch, borderRouter)
        siteHosts=[]
        for host in hostNames:
            h = self.addHost(self.makeMininetName(host, host=True))
            siteHosts.append(h)
            self.addLink(h,switch)
	# create VPN for the VPN instance and for that site
	vmName = siteName + "_V"
	vm = self.addHost(self.makeMininetName (vmName, host=True))
	# create a link to the software switch
	self.addLink(swSwitch,vm)

        self.displayDot()
        return [switch,siteHosts,vm]

    def start(self,net):
	print "Set OpenFlow controller"
	self.setOpenFlow(net)
	print

    def __init__(self):
	self.mininetIndex = 0  # Mininet seems to requires node names to end with a number that is incrementely increased
        self.hostIndex = 0
        self.nodeMap={} # Map matching real node name with the mininet name
        self.testbedNodes={} # Map of all nodes indexed by location name. The entroes are lists [router,switch,ovs]
        self.vpnInstances={}
        Topo.__init__(self)
        print("building SDN locations")
        for loc in locations:
            locationNodes = self.buildLocation(location=loc)
            self.testbedNodes[loc[0]] = locationNodes
        print
        print"building network"
        self.buildRoutersLinks()
        print
        for vpn in vpns:
            vpnName = vpn[0]
            sites = vpn[1]
            allSiteNodes = {};
            print "building VPN " + vpnName
            for site in sites:
                siteNodes = self.buildSite(site=site)
                allSiteNodes[site[0]] = siteNodes
            self.vpnInstances[vpnName] = allSiteNodes
            print
        self.displayNodes()

class ESnetMininet(Mininet):

    def __init__(self, **args):
	global controllerIp, controllerPort
        self.topo = ESnetTestbedTopo()
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
    net = ESnetMininet()
    print "Starts network"
    net.start()
    CLI(net)
    net.stop()
