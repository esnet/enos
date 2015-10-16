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

import sys, binascii, getopt

from mininet.net import Mininet
from mininet.node import Controller, OVSKernelSwitch, RemoteController
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.topo import Topo

from common.api import Node, Host, SDNPop, Link, Port, Site, VPN
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
