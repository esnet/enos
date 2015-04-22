#!/usr/bin/python
import sys

from mininet.testbed import TopoBuilder
from net.es.netshell.api import GenericTopologyProvider, TopologyProvider, GenericHost, GenericNode, GenericPort, GenericLink
from common.api import Properties
from common.openflow import Match, Action, FlowMod, Scope, SimpleController
from odl.client import ODLClient
from common.utils import singleton

nodes = {}


class TestbedNode(GenericNode,Properties):
    def __init__(self,name,props={}):
        GenericNode.__init__(self,name)
        global nodes
        nodes[name] = self
        Properties.__init__(self,name=self.getResourceName(),props=props)

class TestbedLink(GenericLink,Properties):
    def __init__(self,node1,port1,node2,port2,props={}):
        GenericLink.__init__(self,node1,port1,node2,port2)
        Properties.__init__(self,self.getResourceName(),props)

class TestbedHost(GenericHost,Properties):
    def __init__(self,name,props={}):
        GenericHost.__init__(self,name)
        Properties.__init__(self,self.getResourceName(),props)

class TestbedPort(GenericPort,Properties):
    def __init__(self,name,props={}):
        GenericPort.__init__(self,name)
        Properties.__init__(self,self.getResourceName(),props)

    def __init__(self,port):
        GenericPort.__init__(self,port.name)
        Properties.__init__(self,name=port.name,props=port.props)


@singleton
class TestbedTopology (GenericTopologyProvider):

    def displayDot(self):
        sys.stdout.write('.')
        sys.stdout.flush()

    def buildSwitch(self,switch):
        sw = TestbedNode(switch.name,props=switch.props)
        self.addNode(sw)
        switch.props['enosNode'] = sw
        sw.props['controller'] = self.controller

    def buildHost(self,host):
        h = TestbedHost(host.name,props=host.props)
        self.addNode(h)
        host.props['enosNode'] = h

    def buildLink(self,link):
        p1 = link.props['endpoints'][0]
        p2 = link.props['endpoints'][1]
        port1 = TestbedPort(port=p1)
        p1.props['enosPort'] = port1
        port2 = TestbedPort(port=p2)
        p2.props['enosPort'] = port2
        node1 = self.builder.nodes[p1.props['node']].props['enosNode']
        node2 = self.builder.nodes[p2.props['node']].props['enosNode']
        self.addPort (node1,port1)
        self.addPort (node2,port2)
        p1.props['switch'] = node1
        p2.props['switch'] = node2
        l = TestbedLink(node1,port1,node2,port2,props=link.props)
        link.props['enosLink'] = l
        self.addLink(l)

    def buildCore(self):
        for coreRouter in self.builder.coreRouters.items():
            self.buildSwitch(coreRouter[1])
        for hwSwitch in self.builder.hwSwitches.items():
            self.buildSwitch(hwSwitch[1])
        for swSwitch in self.builder.swSwitches.items():
            self.buildSwitch(swSwitch[1])
        for link in self.builder.coreLinks.items():
            self.buildLink(link[1])

    def buildVpn(self,vpn):
        """

        :param vpn: TopoVPN
        :return:
        """
        for s in vpn.props['sites']:
            site = vpn.props['sites'][s]
            siteRouter = site.props['siteRouter']
            self.buildSwitch(siteRouter)
            for h in site.props['hosts']:
                host = site.props['hosts'][h]
                self.buildHost(host)
            self.buildHost(site.props['serviceVm'])

            for l in site.props['links']:
                link = site.props['links'][l]
                self.buildLink(link)

    def buildVpns(self):
        for vpnName in self.builder.vpns:
            vpn = self.builder.vpns[vpnName]
            self.buildVpn(vpn)

    def findCoreRouterPorts(self, router, target):
        """
        Find the router ports facing a target
        """
        coreRouterLinks = []
        siteRouterLinks = []
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

