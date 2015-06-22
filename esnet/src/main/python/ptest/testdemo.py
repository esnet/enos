import net.es.netshell.odl.Controller
import net.es.netshell.odl.PacketHandler

from ptest.testtopo import TestTopo

from ptest.pobject import PController
from ptest.pobject import PMAC
from ptest.pobject import PSwitch, PSiteRouter

from mininet.utility import Logger, InitLogger
from mininet.mat import MATManager
import random
import logging

import sys
sys.prefix = "/lib"
import argparse

class TestDemo(net.es.netshell.odl.PacketHandler.Callback):
    def __init__(self, topo, controller):
        # debug only
        self.topo = topo
        self.controller = controller
    def callback(self, rawPacket):
        return self.controller.callback(PPacket(rawPacket))
    def start(self):
        net.es.netshell.odl.PacketHandler.getInstance().setPacketInCallback(self)
    def pause(self):
        net.es.netshell.odl.PacketHandler.getInstance().setPacketInCallback(None)

demo = None
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--topo", type=int, default=1, action="store", dest="topo", help="select topology. 1: h1-s1-h2; 2: h1-s1-s2-h2")
    parser.add_argument("--level", type=int, default=logging.INFO, action="store", dest="level", help="The log level (10: DEBUG; 20: INFO)")
    args = parser.parse_args(command_args[2:])
    topo = TestTopo.create(args.topo)
    controller = PController("c0")
    topo.setController(controller)
    random.seed(0)
    MATManager.reset()
    InitLogger()
    Logger().setLevel(args.level)
    Logger().debug("testdemo args=%r", args)
    global demo
    demo = TestDemo(topo, controller)
    demo.start()

if __name__ == '__main__':
    main()