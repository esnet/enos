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
from string import join

from net.es.netshell.api import GenericGraph

from common.intent import ProvisioningRenderer, ProvisioningIntent, ProvisioningExpectation
from common.openflow import ScopeOwner, L2SwitchScope, Match, Action, FlowMod

from odl.client import ODLClient
from mininet.enos import TestbedTopology
from common.mac import MACAddress

class WanRenderer(ProvisioningRenderer, ScopeOwner):
    """
    Implements the rendering of provisioning intent for the WAN.
    This pushes out the flow entries to the core routers for forwarding between the
    hardware switches.  It is a quasi-simulation of what we do in the OpenFlow
    testbed to set up connectivity between the switches with OSCARS circuits,
    although not an exact simulation since (as written) we assume that we already
    have VPNs allocated between the different core routers.
    """

    debug = False

    def __init__(self, intent):
        """
        Create renderer object and initialize a bunch of stuff
        :param intent:
        """
        ScopeOwner.__init__(self, name=intent.name)
#        ProvisioningRenderer.__init__(self, name=intent.name)
        self.intent=intent
        self.wan=intent.wan
        # add hwSwitch (in addition to coreRouter only)
        self.nodes = []
        self.links = []
        for pop in self.wan.props['pops']:
            coreRouter = pop.props['coreRouter'].props['enosNode']
            self.nodes.append(coreRouter)
            hwSwitch = pop.props['hwSwitch'].props['enosNode']
            self.nodes.append(hwSwitch)
        for link in self.intent.links:
            self.links.append(link)
            (wanPort1, wanPort2) = link.props['endpoints']
            coreRouter1 = wanPort1.props['node']
            corePort1 = coreRouter1.props['stitchedPortIndex.WAN'][wanPort1.name]
            link1 = corePort1.props['links'][0].props['enosLink'] # assume only one link in the port
            self.links.append(link1)
            coreRouter2 = wanPort2.props['node']
            corePort2 = coreRouter2.props['stitchedPortIndex.WAN'][wanPort2.name]
            link2 = corePort2.props['links'][0].props['enosLink'] # assume only one link in the port
            self.links.append(link2)
        self.intentGraph=intent.graph
        self.graph=self.buildGraph()

        self.active=False
        self.activePorts={}
        self.props['scopeIndex'] = {} # [coreRouter.name] = L2SwitchScope

        # Create scopes for all of the places that we need to touch anything
        for pop in self.wan.props['pops']:
            if self.debug:
                print "WanRenderer: " + pop.name

            # Find the hardware router and core switch in both the topobuilder and base ENOS layers
            coreRouter = pop.props['coreRouter'].props['enosNode']
            # Create and add the scope
            scope=L2SwitchScope(name=intent.name+'-'+coreRouter.name, switch=coreRouter, owner=self,endpoints={})
            scope.props['intent'] = self.intent
            for port in coreRouter.getPorts():
                if port.props['type'] in ['CoreToHw.WAN', 'CoreToCore.WAN']:
                    for link in port.props['links']:
                        scope.addEndpoint(port, link.props['vlan'])
            if self.debug:
                print coreRouter.name + ' scope', scope
            if not coreRouter.props['controller'].addScope(scope):
                print "Cannot add " + str(scope)
            self.props['scopeIndex'][coreRouter.name] = scope
        return

    def __str__(self):
        desc = "WanRenderer: " + self.name + "\n"
        desc += "\tPOPs: " + str.join (", ", (i.name for i in self.wan.props['pops'])) + "\n"
        desc += "\tRouters: " + str.join (", ", (pop.props['coreRouter'].name for pop in self.wan.props['pops'])) + "\n"
        return desc

    def __repr__(self):
        return self.__str__()

    def eventListener(self,event):
        """
        Handle received events from the controller, i.e. PACKET_IN
        :param event: ScopeEvent

        Not sure this is actually useful, since all of the scopes associated with the WanRenderer
        only exist for the purpose of setting up flow entries.  After doing execute() there aren't
        any other actions that need to happen.
        """
        return

    def execute(self):
        """
        Render the intent.
        """
        for pop in self.wan.props['pops']:
            coreRouter = pop.props['coreRouter'].props['enosNode']
            for port1 in coreRouter.getPorts():
                if port1.props['type'].endswith('.WAN'):
                    link1 = port1.props['links'][0].props['enosLink'] # assume only one link in the port
                    port2 = coreRouter.props['stitchedPortIndex.WAN'][port1.name]
                    link2 = port2.props['links'][0].props['enosLink'] # assume only one link in the port
                    self.stitchVlans(coreRouter, link1, link2)
        expectation = WanExpectation(self.name,self,self.intent,self.graph)
        return expectation

    def stitchVlans(self, router, link1, link2):
        """
        Stitch two VLAN interfaces together on a router.
        The router is the common router between the two links.
        """
        controller = router.props['controller']

        vlan1 = link1.props['vlan']
        intf1 = link1.props['portIndex'][router.name].props['enosPort']

        vlan2 = link2.props['vlan']
        intf2 = link2.props['portIndex'][router.name].props['enosPort']

        scope = self.props['scopeIndex'][router.name]
        scope.forward(router, None, vlan1, intf1, None, vlan2, intf2)

    def addLinkIntoGraph(self, link, graph):
        """
        link: enosLink
        """
        graph.addEdge(link.getSrcNode(), link.getDstNode(), link)

    def buildGraph(self):
        """
        Build the graph object.
        It's not exactly clear what we need from the graph object here.
        :return: net.es.netshell.api.GenericGraph
        """
        graph=GenericGraph()
        for node in self.nodes:
            graph.addVertex(node)
        for link in self.links:
            self.addLinkIntoGraph(link, graph)
        return graph

class WanIntent(ProvisioningIntent):
    """
    Describes the WAN setup needed to support the VPN service.
    In general this will consist of a set of hardware switches in various POPs,
    each of which is attached to a core router.  Between the core routers we have
    various configured VLANs for forwarding.  The intent describes those switches
    and POPs.
    """

    def __init__(self, name, wan):
        """
        Creates a provisioning intent for the WAN service.  It contains a
        GenericGraph of the pop-level topology.
        :param name:
        :param pops:  Array of pop objects
        """
        self.wan=wan
        pops=wan.props['pops']
        nodes=map(lambda pop : pop.props['coreRouter'], pops)
        links=filter(lambda link : link.props['endpoints'][0].props['node'] in nodes and link.props['endpoints'][1].props['node'] in nodes, wan.props['links'])
        self.nodes=map(lambda node : node.props['enosNode'], nodes)
        self.links=map(lambda link : link.props['enosLink'], links)
        self.graph=self.buildGraph()
        ProvisioningIntent.__init__(self, name=name, graph=self.graph)

    def __str__(self):
        desc = "WanIntent: " + self.name + "\n"
        desc += "\tPOPs: " + str.join (", ", (i.name for i in self.wan.props['pops'])) + "\n"
        return desc

    def __repr__(self):
        return self.__str__()

    def buildGraph(self):
        """
        Build the graph object.
        Idea here is to show (approximately) POP-layer full-mesh connectivity
        :return: net.es.netshell.api.GenericGraph
        """
        graph=GenericGraph()
        for node in self.nodes:
            graph.addVertex(node)
        for link in self.links:
            graph.addEdge(link.getSrcNode(), link.getDstNode(), link)
        return graph

class WanExpectation(ProvisioningExpectation):
    def __init__(self,name,renderer,intent,graph,props={}):
        ProvisioningExpectation.__init__(self,name=name,renderer=renderer,intent=intent,graph=graph,props=props)
        # Save nextHop ports for stitching?

    def __str__(self):
        desc = "WanExpectation: " + self.name + "\n"
        desc += "\tPOPs: " + str.join (", ", (pop.name for pop in self.intent.wan.props['pops'])) + "\n"
        desc += "\tRouters: " + str.join (", ", (pop.props['coreRouter'].name for pop in self.intent.wan.props['pops'])) + "\n"

        return desc

    def __repr__(self):
        return self.__str__()

