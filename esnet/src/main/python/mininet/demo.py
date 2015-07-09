"""
demo should be run no more than once to initialize the topology.
Global variables such as net, renderers and rendererIndex are shared
to CLI environment.
"""
from mininet.sites import SiteIntent, SiteRenderer
from common.openflow import SimpleController
from mininet.enos import TestbedTopology
from mininet.l2vpn import SDNPopsRenderer,SDNPopsIntent
from mininet.wan import WanRenderer, WanIntent
from net.es.netshell.api import GenericGraphViewer

import copy

import random
from common.utils import InitLogger, Logger
from mininet.mat import MAT

# TODO collect into a global variable demo might be a good idea
renderers = []
rendererIndex = {}
vpns = [] # used in vpn.py only
vpnIndex = {} # used in vpn.py only

if __name__ == '__main__':
    random.seed(0)    # in order to get the same result to simplify debugging
    InitLogger()
    configFileName = None
    net = None
    if len(sys.argv) > 1:
        configFileName = sys.argv[1]
        net = TestbedTopology(fileName=configFileName)
    else:
        net = TestbedTopology()
    # One-time setup for the VPN service
    wi = WanIntent("esnet", net.builder.pops)
    wr = WanRenderer(wi)
    wr.execute()
    renderers.append(wr)
    rendererIndex[wr.name] = wr

    for site in net.builder.sites:
        hosts = map(lambda h : h.props['enosNode'], site.props['hosts'])
        borderRouter = site.props['borderRouter'].props['enosNode']
        siteRouter = site.props['siteRouter'].props['enosNode']
        links = map(lambda l : l.props['enosLink'], site.props['links'])
        intent = SiteIntent(name=site.name, hosts=hosts, borderRouter=borderRouter, siteRouter=siteRouter, links=links)
        sr = SiteRenderer(intent)
        suc = sr.execute() # no function without vpn information
        if not suc:
            Logger().warning('%r.execute() fail', sr)
        renderers.append(sr)
        rendererIndex[sr.name] = sr
