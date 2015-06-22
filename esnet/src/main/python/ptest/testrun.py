#!/usr/bin/python
"""
This python script will be run in the generic python (mininet) instead of jython (netshell)
"""
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel
from mininet.cli import CLI
from mininet.node import Controller, OVSKernelSwitch, RemoteController

from ptest.testtopo import TestTopo
import binascii
import argparse

class TestMininetTopo(Topo):
    "Single switch connected to n hosts."
    def build(self, template):
        for switch in template.switches:
            self.addSwitch(switch.mininetName, dpid=switch.dpid)
        for host in template.hosts:
            self.addHost(host.mininetName)
        for link in template.links:
            self.addLink(link.endpoints[0].node.mininetName, link.endpoints[1].node.mininetName, link.endpoints[0].number, link.endpoints[1].number)
        return
def main():
    # Tell mininet to print useful information
    setLogLevel('info')
    parser = argparse.ArgumentParser()
    parser.add_argument("--topo", type=int, default=1, action="store", dest="topo", help="select topology. 1: h1-s1-s2-h2")
    parser.add_argument("--ip", type=str, default='127.0.0.1', action="store", dest="ip", help="The IP address of the remote controller")
    parser.add_argument("--port", type=int, default=6633, action="store", dest="port", help="The port of the remote controller")
    args = parser.parse_args()
    testtopo = TestTopo.create(args.topo)
    topo = TestMininetTopo(template=testtopo)
    net = Mininet(topo=topo, controller=None)
    net.addController('c0', controller=RemoteController, ip=args.ip, port=args.port)
    net.start()
    print "Dumping host connections"
    dumpNodeConnections(net.hosts)
    CLI(net)
    net.stop()

if __name__ == '__main__':
    main()
