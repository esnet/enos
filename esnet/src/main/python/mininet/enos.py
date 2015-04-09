#!/usr/bin/python
import sys

from mininet.testbed import TopoBuilder
from net.es.netshell.api import GenericTopologyProvider, TopologyProvider, GenericHost, GenericNode, GenericPort, GenericLink
from common.api import Properties
from odl.client import ODLClient

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



class TestbedTopology (GenericTopologyProvider):

    def displayDot(self):
        sys.stdout.write('.')
        sys.stdout.flush()

    def buildSwitch(self,switch):
        sw = TestbedNode(switch.name,props=switch.props)
        self.addNode(sw)
        switch.props['enosNode'] = sw
        switch.props['controller'] = ODLClient()

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

    def __init__(self, fileName = None):
        # Build topology
        self.builder = TopoBuilder(fileName)
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

