#!/usr/bin/python
import sys

from layer2.testbed.builder import TopoBuilder
from net.es.netshell.api import GenericTopologyProvider, TopologyProvider, GenericHost, GenericNode, GenericPort, GenericLink
from layer2.common.mac import MACAddress
from layer2.common.api import Properties, Port
from layer2.common.openflow import Match, Action, FlowMod, Scope, SimpleController
from layer2.odl.client import ODLClient
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

    def buildSite(self,site):
        for host in site.props['hosts']:
            self.buildHost(host)
        switch = site.props['switch']
        self.buildSwitch(switch=switch)

    def buildSites(self):
        for site in self.builder.siteIndex.values():
            self.buildSite(site)

    def buildCore(self):
        for switch in self.builder.switchIndex.values():
            self.buildSwitch(switch)
        for host in self.builder.hostIndex.values():
            self.buildHost(host)
        for link in self.builder.linkIndex.values():
            self.buildLink(link)

    def buildVpns(self):
        pass

    def __init__(self, fileName = None, controller = None):
        if not controller:
            self.controller = ODLClient(topology=self)
        else:
            self.controller = controller
        # Build topology
        self.builder = TopoBuilder(fileName = fileName, controller = self.controller)
        self.buildSites()
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

