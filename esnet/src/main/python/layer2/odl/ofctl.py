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

import urllib2
import sys
import binascii
import json

from layer2.testbed.topology import TestbedTopology
from layer2.testbed import dpid

if not "creds" in globals():
    creds = ("admin","admin")
    globals()['creds'] = creds

def doGET(url,auth=True):
    req = urllib2.Request(url)
    global creds
    if auth:
        (user,password) = creds
        password_manager = urllib2.HTTPPasswordMgrWithDefaultRealm()
        password_manager.add_password(None, url, user, password)

        auth_manager = urllib2.HTTPBasicAuthHandler(password_manager)
        opener = urllib2.build_opener(auth_manager)
        urllib2.install_opener(opener)

    handler = urllib2.urlopen(req)
    return json.load(handler)

def showactive():
    getswitches()


def getswitches():
    url = "http://" + ctrl + ":8181/restconf/config/opendaylight-inventory:nodes/"
    response = doGET(url=url,auth=True)
    nodes = response['nodes']['node']
    switches = []
    print "Active switches"
    for node in nodes:
        dpid = node['id']
        sw = getswitch(dpid=dpid)
        if sw == None:
            print "Active switch " + dpid + " is not in testbed topology."
            continue
        print sw.name
        switches.append(sw)
    print "\nSwitch list is stored into Pything global variable 'switches'"
    globals()['switches'] = switches

def dumpflows(switch,table):
    dpid = makeODLDPID(switch)
    url = "http://" + ctrl + ":8181/restconf/config/opendaylight-inventory:nodes/node/" + dpid + "/flow-node-inventory:table/" + table
    response = doGET(url=url,auth=True)
    flows = response['flow-node-inventory:table'][0]['flow']
    for flow in flows:
        id = flow['id']
        match = flow['match']
        inport = match['in-port']
        vlan = "*"
        if match['vlan-match']['vlan-id']['vlan-id-present']:
            vlan =  match['vlan-match']['vlan-id']['vlan-id']
        ethernet = match['ethernet-match']
        dest = "*"
        if 'ethernet-destination' in ethernet.keys():
            dest = ethernet['ethernet-destination']['address']
        source = "*"
        if 'ethernet-source' in ethernet.keys():
            dest = ethernet['ethernet-source']['address']

        actions = flow['instructions']
        priority = flow ['priority']

        globals()['actions'] = actions

        print "Flow id=",id ,"\n\tmatch: in_port=",inport,"dl_dst=",dest,"dl_src=",source,"vlan=",vlan




def show(switch):
    if 'dpid' in switch.props:
        hexdpid = binascii.hexlify(switch.props['dpid'])
        print switch,"\tdpid: ",hexdpid,"\topenflow: " + str(int(hexdpid,16))
    return None

def makeODLDPID(switch):
    dpid = switch.props['dpid']
    hexdpid = binascii.hexlify(sw.props['dpid'])
    bindpid = str(int(hexdpid,16))
    return "openflow:" + bindpid

def getswitch(name=None,dpid=None):
    if (name,dpid) == (None,None):
        print "invalid name and dpid"
        return None
    switch = None
    if name != None:
        switch = topo.builder.switchIndex[name]
    if dpid != None:
        for (x,sw) in topo.builder.switchIndex.items():
            if not 'dpid' in sw.props:
                # Not an openflow switch
                continue
            hexdpid = binascii.hexlify(sw.props['dpid'])
            bindpid = str(int(hexdpid,16))
            if dpid.lstrip("openflow:") in (hexdpid,bindpid):
                switch = sw
                break
    return switch


def print_syntax():
    print
    print "ofctl <cmd> <cmds options>"
    print
    print "Performs various OpenFlow related action on switches. Commands are:"
    print "\nhelp"
    print "\tPrints this help."
    print "\nset-ctrl <controller host>"
    print "\tThis command is used to set the host where the OpenFlow controller is running."
    print "\tIt can be an IP address or a DNS name. testbed100.es.net is added if necessary."
    print "\tFor instance:"
    print "\t\tofctl set-ctrl aofa-tbn-1 or ofctl set-ctrl aofa-tbn-1.testbed100.es.net"
    print "\tNote that the controller host name is set in the python global variable"
    print "\tand has to be set only once within a session."
    print "\nshow-ctrl"
    print "\tDisplays the host where the OpenFlow controller is running"
    print "\nset-user <login> <password>"
    print "\tSet the user and password that is authorized to use the openflow controller."
    print "\tThis operation needs to be only once within a session. Default is admin/admin"
    print "\nget-switch <name:dpid> [dpid]"
    print "\tRetrieves the switch object refered by either its name or its dpid."
    print "\tThe switch object is then stored into a global python variable named 'switch'"
    print "\tThe DPID can be of variable format that are automatically dected."
    print "\tIt can be hexadecimal or binary, with or without 'openflow:' prefix"
    print "\tFor instance:"
    print "\t\tofctl get-switch amst-tb-of-1"
    print "\t\tofctl get-switch dpid 0201007374617201"
    print "\t\tofctl get-switch dpid 144397081500677121"
    print "\t\t ofctl get-switch dpid openflow:144397081500677121"
    print "\nshow-switch <name>"
    print "\tDisplays the DPID in various format of the switch"
    print "\nshow-active"
    print "\tshows all connected switches and returns the list of switches into Python list."
    print "\ndump-flows <switch name> <table>"
    print "\tShows flow entries of the given switch"

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
    elif cmd == "set-ctrl":
        ctrl = argv[2]
        if not "testbed" in ctrl or ctrl == None:
            ctrl += ".testbed100.es.net"
        globals()['ctrl'] = ctrl
    elif cmd == "set-user":
        creds = (argv[2],argv[3])
    elif cmd == "get-switch":
        name = argv[2]
        dpid = None
        if len(argv) > 3 and argv[2] == "dpid":
            dpid = argv[3]
            name = None
        switch = getswitch(name=name,dpid=dpid)
        if switch == None:
            print "unknown switch"
            sys.exit(0)
        globals()['switch'] = switch
        print "switch " + switch.name + " has been set to the global python variable 'switch'"
    elif cmd == "show-ctrl":
        print ctrl
    elif cmd == "show-switch":
        sw = getswitch(name=argv[2])
        show(switch=sw)
    elif cmd == "show-active":
        showactive()
    elif cmd == "dump-flows":
        sw = getswitch(name=argv[2])
        table = argv[3]
        dumpflows(switch=sw,table=table)

