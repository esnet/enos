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
import sys

from layer2.testbed.builder import TopoBuilder
from net.es.netshell.api import GenericTopologyProvider,TopologyProvider,GenericHost,GenericNode,GenericPort,GenericLink,Container
from net.es.netshell.kernel.exec import KernelThread
from net.es.netshell.boot import BootStrap
from layer2.common.api import Properties, Port
from layer2.common.utils import singleton


class TestbedNode(GenericNode,Properties):
    def __init__(self,name,props={}):
        GenericNode.__init__(self,name)
        Properties.__init__(self,name=self.getResourceName(),props=props)
        self.props['links'] = []

    def getPort(self,name):
        ports = self.getPorts()
        for port in ports:
            if port.name == name:
                return port
        return None


class TestbedLink(GenericLink,Properties):
    def __init__(self,node1,port1,node2,port2,props={}):
        GenericLink.__init__(self,node1,port1,node2,port2)
        Properties.__init__(self,self.getResourceName(),props)
        node1.props['links'].append(self)
        node2.props['links'].append(self)
        self.setSpeed(10*1024) # Assume 10G speed is in Mbps


class TestbedHost(GenericHost,Properties):
    def __init__(self,name,props={}):
        GenericHost.__init__(self,name)
        Properties.__init__(self,self.getResourceName(),props)
        self.props['links'] = []

class TestbedPort(GenericPort,Port):
    def __init__(self,port,node=None):
        GenericPort.__init__(self,port.name)
        Port.__init__(self,name=port.name,props=port.props)
        self.props['macs'] = {} # [mac] = port

@singleton
class TestbedTopology (GenericTopologyProvider):

    def displayDot(self):
        sys.stdout.write('.')
        sys.stdout.flush()

    def buildSwitch(self, switch):
        enosSwitch = TestbedNode(switch.name, props=dict(switch.props))
        self.addNode(enosSwitch)
        switch.props['enosNode'] = enosSwitch

    def buildHost(self,host):
        enosHost = TestbedHost(host.name,props=host.props)
        self.addNode(enosHost)
        host.props['enosNode'] = enosHost

    def buildLink(self,link):
        p1 = link.props['endpoints'][0]
        p2 = link.props['endpoints'][1]
        n1 = p1.props['node']
        n2 = p2.props['node']
        node1 = n1.props['enosNode']
        node2 = n2.props['enosNode']
        port1 = TestbedPort(port=p1)
        port1.props['enosNode'] = node1
        port1.setNode(node1)
        p1.props['enosPort'] = port1
        port2 = TestbedPort(port=p2)
        port2.props['enosNode'] = node2
        port2.setNode(node2)
        p2.props['enosPort'] = port2
        self.addPort (node1,port1)
        self.addPort (node2,port2)
        p1.props['switch'] = node1
        p2.props['switch'] = node2
        l = TestbedLink(node1,port1,node2,port2,props=link.props)
        link.props['enosLink'] = l
        self.addLink(l)
        # Links are assumed to be uni-directional. Create reverse link
        r = TestbedLink(node1=node2,port1=port2,node2=node1,port2=port1)
        self.addLink(r)

    def buildNodes(self):
        for switch in self.builder.switchIndex.values():
            self.buildSwitch(switch)
        for host in self.builder.hostIndex.values():
            self.buildHost(host)
        for link in self.builder.linkIndex.values():
            self.buildLink(link)


    def toGraph(self):
        graph = self.getGraph(TopologyProvider.WeightType.TrafficEngineering)
        # Add a non null arbitrary weight
        for e in graph.edgeSet():
            graph.setEdgeWeight(e, 1)

    def __init__(self, fileName = None):
        # Build topology
        self.builder = TopoBuilder(fileName = fileName)
        self.buildNodes()

def linkednode(link,host,port=None):
    """
    Retrieve the host/port connected to provide host/port
    :param link:
    :param host: name of host (string)
    :param port: optional (string)
    :return:
    """
    (srcNode,srcPort,dstNode,dstPort,vlan) = parselink(link)

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

def getlinks(node1,node2):
    global topo
    links = []
    for (name,link) in topo.builder.linkIndex.items():
        (dstNode,dstPort) = linkednode(link,node1)
        if (dstNode,dstPort) == (None,None):
            continue
        (dstNode,dstPort) = linkednode(link,node2)
        if (dstNode,dstPort) == (None,None):
            continue
        links.append(link)
    return links

def parselink(link):
    [srcNode,srcPort,dstNode,dstPort,vlan] = link.name.split("#")
    srcNode = srcNode.split("@")[0]
    dstNode = dstNode.split("@")[0]
    return (srcNode,srcPort,dstNode,dstPort,vlan)

def displaylink(link):
    (srcNode,srcPort,dstNode,dstPort,vlan) = parselink(link)
    print "Link src",srcNode,srcPort,"\tdst",dstNode,dstPort,"\tvlan",vlan

def createdb(containerName):
    user = KernelThread.currentKernelThread().getUser()
    if not  BootStrap.getBootStrap().getDataBase().collectionExists(user.getName(),containerName):
        Container.createContainer(user.getName(),containerName)
    container = Container.getContainer(containerName)


def print_syntax():
    print
    print "topology <cmd> <cmds options>"
    print "Configures testbed hosts and their datapath. Commands are:"
    print " Commands are:"
    print "\nhelp"
    print "\tPrints this help."
    print "\ncreate-db <container name> creates a container and populates it with the topology."
    print "\nshow-link:"
    print "\n\tshow-link all Displays all links."
    print "\n\tshow-link all host <host name> [port <port name> Displays all links ending\n\tonto the specified host."
    print "\n\tshow-link betwen host host: Display links between two hosts."

    print

if not 'topo' in globals() or topo == None:
    topo = TestbedTopology()
    globals()['topo'] = topo

if __name__ == '__main__':
    # Retrieve topology
    if not 'topo' in globals():
        topo = TestbedTopology()
        globals()['topo'] = topo

    argv = sys.argv

    cmd = argv[1]
    if cmd == "help":
        print_syntax()
    elif cmd == "create-db":
        container = argv[2]
        createdb(container)
    elif cmd == "show-link":
        link = argv[2]
        if link == 'all':
            host = None
            port = None
            if 'host' in argv:
                host = argv[4]
                if 'port' in argv:
                    port = argv[6]
            for (name,link) in topo.builder.linkIndex.items():
                if host != None:
                    (dstNode,dstPort) = linkednode(link,host,port)
                    if (dstNode,dstPort) == (None,None):
                        continue
                displaylink(link)
        elif link == "between":
            host1 = argv[3]
            host2 = argv[4]
            links = getlinks(host1,host2)
            for link in links:
                displaylink(link)
