import urllib2
import sys
import binascii

from layer2.testbed.topology import TestbedTopology
from layer2.testbed import dpid

"""
#url= 'http://aofa-tbn-1:8181/restconf/config/opendaylight-inventory:nodes/node/openflow:144397081500677121/table/2/flow/4'
#url="http://www.cnn.com"
url="http://aofa-tbn-1.testbed100.es.net:8181/restconf/operational/opendaylight-inventory:nodes/node/openflow:144397081500677121/table/2"

req = urllib2.Request(url)

password_manager = urllib2.HTTPPasswordMgrWithDefaultRealm()
password_manager.add_password(None, url, 'admin', 'admin')

auth_manager = urllib2.HTTPBasicAuthHandler(password_manager)
opener = urllib2.build_opener(auth_manager)

urllib2.install_opener(opener)

handler = urllib2.urlopen(req)

print handler.getcode()
print handler.headers.getheader('content-type')

lines = handler.readlines()
for line in lines:
    print line
"""


def dumpflows(switch):
    print switch

def show(switch):
    if 'dpid' in switch.props:
        hexdpid = binascii.hexlify(switch.props['dpid'])
        print switch,"\tdpid: ",hexdpid,"\topenflow: " + str(int(hexdpid,16))



    return None

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
    print "help"
    print "\tPrints this help."
    print "set-ctrl <controller host>"
    print "\tThis command is used to set the host where the OpenFlow controller is running."
    print "\tIt can be an IP address or a DNS name. testbed100.es.net is added if necessary."
    print "\tFor instance:"
    print "\t\tofctl set-ctrl aofa-tbn-1 or ofctl set-ctrl aofa-tbn-1.testbed100.es.net"
    print "\tNote that the controller host name is set in the python global variable"
    print "\tand has to be set only once."
    print "show-ctrl"
    print "\tDisplays the host where the OpenFlow controller is running"
    print "get-switch <name:dpid> [dpid]"
    print "\tRetrieves the switch object refered by either its name or its dpid."
    print "\tThe switch object is then stored into a global python variable named 'switch'"
    print "\tThe DPID can be of variable format that are automatically dected."
    print "\tIt can be hexadecimal or binary, with or without 'openflow:' prefix"
    print "\tFor instance:"
    print "\t\tofctl get-switch amst-tb-of-1"
    print "\t\tofctl get-switch dpid 0201007374617201"
    print "\t\tofctl get-switch dpid 144397081500677121"
    print "\t\t ofctl get-switch dpid openflow:144397081500677121"
    print "show-switch <name>"
    print "\tDisplays the DPID in various format of the switch"


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
    elif cmd == "dump-flows":
        sw = getswitch(name=argv[2])
        dumpflows(switch=sw)

