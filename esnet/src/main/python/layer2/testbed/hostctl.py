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
import struct
import jarray
from java.math import BigInteger

from layer2.testbed.oscars import getgri,getgrinode,displaygri,griendpoints
from layer2.testbed.topology import TestbedTopology,getlinks,linkednode
from layer2.odl.ofctl import corsaforward
from layer2.testbed.topology import TestbedTopology

from net.es.netshell.controller.client import SdnControllerClient

# Hardcode information about hosts. Eventually this should be discovered by the ENOS
# host agent registering its interfaces and other meta data.

default_controller="aofa-tbn-1.testbed100.es.net"

if not 'SCC' in globals() or SCC == None:
    SCC = SdnControllerClient()
    globals()['SCC'] = SCC

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

def setmeter(switch, meter, cr, cbs, er, ebs):
    return SCC.SdnInstallMeter(javaByteArray(switch.props['dpid']), meter, cr, cbs, er, ebs)

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
                       host_rewritemac = None):
    """
    Set up forwarding entry on a switch/pop that is remote to a given host.
    This entry takes traffic from a site, translating MAC if necessary,
    and forwarding on a WAN circuit headed towards the host.
    """
    global default_controller
    hostmac = getdatapaths(host)[0]['mac']
    translated_hostmac = hostmac
    if host_rewritemac != None:
        translated_hostmac = host_rewritemac

    baseid = host['name'] + ":"+str(hostvlan)+"-"+gri.getName()
    if dobroadcast:
        flowid = baseid + "-broadcast-out"
        broadcast = "FF:FF:FF:FF:FF:FF"
    flowid = baseid + "to-remote-host"

    SCC.SdnInstallForward1(javaByteArray(switch.props['dpid']),
                           1,
                           BigInteger.ZERO,
                           str(remotehost_port),
                           int(remotehost_vlan),
                           "00:00:00:00:00:00",
                           hostmac,
                           str(remotehwport_tocore),
                           int(corevlan),
                           translated_hostmac,
                           0,
                           0,
                           meter)

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
                     host_rewritemac = None):
    """
    Set up forwarding entries on the switches local to a host.
    """
    global default_controller
    baseid = host['name'] +":"+hostport+":"+str(hostvlan)+"-"+gri.getName()
    hostmac = getdatapaths(host)[0]['mac']
    translated_hostmac = hostmac
    if host_rewritemac != None:
        translated_hostmac = host_rewritemac
    if dobroadcast:
        broadcast = "FF:FF:FF:FF:FF:FF"
#        translated_broadcast = broadcast
#        if False:
#            translated_broadcast = MAT()
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
        # XXX convert to SdnInstallForward1()

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
        # XXX convert to SdnInstallForward1()

    # Forward inbound WAN traffic from core router to local site/host.
    # Also de-translate destination MAC address if necessary.
    flowid = baseid + "-to-host"
    SCC.SdnInstallForward1(javaByteArray(sw.props['dpid']),
                           1,
                           BigInteger.ZERO,
                           str(tocoreport),
                           int(tocorevlan),
                           "00:00:00:00:00:00",
                           translated_hostmac,
                           str(tohostport),
                           int(hostvlan),
                           hostmac,
                           0,
                           0,
                           meter)


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
             host_rewritemac = None):
    """
    Given a host and a remote host, and the POPs to which their sites are attached, set up two-way forwarding.
    This function takes care of finding the hardware switch and ports.
    :param localpop:
    :param remotepop:
    :param host:
    :param remotehost:
    :param gri:
    :param hostvlan:
    :param remotehostvlan:
    :param meter:
    :param host_rewritemac:
    :return:
    """
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
    # Find hwswitch/port - core/port
    hwport_tocore = getgriport(hwswitch,core,coreport)
    # Find remotehwswitch/port - remotecore/port
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
                     host_rewritemac= host_rewritemac)

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
                       host_rewritemac= host_rewritemac)

    return True


def connectgri(host,
               gri,
               remotehost,
               hostvlan,
               remotehostvlan,
               meter=3,
               host_rewritemac=None):
    """
    Set up forwarding entries to connect a host to a remote host via a given GRI.
    This function takes care of figuring out the POPs involved.
    """
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
                  host_rewritemac= host_rewritemac)
    if not res:
        return

    return True

def javaByteArray(a):
    """
    Make a Java array of bytes from unsigned bytes in Python.  Note that Java
    bytes are signed, whereas in Python they may be either signed or unsigned.
    :param a:
    :return:
    """
    b = jarray.zeros(len(a), 'b')
    for i in range(len(a)):
        b[i] = struct.unpack('b', struct.pack('B', a[i]))[0]
    return b

def print_syntax():
    print
    print "hostctl <cmd> <cmds options>"
    print "Configures testbed hosts and their datapath. Commands are:"
    print "\tCommands are:\n"
    print "\thelp: prints this help."
    print "\tshow-host <host name | all> Displays information about a host or all hosts"
    print "\tcreate <host-name> pop <pop-name>: creates a new host on the provided SDN POP"
    print "\tdelete <host-name>: deletes a host"
    print "\tadd-user <host-name> user <user-name> [priv <root:user>] Creates a user on a host. An optional"
    print "\t\tprivilege level can be provided, otherwise, normal user privilege is default. Note that the"
    print "\t\tcommand will create an initial password."
    print "\trem-user <host-name> user <user-name>: remove user from a host."
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



