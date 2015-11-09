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

from layer2.testbed.oscars import getgri,getgrinode,displaygri
from layer2.testbed.topology import TestbedTopology,getlinks,linkednode


# Hardcode information about hosts. Eventually this should be discovered by the ENOS
# host agent registering its interfaces and other meta data.

amst_tbn_1 = {
    'name': 'amst-tbn-1',
    'interfaces': [ {'name': 'eth10','mac':'90:e2:ba:89:e4:a8','props':{'data':False}}, \
                    {'name': 'eth11','mac':'90:e2:ba:89:e4:a9','props':{'data':False}}, \
                    {'name': 'eth12','mac':'90:e2:ba:89:e5:10','props':{'data':False}}, \
                    {'name': 'eth13','mac':'90:e2:ba:89:e5:11','props':{'data':False}}, \
                    {'name': 'eth14','mac':'00:02:c9:34:f8:00','props':{'data':False}}, \
                    {'name': 'eth15','mac':'00:02:c9:34:f8:01','props':{'data':False}}, \
                    {'name': 'eth16','mac':'90:e2:ba:89:e5:24','props':{'data':False}}, \
                    {'name': 'eth17','mac':'90:e2:ba:89:e5:24','props':{'data':True}} ],
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

def connectgri(host,gri,hostvlan=100):
    pop = topo.builder.popIndex[host['pop']]
    core = pop.props['coreRouter'].name
    (core,coredom,coreport,corevlan) = getgrinode(gri,core)
    datapath = getdatapaths(host)[0] # Assumes the first datapath
    hostport = datapath['name']
    hwswitch = pop.props['hwSwitch'].name
    print "datapath",datapath
    # Find hwswith/port - core/port
    links = getlinks(core,hwswitch)
    corelink = None
    for link in links:
        (node,port) = linkednode (link,hwswitch)
        if port != None and port == coreport:
            # found the link between HwSwith and Core that ends to the OSCARS circuit.
            corelink = link
            break
    (node,hwport_tocore) = linkednode (corelink,core)
    # Find host/prot hwswitch/port
    links = getlinks(host,hwswitch)
    hostlink = None
    for link in links:
        (node,port) = linkednode (link,hwswitch)
        if port != None and port == hostport:
            # found the link between HwSwith and Core that ends to the OSCARS circuit.
            hostlink = link
            break
    (node,hwport_tohost) = linkednode (hostlink,host)
    print host,hostport,"--",hostvlan,'--',hwport_tohost,"##",hwswitch,"##",hwport_tocore,"--",corevlan








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


if __name__ == '__main__':
    # Retrieve topology
    if not 'topo' in globals():
        topo = TestbedTopology()
        globals()['topo'] = topo
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
            display(tbns[host])
    elif (cmd == "connect"):
        host = tbns[argv[2]]
        vlan = argv[4]
        if ('gri') in argv:
            gri = getgri(argv[6])
            if gri == None:
                print "unknown GRI"
                sys.exit()
            connectgri(host,gri)



