#!/usr/bin/python

import struct,binascii
from array import array

from layer2.common.api import Node, SDNPop, Link, Port, Site, Wan, VPN, Host, HwSwitch, SwSwitch
from layer2.common.mac import MACAddress

# All switches including site routers, core routers, hw switches, and sw switches should
# not have the same name so that the name of each port could be unique.
# site = [siteRouterName, [hostNames], popName, portNo]
# Note: Since flowmod could not forward a packet to where it comes from,
#  multiple sites in the same pop must have different portNo! (otherwise, the broadcast won't work.)
lblsite = ["lbl.gov",['lbl-diskpt1'],"denv"]
anlsite = ["anl.gov",['lbl-diskpt1'],"wash"]
bnlsite = ["cern.ch",['lbl-diskpt1'],"aofa"]

sites = [lblsite, anlsite, bnlsite]

denv=["denv",'denv-tb-of-1',"denv-cr5"]
wash=["wash",'wash-tb-of-1',"wash-cr5"]
aofa=["aofa",'aofa-tb-of-1',"aofa-cr5"]


# Default locations
locations=[denv,wash,aofa]

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

    def addSDNPop(self, popname, hwswitchname, coreroutername, swswitchname):
        pop = SDNPop(name=popname, hwswitchname=hwswitchname, coreroutername=coreroutername, swswitchname=swswitchname)
        self.addSwitch(pop.props['hwSwitch'])
        self.addSwitch(pop.props['coreRouter'])
        self.addSwitch(pop.props['swSwitch'])
        self.addHost(pop.props['serviceVm'])
        # self.addLinks(pop.props['links'])
        self.popIndex[popname] = pop
        self.pops.append(pop)

    def displaySwitches(self):
        print "\nName\t\t\tDPID\t\tODL Name\n"
        for sw in self.switches:
            if 'dpid' in sw.props:
                print sw.name,"\t",binascii.hexlify(sw.props['dpid']),"\topenflow:" + str(sw.props['dpid'][7])
        print "\n\n"

    def loadDefault(self):

        # init self.pops
        for location in self.locations:
            (popname, hwswitchname, coreroutername, swswitchname) = (location[0], location[1], location[2], location[0] + "-ovs")
            self.addSDNPop(popname, hwswitchname, coreroutername, swswitchname)

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


	
