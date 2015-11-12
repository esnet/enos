#!/usr/bin/python
#
# ENOS, Copyright (c) 2015, The Regents of the University of California,
# through Lawrence Berkeley National Laboratory (subject to receipt of any
# required approvals from the U.S. Dept. of Energy).  All rights reserved.
#
# If you have questions about your rights to use or distribute this software,
# please contact Berkeley Lab's Technology Transfer Department at TTD@lbl.gov.
#
# NOTICE.  This software is owned by the U.S. Department of Energy.  As such,
# the U.S. Government has been granted for itself and others acting on its
# behalf a paid-up, nonexclusive, irrevocable, worldwide license in the Software
# to reproduce, prepare derivative works, and perform publicly and display
# publicly.  Beginning five (5) years after the date permission to assert
# copyright is obtained from the U.S. Department of Energy, and subject to
# any subsequent five (5) year renewals, the U.S. Government is granted for
# itself and others acting on its behalf a paid-up, nonexclusive, irrevocable,
# worldwide license in the Software to reproduce, prepare derivative works,
# distribute copies to the public, perform publicly and display publicly, and
# to permit others to do so.
#

from layer2.testbed.oscars import getgri,getgrinode,displaygri,griendpoints
from layer2.testbed.topology import TestbedTopology,getlinks,linkednode
from layer2.odl.ofctl import corsaforward
from layer2.testbed.topology import TestbedTopology


# Hardcode information about hosts. Eventually this should be discovered by the ENOS
# host agent registering its interfaces and other meta data.

default_controller="aofa-tbn-1.testbed100.es.net"

amst_tbn_1 = {
    'name': 'amst-tbn-1',
    'interfaces': [ {'name': 'eth10','mac':'90:e2:ba:89:e4:a8','props':{'data':False}}, \
                    {'name': 'eth11','mac':'90:e2:ba:89:e4:a9','props':{'data':False}}, \
                    {'name': 'eth12','mac':'90:e2:ba:89:e5:10','props':{'data':False}}, \
                    {'name': 'eth13','mac':'90:e2:ba:89:e5:11','props':{'data':False}}, \
                    {'name': 'eth14','mac':'00:02:c9:34:f8:00','props':{'data':False}}, \
                    {'name': 'eth15','mac':'00:02:c9:34:f8:01','props':{'data':False}}, \
                    {'name': 'eth16','mac':'90:e2:ba:89:e5:24','props':{'data':False}}, \
                    {'name': 'eth17','mac':'90:e2:ba:89:e5:25','props':{'data':True}} ],
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
                    {'name': 'eth17','mac':'00:60:dd:45:64:ec','props':{'data':False}} ],
    'pop':"star"
}

denv_tbn_1 = {
    'name': 'denv-tbn-1',
    'interfaces': [ {'name': 'eth10','mac':'00:60:dd:46:52:32','props':{'data':False}}, \
                    {'name': 'eth11','mac':'00:60:dd:45:6f:b0','props':{'data':False}} ],
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
                    {'name': 'eth11','mac':'90:e2:ba:89:ee:7d','props':{'data':False}} ],
    'pop':"aofa"
}


tbns = {'amst-tbn-1':amst_tbn_1,
        'cern-272-tbn-1':cern_272_tbn_1,
        'wash-tbn-1':wash_tbn_1,
        'star-tbn-4':star_tbn_4,
        'denv-tbn-1':denv_tbn_1,
        'atla-tbn-1':atla_tbn_1,
        'aofa-tbn-1':aofa_tbn_1}

def getdatapaths(host):
    interfaces = []
    for interface in host['interfaces']:
        if interface['props']['data']:
            interfaces.append(interface)
    return interfaces

def display(host):
    hostname = host['name']
    print "Host:",hostname
    print "\tinterfaces:"
    for interface in tbns[hostname]['interfaces']:
        datastatus = "Available"
        if not interface['props']['data']:
            datastatus = "Reserved for OVS"
        print "\t\tname", interface['name'],"mac",interface['mac'],datastatus

def connectremoteplane(switch,
                       host,
                       hostvlan,
                       remotehost_port,
                       remotehost,
                       remotehost_vlan,
                       remotehwport_tocore,
                       corevlan,
                       gri,
                       meter=3,
                       dobroadcast=False,
                       host_rewitemac = None):
    global default_controller
    hostmac = getdatapaths(host)[0]['mac']
    translated_hostmac = hostmac
    if host_rewitemac != None:
        translated_hostmac = host_rewitemac

    baseid = host['name'] + ":"+str(hostvlan)+"-"+gri.getName()
    if dobroadcast:
        flowid = baseid + "-broadcast-out"
        broadcast = "FF:FF:FF:FF:FF:FF"
    flowid = baseid + "to-remote-host"

    corsaforward (switch,
                  flowid,
                  remotehost_port,
                  hostmac,
                  remotehost_vlan,
                  remotehwport_tocore,
                  translated_hostmac,
                  corevlan,
                  meter,
                  controller=default_controller)


def connectdataplane(switch,
                     host,
                     hostport,
                     hostvlan,
                     sw,
                     tohostport,
                     tocoreport,
                     tocorevlan,
                     gri,
                     meter=3,
                     dobroadcast=False,
                     host_rewitemac = None):
    global default_controller
    baseid = host['name'] +":"+hostport+":"+str(hostvlan)+"-"+gri.getName()
    hostmac = getdatapaths(host)[0]['mac']
    translated_hostmac = hostmac
    if host_rewitemac != None:
        translated_hostmac = host_rewitemac
    if dobroadcast:
        broadcast = "FF:FF:FF:FF:FF:FF"
        flowid = baseid + "-broadcast-out"
        corsaforward (switch,
                      flowid,
                      tohostport,
                      broadcast,
                      hostvlan,
                      tocoreport,
                      broadcast,
                      tocorevlan,
                      meter,
                      controller=default_controller)

        flowid = baseid + "-broadcast-in"
        corsaforward (sw,
                      flowid,
                      tocoreport,
                      broadcast,
                      tocorevlan,
                      tohostport,
                      broadcast,
                      hostvlan,
                      meter,
                      controller=default_controller)

    flowid = baseid + "-to-host"
    corsaforward (sw,
                  flowid,
                  tocoreport,
                  translated_hostmac,
                  tocorevlan,
                  tohostport,
                  hostmac,
                  hostvlan,
                  meter,
                  controller=default_controller)


def getgriport(hwswitch,core,griport):
    """
    In the following logical topology <Host> - <HwSwitch> - <Core Router>, the OSCARS circuits ends onto the
    port on the core router connected to the HwSwitch. This function returns the port on the HwSwitch that
    is connected to the the core router when the OSCARS circuit terminates.
    """
    hwswitchname = hwswitch.name
    corename = core.name
    links = getlinks(corename, hwswitchname)
    if links == None or len(links) == 0:
        print "No links from",corename,"to",hwswitchname
        return False
    corelink = None
    for link in links:
        (node,port) = linkednode (link, hwswitchname)
        if port != None and port == griport:
            # found the link between HwSwith and Core that ends to the OSCARS circuit.
            corelink = link
            break
    (node,hwport_tocore) = linkednode (corelink,corename)
    return hwport_tocore

def connect (localpop,
             remotepop,
             host,
             remotehost,
             gri,
             hostvlan,
             remotehostvlan,
             meter=3,
             host_rewitemac = None):
    hostname = host['name']
    remotehostname = remotehost['name']
    core = localpop.props['coreRouter']
    corename = core.name
    (corename,coredom,coreport,corevlan) = getgrinode(gri,corename)
    remotecore = remotepop.props['coreRouter']
    remotecorename = remotecore.name
    (remotecorename,remotecoredom,remotecoreport,remotecorevlan) = getgrinode(gri,remotecorename)
    datapath = getdatapaths(host)[0] # Assumes the first datapath
    hostport = datapath['name']
    remotedatapath = getdatapaths(remotehost)[0] # Assumes the first datapath
    remotehostport = remotedatapath['name']
    hwswitch = localpop.props['hwSwitch']
    hwswitchname = hwswitch.name
    remotehwswitch = remotepop.props['hwSwitch']
    remotehwswitchname = remotehwswitch.name
    remotelinks = getlinks(remotecorename, remotehwswitchname)
    # Find hwswith/port - core/port
    hwport_tocore = getgriport(hwswitch,core,coreport)
    # Find remotehwswith/port - remotecore/port
    remotehwport_tocore = getgriport(remotehwswitch,remotecore,remotecoreport)

    # Find the port on the HwSwitch that is connected to the host's port
    links = getlinks(hostname, hwswitchname)
    if links == None or len(links) == 0:
        print "No links from",hostname,"to",hwswitchname
        return False
    hostlink = None
    for link in links:
        (node,port) = linkednode (link, hwswitchname)
        if port != None and port == hostport:
            # found the link
            hostlink = link
            break
    (node,hwport_tohost) = linkednode ( hostlink,hostname)

    connectdataplane(hwswitch,
                     host,
                     hostport,
                     hostvlan,
                     hwswitch,
                     hwport_tohost,
                     hwport_tocore,
                     corevlan,
                     gri,
                     meter,
                     host_rewitemac = host_rewitemac)

    # Find the port on the remote HwSwitch that is connected to the remote host's port
    links = getlinks(remotehostname, remotehwswitchname)
    if links == None or len(links) == 0:
        print "No links from",remotehostname,"to",remotehwswitchname
        return False
    hostlink = None
    for link in links:
        (node,port) = linkednode (link, remotehwswitchname)
        if port != None and port == remotehostport:
            # found the link
            hostlink = link
            break

    (node,remotehwport_tohost) = linkednode ( hostlink,remotehostname)

    connectremoteplane(switch = remotehwswitch,
                       host = host,
                       hostvlan = hostvlan,
                       remotehost_port = remotehwport_tohost,
                       remotehost = remotehost,
                       remotehost_vlan = remotehostvlan,
                       remotehwport_tocore =remotehwport_tocore,
                       corevlan = corevlan,
                       gri = gri,
                       meter = meter,
                       host_rewitemac = host_rewitemac)

    return True


def connectgri(host,
               gri,
               remotehost,
               hostvlan,
               remotehostvlan,
               meter=3,
               host_rewitemac=None):
    # Get both endpoints of the GRI
    (e1,e2) = griendpoints(gri)
    hostpop = topo.builder.popIndex[host['pop']]
    core1 = topo.builder.switchIndex[e1[1]]
    core2 = topo.builder.switchIndex[e2[1]]
    pop1 = core1.props['pop']
    pop2 = core2.props['pop']
    remotepop = None
    if hostpop.name == pop1.name:
        remotepop = pop2
    elif hostpop.name == pop2.name:
        remotepop = pop1
    if remotepop == None:
        print "gri",gri, "does not provide connectivity from",host,"to",remotehost
        return False

    res = connect(localpop = hostpop,
                  remotepop = remotepop,
                  host = host,
                  remotehost = remotehost,
                  gri = gri,
                  hostvlan = hostvlan,
                  remotehostvlan = remotehostvlan,
                  meter = meter,
                  host_rewitemac = host_rewitemac)
    if not res:
        return

    return True


def print_syntax():
    print
    print "hostctl <cmd> <cmds options>"
    print "Configures testbed hosts and their datapath. Commands are:"
    print " Commands are:"
    print "\nhelp"
    print "\tPrints this help."
    print "\nshow-host <host name | all> Displays information about a host or all hosts"
    print "\nconnect <hostname> vlan <vlan> gri <gri> Sets the datapath to the end of the specified OSCARS GRI."
    print "\tthe circuits terminates on the host at the specified vlan."

    print


# Retrieve topology
if not 'topo' in globals() or topo == None:
    topo = TestbedTopology()
    globals()['topo'] = topo


if __name__ == '__main__':
    global topo
    argv = sys.argv

    cmd = argv[1]
    if cmd == "help":
        print_syntax()
    elif cmd == "show-host":
        host = argv[2]
        if host == 'all':
            for (name,host) in tbns.items():
                display(host)
                print
        else:
            if not host in tbns:
                print "unknown host"
                sys.exit()
            display(tbns[host])
    elif (cmd == "connect"):
        if not host in tbns:
            print "unknown host"
            sys.exit()
        host = tbns[argv[2]]
        vlan = argv[4]
        if ('gri') in argv:
            gri = getgri(argv[6])
            if gri == None:
                print "unknown GRI"
                sys.exit()
            connectgri(host,gri)



