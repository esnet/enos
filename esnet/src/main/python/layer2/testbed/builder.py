#!/usr/bin/python

import struct,binascii
from array import array

from layer2.common.api import Node, SDNPop, Link, Port, Site, Wan, VPN, Host, HwSwitch, SwSwitch
from layer2.common.mac import MACAddress
from layer2.testbed import dpid

# All switches including site routers, core routers, hw switches, and sw switches should
# not have the same name so that the name of each port could be unique.
# site = [siteRouterName, [hostNames], popName, portNo]
# Note: Since flowmod could not forward a packet to where it comes from,
#  multiple sites in the same pop must have different portNo! (otherwise, the broadcast won't work.)

# Simulated sites ESnet production diskpt's
lblsite = ["lbl.gov",['lbl-diskpt1'],"denv"]
anlsite = ["anl.gov",['lbl-diskpt1'],"wash"]
bnlsite = ["cern.ch",['lbl-diskpt1'],"aofa"]

sites = [lblsite, anlsite, bnlsite]

# DENV
denvlinks=[
    ["denv-cr5","9/1/4","denv-tb-of-1","23"],
    ["denv-cr5","9/1/5","denv-tb-of-1","24"],
    ["denv-ovs","eth10","denv-tb-of-1","1"],
    ["denv-ovs","eth11","denv-tb-of-1","2"]
]
denv=["denv",'denv-tb-of-1',"denv-cr5",denvlinks]


# WASH
washlinks = [
    ["wash-cr5","10/1/11","wash-tb-of-1","23"],
    ["wash-cr5","10/1/12","wash-tb-of-1","24"],
    ["wash-ovs","eth10","wash-tb-of-1","1"],
    ["wash-ovs","eth11","wash-tb-of-1","2"]
]
wash=["wash",'wash-tb-of-1',"wash-cr5", washlinks]

# AOFA
aofalinks = [
    ["aofa-cr5","10/1/3","aofa-tb-of-1","23"],
    ["aofa-cr5","10/1/4","aofa-tb-of-1","24"],
    ["aofa-ovs","eth10","aofa-tb-of-1","1"],
    ["aofa-ovs","eth11","aofa-tb-of-1","2"]
]
aofa=["aofa",'aofa-tb-of-1',"aofa-cr5",aofalinks]

# AMST
amstlinks = [
    ["amst-cr5","10/1/3","amst-tb-of-1","17"],
    ["amst-cr5","10/1/4","amst-tb-of-1","18"],
    ["amst-cr5","10/1/5","amst-tb-of-1","19"],
    ["amst-cr5","10/1/6","amst-tb-of-1","20"],
    ["amst-cr5","10/2/1","amst-tb-of-1","21"],
    ["amst-cr5","10/2/2","amst-tb-of-1","22"],
    ["amst-cr5","10/2/3","amst-tb-of-1","23"],
    ["amst-cr5","10/2/4","amst-tb-of-1","24"],
    ["amst-ovs","eth10","amst-tb-of-1","1"],
    ["amst-ovs","eth11","amst-tb-of-1","2"],
    ["amst-ovs","eth12","amst-tb-of-1","3"],
    ["amst-ovs","eth13","amst-tb-of-1","4"],
    ["amst-ovs","eth14","amst-tb-of-1","5"],
    ["amst-ovs","eth15","amst-tb-of-1","6"],
    ["amst-ovs","eth16","amst-tb-of-1","7"],
    ["amst-ovs","eth17","amst-tb-of-1","8"]
]
amst=["amst",'amst-tb-of-1',"amst-cr5",amstlinks]

# CERN
cernlinks = [
    ["cern-cr5","10/1/4","cern-tb-of-1","20"],
    ["cern-cr5","10/1/5","cern-tb-of-1","21"],
    ["cern-cr5","10/1/6","cern-tb-of-1","22"],
    ["cern-cr5","10/2/5","cern-tb-of-1","23"],
    ["cern-cr5","10/2/6","cern-tb-of-1","24"],
    ["cern-ovs","eth10","cern-tb-of-1","1"],
    ["cern-ovs","eth11","cern-tb-of-1","2"],
    ["cern-ovs","eth12","cern-tb-of-1","3"],
    ["cern-ovs","eth13","cern-tb-of-1","4"],
    ["cern-ovs","eth14","cern-tb-of-1","5"]
]
cern=["cern",'cern-tb-of-1',"cern-cr5",cernlinks]

# ATLA
atlalinks = [
    ["atla-cr5","10/1/9","atla-tb-of-1","21"],
    ["atla-cr5","10/1/10","atla-tb-of-1","22"],
    ["atla-cr5","10/1/10","atla-tb-of-1","23"],
    ["atla-cr5","10/1/11","atla-tb-of-1","24"],
    ["atla-ovs","eth10","atla-tb-of-1","1"],
    ["atla-ovs","eth11","atla-tb-of-1","2"],
    ["atla-ovs","eth12","atla-tb-of-1","3"],
    ["atla-ovs","eth13","atla-tb-of-1","4"]
]
atla=["atla",'atla-tb-of-1',"atla-cr5",atlalinks]

# STAR
starlinks = [
    ["star-cr5","9/2/3","star-tb-of-1","17"],
    ["star-cr5","9/2/4","star-tb-of-1","18"],
    ["star-cr5","9/2/5","star-tb-of-1","19"],
    ["star-cr5","9/2/6","star-tb-of-1","20"],
    ["star-cr5","10/1/5","star-tb-of-1","21"],
    ["star-cr5","10/1/6","star-tb-of-1","22"],
    ["star-cr5","10/1/11","star-tb-of-1","23"],
    ["star-cr5","10/1/12","star-tb-of-1","24"],
    ["star-ovs","eth10","star-tb-of-1","1"],
    ["star-ovs","eth11","star-tb-of-1","2"],
    ["star-ovs","eth12","star-tb-of-1","3"],
    ["star-ovs","eth13","star-tb-of-1","4"],
    ["star-ovs","eth14","star-tb-of-1","5"],
    ["star-ovs","eth15","star-tb-of-1","6"],
    ["star-ovs","eth16","star-tb-of-1","7"],
    ["star-ovs","eth17","star-tb-of-1","8"]
]
star=["star",'star-tb-of-1',"star-cr5",starlinks]

# LBL  POP is not yet deployed


# SDN POP's
locations=[denv,wash,aofa,amst,cern,atla,star]



class TopoBuilder ():

    debug = False;

    def __init__(self, fileName = None, controller = None):
        """
        Create a testbed topology
        :param fileName: filename for configuration (None for hard-coded default)
        :param network: Hash of ip, netmask for host IPv4 address assignment
        :param controller: Controller object (or subclass thereof)
        :return:
        """
        self.hostID = 1
        self.switchID = 1
        self.dpidIndex = 1
        self.nodes = {}
        self.hosts = []
        self.hostIndex = {} # [hostname] = Host
        self.switches = []
        self.switchIndex = {} # [switchname] = Switch
        self.links = [] # all links including those in sites, pops, vpns, and wan
        self.linkIndex = {} # [linkname] = Link
        self.ports = [] # all ports
        self.portIndex = {} # [portname] = Port
        self.sites = []
        self.siteIndex = {} # [sitename] = Site
        self.sitesConfig = []
        self.pops = []
        self.popIndex = {} # [popname] = SDNPop
        self.wan = Wan(name='esnet')
        self.dpidToName = {}
        self.controller = controller

        if fileName != None:
            self.loadConfiguration(fileName)
        else:
            self.locations = locations
            self.sitesConfig = sites
        self.loadDefault()

    def addSwitch(self, switch):
        self.switches.append(switch)
        self.switchIndex[switch.name] = switch

    def addHost(self, host):
        self.hosts.append(host)
        self.hostIndex[host.name] = host

    def addPort(self, port):
        if not port.name in self.portIndex:
            self.ports.append(port)
            self.portIndex[port.name] = port

    def addLink(self, link):
        self.links.append(link)
        self.linkIndex[link.name] = link
        self.addPort(link.props['endpoints'][0])
        self.addPort(link.props['endpoints'][1])

    def addLinks(self, links):
        for link in links:
            self.addLink(link)

    def addSDNPop(self, popname, hwswitchname, coreroutername, swswitchname,links):
        pop = SDNPop(name=popname,
                     hwswitchname=hwswitchname,
                     coreroutername=coreroutername,
                     swswitchname=swswitchname,
                     links=links)

        hwSwitch = pop.props['hwSwitch']
        swSwitch = pop.props['swSwitch']
        coreRouter = pop.props['coreRouter']
        hwSwitch.props['dpid'] = dpid.encodeDPID(location=popname,
                                                 vendor=dpid.Vendors.Corsa,
                                                 role=dpid.Roles.POPHwSwitch,
                                                 id=1)
        swSwitch.props['dpid'] = dpid.encodeDPID(location=popname,
                                                 vendor=dpid.Vendors.OVS,
                                                 role=dpid.Roles.POPSwSwitch,
                                                 id=1)
        self.addSwitch(hwSwitch)
        self.addSwitch(coreRouter)
        self.addSwitch(swSwitch)
        self.addHost(pop.props['serviceVm'])
        self.popIndex[popname] = pop
        self.pops.append(pop)
        for l in links:
            (n1,p1,n2,p2) = (self.switchIndex[l[0]],
                             Port(l[1]),
                             self.switchIndex[l[2]],
                             Port(l[3]))
            p1.props['node'] = n1
            n1.props['ports'][p1.name] = p1
            p2.props['node'] = n2
            n2.props['ports'][p2.name] = p2
            self.addPort(p1)
            self.addPort(p2)
            link = Link(name='%s:%s-%s:%s' % (n1.name,p1.name,n2.name,n2.name),ports=[p1,p2])
            if hwSwitch.name == n1.name and swSwitch.name == n2.name:
                link.setPortType('HwToSw.WAN', 'SwToHw.WAN')
            elif hwSwitch.name == n2.name and swSwitch.name == n1.name:
                link.setPortType('SwToHw.WAN', 'HwToSw.WAN')
            elif hwSwitch.name == n1.name and coreRouter.name == n2.name:
                link.setPortType('HwToCore.WAN', 'CoreToHw.WAN')
            elif hwSwitch.name == n2.name and coreRouter.name == n1.name:
                link.setPortType('CoreToCore.WAN', 'HwToCore.WAN')
            self.addLink(link)

    def displaySwitches(self):
        print "\nName\t\t\tDPID\t\tODL Name\n"
        for sw in self.switches:
            if 'dpid' in sw.props:
                hexdpid = binascii.hexlify(sw.props['dpid'])
                print sw.name,"\t",hexdpid,"\topenflow:" + str(int(hexdpid,16))
        print "\n\n"

    def loadDefault(self):

        # init self.pops
        for location in self.locations:
            (popname, hwswitchname, coreroutername, swswitchname,links) = (location[0],
                                                                           location[1],
                                                                           location[2],
                                                                           location[0] + "-ovs",
                                                                           location[3]
                                                                           )
            self.addSDNPop(popname, hwswitchname, coreroutername, swswitchname,links)

        # Create links

        # create mesh between core routers, attached to VLANs between the core routers and hardware switches
        """
        self.wan.connectAll(self.pops, 1000)
        self.addLinks(self.wan.props['links'])

        for (sitename, hostnames, popname, portno) in self.sitesConfig:
            site = self.addSite(sitename, popname, portno)
            for name in hostnames:
                hostname = name + "@" + sitename
                host = Host(name=hostname)
                site.addHost(host)
                self.addHost(host)
            self.addLinks(site.props['links'])

        for host in self.hosts:
            self.updateHost(host)
        for switch in self.switches:
            self.updateSwitch(switch)
        """


    def loadConfiguration(self,fileName):
        """
        loads the topology Mininet needs to create as described in a file. The format is a dictionary with
        the following structure:


        :param fileName:
        :return:
        """
        f = open(fileName,"r")
        self.config = eval (f.read())
        f.close()

if __name__ == '__main__':
    topo = TopoBuilder()
    topo.displaySwitches()


	
