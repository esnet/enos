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
import sys

from mininet.testbed import TopoBuilder
from net.es.netshell.api import GenericTopologyProvider, TopologyProvider, GenericHost, GenericNode, GenericPort, GenericLink
from common.api import Properties, Port
from common.openflow import Match, Action, FlowMod, Scope, SimpleController
from odl.client import ODLClient
from common.utils import singleton

from common.mac import MACAddress

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

class TestbedHost(GenericHost,Properties):
    def __init__(self,name,props={}):
        GenericHost.__init__(self,name)
        Properties.__init__(self,self.getResourceName(),props)
        self.props['links'] = []

class TestbedPort(GenericPort,Port):
    def __init__(self,port):
        GenericPort.__init__(self,port.name)
        Port.__init__(self,name=port.name,props=port.props)
        self.props['macs'] = {} # [mac] = port


@singleton
class TestbedTopology (GenericTopologyProvider):

    def displayDot(self):
        sys.stdout.write('.')
        sys.stdout.flush()

    def buildSwitch(self, switch):
        enosSwitch = TestbedNode(switch.name, props=dict(switch.props, controller=self.controller))
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
        p1.props['enosPort'] = port1
        port2 = TestbedPort(port=p2)
        port2.props['enosNode'] = node2
        p2.props['enosPort'] = port2
        self.addPort (node1,port1)
        self.addPort (node2,port2)
        p1.props['switch'] = node1
        p2.props['switch'] = node2
        l = TestbedLink(node1,port1,node2,port2,props=link.props)
        link.props['enosLink'] = l
        self.addLink(l)

    def buildCore(self):
        for switch in self.builder.switches:
            self.buildSwitch(switch)
        for host in self.builder.hosts:
            self.buildHost(host)
        for link in self.builder.links:
            self.buildLink(link)

    def buildVpns(self):
        pass

    def findCoreRouterPorts(self, router, target):
        """
        Find the router ports facing a target
        """
        coreRouterPortLinks = {}

        for p in router.props['ports']:
            for p2 in target.props['ports']:
                if router.props['ports'][p].props['link'] == target.props['ports'][p2].props['link']:
                    coreRouterPortLinks[p] = router.props['ports'][p]
        return coreRouterPortLinks

    def selectPort(self, ports):
        """
        Select a port that we want to use from a set of ports.  Use this to
        pick one from a set of ports going to parallel links.  For now
        we'll prefer the lowest numbered ports and best-effort service.
        """
        for p in ports:
            linkName = ports[p].props['link']
            if linkName[-1:] == '1' or linkName[-12:] == ':best-effort':
                return ports[p]
        return None

    def makeCircuitOnNode(self, controller, scope, router, startPort, endPort, startVlan, endVlan):
        """
        Set up the virtual circuit mapping on a router.  This is a bidirectional
        circuit, so we need to insert two flow entries, one in each direction.
        """
        print "On router " + router.name + ":"
        print startPort.name + " (" + startPort.props['link'] + ") VLAN " + str(startVlan) + " -> " + endPort.name + " (" + endPort.props['link'] + ") VLAN " + str(endVlan)
        print endPort.name + " (" + endPort.props['link'] + ") VLAN " + str(endVlan) + " -> " + startPort.name + " (" + startPort.props['link'] + ") VLAN " + str(startVlan)

        # If a controller is specified, push flows to it.
        if controller:
            m1 = Match()
            m1.props['in_port'] = startPort.name
            m1.props['vlan'] = startVlan
            a1 = Action()
            a1.props['vlan'] = endVlan
            a1.props['out_port'] = endPort.name
            f1 = FlowMod(scope, router, a1, m1)
            controller.addFlowMod(f1)

            m2 = Match()
            m2.props['in_port'] = endPort.name
            m2.props['vlan'] = endVlan
            a2 = Action()
            a2.props['vlan'] = startVlan
            a2.props['out_port'] = startPort.name
            f2 = FlowMod(scope, router, a2, m2)
            controller.addFlowMod(f2)

    def makeCircuit(self, controller, scope, startTarget, routers, endTarget, vlan):
        """
        Make a virtual circuit
        """

        router = routers[0]
        startPorts = self.findCoreRouterPorts(router, startTarget)
        endPort = None

        if len(routers) == 1:
            # Only one router in the path, so hook the start and end targets together
            endPorts = self.findCoreRouterPorts(router, endTarget)
        else:
            # Multiple routers, so hook the start target to the router interface
            # facing the next router in the path
            endPorts = self.findCoreRouterPorts(router, routers[1])

        startPort = self.selectPort(startPorts)
        endPort = self.selectPort(endPorts)
        self.makeCircuitOnNode(controller, scope, router, startPort, endPort, vlan, vlan)

        # If there are more routers left to set up, call ourselves recursively
        # to do the rest.  This is a cool form of tail recursion.
        if len(routers) > 1:
            self.makeCircuit(controller, scope, router, routers[1:], endTarget, vlan)


    def makeCircuitNames(self, controller, scope, startTargetName, routerNames, endTargetName, vlan):
        """
        Make a virtual circuit given node names.
        This function looks up the node names in the network model and feeds
        the corresponding objects to makeCircuit.
        """

        startTarget = self.builder.nodes[startTargetName]
        endTarget = self.builder.nodes[endTargetName]

        routers = []
        for r in routerNames:
            routers.append(self.builder.coreRouters[r])

        self.makeCircuit(controller, scope, startTarget, routers, endTarget, vlan)

    def __init__(self, fileName = None, controller = None):
        if not controller:
            self.controller = ODLClient(topology=self)
        else:
            self.controller = controller
        # Build topology
        self.builder = TopoBuilder(fileName = fileName, controller = self.controller)
        self.buildCore()
        self.buildVpns()
        if not controller:
            # now that self.builder is ready
            self.controller.init()

if __name__ == '__main__':
    # todo: real argument parsing.
    configFileName = None
    net=None
    if len(sys.argv) > 1:
        configFileName = sys.argv[1]
        net = TestbedTopology(fileName=configFileName)
    else:
        net = TestbedTopology()
    # viewer = net.getGraphViewer(TopologyProvider.WeightType.TrafficEngineering)
    graph = net.getGraph(TopologyProvider.WeightType.TrafficEngineering)

