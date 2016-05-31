#!/usr/bin/python
#
# ESnet Network Operating System (ENOS) Copyright (c) 2015, The Regents
# of the University of California, through Lawrence Berkeley National
# Laboratory (subject to receipt of any required approvals from the
# U.S. Dept. of Energy).  All rights reserved.
#
# If you have questions about your rights to use or distribute this
# software, please contact Berkeley Lab's Innovation & Partnerships
# Office at IPO@lbl.gov.
#
# NOTICE.  This Software was developed under funding from the
# U.S. Department of Energy and the U.S. Government consequently retains
# certain rights. As such, the U.S. Government has been granted for
# itself and others acting on its behalf a paid-up, nonexclusive,
# irrevocable, worldwide license in the Software to reproduce,
# distribute copies to the public, prepare derivative works, and perform
# publicly and display publicly, and to permit other to do so.
#
import struct,binascii

from layer2.common.api import Node, SDNPop, Link, Port, Site, Wan, Host, HwSwitch, SwSwitch, Switch
from layer2.testbed import dpid, oscars

from layer2.common.utils import Logger

# Logical POPs topology
poptopology=[
    ["denv","star"],
    ["denv","atla"],
    ["atla","wash"],
    ["star","wash"],
    ["star","aofa"],
    ["aofa","wash"],
    ["aofa","amst"],
    ["wash","cern"],
    ["amst","cern"]
]

defaultvlanbase=980
defaultvlaniter=10

# DENV
denvlinks=[
    ["denv-cr5","9/1/4","denv-tb-of-1","23"],
    ["denv-cr5","9/1/5","denv-tb-of-1","24"],
    ["denv-ovs","eth10","denv-tb-of-1","1"],
    ["denv-tbn-1","eth11","denv-tb-of-1","2"]
]
denv=["denv",'denv-tb-of-1',"denv-cr5","denv-ovs",denvlinks]

# WASH
washlinks = [
    ["wash-cr5","10/1/11","wash-tb-of-1","23"],
    ["wash-cr5","10/1/12","wash-tb-of-1","24"],
    ["wash-ovs","eth10","wash-tb-of-1","2"],    # Miswired, does not correspond to WASH deployment document
    ["wash-tbn-1","eth11","wash-tb-of-1","1"]   # Miswired, does not correspond to WASH deployment document
]

wash=["wash",'wash-tb-of-1',"wash-cr5","wash-ovs", washlinks]

# AOFA
aofalinks = [
    ["aofa-cr5","10/1/3","aofa-tb-of-1","23"],
    ["aofa-cr5","10/1/4","aofa-tb-of-1","24"],
    ["aofa-ovs","eth10","aofa-tb-of-1","1"],
    ["aofa-tbn-1","eth11","aofa-tb-of-1","2"]
]


aofa=["aofa",'aofa-tb-of-1',"aofa-cr5","aofa-ovs",aofalinks]

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
    ["amst-tbn-1","eth11","amst-tb-of-1","2"],
    ["amst-tbn-1","eth12","amst-tb-of-1","3"],
    ["amst-tbn-1","eth13","amst-tb-of-1","4"],
    ["amst-tbn-1","eth16","amst-tb-of-1","5"], # Proxmox-induced interface wiring
    ["amst-tbn-1","eth17","amst-tb-of-1","6"], # Proxmox-induced interface wiring
    ["amst-tbn-1","eth14","amst-tb-of-1","7"], # Proxmox-induced interface wiring
    ["amst-tbn-1","eth15","amst-tb-of-1","8"]  # Proxmox-induced interface wiring
]

amst=["amst",'amst-tb-of-1',"amst-cr5","amst-ovs",amstlinks]

# CERN
cernlinks = [
    ["cern-272-cr5","10/1/4","cern-272-tb-of-1","20"],
    ["cern-272-cr5","10/1/5","cern-272-tb-of-1","21"],
    ["cern-272-cr5","10/1/6","cern-272-tb-of-1","22"],
    ["cern-272-cr5","10/2/5","cern-272-tb-of-1","23"],
    ["cern-272-cr5","10/2/6","cern-272-tb-of-1","24"],
    ["cern-272-ovs","eth10","cern-272-tb-of-1","2"],    # Miswired, does not correspond to CERN-272 deployment document
    ["cern-272-tbn-1","eth11","cern-272-tb-of-1","1"],    # Miswired, does not correspond to CERN-272 deployment document
    ["cern-272-tbn-1","eth12","cern-272-tb-of-1","3"],
    ["cern-272-tbn-1","eth13","cern-272-tb-of-1","4"],
    ["cern-272-tbn-1","eth14","cern-272-tb-of-1","5"]
]

cern=["cern",'cern-272-tb-of-1',"cern-272-cr5","cern-272-ovs",cernlinks]

# ATLA
atlalinks = [
    ["atla-cr5","10/1/9","atla-tb-of-1","21"],
    ["atla-cr5","10/1/10","atla-tb-of-1","22"],
    ["atla-cr5","10/1/11","atla-tb-of-1","23"],
    ["atla-cr5","10/1/12","atla-tb-of-1","24"],
    ["atla-ovs","eth10","atla-tb-of-1","1"],
    ["atla-tbn-1","eth11","atla-tb-of-1","2"],
    ["atla-tbn-1","eth12","atla-tb-of-1","3"],
    ["atla-tbn-1","eth13","atla-tb-of-1","4"]
]
atla=["atla",'atla-tb-of-1',"atla-cr5","atla-ovs",atlalinks]

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
    ["star-tbn-4","eth11","star-tb-of-1","2"],
    ["star-tbn-4","eth12","star-tb-of-1","3"],
    ["star-tbn-4","eth13","star-tb-of-1","4"],
    ["star-tbn-4","eth14","star-tb-of-1","5"],
    ["star-tbn-4","eth15","star-tb-of-1","6"],
    ["star-tbn-4","eth16","star-tb-of-1","7"],
    ["star-tbn-4","eth17","star-tb-of-1","8"]
]

star=["star",'star-tb-of-1',"star-cr5","star-ovs",starlinks]

amst_tbn_1 = {
    'name': 'amst-tbn-1',
    'interfaces': [ {'name': 'eth10','mac':'90:e2:ba:89:e4:a8','props':{'data':False}}, \
                    {'name': 'eth11','mac':'90:e2:ba:89:e4:a9','props':{'data':True}}, \
                    {'name': 'eth12','mac':'90:e2:ba:89:e5:10','props':{'data':False}}, \
                    {'name': 'eth13','mac':'90:e2:ba:89:e5:11','props':{'data':False}}, \
                    {'name': 'eth16','mac':'00:02:c9:34:f8:00','props':{'data':False}}, \
                    {'name': 'eth17','mac':'00:02:c9:34:f8:01','props':{'data':False}}, \
                    {'name': 'eth14','mac':'90:e2:ba:89:e5:24','props':{'data':False}}, \
                    {'name': 'eth15','mac':'90:e2:ba:89:e5:25','props':{'data':False}} ],
    'pop':"amst"
}

cern_272_tbn_1 = {
    'name': 'cern-272-tbn-1',
    'interfaces': [ {'name': 'eth10','mac':'90:e2:ba:89:f5:00','props':{'data':False}}, \
                    {'name': 'eth11','mac':'90:e2:ba:89:f5:01','props':{'data':False}}, \
                    {'name': 'eth12','mac':'00:02:c9:34:f7:b0','props':{'data':False}}, \
                    {'name': 'eth13','mac':'00:02:c9:34:f7:b1','props':{'data':False}}, \
                    {'name': 'eth14','mac':'90:e2:ba:89:ee:a0','props':{'data':True}} ],
    'pop':"cern"
}

wash_tbn_1 = {
    'name': 'wash-tbn-1',
    'interfaces': [ {'name': 'eth10','mac':'00:60:dd:45:62:00','props':{'data':False}}, \
                    {'name': 'eth11','mac':'00:60:dd:46:52:30','props':{'data':True}} ],
    'pop':"wash"
}

star_tbn_4 = {
    'name': 'star-tbn-4',
    'interfaces': [ {'name': 'eth10','mac':'00:60:dd:45:65:09','props':{'data':False}}, \
                    {'name': 'eth11','mac':'00:60:dd:45:65:08','props':{'data':False}}, \
                    {'name': 'eth12','mac':'00:60:dd:45:64:f9','props':{'data':False}}, \
                    {'name': 'eth13','mac':'00:60:dd:45:64:f8','props':{'data':False}}, \
                    {'name': 'eth14','mac':'00:02:c9:24:48:00','props':{'data':False}}, \
                    {'name': 'eth15','mac':'00:02:c9:24:48:01','props':{'data':False}}, \
                    {'name': 'eth16','mac':'00:60:dd:45:64:ed','props':{'data':False}}, \
                    {'name': 'eth17','mac':'00:60:dd:45:64:ec','props':{'data':True}} ],
    'pop':"star"
}

denv_tbn_1 = {
    'name': 'denv-tbn-1',
    'interfaces': [ {'name': 'eth10','mac':'00:60:dd:46:52:32','props':{'data':False}}, \
                    {'name': 'eth11','mac':'00:60:dd:45:6f:b0','props':{'data':True}} ],
    'pop':"denv"
}

atla_tbn_1 = {
    'name': 'atla-tbn-1',
    'interfaces': [ {'name': 'eth10','mac':'90:e2:ba:89:e2:54','props':{'data':False}}, \
                    {'name': 'eth11','mac':'90:e2:ba:89:e2:55','props':{'data':False}}, \
                    {'name': 'eth12','mac':'90:e2:ba:89:f5:9c','props':{'data':False}}, \
                    {'name': 'eth13','mac':'90:e2:ba:89:f5:9d','props':{'data':False}} ],
    'pop':"atla"
}

aofa_tbn_1 = {
    'name': 'aofa-tbn-1',
    'interfaces': [ {'name': 'eth10','mac':'90:e2:ba:89:ee:7c','props':{'data':False}}, \
                    {'name': 'eth11','mac':'90:e2:ba:89:ee:7d','props':{'data':True}} ],
    'pop':"aofa"
}


tbns = {'amst-tbn-1':amst_tbn_1,
        'cern-272-tbn-1':cern_272_tbn_1,
        'wash-tbn-1':wash_tbn_1,
        'star-tbn-4':star_tbn_4,
        'denv-tbn-1':denv_tbn_1,
        'atla-tbn-1':atla_tbn_1,
        'aofa-tbn-1':aofa_tbn_1}


# SDN POP's
locations=[denv,wash,aofa,amst,cern,atla,star]
testbedPops = {"denv":denv,"wash":wash,"aofa":aofa,"amst":amst,"cern":cern,"atla":atla,"star":star}

def getPopRouter(popname):
    pop = getPop(popname)
    return pop[2]

def getPop(popname):
    global testbedPops
    return testbedPops[popname]


class TopoBuilder ():

    debug = False;
    logger = Logger('TopoBuilder')

    def __init__(self, fileName = None, controller = None):
        """
        Create a testbed topology
        :param fileName: filename for configuration (None for hard-coded default)
        :param network: Hash of ip, netmask for host IPv4 address assignment
        :param controller: Controller object (or subclass thereof)
        :return:
        """
        self.hostIndex = {} # [hostname] = Host
        self.switchIndex = {} # [switchname] = Switch
        self.linkIndex = {} # [linkname] = Links
        self.popIndex = {} # [popname] = SDNPop
        self.wan = Wan(name='esnet',topo=self)
        self.controller = controller
        self.locations = locations
        self.loadDefault()


    def getNode(self,name):
        if name in self.switchIndex:
            return self.switchIndex[name]
        elif name in self.hostIndex:
            return self.hostIndex[name]
        return None

    def addSwitch(self, switch):
        self.switchIndex[switch.name] = switch

    def addHost(self, host):
        self.hostIndex[host.name] = host

    def addSDNPop(self, popname, hwswitchname, coreroutername, swswitchname,links):
        """
        Configure the various elements of an SDN POP
        :param popname: Name of POP
        :param hwswitchname: Name of hardware SDN switch
        :param coreroutername: Name of core router
        :param swswitchname: Name of software SDN switch
        :param links: Set of physical links within the POP
        :return: None
        """
        pop = SDNPop(name=popname,
                     hwswitchname=hwswitchname,
                     coreroutername=coreroutername,
                     swswitchname=swswitchname)

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
        self.popIndex[popname] = pop

        for [n1,p1,n2,p2] in links:
            node1 = self.getNode(n1)
            node2 = self.getNode(n2)
            port1 = Port(name=p1,node=node1)
            port2 = Port(name=p2,node=node2)
            node1.addPort(port1)
            node2.addPort(port2)
            link = Link(ports = [port1,port2])
            self.linkIndex[link.name] = link


    def getLink(self,n1,p1,n2,p2,vlan):
        for link in self.linkIndex.values():
            endpoints = link.props['endpoints']
            v = link.props['vlan']
            port1 = endpoints[0]
            port2 = endpoints[1]
            node1 = port1.props['node']
            node2 = port2.props['node']
            if (node1.name,port1.name,node2.name,port2.name,v) == (n1,p1,n2,p2,vlan):
                return link
        return None


    def updateSwitch(self, switch):
        role = switch.get('role')
        if role: # hwSwitch, coreRouter, swSwitch
            switch.update({'controller':self.controller})


    def displaySwitches(self):
        print "\nName\t\t\tDPID\t\tODL Name\n"
        for sw in self.switchIndex.values():
            if 'dpid' in sw.props:
                hexdpid = binascii.hexlify(sw.props['dpid'])
                print sw.name,"\t",hexdpid,"\topenflow:" + str(int(hexdpid,16))
        print "\n\n"


    def loadDefault(self):

        # Adds Testbed hosts
        global tbns
        for (name,tbn) in tbns.items():
            host = Host(name=name,domain="testbed100.es.net")
            self.hostIndex[name] = host

        # init self.pops
        for location in self.locations:
            (popname, hwswitchname, coreroutername, swswitchname,links) = (location[0],
                                                                           location[1],
                                                                           location[2],
                                                                           location[3],
                                                                           location[4]
                                                                           )

            self.addSDNPop(popname, hwswitchname, coreroutername, swswitchname,links)


        for switch in self.switchIndex.values():
            self.updateSwitch(switch)

if __name__ == '__main__':
    builder = TopoBuilder()
    builder.displaySwitches()


	
