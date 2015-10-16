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

"""
demo should be run no more than once to initialize the topology.
Global variables such as net, renderers and rendererIndex are shared
to CLI environment.
"""
from mininet.sites import SiteIntent, SiteRenderer
from mininet.enos import TestbedTopology
from mininet.l2vpn import SDNPopsRenderer,SDNPopsIntent
from mininet.wan import WanRenderer, WanIntent

import random
from common.utils import InitLogger, Logger

# TODO collect into a global variable demo might be a good idea
try:
    if net == TestbedTopology(): # singleton
        print "Please reload first"
    else: # rare situation; net might be reloaded in python interactive intepreter manually
        net = None
except: # the case that net is not existed (in the very begining) yet
    net = None
    renderers = []
    rendererIndex = {}
    vpns = [] # used in vpn.py only
    vpnIndex = {} # used in vpn.py only

def main():
    global net
    global renderers
    global rendererIndex
    global vpns
    global vpnIndex
    if net:
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
        net = TestbedTopology(fileName=configFileName)
    else:
        net = TestbedTopology()
    # One-time setup for the VPN service
    wi = WanIntent("esnet", net.builder.wan)
    wr = WanRenderer(wi)
    wr.execute()
    renderers.append(wr)
    rendererIndex[wr.name] = wr

    for site in net.builder.sites:
        intent = SiteIntent(name=site.name, site=site)
        sr = SiteRenderer(intent)
        suc = sr.execute() # no function without vpn information
        if not suc:
            Logger().warning('%r.execute() fail', sr)
        renderers.append(sr)
        rendererIndex[sr.name] = sr
    print "Now the demo environment is ready."

if __name__ == '__main__':
    main()
