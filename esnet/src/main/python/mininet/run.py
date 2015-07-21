#!/usr/bin/python
import sys, binascii, getopt

from mininet.net import Mininet
from mininet.node import Controller, OVSKernelSwitch, RemoteController
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.topo import Topo

from common.api import Node, Host, ServiceVm, SDNPop,Link,Port,Site,VPN
from testbed import TopoBuilder
from common.mac import MACAddress
#
# OpenFlow controller IP and ports
#
controllerIp='127.0.0.1'
controllerPort=6633
configFileName = None


class TestbedTopo(Topo):

    def setOpenFlow(self,net):
        global locations, viewAll

        for switch in self.openflowSwitches:
            net.getNodeByName(switch.props['mininetSwitch']).start([net.ctrl])

    def displayDot(self):
        sys.stdout.write('.')
        sys.stdout.flush()


    def start(self,net):
        self.setOpenFlow(net)

    def buildSwitch(self,switch):
        dpid = binascii.hexlify(switch.props['dpid'])
        sw = self.addSwitch(switch.props['mininetName'],listenPort=6634,dpid=dpid)
        switch.props['mininetSwitch'] = sw
        self.openflowSwitches.append(switch)

    def buildHost(self,host):
        mac = None
        if 'mac' in host.props:
            mac = str(host.props['mac'])
        h = self.addHost(host.props['mininetName'], mac=mac)
        host.props['mininetHost'] = h

    def buildLink(self,link):
        port1 = link.props['endpoints'][0]
        port2 = link.props['endpoints'][1]
        node1 = port1.props['node']
        node2 = port2.props['node']
        self.addLink(node1.props['mininetName'],node2.props['mininetName'],port1.props['interfaceIndex'],port2.props['interfaceIndex'])

    def buildCore(self):
        for switch in self.builder.switches:
            self.buildSwitch(switch)
        for host in self.builder.hosts:
            self.buildHost(host)
        for link in self.builder.links:
            self.buildLink(link)

    def buildVpn(self,vpn):
        """
        :param vpn: TopoVPN
        :return:
        """

    def buildVpns(self):
        pass
    def __init__(self, fileName = None):
        Topo.__init__(self)
        self.openflowSwitches = []
        # Build topology
        self.builder = TopoBuilder(fileName)
        self.buildCore()
    def addVm(self, vpnname, popname, wanVlan = 0):
        """
        Could be invoked in mininet CLI
        :param popname:
        """
        if not popname in self.builder.popIndex:
            print "pop %s not found" % popname
            return
        name = "%s-%s-vm" % (vpnname, popname)
        host = ServiceVm(name=name)
        self.builder.addHost(host)
        self.builder.updateHost(host)
        hostname = host.props['mininetName']
        self.addHost(hostname, mac=str(host.props['mac']))
        pop = self.builder.popIndex[popname]
        swSwitch = pop.props['swSwitch']
        link = Link.create(host, swSwitch, wanVlan)
        self.builder.addLink(link)
        port1 = link.props['endpoints'][0]
        port2 = link.props['endpoints'][1]
        node1 = port1.props['node']
        node2 = port2.props['node']
        self.addLink(node1.props['mininetName'],node2.props['mininetName'],port1.props['interfaceIndex'],port2.props['interfaceIndex'])


class ESnetMininet(Mininet):

    def __init__(self, **args):
        global controllerIp, controllerPort, configFileName
        self.topo = TestbedTopo()
        args['topo'] = self.topo
        args['switch'] = OVSKernelSwitch
        args['controller'] = RemoteController
        args['build'] = False
        Mininet.__init__(self, **args)
        self.ctrl = self.addController( 'c0', controller=RemoteController, ip=controllerIp, port=controllerPort)
        if configFileName:
            with open(configFileName, "r") as f:
                for line in f:
                    data = line.split()
                    vpnname = data[0]
                    popname = data[1]
                    wanVlan = 0
                    if len(data) >= 3:
                        wanVlan = data[2]
                    self.topo.addVm(vpnname, popname, wanVlan)
    def start(self):
        "Start controller and switches."
        if not self.built:
            self.build()
        self.topo.start(self)

    def listPop(self):
        for pop in self.topo.builder.pops:
            print pop

if __name__ == '__main__':
    opts, args = getopt.getopt(sys.argv[1:],"f:c:p:",['file=','controller=','port='])
    for opt, arg in opts:
        if opt in ['-f','--file']:
            configFileName = arg
        elif opt in ['-c','--controller']:
            controllerIp = arg
        elif opt in ['-p','--port']:
            controllerPort = int(arg)

    setLogLevel( 'info' )

    net = ESnetMininet()

    net.start()
    net.topo.builder.displaySwitches()
    CLI(net)
    net.stop()
