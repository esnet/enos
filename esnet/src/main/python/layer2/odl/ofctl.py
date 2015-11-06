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
from layer2.testbed.dpid import decodeDPID

if not "creds" in globals():
    creds = ("admin","admin")
    globals()['creds'] = creds

def doGET(url,auth=True):
    req = urllib2.Request(url)
    global creds
    try:
        if auth:
            (user,password) = creds
            password_manager = urllib2.HTTPPasswordMgrWithDefaultRealm()
            password_manager.add_password(None, url, user, password)

            auth_manager = urllib2.HTTPBasicAuthHandler(password_manager)
            opener = urllib2.build_opener(auth_manager)
            urllib2.install_opener(opener)

        handler = urllib2.urlopen(req)
        return json.load(handler)
    except:
        return None

def showactive():
    getswitches()


def getswitches():
    url = "http://" + ctrl + ":8181/restconf/config/opendaylight-inventory:nodes/"
    response = doGET(url=url,auth=True)
    if response == None:
        print "no active swicthes"
        return None
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
    id = makeODLDPID(switch)
    if table == None:
        table = gettable(switch)
    url = "http://" + ctrl + ":8181/restconf/config/opendaylight-inventory:nodes/node/" + id + "/flow-node-inventory:table/" + table
    response = doGET(url=url,auth=True)
    if (response == None):
        print "No flow"
        return None

    tables = response['flow-node-inventory:table']
    for table in tables:
        tableid = table['id']
        flows = table['flow']
        print "Table ",tableid
        for flow in flows:
            id = flow['id']
            match = flow['match']
            inport = "*"
            if 'in-port' in match:
                inport = match['in-port']
            vlan = "*"
            if 'vlan-match' in match and 'vlan-id' in match['vlan-match'] and match['vlan-match']['vlan-id']['vlan-id-present']:
                vlan =  match['vlan-match']['vlan-id']['vlan-id']
            source = "*"
            dest = "*"
            if 'ethernet-match' in match:
                ethernet = match['ethernet-match']
                if 'ethernet-destination' in ethernet.keys():
                    dest = ethernet['ethernet-destination']['address']
                if 'ethernet-source' in ethernet.keys():
                    dest = ethernet['ethernet-source']['address']
            priority = flow ['priority']
            cookie = ""
            if 'cookie'  in flow:
                cookie = flow['cookie']
            print "\tflow id",id,"priority",priority,'cookie',cookie,"\n\t\tmatch: in_port",inport,"dl_dst",dest,"dl_src",source,"vlan",vlan
            instructions = flow['instructions']['instruction']
            print "\t\tinstructions:"
            for instruction in instructions:
                order = instruction['order']

                if 'meter' in instruction:
                    meter = instruction['meter']['meter-id']
                    print "\t\t\torder=",order,"meter",meter
                    continue

                if 'apply-actions' in instruction and 'action' in instruction['apply-actions']:
                    actions = instruction['apply-actions']['action']
                    print "\t\t\torder",order,"actions:"
                    for action in actions:
                        order2 = action['order']
                        if 'output-action' in action:
                            port = action['output-action']['output-node-connector']
                            max = action['output-action']['max-length']
                            print "\t\t\t\torder",order2,"output port",port,"maximum length",max
                            continue
                        if 'set-vlan-pcp-action' in action:
                            pcp = action['set-vlan-pcp-action']
                            print "\t\t\t\torder",order2,"set vlan pcp",pcp
                            continue
                        if 'set-field' in action:
                            if 'vlan-match' in action['set-field']:
                                present = action['set-field']['vlan-match']['vlan-id']['vlan-id-present']
                                vlan = action['set-field']['vlan-match']['vlan-id'] ['vlan-id']
                                print "\t\t\t\torder",order2,"set field vlan id",vlan,"is present",present
                                continue
                        if 'set-dl-dst-action' in action:
                            address = action['set-dl-dst-action']['address']
                            print "\t\t\t\torder",order2,"set dl-dst",address
                            continue
                        if 'set-dl-src-action' in action:
                            address = action['set-dl-src-action']['address']
                            print "\t\t\t\torder",order2,"set dl-src",address
                            continue
                        if 'set-queue-action' in action:
                            qid = action['set-queue-action']['queue-id']
                            print "\t\t\t\torder",order2,"set queue id",qid
                            continue
                        print "unkwon action:",action






def show(switch):
    if 'dpid' in switch.props:
        hexdpid = binascii.hexlify(switch.props['dpid'])
        print switch,"\tdpid: ",hexdpid,"\topenflow: " + str(int(hexdpid,16))
    return None

def makeODLDPID(switch):
    hexdpid = binascii.hexlify(sw.props['dpid'])
    bindpid = str(int(hexdpid,16))
    return "openflow:" + bindpid

def gettable(switch):
    id = switch.props['dpid']
    (vendor,role,location,id) = decodeDPID(id)
    if vendor == 1:
        # OVS
        return '0'
    if vendor == 2:
        # Corsa
        return '2'

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
    print "\t\tofctl dump-flows <switch-name> displays flows from the default table. ovs = table 0, corsa = table 2"
    print "\t\tofctl dump-flows <switch-name> table <table number> displays the flows of a given table "

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
        table = None
        if 'table' in argv:
            table = argv[4]
        dumpflows(switch=sw,table=table)

