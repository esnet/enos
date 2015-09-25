from array import array
import binascii

from layer2.common.intent import ProvisioningRenderer, ProvisioningIntent, ProvisioningExpectation
from layer2.common.openflow import ScopeOwner,PacketInEvent, FlowMod, Match, Action, L2SwitchScope, PacketOut, SimpleController
from layer2.testbed.topology import TestbedHost, TestbedNode, TestbedPort, TestbedLink, TestbedTopology

from net.es.netshell.api import GenericGraph
from layer2.common.utils import Logger
from layer2.common.mac import MACAddress
import threading
class SiteRenderer(ProvisioningRenderer,ScopeOwner):
    """
    Implements the rendering of provisioning intents on the Site. This class is responsible for pushing the proper
    flowMods that will forward packets between the hosts and the ESnet border router. Typically the topology is

         host(s) <-> siteRouter <-> borderRouter

         Simple vlan/port mach and outport /vlan on siteRouter needs to be set
    """
    debug = False
    lastEvent = None
    logger = Logger('SiteRenderer')

    def __init__(self, intent):
        """
        Generic constructor. Translate the intent
        :param intent: SiteIntent
        :return:
        """
        ScopeOwner.__init__(self,name=intent.name)
        self.intent = intent
        self.site = self.intent.site
        self.siteRouter = self.intent.siteRouter
        self.borderRouter = self.intent.borderRouter
        graph = intent.graph
        self.macs = {}
        self.active = False
        self.activePorts = {} # [portname] = TestbedPort
        self.lock = threading.Lock()
        self.props['lanVlanIndex'] = {} # [siteVlan] = lanVlan
        self.props['siteVlanIndex'] = {} # [lanVlan] = siteVlan
        self.props['portsIndex'] = {} # [lanVlan] = list of TestbedPort that allows lanVlan to pass
        self.props['portIndex'] = {} # [str(mac)] = TestbedPort that links to the MAC
        self.props['scopeIndex'] = {} # [switch.name] = L2SwitchScope
        self.props['borderToSitePort'] = None # the port linking siteRouter and borderRouter
        self.props['borderToSDNPort'] = None # the port linking borderRouter and hwSwitch

        # cheating by awaring all the hosts to avoid any possible missed packet
        for host in self.site.props['hosts']:
            port = host.props['ports'][1].props['links'][0].props['portIndex'][self.siteRouter.name]
            self.props['portIndex'][str(host.props['mac'])] = port.props['enosPort']

        # Create scope for the site router
        siteScope = L2SwitchScope(name=intent.name,switch=self.siteRouter,owner=self)
        siteScope.props['intent'] = self.intent
        self.props['scopeIndex'][self.siteRouter.name] = siteScope
        for port in self.siteRouter.getPorts():
            self.activePorts[port.name] = port
            port.props['scope'] = siteScope
        siteScope.addEndpoint(self.siteRouter.props['toWanPort'])
        self.siteRouter.props['controller'].addScope(siteScope)
        # Create scope for the border router
        wanScope = L2SwitchScope(name="%s.wan" % intent.name,switch=self.borderRouter,owner=self)
        wanScope.props['intent'] = self.intent
        self.props['scopeIndex'][self.borderRouter.name] = wanScope
        borderToSitePort = self.borderRouter.props['sitePortIndex'][self.site.name].props['enosPort']
        self.activePorts[borderToSitePort.name] = borderToSitePort
        borderToSitePort.props['scope'] = wanScope
        wanScope.addEndpoint(borderToSitePort)
        borderToSDNPort = self.borderRouter.props['stitchedPortIndex'][borderToSitePort.name]
        self.activePorts[borderToSDNPort.name] = borderToSDNPort
        borderToSDNPort.props['scope'] = wanScope
        """
        The reason we comment out this line is:
        Since we'd like to support multiple sites, borderToSDNPort could be shared.
        Therefore, we can not occupy it alone.
        The scope should be added later while 'vpn addsite'.
        """
        # wanScope.addEndpoint(borderToSDNPort)
        self.props['borderToSitePort'] = borderToSitePort
        self.props['borderToSDNPort'] = borderToSDNPort
        self.borderRouter.props['controller'].addScope(wanScope)
    def checkVlan(self, lanVlan, siteVlan):
        # could be invoked in CLI
        # if lanVlan or siteVlan exists already, they must exactly identical to original values
        if (lanVlan in self.props['siteVlanIndex'] and self.props['siteVlanIndex'][lanVlan] != siteVlan) or (siteVlan in self.props['lanVlanIndex'] and self.props['lanVlanIndex'][siteVlan] != lanVlan):
            SiteRenderer.logger.warning("different lanVlan and siteVlan is not allowed")
            return False
        return True
    def addVlan(self, lanVlan, siteVlan):
        # could be invoked in CLI
        if not self.checkVlan(lanVlan, siteVlan):
            return
        self.props['lanVlanIndex'][siteVlan] = lanVlan
        self.props['siteVlanIndex'][lanVlan] = siteVlan
        self.stitch(siteVlan)
    def delVlan(self, lanVlan, siteVlan):
        # could be invoked in CLI
        if not self.checkVlan(lanVlan, siteVlan):
            return
        self.cut(siteVlan)
        self.props['lanVlanIndex'].pop(siteVlan)
        self.props['siteVlanIndex'].pop(lanVlan)
        siteScope = self.props['scopeIndex'][self.siteRouter.name]
        for (key, flowmod) in siteScope.props['flowmodIndex'].items():
            found = False
            if not found:
                found = flowmod.match.props['dl_dst'].isBroadcast()
            if not found:
                if flowmod.match.props['in_port'].props['type'] == 'SiteToHost':
                    found = flowmod.match.props['vlan'] == lanVlan
                else:
                    found = flowmod.match.props['vlan'] == siteVlan
            if not found:
                for action in flowmod.actions:
                    if action.props['out_port'].props['type'] == 'SiteToHost':
                        if action.props['vlan'] == lanVlan:
                            found = True
                            break
                    else:
                        if action.props['vlan'] == siteVlan:
                            found = True
                            break
            if not found:
                # here we try to keep some flowmods that are not related to the site at all
                continue
            siteScope.delFlowMod(flowmod)
        for port in self.siteRouter.props['ports'].values():
            if port.props['type'] == 'SiteToHost':
                siteScope.delEndpoint(port, lanVlan)
            else:
                siteScope.delEndpoint(port, siteVlan)
        if lanVlan in self.props['portsIndex']:
            self.props['portsIndex'].pop(lanVlan)
    def addHost(self, host, lanVlan):
        # could be invoked in CLI
        with self.lock:
            if not lanVlan in self.props['siteVlanIndex']:
                SiteRenderer.logger.warning("lanVlan %d not found" % lanVlan)
                return

            toHostPort = self.siteRouter.props['hostPortIndex'][host.name].props['enosPort']

            if not lanVlan in self.props['portsIndex']:
                self.props['portsIndex'][lanVlan] = []
            self.props['portsIndex'][lanVlan].append(toHostPort)

            siteScope = self.props['scopeIndex'][self.siteRouter.name]
            siteScope.addEndpoint(toHostPort, lanVlan)
    def delHost(self, host, lanVlan):
        # could be invoked in CLI
        with self.lock:
            if not lanVlan in self.props['siteVlanIndex']:
                SiteRenderer.logger.warning("lanVlan %d not found" % lanVlan)
                return

            toHostPort = self.siteRouter.props['hostPortIndex'][host.name].props['enosPort']
            if not toHostPort in self.props['portsIndex'][lanVlan]:
                SiteRenderer.logger.warning("host %s not exists" % host.name)
                return
            self.props['portsIndex'][lanVlan].remove(toHostPort)

            siteScope = self.props['scopeIndex'][self.siteRouter.name]
            for (key, flowmod) in siteScope.props['flowmodIndex'].items():
                found = False
                if not found:
                    found = flowmod.match.props['in_port'].name == toHostPort.name and flowmod.match.props['vlan'] == lanVlan
                if not found:
                    for action in flowmod.actions:
                        if action.props['out_port'].name == toHostPort.name and action.props['vlan'] == lanVlan:
                            found = True
                            break
                if not found:
                    # here we try to keep some flowmods that are not related to the host at all
                    continue
                """
                A possible improvement here might be:
                Try to modify the broadcast flowmod instead of deleting it.
                However, neither site router nor broadcast is our concern in
                the demo, so I just delete it directly.
                """
                siteScope.delFlowMod(flowmod)
            siteScope.delEndpoint(toHostPort, lanVlan)

    def __str__(self):
        return "SiteRenderer(name=%s, activePorts=%r, scopeIndex=%r)" % (self.name, self.activePorts, self.props['scopeIndex'])

    def __repr__(self):
        return self.__str__()

    def eventListener(self,event):
        """
        The implementation of this class is expected to overwrite this method if it desires
        to receive events from the controller such as PACKET_IN
        :param event: ScopeEvent
        """
        if event.__class__ != PacketInEvent:
            SiteRenderer.logger.warning("%s is not a PACKET_IN." % event)
        with self.lock:
            if not 'vlan' in event.props:
                # no VLAN, reject
                SiteRenderer.logger.debug("no VLAN, reject %r" % event)
                return
            SiteRenderer.logger.debug("eventListener: %r" % event)
            if SiteRenderer.debug:
                SiteRenderer.lastEvent = event

            inPort = event.props['in_port'].props['enosPort']
            srcMac = event.props['dl_src']
            dstMac = event.props['dl_dst']
            inVlan = event.props['vlan']
            if inPort.props['type'] == 'SiteToHost':
                lanVlan = inVlan
                siteVlan = self.props['siteVlanIndex'][lanVlan]
            elif inPort.props['type'] == 'SiteToCore':
                siteVlan = inVlan
                lanVlan = self.props['lanVlanIndex'][siteVlan]
            else:
                SiteRenderer.logger.warning("Unknown event %r in %r" % (event, self))
                return
            # update information of which port the srcMac belongs
            if not str(srcMac) in self.props['portIndex']:
                self.props['portIndex'][str(srcMac)] = inPort

            etherType = event.props['ethertype']
            payload=event.props['payload']
            switch = inPort.props['node'].props['enosNode']
            switchController = switch.props['controller']
            scope = inPort.props['scope']
            if dstMac.isBroadcast():
                outputs = []
                if inPort.props['type'] == 'SiteToHost':
                    outputs.append((dstMac, siteVlan, switch.props['toWanPort']))
                for outPort in self.props['portsIndex'][lanVlan]:
                    if outPort.name == inPort.name:
                        continue
                    outputs.append((dstMac, lanVlan, outPort))
                scope.multicast(switch, dstMac, inVlan, inPort, outputs)
                for (outMac, outVlan, outPort) in outputs:
                    scope.send(switch, outPort, srcMac, outMac, etherType, outVlan, payload)
            else:
                if not str(dstMac) in self.props['portIndex']:
                    SiteRenderer.logger.warning("Unknown destination (%r) on site %r" % (event, self))
                    # return
                    # hack that all unknown mac should go to wan
                    self.props['portIndex'][str(dstMac)] = switch.props['toWanPort']
                outPort = self.props['portIndex'][str(dstMac)]
                if outPort.props['type'] == 'SiteToCore':
                    outVlan = siteVlan
                else:
                    outVlan = lanVlan
                scope.forward(switch, dstMac, inVlan, inPort, dstMac, outVlan, outPort)
                scope.send(switch, outPort, srcMac, dstMac, etherType, outVlan, payload)
    def stitch(self, siteVlan):
        siteScope = self.props['scopeIndex'][self.siteRouter.name]
        siteRouterToWanPort = self.siteRouter.props['toWanPort'].props['enosPort']
        siteScope.addEndpoint(siteRouterToWanPort, siteVlan)

        inPort = self.props['borderToSitePort']
        outPort = self.props['borderToSDNPort']
        wanScope = self.props['scopeIndex'][self.borderRouter.name]
        wanScope.addEndpoint(inPort, siteVlan)
        wanScope.addEndpoint(outPort, siteVlan)
        success = True
        for (direction, port1, port2) in [('site_to_hw', inPort, outPort), ('hw_to_site', outPort, inPort)]:
            if not wanScope.forward(self.borderRouter, None, siteVlan, port1, None, siteVlan, port2):
                success = False
        return success

    def cut(self, siteVlan):
        siteScope = self.props['scopeIndex'][self.siteRouter.name]
        siteRouterToWanPort = self.siteRouter.props['toWanPort'].props['enosPort']

        wanScope = self.props['scopeIndex'][self.borderRouter.name]

        inPort = self.props['borderToSitePort']
        outPort = self.props['borderToSDNPort']
        success = True
        for (direction, port1, port2) in [('site_to_hw', inPort, outPort), ('hw_to_site', outPort, inPort)]:
            if not wanScope.stopForward(self.borderRouter, None, siteVlan, port1, None, siteVlan, port2):
                success = False
        siteScope.delEndpoint(siteRouterToWanPort, siteVlan)
        wanScope.delEndpoint(inPort, siteVlan)
        wanScope.delEndpoint(outPort, siteVlan)
        return success

    def setBorderRouter(self):
        success = True
        for siteVlan in self.props['siteVlanIndex'].values():
            if not self.stitch(siteVlan):
                success = False
        return success

    def removeFlowEntries(self):
        return False


    def execute(self):
        """
        Note: this function is not useful so far, since all the rule is
        configured dynamically in runtime.

        Renders the intent.
        :return: Expectation when succcessful, None otherwise
        """
        # Request the scope to the controller
        self.active = True
        # set broadcast flow entry
        success = self.setBorderRouter()

        return success


    def destroy(self):
        """
        Destroys or stop the rendering of the intent.
        :return: True if successful
        """
        self.active = False
        return self.removeFlowEntries()


class SiteExpectation(ProvisioningExpectation):
    def __init__(self,name,itent,renderer,hostsEndpoints,wanEndpoint):
        ProvisioningExpectation.__init__(self)



class SiteIntent(ProvisioningIntent):
    def __init__(self, name, site):
        """
        Creates a provisioning intent providing a GenericGraph of the logical view of the
        topology that is intended to be created.
        :param site: Site
        """
        self.site = site
        siteRouter = site.props['siteRouter']
        borderRouter = site.props['borderRouter']
        nodes = []
        nodes.append(siteRouter)
        nodes.append(borderRouter)
        nodes.extend(site.props['hosts'])
        links = site.props['links']

        self.nodes = map(lambda node : node.props['enosNode'], nodes)
        self.siteRouter = siteRouter.props['enosNode']
        self.borderRouter = borderRouter.props['enosNode']
        self.links = map(lambda link : link.props['enosLink'], links)
        self.graph = self.buildGraph()
        ProvisioningIntent.__init__(self,name=name,graph=self.graph)


    def buildGraph(self):
        graph = GenericGraph()
        for node in self.nodes:
            graph.addVertex(node)
        for link in self.links:
            node1 = link.getSrcNode()
            node2 = link.getDstNode()
            graph.addEdge(node1,node2,link)
        return graph

