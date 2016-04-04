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
import urllib2
import sys
import binascii
import json

from layer2.testbed.topology import TestbedTopology
from layer2.testbed.dpid import decodeDPID

if not "creds" in globals():
    creds = ("admin","admin")
    globals()['creds'] = creds

def urlsend (url,method="GET",auth=True,data=None):
    req = urllib2.Request(url)
    req.get_method = lambda: method
    global creds
    try:
        if auth:
            (user,password) = creds
            password_manager = urllib2.HTTPPasswordMgrWithDefaultRealm()
            password_manager.add_password(None, url, user, password)

            auth_manager = urllib2.HTTPBasicAuthHandler(password_manager)
            opener = urllib2.build_opener(auth_manager)
            urllib2.install_opener(opener)
        handler = None
        if method == "PUT":
            req.add_header('Content-Type', 'application/json')
            handler = urllib2.urlopen(req,data)
        else:
            handler = urllib2.urlopen(req)
        return json.load(handler)
    except:
        return None

def showactive():
    getswitches()


def getswitches(controller=None):
    global ctrl
    if controller == None:
        controller = ctrl
    url = "http://" + controller + ":8181/restconf/operational/opendaylight-inventory:nodes/"
    response = urlsend(url=url,auth=True)
    if response == None:
        print "no active switches"
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
    print "\nSwitch list is stored into Python global variable 'switches'"
    globals()['switches'] = switches

def dumpflows(switch,table,controller=None):
    global ctrl
    if controller == None:
        controller = ctrl
    id = makeODLDPID(switch)
    if table == None:
        table = gettable(switch)
    url = "http://" + controller + ":8181/restconf/config/opendaylight-inventory:nodes/node/" + id + "/flow-node-inventory:table/" + table
    response = urlsend(url=url,auth=True)
    if (response == None):
        print "No flow"
        return None
    decodeflow(response)

def decodeflow(response):
    tables = response['flow-node-inventory:table']
    for table in tables:
        tableid = table['id']
        if not 'flow' in table:
            return None
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
                    source = ethernet['ethernet-source']['address']
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
                            max = 0
                            if 'max-length'in action['output-action']:
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
                            if 'in-port'in action['set-field']:
                                in_port = action['set-field']['in-port']
                                print "\t\t\t\torder",order2,"set field in-port",in_port
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
                        if 'set-vlan-id-action' in action:
                            vid = action['set-vlan-id-action']['vlan-id']
                            print "\t\t\t\torder",order2,"set vlan-id",vid
                            continue
                        print "unknown action:",action

def getflows(switch,table,safe=True,controller=None):
    global ctrl
    if controller == None:
        controller = ctrl
    id = makeODLDPID(switch)
    if table == None:
        table = gettable(switch)
    url = "http://" + controller + ":8181/restconf/config/opendaylight-inventory:nodes/node/" + id + "/flow-node-inventory:table/" + table
    response = urlsend(url=url,auth=True)
    if (response == None):
        return []
    ids = []
    tables = response['flow-node-inventory:table']
    for table in tables:
        if not 'flow' in table:
            return None
        flows = table['flow']
        for flow in flows:
            delete = True
            id = flow['id']
            instructions = flow['instructions']['instruction']
            for instruction in instructions:
                if 'apply-actions' in instruction and 'action' in instruction['apply-actions']:
                    actions = instruction['apply-actions']['action']
                    for action in actions:
                        order2 = action['order']
                        if 'output-action' in action:
                            port = action['output-action']['output-node-connector']
                            if port == 'CONTROLLER':
                                if safe:
                                    delete = False
            if delete:
                ids.append(id)
    return ids


def _deleteflow(switch,table,flowid,controller=None):
    global ctrl
    if controller == None:
        controller = ctrl
    id = makeODLDPID(switch)
    if table == None:
        table = gettable(switch)
    url ="http://" + controller + ":8181/restconf/config/opendaylight-inventory:nodes/node/" + \
         id + "/flow-node-inventory:table/" + table + "/flow/" + flowid
    response = urlsend(url=url,auth=True,method="DELETE")


def deleteflow(switch,table,flowid,safe=True):
    if flowid != "all":
        _deleteflow(switch,table,flowid)
    else:
        ids = getflows(switch=switch,table=table,safe=safe)
        if ids == None or len(ids) == 0:
            return
        for id in ids:
            print "delete flow",id
            _deleteflow(switch=switch,table=table,flowid=id)

def corsaforward(switch,flowid, in_port, in_dst, in_vlan,out_port,out_dst,out_vlan,meter=3,controller=None ):
    global ctrl
    if controller == None:
        controller = ctrl
    id = makeODLDPID(switch)
    table = gettable(switch)
    priority = 1
    if meter == None:
        meter = 3
    entry = '{"flow-node-inventory:flow":[{"table_id":'+ str(table) + ','
    entry += '"id":"' + flowid + '",'
    entry += '"match":{"vlan-match":{"vlan-id":{"vlan-id":' + str(in_vlan) + ',"vlan-id-present":True}},'
    entry += '"in-port":"' + str(in_port) + '",'
    entry += '"ethernet-match":{"ethernet-destination":{"address":"' + in_dst + '"}}},'
    entry += '"priority":' + str(priority) + ','
    entry += '"instructions":{"instruction":[{"order":1,"meter":{"meter-id":' + str(meter) + '}},'
    entry += '{"order":0,"apply-actions":{"action":[{"order":0,"output-action":{"output-node-connector":"' + out_port + '","max-length":65535}},'
    entry += '{"order":2,"set-vlan-pcp-action":{"vlan-pcp":0}},{"order":1,"set-field":{"vlan-match":{"vlan-id":{"vlan-id":' + str(out_vlan)
    entry += ',"vlan-id-present":True}}}},'
    entry += '{"order":4,"set-dl-dst-action":{"address":"' + out_dst +'"}},{"order":3,"set-queue-action":{"queue-id":0}}]}}]},"cookie":0}]}'

    flow = eval (entry)
    data = json.dumps(flow)

    url = "http://" + controller + ":8181/restconf/config/opendaylight-inventory:nodes/node/" + id + "/table/" + table + "/flow/" + flowid
    response = urlsend(url=url,auth=True,method="PUT",data = data)

def ovsforward(switch,flowid, in_port, in_dst, in_vlan,out_port,out_dst,out_vlan,priority=1,meter=5 ):
    id = makeODLDPID(switch)
    table = gettable(switch)
    if meter == None:
        meter = 5

def ovsbroadcast(switch,idprefix,in_port,in_vlan,datapaths,priority=1,meter=5,controller=None):
    global ctrl
    if controller == None:
        controller = ctrl
    id = makeODLDPID(switch)
    table = gettable(switch)
    if meter == None:
        meter = 5
    flowid = idprefix + "-broadcast"

    req={"flow-node-inventory:flow":[]}
    flow = {"table_id": table}
    req['flow-node-inventory:flow'].append(flow)
    flow['id'] = flowid
    match = {"vlan-match":{"vlan-id":{"vlan-id":' + in_vlan + ',"vlan-id-present":True}}}
    match["in-port"] = in_port
    match["ethernet-match"] = {"ethernet-destination":{"address":"FF:FF:FF:FF:FF:FF"}}

    flow['match'] = match
    flow['priority'] = priority

    instructions = {"instruction":[]}
    flow['instructions'] = instructions
    inst = {"order":1,"meter":{"meter-id": str(meter)}}
    instructions['instruction'].append(inst)
    index = 0
    actions = []
    for (out_port,out_vlan) in datapaths:
        action = {"order": index,"output-action":{"output-node-connector":out_port,"max-length":65535}}
        actions.append(action)
        action = {"order": index + 2,"set-vlan-pcp-action":{"vlan-pcp":0}}
        actions.append(action)
        action = {"order":index + 1,"set-field":{"vlan-match":{"vlan-id":{"vlan-id":out_vlan},"vlan-id-present":True}}}
        actions.append(action)
        action = {"order":index + 4,"set-dl-dst-action":{"address":"FF:FF:FF:FF:FF:FF"}}
        actions.append(action)
        action = {"order":index + 3,"set-queue-action":{"queue-id":0}}
        actions.append(action)
    inst = {"order":0,"apply-actions":{"action":actions}}
    instructions['instruction'].append(inst)
    flow['cookie'] = 0
    data = json.dumps(req)
    print data
    url = "http://" + controller + ":8181/restconf/config/opendaylight-inventory:nodes/node/" + id + "/table/" + table + "/flow/" + flowid
    response = urlsend(url=url,auth=True,method="PUT",data = data)


def show(switch):
    if 'dpid' in switch.props:
        hexdpid = binascii.hexlify(switch.props['dpid'])
        print switch,"\tdpid: ",hexdpid,"\topenflow: openflow:" + str(int(hexdpid,16))
    return None

def makeODLDPID(switch):
    hexdpid = binascii.hexlify(switch.props['dpid'])
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
        if not name in topo.builder.switchIndex:
            return None
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
    print "\t\tofctl get-switch dpid openflow:144397081500677121"
    print "\nshow-switch <name>"
    print "\tDisplays the DPID in various format of the switch"
    print "\nshow-active"
    print "\tshows all connected switches and returns the list of switches into Python list."
    print "\ndump-flows <switch name> <table>"
    print "\tShows flow entries of the given switch"
    print "\t\tofctl dump-flows <switch-name> displays flows from the default table. ovs = table 0, corsa = table 2"
    print "\t\tofctl dump-flows <switch-name> table <table number> displays the flows of a given table "
    print "\ndel-flow <switch> [table <table number>] flow <flowid> | all [force] "
    print "\tDeletes a flow in a table on a switch. table <table number> can be ommited, default tables"
    print "\tare then assumed. If flow is 'all', then all flows other than PACKET_IN support entries are then"
    print "\tremoved."
    print "\nadd-flow <switch> <flow_id> <in_port> <in_dst> <in_vlan> <out_port> <out_dst> <out_vlan> [meter]"
    print "\nadd-broadcast <switch> <flow_id> <in_port> <in_vlan> <out1_port> <out1_vlan> .. <outN_port> <outNout_vlan"

    print


if __name__ == '__main__':
    # Retrieve topology
    if not 'topo' in globals() or topo == None:
        topo = TestbedTopology()
        globals()['topo'] = topo

    global topo
    global ctrl

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
        if sw == None:
            print "unknown switch"
            sys.exit(0)
        show(switch=sw)
    elif cmd == "show-active":
        showactive()
    elif cmd == "dump-flows":
        sw = getswitch(name=argv[2])
        if sw == None:
            print "unknown switch"
            sys.exit(0)
        table = None
        if 'table' in argv:
            table = argv[4]
        dumpflows(switch=sw,table=table)
    elif cmd == "del-flow":
        sw = getswitch(name=argv[2])
        if sw == None:
            print "unknown switch"
            sys.exit(0)
        table = None
        flow = None
        if 'table' in argv:
            table = argv[4]
            flow = argv[6]
        else:
            flow = argv[4]
        besafe = True
        if 'force' in argv:
            besafe = False
        deleteflow(switch=sw,table=table,flowid=flow,safe=besafe)
    elif cmd == "add-flow":
        sw = getswitch(name=argv[2])
        if sw == None:
            print "unknown switch"
            sys.exit(0)
        flow_id = argv[3]
        in_port = argv[4]
        in_dst = argv[5]
        in_vlan = argv[6]
        out_port = argv[7]
        out_dst = argv[8]
        out_vlan = argv[9]
        meter = None
        if len(argv) > 10:
            meter = argv[10]
        id = sw.props['dpid']
        (vendor,role,location,id) = decodeDPID(id)
        if vendor == 2:
            # Corsa
            corsaforward(sw,flow_id,in_port,in_dst,in_vlan,out_port,out_dst,out_vlan,meter)
    elif cmd == "add-broadcast":
        sw = getswitch(name=argv[2])
        if sw == None:
            print "unknown switch"
            sys.exit(0)
        flow_id = argv[3]
        in_port = argv[4]
        in_vlan = argv[5]
        out =iter(argv[6:])
        datapaths = []
        for port in out:
            vlan = next(out)
            datapaths.append((port,vlan))
        ovsbroadcast(sw,flow_id,in_port,in_vlan,datapaths)

    else:
        print "Bad command.  For a command list, run:"
        print "  ofctl help"


