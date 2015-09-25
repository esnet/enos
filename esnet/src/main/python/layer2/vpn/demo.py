"""
demo should be run no more than once to initialize the topology.
Global variables such as net, renderers and rendererIndex are shared
to CLI environment.
"""
from layer2.testbed.topology import TestbedTopology
from layer2.vpn.l2vpn import SDNPopsRenderer,SDNPopsIntent
from layer2.vpn.wan import WanRenderer, WanIntent

import random
from layer2.common.utils import InitLogger, Logger

# TODO collect into a global variable demo might be a good idea
try:
    if topo == TestbedTopology(): # singleton
        print "Please reload first"
    else: # rare situation; topo might be reloaded in python interactive intepreter manually
        topo = None
except: # the case that topo is not existed (in the very begining) yet
    topo = None
    renderers = []
    rendererIndex = {}
    vpns = [] # used in vpn.py only
    vpnIndex = {} # used in vpn.py only

def main():
    global topo
    global renderers
    global rendererIndex
    global vpns
    global vpnIndex
    if topo:
        return

    renderers = []
    rendererIndex = {}
    vpns = [] # used in vpn.py only
    vpnIndex = {} # used in vpn.py only

    random.seed(0)    # in order to get the same result to simplify debugging
    InitLogger()
    configFileName = None
    if len(sys.argv) > 1:
        configFileName = sys.argv[1]
        topo = TestbedTopology(fileName=configFileName)
    else:
        topo = TestbedTopology()
    # One-time setup for the VPN service
    wi = WanIntent("esnet", topo.builder.wan)
    wr = WanRenderer(wi)
    wr.execute()
    renderers.append(wr)
    rendererIndex[wr.name] = wr

    print "Now the demo environment is ready."

if __name__ == '__main__':
    main()
