#!/usr/bin/python

import struct,binascii
from array import array

from common.api import Node, SDNPop, Link, Port, Site, Wan, VPN, Host, SiteRouter, CoreRouter, HwSwitch, SwSwitch
from common.mac import MACAddress

# All switches including site routers, core routers, hw switches, and sw switches should
# not have the same name so that the name of each port could be unique.
# site = [siteRouterName, [hostNames], popName, portNo]
# Note: Since flowmod could not forward a packet to where it comes from,
#  multiple sites in the same pop must have different portNo! (otherwise, the broadcast won't work.)
lblsite = ["lbl.gov",['lbl-diskpt1'],"denv", 0]
anlsite = ["anl.gov",['lbl-diskpt1'],"wash", 0]
bnlsite = ["cern.ch",['lbl-diskpt1'],"aofa", 0]

sites = [lblsite, anlsite, bnlsite]

denv=["denv",'denv-tb-of-1',"denv-cr5",1]
wash=["wash",'wash-tb-of-1',"wash-cr5",1]
aofa=["aofa",'aofa-tb-of-1',"aofa-cr5",1]


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
        self.mininetToRealNames = {}
        self.controller = controller

        if fileName != None:
            self.loadConfiguration(fileName)
        else:
            self.locations = locations
            self.sitesConfig = sites
        self.loadDefault()

    def displaySwitches(self):
        print "\nName\t\t\tDPID\t\tODL Name\tMininet Name\n"
        for sw in self.switches:
            if 'dpid' in sw.props:
                print sw.name,"\t",binascii.hexlify(sw.props['dpid']),"\topenflow:" + str(sw.props['dpid'][7]),"\t",sw.props['mininetName']
        print "\n\n"

    def displayHosts(self,vpn):
        print "\nName\t\tIPv4 Address\tMininet Name\t"
        for host in self.hosts:
            print h.name,"\t",h.props['ip'],"\t",h.props['mininetName']
        print "\n\n"




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


	
