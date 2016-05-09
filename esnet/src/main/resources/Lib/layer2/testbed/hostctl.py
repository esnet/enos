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
import array
import jarray
import binascii
from java.math import BigInteger

from net.es.netshell.api import Container

# from layer2.testbed.oscars import getgri,getgrinode,displaygri,griendpoints
from layer2.testbed.vc import vcendpoints, getvcnode

import sys
if "debugNoController" in dir(sys) and sys.debugNoController:
    class X:
        value = None
        def __init__(self,*args):
            value = args
        def __repr__(self):
            return str(self.value);

    class Z:
        something=True
        def SdnInstallMeter(*args):
            print "Stub InstallMeter",args[1:]
            return True
        def SdnInstallForward1 (*args):
            print "Stub InstallForward1",args[1:]
            return X(args)
        def SdnInstallForward (*args):
            print "Stub InstallForward",args[1:]
            return X(args)
        def SdnDeleteForward (*args):
            print "Stub DeleteForward",args[1:]
        def setCallback(*args):
            pass


    from net.es.netshell.api import PersistentObject
    class SdnControllerClientL2Forward (PersistentObject):
        def __init__(self,outPort=None,vlan=None,dstMac=None):
            PersistentObject.__init__(self)
            self.properties['outPort'] = str(outPort)
            self.properties['vlan'] = str(vlan)
            self.properties['dstMac'] = str(dstMac)
        def __repr__(self):
            return self.saveToJSON()

    class SdnControllerClientCallback:
        def setcallBack(*args):
            print "Stub setcallBack",args[1:]

    def SdnControllerClient():
        return Z()

else:
    from net.es.netshell.controller.client import SdnControllerClient, SdnControllerClientL2Forward

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

def getlinks2(topology, node1, node2):
    """
    Return all of the links between two nodes in a topology
    :param topology: (topology object)
    :param node1: (string)
    :param node2: (string)
    :return: list of node objects (resources)
    """
    allLinks = topology.loadResources({"resourceType":"Link"})
    links = []
    for l in allLinks:
        (dstNode,dstPort) = linkednode2(l,node1)
        if (dstNode,dstPort) == (None, None):
            continue
        (dstNode,dstPort) = linkednode2(l,node2)
        if (dstNode,dstPort) == (None, None):
            continue
        links.append(l)
    return links

def parselink2(link):
    """
    Parse the name of a link and return a list of parsed elements.
    Names are in the form:  "atla-cr5--10/1/10--atla-tb-of-1--23".
    XXX WAN links have different names.  We need to parse them
    differently to get the endpoints.
    :param link: link object as resource
    :return: 5-tuple of source node and port, destination node and port, and VLAN (all strings)
    """
    [srcNode,srcPort,dstNode,dstPort] = link.resourceName.split("--")
    return (srcNode,srcPort,dstNode,dstPort,"0")

def linkednode2(link, host, port= None):
    """
    Retrieve the host/port connected to provide host/port
    :param link: link object as resource
    :param host: name of host (string)
    :param port: optional (string)
    :return: name of node (string), name of port (string)
    """
    (srcNode,srcPort,dstNode,dstPort,vlan) = parselink2(link)

    if (port != None):
        if (srcNode,srcPort) == (host,port):
            return (dstNode,dstPort)
        elif (dstNode,dstPort) == (host,port):
            return (srcNode,srcPort)
        return (None,None)
    if srcNode == host:
        return (dstNode,dstPort)
    elif dstNode == host:
        return (srcNode,srcPort)
    return (None,None)

def setcallback(cb):
    SCC.setCallback(cb)
    print "callback set"

def clearcallback():
    SCC.clearCallback()
    print "callback cleared"

def setmeter(switch, meter, cr, cbs, er, ebs):
    return SCC.SdnInstallMeter(javaByteArray2(switch.properties['DPID']), meter, cr, cbs, er, ebs)

def connectremoteplanemac(remotesw,
                          hostmac,
                          hostvlan,
                          remotehost_port,
                          remotehost_vlan,
                          remotehwport_tocore,
                          corevlan,
                          vc,
                          meter=3,
                          host_rewritemac = None):
    """
    Set up forwarding entry on a switch/pop that is remote to a given host.
    This entry takes traffic from a site, translating MAC if necessary,
    and forwarding on a WAN circuit headed towards the host.  Returns a FlowHandle.
    """
    translated_hostmac = hostmac
    if host_rewritemac != None:
        translated_hostmac = host_rewritemac

    baseid = hostmac + ":" + str(hostvlan) + "-" + vc.getResourceName()
    flowid = baseid + "from-remote-host"

    fh = SCC.SdnInstallForward1(javaByteArray2(remotesw.properties['DPID']),
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
    return fh

def connectdataplanemac(hostmac,
                        hostvlan,
                        sw,
                        tohostport,
                        tocoreport,
                        tocorevlan,
                        vc,
                        meter=3,
                        host_rewritemac = None):
    """
    Set up forwarding entries on the switches local to a host.
    Returns a FlowHandle.
    """
    baseid = hostmac + ":" + str(hostvlan) + "-" + vc.getResourceName()
    translated_hostmac = hostmac
    if host_rewritemac != None:
        translated_hostmac = host_rewritemac

    # Forward inbound WAN traffic from core router to local site/host.
    # Also de-translate destination MAC address if necessary.
    flowid = baseid + "-to-host"
    fh = SCC.SdnInstallForward1(javaByteArray2(sw.properties['DPID']),
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
    return fh



def getgriport(topology,hwswitch,core,griport):
    """
    In the following logical topology <Host> - <HwSwitch> - <Core Router>, the OSCARS circuits ends onto the
    port on the core router connected to the HwSwitch. This function returns the port on the HwSwitch that
    is connected to the the core router when the OSCARS circuit terminates.
    """
    hwswitchname = hwswitch.resourceName
    corename = core.resourceName

    links = getlinks2(topology, corename, hwswitchname)
    if links == None or len(links) == 0:
        print "No links from",corename,"to",hwswitchname
        return False
    corelink = None
    for link in links:
        (node,port) = linkednode2(link, hwswitchname)
        if port != None and port == griport:
            # found the link between HwSwith and Core that ends to the OSCARS circuit.
            corelink = link
            break
    (node,hwport_tocore) = linkednode2(corelink,corename)
    return hwport_tocore

def connectmac(localpop,
               remotepop,
               localsiteport,
               localsitevlan,
               remotesiteport,
               remotesitevlan,
               hostmac,
               vc,
               meter=3,
               host_rewritemac = None):
    """
    Given a pair of sites, and a host at one of the sites, set up one-way forwarding to get
    unicast packets to the host.
    This function takes care of finding the hardware switch and inter-POP ports.
    :param localpop:        POP object
    :param remotepop:       POP object
    :param localsitevlan:   VLAN tag
    :param localsiteport:   local hardware switch port for site attachment
    :param remotesitevlan:  VLAN tag
    :param remotesiteport:  remote hardware switch port for site attachment
    :param hostmac:         local host MAC address (string)
    :param vc:
    :param meter:
    :param host_rewritemac: translated local host MAC address
    :return: List of FlowHandles
    """
    core = Container.fromAnchor(localpop.properties['CoreRouter'])
    corename = core.resourceName
    (corename,coredom,coreport,corevlan) = getvcnode(vc,corename)
    remotecore = Container.fromAnchor(remotepop.properties['CoreRouter'])
    remotecorename = remotecore.resourceName
    (remotecorename,remotecoredom,remotecoreport,remotecorevlan) = getvcnode(vc,remotecorename)

    # Find hwswitch/port - core/port
    topology = Container.getContainer(localpop.properties['HwSwitch']['containerName'])

    hwswitch = Container.fromAnchor(localpop.properties['HwSwitch'])
    hwport_tocore = getgriport(topology, hwswitch, core, coreport)
    # Find remotehwswitch/port - remotecore/port
    remotehwswitch = Container.fromAnchor(remotepop.properties['HwSwitch'])
    remotehwport_tocore = getgriport(topology, remotehwswitch, remotecore, remotecoreport)

    # Find the port on the HwSwitch that is connected to the host's port
    hwport_tosite = localsiteport

    fh1 = connectdataplanemac(hostmac= hostmac,
                              hostvlan= localsitevlan,
                              sw= hwswitch,
                              tohostport= hwport_tosite,
                              tocoreport= hwport_tocore,
                              tocorevlan= corevlan,
                              vc= vc,
                              meter= meter,
                              host_rewritemac= host_rewritemac)
    if fh1 == None:
        return None

    # Find the port on the remote HwSwitch that is connected to the remote host's port
    remotehwport_tosite = remotesiteport

    fh2 = connectremoteplanemac(remotesw = remotehwswitch,
                                hostmac= hostmac,
                                hostvlan= localsitevlan,
                                remotehost_port= remotehwport_tosite,
                                remotehost_vlan= remotesitevlan,
                                remotehwport_tocore= remotehwport_tocore,
                                corevlan= corevlan,
                                vc= vc,
                                meter= meter,
                                host_rewritemac= host_rewritemac)
    if fh2 == None:
        SCC.deleteforward(fh1)
        return None

    fhs = (fh1, fh2)
    return fhs

def connecthostbroadcast(localpop,
                         hwport_tosite,
                         sitevlan,
                         meter=3,
                         broadcast_rewritemac = None):
    """
    Create entries on the local hardware switch that pass broadcast traffic
    to and from the connected host
    :param localpop: POP object
    :param hwport_tosite: port on hardware switch facing the site (string)
    :param sitevlan: VLAN number of site attachment
    :param meter:
    :param broadcast_rewritemac: Mapped Ethernet broadcast address
    :return:
    """

    hwswitch = Container.fromAnchor(localpop.properties['HwSwitch'])
    hwswitchname = hwswitch.resourceName
    swswitch = Container.fromAnchor(localpop.properties['SwSwitch'])
    swswitchname = swswitch.resourceName
    topology = Container.getContainer(localpop.properties['SwSwitch']['containerName'])

    # Find the port on the HwSwitch connected to the software switch
    links = getlinks2(topology, hwswitchname, swswitchname)
    if links == None or len(links) == 0:
        print "No links from", hwswitchname, "to", swswitchname
        return False
    hwport_tosw = None
    for link in links:
        (node, port) = linkednode2(link, swswitchname)
        if port != None:
            # Found the link we're looking for
            hwport_tosw = port
            break

    broadcast = "FF:FF:FF:FF:FF:FF"
    translated_broadcast = broadcast
    if broadcast_rewritemac != None:
        translated_broadcast = broadcast_rewritemac

    fh1 = SCC.SdnInstallForward1(javaByteArray2(hwswitch.properties['DPID']),
                           1,
                           BigInteger.ZERO,
                           str(hwport_tosw),
                           int(sitevlan),
                           "00:00:00:00:00:00",
                           translated_broadcast,
                           str(hwport_tosite),
                           int(sitevlan),
                           broadcast,
                           0,
                           0,
                           meter)
    if fh1 == None:
        return None

    fh2 = SCC.SdnInstallForward1(javaByteArray2(hwswitch.properties['DPID']),
                           1,
                           BigInteger.ZERO,
                           str(hwport_tosite),
                           int(sitevlan),
                           "00:00:00:00:00:00",
                           broadcast,
                           str(hwport_tosw),
                           int(sitevlan),
                           translated_broadcast,
                           0,
                           0,
                           meter)
    if fh2 == None:
        SCC.deleteforward(fh1)
        return None

    return (fh1, fh2)

def connectentryfanoutmac(localpop,
                       hostmac,
                       hostvlan,
                       forwards,
                       meter,
                       mac):
    """
    Create fanout entry on source POP's software switch
    :param localpop:  POP object
    :param hostmac: host MAC address
    :param hostvlan: VLAN number of host attachment
    :param forwards: array of SDNControllerClientL2Forward
    :param meter:
    :param mac:
    :return: SdnControllerClientFlowHandle
    """
    hwswitch = Container.fromAnchor(localpop.properties['HwSwitch'])
    hwswitchname = hwswitch.resourceName
    swswitch = Container.fromAnchor(localpop.properties['SwSwitch'])
    swswitchname = swswitch.resourceName
    topology = Container.getContainer(localpop.properties['SwSwitch']['containerName'])

    # print "connectentryfanout localpop", localpop, "host", host, "hostvlan", hostvlan, "mac", mac

    # Find the port on the software switch connected to the hardware switch
    links = getlinks2(topology, swswitchname, hwswitchname)
    if links == None or len(links) == 0:
        print "No links from", swswitchname, "to", hwswitchname
        return None
    hwswitchlink = None
    swport_tohw = None
    for link in links:
        (node, port) = linkednode2(link, hwswitchname)
        if port != None:
            # Found it!
            hwswitchlink = link
            swport_tohw = port
            break
    if swport_tohw == None:
        print "No output port on", swswitchname, "facing", hwswitchname
        return None

    # The fanout flow is "interesting" in that the input plus the multiple outputs
    # all are on the same port (but different VLANs).  Fill in the outputs.
    for f in forwards:
        f.outPort = str(swport_tohw)
        # print "FORW:  outport", f.outPort, "vlan", f.vlan, "dstMac", f.dstMac

    # Convert the list of forwarding destinations to a Java array.
    fwdsarr = jarray.array(forwards, SdnControllerClientL2Forward)

    # print "dpid", swswitch.props['dpid']
    # This flow being installed is unusual in that it does a source MAC address
    # filter as well
    fh = SCC.SdnInstallForward(javaByteArray2(swswitch.properties['DPID']),
                               1,
                               BigInteger.ZERO,
                               str(swport_tohw),
                               int(hostvlan),
                               hostmac,
                               mac,
                               fwdsarr,
                               0,
                               0,
                               meter)

    return fh

def connectexitfanout(localpop,
                       corevlan,
                       forwards,
                       meter,
                       mac):
    """
    Create exit fanout flow on software switch of a destination POP.
    This handles broadcast traffic before it exits the network
    :param localpop: POP object
    :param corevlan: VLAN number coming from core
    :param forwards: array of SDNControllerClientL2Forward
    :param meter:
    :param mac:
    :return: SDNControllerClientFlowHandle
    """

    hwswitch = Container.fromAnchor(localpop.properties['HwSwitch'])
    hwswitchname = hwswitch.resourceName
    swswitch = Container.fromAnchor(localpop.properties['SwSwitch'])
    swswitchname = swswitch.resourceName
    topology = Container.getContainer(localpop.properties['SwSwitch']['containerName'])

    # print "connectexitfanout localpop", localpop, "corevlan", corevlan, "mac", mac

    # Find the port on the software switch connected to the hardware switch
    links = getlinks2(topology, swswitchname, hwswitchname)
    if links == None or len(links) == 0:
        print "No links from", swswitchname, "to", hwswitchname
        return None
    hwswitchlink = None
    swport_tohw = None
    for link in links:
        (node, port) = linkednode2(link, hwswitchname)
        if port != None:
            # Found it!
            hwswitchlink = link
            swport_tohw = port
            break
    if swport_tohw == None:
        print "No output port on", swswitchname, "facing", hwswitchname
        return None

    for f in forwards:
        f.outPort = str(swport_tohw)
        # print "FORW:  outport", f.outPort, "vlan", f.vlan, "dstMac", f.dstMac

    # Convert the list of forwarding destinations to a Java array.
    fwdsarr = jarray.array(forwards, SdnControllerClientL2Forward)

    # print "dpid", swswitch.props['dpid']
    fh = SCC.SdnInstallForward(javaByteArray2(swswitch.properties['DPID']),
                               1,
                               BigInteger.ZERO,
                               str(swport_tohw),
                               int(corevlan),
                               None,
                               mac,
                               fwdsarr,
                               0,
                               0,
                               meter)

    return fh

def connectgrimac(topology,
                  hostmac,
                  siteport,
                  sitevlan,
                  sitepop,
                  remotesiteport,
                  remotesitevlan,
                  vc,
                  meter=3,
                  host_rewritemac=None):
    """
    Set up forwarding entries to connect a host to a remote POP via a given GRI.
    This function takes care of figuring out the POPs involved.
    :param topology:        Topology/Container, needed for finding GRI endpoints
    :param hostmac:         MAC address of source (string)
    :param siteport:        port on hardware switch facing site
    :param sitevlan:        VLAN to site
    :param sitepop:         POP object
    :param remotesiteport:  port on remote hardware switch facing remote site
    :param remotesitevlan:  VLAN to site
    :param vc:
    :param meter:           meter
    :param host_rewritemac: Translated MAC address (string)
    :return: List of FlowHandles or None
    """
    # Get both endpoints of the GRI
    (e1,e2) = vcendpoints(vc)
    core1 = topology.loadResource(e1[1])
    if 'Role' not in core1.properties.keys() or core1.properties['Role'] != 'CoreRouter' or 'Pop' not in core1.properties.keys():
        print core1.resourceName, "is not a core router"
        return None
    core2 = topology.loadResource(e2[1])
    if 'Role' not in core2.properties.keys() or core2.properties['Role'] != 'CoreRouter' or 'Pop' not in core2.properties.keys():
        print core1.resourceName, "is not a core router"
        return None
    pop1name = core1.properties['Pop']
    pop2name = core2.properties['Pop']

    remotepopname = None
    if sitepop.resourceName == pop1name:
        remotepopname = pop2name
    elif sitepop.resourceName == pop2name:
        remotepopname = pop1name
    if remotepopname == None:
        print "vc", vc, "does not provide connectivity for", hostmac, "from", remotepop.resourceName, "to", sitepop.resourceName
        return None

    remotepop = topology.loadResource(remotepopname)
    if remotepop == None:
        print "Unable to retrieve remote POP", remotepopname
        return None

    res = connectmac(localpop= sitepop,
                     remotepop= remotepop,
                     localsiteport= siteport,
                     localsitevlan= sitevlan,
                     remotesiteport= remotesiteport,
                     remotesitevlan= remotesitevlan,
                     hostmac= hostmac,
                     vc= vc,
                     meter = meter,
                     host_rewritemac= host_rewritemac)
    return res

def swconnect(localpop, remotepop, mac, vc, meter):
    """ Set up two-way connectivity between ports on the software switches for a given MAC
    :param localpop: POP object (Resource)
    :param remotepop: POP object (Resource)
    :param mac:
    :param vc
    :param meter:
    :return: List of FlowHandles
    """
    print "swconnect entry with vc", vc.resourceName
    core = Container.fromAnchor(localpop.properties['CoreRouter'])
    corename = core.resourceName
    print "corename", corename
    print getvcnode(vc, corename)
    (corename,coredom,coreport,corevlan) = getvcnode(vc, corename)
    remotecore = Container.fromAnchor(remotepop.properties['CoreRouter'])
    remotecorename = remotecore.resourceName
    print "remotecorename", remotecorename
    print getvcnode(vc, remotecorename)
    (remotecorename,remotecoredom,remotecoreport,remotecorevlan) = getvcnode(vc, remotecorename)

    print corename, "<->", remotecorename

    hwswitch = Container.fromAnchor(localpop.properties['HwSwitch'])
    hwswitchname = hwswitch.resourceName
    swswitch = Container.fromAnchor(localpop.properties['SwSwitch'])
    swswitchname = swswitch.resourceName

    remotehwswitch = Container.fromAnchor(remotepop.properties['HwSwitch'])
    remotehwswitchname = remotehwswitch.resourceName
    remoteswswitch = Container.fromAnchor(remotepop.properties['SwSwitch'])
    remoteswswitchname = remoteswswitch.resourceName

    topology = Container.getContainer(localpop.properties['SwSwitch']['containerName'])

    # Find hwswitch/port - core/port
    hwport_tocore = getgriport(topology, hwswitch, core, coreport)
    print "hwport_tocore", hwport_tocore
    # Find remotehwswitch/port - remotecore/port
    remotehwport_tocore = getgriport(topology, remotehwswitch, remotecore, remotecoreport)
    print "remotehwport_tocore", remotehwport_tocore

    links = getlinks2(topology, hwswitchname, swswitchname)
    if links == None or len(links) == 0:
        print "No links from ", hwswitchname, " to ", swswitchname
        return None
    hwswlink = None
    for l in links:
        (node, port) = linkednode2(l, swswitchname)
        if port != None:
            # Found the (a) link
            hwswlink = l
            hwport_tosw = port
            break
    print "hwport_tosw", hwport_tosw

    remotelinks = getlinks2(topology, remotehwswitchname, remoteswswitchname)
    if remotelinks == None or len(remotelinks) == 0:
        print "No links from ", remotehwswitchname, " to ", remoteswswitchname
        return None
    remotehwswlink = None
    for l in remotelinks:
        (node, port) = linkednode2(l, remoteswswitchname)
        if port != None:
            # Found the (a) link
            remotehwswlink = l
            remotehwport_tosw = port
            break
    print "remotehwport_tosw", remotehwport_tosw

    # Find the ports on hwswitch and remotehwswitch that go to the corresponding software switches

    # Set up forwarding for broadcast traffic from the new local pop
    # Install outbound flow on hwswitch from swswitch to the GRI
    fh1 = SCC.SdnInstallForward1(javaByteArray2(hwswitch.properties['DPID']),
                           1,
                           BigInteger.ZERO,
                           str(hwport_tosw), # hw port facing software switch
                           int(corevlan),
                           "00:00:00:00:00:00",
                           mac,
                           str(hwport_tocore),
                           int(corevlan),
                           mac,
                           0,
                           0,
                           meter)
    if fh1 == None:
        return None

    # Install inbound flow on remotehwswitch from GRI to remoteswswitch
    fh2 = SCC.SdnInstallForward1(javaByteArray2(remotehwswitch.properties['DPID']),
                           1,
                           BigInteger.ZERO,
                           str(remotehwport_tocore),
                           int(remotecorevlan),
                           "00:00:00:00:00:00",
                           mac,
                           str(remotehwport_tosw), # remotehw port facing remote software switch
                           int(remotecorevlan),
                           mac,
                           0,
                           0,
                           meter)
    if fh2 == None:
        SCC.deleteforward(fh1)
        return None

    # Set up forwarding for broadcast traffic to the new local pop
    # Install inbound flow on hwswitch from GRI to swswitch
    fh3 = SCC.SdnInstallForward1(javaByteArray2(hwswitch.properties['DPID']),
                           1,
                           BigInteger.ZERO,
                           str(hwport_tocore),
                           int(corevlan),
                           "00:00:00:00:00:00",
                           mac,
                           str(hwport_tosw), # hw port facing software switch
                           int(corevlan),
                           mac,
                           0,
                           0,
                           meter)
    if fh3 == None:
        SCC.deleteforward(fh1)
        SCC.deleteforward(fh2)
        return None

    # Install outbound flow on remotehwswitch from remoteswswitch to GRI
    fh4 = SCC.SdnInstallForward1(javaByteArray2(remotehwswitch.properties['DPID']),
                           1,
                           BigInteger.ZERO,
                           str(remotehwport_tosw), # remotehw port facing remote software switch
                           int(remotecorevlan),
                           "00:00:00:00:00:00",
                           mac,
                           str(remotehwport_tocore),
                           int(remotecorevlan),
                           mac,
                           0,
                           0,
                           meter)
    if fh4 == None:
        SCC.deleteforward(fh1)
        SCC.deleteforward(fh2)
        SCC.deleteforward(fh3)
        return None

    # Return something
    return (fh1, fh2, fh3, fh4)

def deleteforward(fh):
    """
    Delete a configured flow
    :param fh: SdnControllerClientFlowHandle
    :return:
    """
    SCC.SdnDeleteForward(fh)

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

def javaByteArray2(s):
    """
    Make a Java array of bytes from a string of hex digits.
    """
    a = array.array('B', binascii.unhexlify(s))
    return javaByteArray(a)

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

if __name__ == '__main__':
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



