#!/usr/bin/python
import sys

from mininet.net import Mininet
from mininet.node import Controller, OVSKernelSwitch, RemoteController
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.topo import Topo

from api import Node, SDNPop,Link,Port,Site,VPN
from testbed import TopoBuilder

#
# OpenFlow controller IP and ports
#
controllerIp='192.168.56.1'
controllerPort=6633


class TestbedTopo(Topo):

    def setOpenFlow(self,net):
        global locations, viewAll

        print self.openflowSwitches
        for switch in self.openflowSwitches:
            net.getNodeByName(switch.props['mininetSwitch']).start([net.ctrl])

    def displayDot(self):
        sys.stdout.write('.')
        sys.stdout.flush()


    def start(self,net):
        self.setOpenFlow(net)

    def buildSwitch(self,switch):
        sw = self.addSwitch(switch.props['mininetName'],listenPort=6634,dpid=switch.props['dpid'])
        switch.props['mininetSwitch'] = sw
        self.openflowSwitches.append(switch)

    def buildHost(self,host):
        h = self.addHost(host.props['mininetName'])
        host.props['mininetHost'] = h

    def buildLink(self,link):
        port1 = link.props['endpoints'][0]
        port2 = link.props['endpoints'][1]
        node1 = self.builder.nodes[port1.props['node']]
        node2 = self.builder.nodes[port2.props['node']]
        self.addLink(node1.props['mininetName'],node2.props['mininetName'],int(port1.name[3:]),int(port2.name[3:]))


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
        Topo.__init__(self)
        self.openflowSwitches = []
        # Build topology
        self.builder = TopoBuilder(fileName)
        self.buildCore()
        self.buildVpns()


class ESnetMininet(Mininet):

    def __init__(self, **args):
        global controllerIp, controllerPort
        self.topo = TestbedTopo()
        args['topo'] = self.topo
        args['switch'] = OVSKernelSwitch
        args['controller'] = RemoteController
        args['build'] = False
        Mininet.__init__(self, **args)
        self.ctrl = self.addController( 'c0', controller=RemoteController, ip=controllerIp, port=controllerPort)

    def start(self):
        "Start controller and switches."
        if not self.built:
            self.build()
        self.topo.start(self)

if __name__ == '__main__':
    setLogLevel( 'info' )
    # todo: real argument parsing.
    configFileName = None
    if len(sys.argv) > 1:
        configFileName = sys.argv[1]
        net = ESnetMininet(fileName=configFileName)
    else:
        net = ESnetMininet()

    net.start()
    CLI(net)
    net.stop()