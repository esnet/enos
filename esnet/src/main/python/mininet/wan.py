from string import join

from net.es.netshell.api import GenericGraph

from common.intent import ProvisioningRenderer, ProvisioningIntent
from common.openflow import ScopeOwner, L2SwitchScope, Match, Action, FlowMod

from mininet.enos import TestbedTopology

class WanRenderer(ProvisioningRenderer, ScopeOwner):
    """
    Implements the rendering of provisioning intent for the WAN.
    This pushes out the flow entries to the core routers for forwarding between the
    hardware switches.  It is a quasi-simulation of what we do in the OpenFlow
    testbed to set up connectivity between the switches with OSCARS circuits,
    although not an exact simulation since (as written) we assume that we already
    have VPNs allocated between the different core routers.
    """

    debug = True

    def __init__(self, intent):
        """
        Create renderer object and initialize a bunch of stuff
        :param intent:
        """
        ScopeOwner.__init__(self, name=intent.name)
#        ProvisioningRenderer.__init__(self, name=intent.name)
        self.pops=intent.pops
        self.graph=intent.graph
        self.intent = intent

        self.active=False
        self.activePorts={}
        self.flowmods=[]
        self.scopes={}

        # Create scopes for all of the places that we need to touch anything
        for pop in self.pops:

            if self.debug:
                print "WanRenderer: " + pop.name

            # Find the hardware router and core switch in both the topobuilder and base ENOS layers
            coreRouter=pop.props['coreRouter']
            enosCoreRouter=coreRouter.props['enosNode']

            # Create and add the scope
            scope=L2SwitchScope(name=intent.name+'-'+enosCoreRouter.name, switch=enosCoreRouter, owner=self)
            scope.props['endpoints'] = []
            scope.props['intent'] = self.intent
            # We need to add all of the places that WAN circuits terminate as scope endpoints
            for circuit in coreRouter.props['WAN-Circuits']:
                port = None
                # Each circuit has two endpoints, need to check them both
                for ep in circuit.props['endpoints']:
                    if ep.props['node'] == coreRouter.name:
                        port = ep.props['enosPort']
                vlan=circuit.props['vlan']
                if port == None:
                    print "Can't find this router among circuit endpoints"
                if self.debug:
                    print "WAN circuit " + str(port) + " vlan " + str(vlan)
                scope.props['endpoints'].append((port.name, [vlan]))
            for circuit in coreRouter.props['toHwSwitch']:
                port = None
                for ep in circuit.props['endpoints']:
                    if ep.props['node'] == coreRouter.name:
                        port = ep.props['enosPort']
                vlan=circuit.props['vlan']
                if port == None:
                    print "Can't find this router among circuit endpoints"
                if self.debug:
                    print "To HW switch " + str(port) + " vlan " + str(vlan)
                scope.props['endpoints'].append((port.name, [vlan]))
            if self.debug:
                print enosCoreRouter.name + ' scope', scope
            if not enosCoreRouter.props['controller'].addScope(scope):
                print "Cannot add " + str(scope)
            self.scopes[enosCoreRouter.name] = scope

            # Create scopes for all of the OpenFlow switches
            hwSwitch=pop.props['hwSwitch']
            enosHwSwitch=hwSwitch.props['enosNode']

            # Create and add scopes for interfaces on the hardware switch going to the software switch and core router
            scope=L2SwitchScope(name=intent.name+'-'+enosHwSwitch.name, switch=enosHwSwitch, owner=self)
            scope.props['endpoints'] = []
            scope.props['intent'] = self.intent
            for circuit in hwSwitch.props['toSwSwitch']:
                port = None
                for ep in circuit.props['endpoints']:
                    if ep.props['node'] == hwSwitch.name:
                        port = ep.props['enosPort']
                vlan=circuit.props['vlan']
                if port == None:
                    print "Can't find this hardware switch among circuit endpoints"
                scope.props['endpoints'].append((port.name, [vlan]))
            for circuit in hwSwitch.props['toCoreRouter']:
                port = None
                for ep in circuit.props['endpoints']:
                    if ep.props['node'] == hwSwitch.name:
                        port = ep.props['enosPort']
                vlan=circuit.props['vlan']
                if port == None:
                    print "Can't find this hardware switch among circuit endpoints"
                scope.props['endpoints'].append((port.name, [vlan]))
            if self.debug:
                print enosHwSwitch.name + ' scope', scope
            if not enosHwSwitch.props['controller'].addScope(scope):
                print "Cannot add " + str(scope)
            self.scopes[enosHwSwitch] = scope

        return

    def __str__(self):
        desc = "WanRenderer: " + self.name + "\n"
        desc += "\tPOPs: " + str.join (", ", (i.name for i in self.pops)) + "\n"
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

        # Create the mesh of virtual circuits between the hardware switches
        targets = self.pops
        for p1 in self.pops:
            targets = targets[1:]
            for p2 in targets:

                # Assumption:  All of the virtual circuits we create are of the form:
                # cr1 <-> sw1 <-> sw2 <-> cr2
                cr1 = p1.props['coreRouter'].props['enosNode']
                cr2 = p2.props['coreRouter'].props['enosNode']

                sw1 = p1.props['hwSwitch'].props['enosNode']
                sw2 = p2.props['hwSwitch'].props['enosNode']

                # First find the link between the two core routers.
                # We assume here that there is only one per router pair.  In a more
                # general case we would have to implement some kind of selection algorithm.
                linkcr1cr2 = None
                for l in cr1.props['WAN-Circuits']:
                    if l in cr2.props['WAN-Circuits']:
                        linkcr1cr2 = l
                if linkcr1cr2 is None:
                    print "Couldn't find link between " + cr1.name + " and " + cr2.name

                # We need to get the VLAN number.  There is an assumption that a virtual
                # circuit has only one VLAN id throughput its entire length.
                vlan = linkcr1cr2.props['vlan']
                if self.debug:
                    print "Found inter-pop link: " + str(linkcr1cr2) + " VLAN " + str(vlan)

                # Find the links on the routers that go to their respective hardware
                # switches.  We can do this by matching up the VLAN tags
                linksw1cr1 = None
                for l in cr1.props['toHwSwitch']:
                    if l.props['vlan'] == vlan:
                        linksw1cr1 = l
                if linksw1cr1 is None:
                    print "Couldn't find link between " + sw1.name + " and " + cr1.name
                if self.debug:
                    print "Found link to switch: " + str(linksw1cr1)

                linksw2cr2 = None
                for l in cr2.props['toHwSwitch']:
                    if l.props['vlan'] == vlan:
                        linksw2cr2 = l
                if linksw2cr2 is None:
                    print "Couldn't find link between " + sw2.name + " and " + cr2.name
                if self.debug:
                    print "Found link to switch: " + str(linksw1cr1)

                # Having found all the links, then stitch them together
                self.stitchVlans(cr1, linksw1cr1, linkcr1cr2)
                self.stitchVlans(cr2, linkcr1cr2, linksw2cr2)

        return

    def stitchVlans(self, router, link1, link2):
        """
        Stitch two VLAN interfaces together on a router.
        The router is the common router between the two links.

        """
        controller = router.props['controller']

        vlan1 = link1.props['vlan']
        intf1 = None
        for ep in link1.props['endpoints']:
            if ep.props['node'] == router.name:
                intf1 = ep.props['enosPort']
        if intf1 is None:
            print "Couldn't find correct end of link " + str(link1) + " on " + router.name

        vlan2 = link2.props['vlan']
        intf2 = None
        for ep in link2.props['endpoints']:
            if ep.props['node'] == router.name:
                intf2 = ep.props['enosPort']
        if intf2 is None:
            print "Couldn't find correct end of link " + str(link2) + " on " + router.name

        if controller:

            scope = self.scopes[router.name]
            if scope is None:
                print "Couldn't locate scope for " + str(router)
            if self.debug:
                print "Scope id " + str(scope.id) + " " + str(scope)
                print "Router DPID " + str(router.props['dpid'])

            m1 = Match('')
            m1.props['in_port'] = intf1
            m1.props['vlan'] = vlan1
            a1 = Action('')
            a1.props['vlan'] = vlan2
            a1.props['out_port'] = intf2
            f1 = FlowMod(scope, router, m1, "", [a1])
            if self.debug:
                print 'Push flow ' + str(f1)
            controller.addFlowMod(f1)

            m2 = Match('')
            m2.props['in_port'] = intf2
            m2.props['vlan'] = vlan2
            a2 = Action('')
            a2.props['vlan'] = vlan1
            a2.props['out_port'] = intf1
            f2 = FlowMod(scope, router, m2, "", [a2])
            if self.debug:
                print 'Push flow ' + str(f2)
            controller.addFlowMod(f2)


class WanIntent(ProvisioningIntent):
    """
    Describes the WAN setup needed to support the VPN service.
    In general this will consist of a set of hardware switches in various POPs,
    each of which is attached to a core router.  Between the core routers we have
    various configured VLANs for forwarding.  The intent describes those switches
    and POPs.
    """

    def __init__(self, name, pops):
        """
        Creates a provisioning intent for the WAN service.  It contains a
        GenericGraph of the pop-level topology.
        :param name:
        :param pops:  Array of pop objects
        """
        self.pops=pops
        self.graph=self.buildGraph()
        ProvisioningIntent.__init__(self, name=name, graph=self.graph)
        return

    def buildGraph(self):
        """
        Build the graph object.
        It's not exactly clear what we need from the graph object here.
        :return: net.es.netshell.api.GenericGraph
        """
        graph=GenericGraph()

        popsSoFar=[]
        for pop in self.pops:
            coreRouter=pop.props['coreRouter']
            hwRouter=pop.props['hwSwitch']
            enosCoreRouter=pop.props['coreRouter'].props['enosNode']
            enosHwSwitch= pop.props['hwSwitch'].props['enosNode']
            graph.addVertex(enosCoreRouter)
            graph.addVertex(enosHwSwitch)

            # Find the link between the HW switch and the core router.
            # This is the topobuilder layer.  There might be multiple
            # links here...arbitrarily pick the first one.
            link=pop.props['hwSwitch'].props['toCoreRouter'][0]
            enoslink=link.props['enosLink']
            vlan=link.props['vlan']

            node1=enoslink.getSrcNode()
            node2=enoslink.getDstNode()
            graph.addEdge(node1, node2, enoslink)

            # Now make the mesh of VCs between
            for (pop2) in popsSoFar:
                if pop == pop2:
                    continue
                coreRouter2=pop2.props['coreRouter'].props['enosNode']
                # WANCircuit?
                popsSoFar.append(pop2)

        return graph
