from string import join

from net.es.netshell.api import GenericGraph

from common.intent import ProvisioningRenderer, ProvisioningIntent
from common.openflow import ScopeOwner, L2SwitchScope

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
                scope.props['endpoints'].append((port.name, [vlan]))
            for circuit in coreRouter.props['toHwSwitch']:
                port = None
                for ep in circuit.props['endpoints']:
                    if ep.props['node'] == coreRouter.name:
                        port = ep.props['enosPort']
                vlan=circuit.props['vlan']
                if port == None:
                    print "Can't find this router among circuit endpoints"
                scope.props['endpoints'].append((port.name, [vlan]))
            if self.debug:
                print enosCoreRouter.name + ' scope', scope
            enosCoreRouter.props['controller'].addScope(scope)
            self.scopes[enosCoreRouter] = scope

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
            enosHwSwitch.props['controller'].addScope(scope)
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
        for p in self.pops:
            targets = targets[1:]
            for p2 in targets:

                link=p.props['hwSwitch'].props['toCoreRouter'][0]
                vlan = link.props['vlan']

                link2 = p2.props['hwSwitch'].props['toCoreRouter'][0]
                vlan2 = link2.props['vlan']

                if self.debug:
                    print "Create virtual circuit from " + p.name + " to " + p2.name
                    print "\tFrom " + p.props['hwSwitch'].name + " vlan " + str(vlan) + " to " + p2.props['hwSwitch'].name + " vlan " + str(vlan2)
                    print "\tVia " + p.props['coreRouter'].name + ", " + p2.props['coreRouter'].name

                self.makeCircuit(p.props['hwSwitch'], vlan, [p.props['coreRouter'], p2.props['coreRouter']], p2.props['hwSwitch'], vlan2)

        return

    def findCoreRouterPorts(self, router, target):
        """
        Find the router ports facing a target
        :param router, topobuilder level node
        :param target, topobuilder level node
        """
        coreRouterPortLinks = []

        print "findCoreRouterPorts " + router.name + " -> " + target.name

        for p in router.props['ports']:
            for p2 in target.props['ports']:
                if router.props['ports'][p].props['link'] == target.props['ports'][p2].props['link']:
                    coreRouterPortLinks.append(router.props['ports'][p])
        return coreRouterPortLinks

    def selectPort(self, ports):
        """
        Select a port that we want to use from a set of ports.  Use this to
        pick one from a set of ports going to parallel links.  For now
        we'll prefer the lowest numbered ports and best-effort service.
        """
        for p in ports:
            linkName = ports[p].props['link']
            if linkName[-1:] == '1' or linkName[-12:] == ':best-effort':
                return ports[p]
        return None


    def makeCircuit(self, startTarget, startVlan, routers, endTarget, endVlan):
        """
        Make a virtual circuit one hop at a time.
        :param startTarget:  topobuilder level start host
        :param startVlan:  starting VLAN tag on startTarget
        :param routers:  array of topobuilder level routerse
        :param endTarget:  topobuilder level end host
        :param endVlan:  ending VLAN tag on endTarget
        """
        router = routers[0]
        enosRouter = router.props['enosNode']
        scope = self.scopes[enosRouter]
        controller = enosRouter.props['controller']

        if len(routers) == 1:
            # Only one router on the path, so hook the start and end targets together
            inPorts = self.findCoreRouterPorts(router, startTarget)
            outPorts = self.findCoreRouterPorts(router, endTarget)
        else:
            inPorts = self.findCoreRouterPorts(router, startTarget)
            outPorts = self.findCoreRouterPorts(router, routers[1])

        print "makeCircuit "
        print "\tinPorts ", inPorts
        print "\toutPorts ", outPorts

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
