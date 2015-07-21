from array import array
import binascii

from common.intent import ProvisioningRenderer, ProvisioningIntent, ProvisioningExpectation
from common.openflow import ScopeOwner,PacketInEvent, FlowMod, Match, Action, L2SwitchScope, PacketOut, SimpleController
from mininet.enos import TestbedTopology
from mininet.enos import TestbedHost, TestbedNode, TestbedPort, TestbedLink

from net.es.netshell.api import GenericGraph
from common.utils import Logger
from common.mac import MACAddress
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
        self.flowmodIndex = {} # [FlowMod.key()] = FlowMod
        self.props['lanVlanIndex'] = {} # [wanVlan] = lanVlan
        self.props['wanVlanIndex'] = {} # [lanVlan] = wanVlan
        self.props['portsIndex'] = {} # [lanVlan] = list of TestbedPort that participates in the VPN
        self.props['siteScope'] = None
        self.props['wanScope'] = None
        self.props['borderToSitePort'] = None # the port linking siteRouter and borderRouter
        self.props['borderToSDNPort'] = None # the port linking borderRouter and hwSwitch

        # Create scope for the site router
        scope = L2SwitchScope(name=intent.name,switch=self.siteRouter,owner=self)
        scope.props['intent'] = self.intent
        self.props['siteScope'] = scope
        for port in self.siteRouter.getPorts():
            self.activePorts[port.name] = port
            port.props['scope'] = scope
        scope.addEndpoint(self.siteRouter.props['toWanPort'])
        self.siteRouter.props['controller'].addScope(scope)
        # Create scope for the border router
        scope2 = L2SwitchScope(name="%s.wan" % intent.name,switch=self.borderRouter,owner=self)
        scope2.props['intent'] = self.intent
        self.props['wanScope'] = scope2
        borderToSitePort = self.borderRouter.props['sitePortIndex'][self.site.name].props['enosPort']
        self.activePorts[borderToSitePort.name] = borderToSitePort
        borderToSitePort.props['scope'] = scope2
        scope2.addEndpoint(borderToSitePort)
        borderToSDNPort = self.borderRouter.props['stitchedPortIndex'][borderToSitePort.name]
        self.activePorts[borderToSDNPort.name] = borderToSDNPort
        borderToSDNPort.props['scope'] = scope2
        scope2.addEndpoint(borderToSDNPort)
        self.props['borderToSitePort'] = borderToSitePort
        self.props['borderToSDNPort'] = borderToSDNPort
        self.borderRouter.props['controller'].addScope(scope2)
    def checkVlan(self, lanVlan, wanVlan):
        # could be invoked in CLI
        # if lanVlan or wanVlan exists already, they must exactly identical to original values
        if (lanVlan in self.props['wanVlanIndex'] and self.props['wanVlanIndex'][lanVlan] != wanVlan) or (wanVlan in self.props['lanVlanIndex'] and self.props['lanVlanIndex'][wanVlan] != lanVlan):
            SiteRenderer.logger.warning("different lanVlan and wanVlan is not allowed")
            return False
        return True
    def addVlan(self, lanVlan, wanVlan):
        # could be invoked in CLI
        if not self.checkVlan(lanVlan, wanVlan):
            return
        self.props['lanVlanIndex'][wanVlan] = lanVlan
        self.props['wanVlanIndex'][lanVlan] = wanVlan
        self.stitch(wanVlan)
    def addHost(self, host, lanVlan):
        # could be invoked in CLI
        if not lanVlan in self.props['wanVlanIndex']:
            SiteRenderer.logger.warning("lanVlan %d not found" % lanVlan)
            return

        toHostPort = self.siteRouter.props['hostPortIndex'][host.name].props['enosPort']

        if not lanVlan in self.props['portsIndex']:
            self.props['portsIndex'][lanVlan] = []
        self.props['portsIndex'][lanVlan].append(toHostPort)

        scope = self.props['siteScope']
        scope.addEndpoint(toHostPort, lanVlan)
    def __str__(self):
        return "SiteRenderer(name=%s, activePorts=%r, siteScope=%r, wanScope=%r)" % (self.name, self.activePorts, self.props['siteScope'], self.props['wanScope'])
        desc = "SiteRenderer: " + self.name + "\n"
        desc += "\tSite scope:\n" + str(self.props['siteScope'])
        desc += "\tWAN scope:\n" + str(self.props['wanScope'])
        desc += "\tPorts:\n"
        for (x,port) in self.activePorts.items():
            desc +=  str(port)
        desc += "\n\tWAN port to site:\n" + str(self.props['borderToSitePort'])
        desc += "\n\tWAN port to SDN:\n" + str(self.props['borderToSDNPort'])
        desc += "\n"
        return desc

    def __repr__(self):
        return self.__str__()

    def eventListener(self,event):
        """
        The implementation of this class is expected to overwrite this method if it desires
        to receive events from the controller such as PACKET_IN
        :param event: ScopeEvent
        """
        if event.__class__ == PacketInEvent:
            # This is a PACKET_IN. Learn the source MAC address
            if not 'vlan' in event.props:
                # no VLAN, reject
                SiteRenderer.logger.debug("no VLAN, reject %r" % event)
                return
            SiteRenderer.logger.debug("%r" % event)
            if SiteRenderer.debug:
                SiteRenderer.lastEvent = event
            in_port = event.props['in_port'].props['enosPort']
            dl_src = event.props['dl_src']
            vlan = event.props['vlan']
            # set the flow entry to forward packet to that MAC to this port
            success = self.setMAC(port=in_port, vlan=vlan, mac=dl_src)
            if not success:
                SiteRenderer.logger.warning("Cannot set MAC %s on %r.%r" % (dl_src, in_port, vlan))

            dl_dst = event.props['dl_dst']
            mac = dl_src
            etherType = event.props['ethertype']
            if dl_dst.isBroadcast():
                success = self.broadcast(vlan=vlan, inPort=in_port,srcMac=dl_src,dstMac=dl_dst,etherType=etherType,payload=event.props['payload'])
                if not success:
                    SiteRenderer.logger.warning("Cannot send broadcast packet")
            else:
                SiteRenderer.logger.warning("Unknown destination (%r) on site %r" % (event, self))

    def broadcast(self,vlan,inPort,srcMac,dstMac,etherType,payload) :
        switchController = self.siteRouter.props['controller']
        siteRouterName = inPort.props['node'].name
        scope = inPort.props['scope']
        fromLAN = (inPort.props['type'] == 'SiteToHost')
        if fromLAN:
            lanVlan = vlan
            wanVlan = self.props['wanVlanIndex'][vlan]
        else: # from WAN
            lanVlan = self.props['lanVlanIndex'][vlan]
            wanVlan = vlan
        success = True
        for port in self.activePorts.values():
            if port == inPort:
                # no need to send the broadcast back to itself
                continue
            if port.props['type'] == 'SiteToHost' and port in self.props['portsIndex'][lanVlan]:
                vlan = lanVlan
                packet = PacketOut(port=port,dl_src=srcMac,dl_dst=dstMac,etherType=etherType,vlan=vlan,scope=scope,payload=payload)
                if not switchController.isPacketOutValid(packet):
                    # the host did not participate the VPN
                    continue
            elif port.props['type'] == 'SiteToCore':
                vlan = wanVlan
                packet = PacketOut(port=port,dl_src=srcMac,dl_dst=dstMac,etherType=etherType,vlan=vlan,scope=scope,payload=payload)
            else: #SDNToSite, CoreToHw
                continue
            if SiteRenderer.debug:
                print packet
            res = switchController.send(packet)
            if not res:
                success = False
        return success


    def setMAC(self, port, vlan, mac):
        """
        Rules of adding flowmods:
        from LAN:
        1. match:{dst:mac,vlan:wanVlan},action:{vlan:lanVlan,output:port}
        2. match:{dst:mac,vlan:lanVlan},action:{output:port}
        3. match:{src:mac,dst:B,vlan:lanVlan,inport:port},action:{output:lanPorts,vlan:wanVlan,output:wanPort}
        from WAN:
        1. match:{dst:mac,vlan:lanVlan},action:{vlan:wanVlan,output:port}
        3. match:{src:mac,dst:B,vlan:wanVlan,inport:port},action:{vlan:lanVlan,output:lanPorts}
        """
        SiteRenderer.logger.debug("Set flow entries for MAC= %r port=%r vlan=%r" % (mac, port, vlan))
        scope = port.props['scope']
        switch = port.props['enosNode']
        controller = switch.props['controller']
        if port.props['type'] == 'SiteToHost':
            lanVlan = vlan
            wanVlan = self.props['wanVlanIndex'][vlan]
            oppVlan = wanVlan
            oppPorts = [self.siteRouter.props['toWanPort']]
        else: # 'SiteToCore'
            wanVlan = vlan
            lanVlan = self.props['lanVlanIndex'][vlan]
            oppVlan = lanVlan
            oppPorts = self.props['portsIndex'][lanVlan]
        # 1. dispatch packets from opposite port
        for oppPort in oppPorts:
            mod = FlowMod.create(scope,switch,{'dl_dst':mac, 'vlan':oppVlan, 'in_port':oppPort},{'vlan':vlan, 'out_port':port})
            mod.props['renderer'] = self
            if scope.checkFlowMod(mod):
                return True # existed already
            success = True
            scope.addFlowMod(mod)
            if not controller.addFlowMod(mod):
                success = False

        # 2. dispatch packets from lan to lan
        if port.props['type'] == 'SiteToHost':
            for lanPort in self.props['portsIndex'][lanVlan]:
                if lanPort == port:
                    continue
                mod = FlowMod.create(scope,switch,{'dl_dst':mac, 'vlan':vlan, 'in_port':lanPort}, {'out_port':port})
                scope.addFlowMod(mod)
                if not controller.addFlowMod(mod):
                    success = False

        # 3. broadcast packets from lan
        match = Match(props={'dl_src':mac, 'dl_dst':MACAddress.createBroadcast(), 'vlan':vlan, 'in_port':port})
        if port.props['type'] == 'SiteToHost':
            actions = []
            if len(self.props['portsIndex'][lanVlan]) > 1:
                excludeSelf = copy.copy(self.props['portsIndex'][lanVlan])
                excludeSelf.remove(port)
                actions.append(Action({'out_ports':excludeSelf}))
            wanPort = self.siteRouter.props['toWanPort']
            actions.append(Action(props={'vlan':wanVlan,'out_port':wanPort}))
        else: # SiteToCore
            action = Action(props={'vlan':lanVlan, 'out_ports':self.props['portsIndex'][lanVlan]})
            actions = [action]
        mod = FlowMod(scope=scope,switch=switch,match=match,actions=actions)
        scope.addFlowMod(mod)
        if not controller.addFlowMod(mod):
            success = False
        return success
    def stitch(self, wanVlan):
        siteScope = self.props['siteScope']
        siteRouterToWanPort = self.siteRouter.props['toWanPort'].props['enosPort']
        siteScope.addEndpoint(siteRouterToWanPort, wanVlan)

        inPort = self.props['borderToSitePort']
        outPort = self.props['borderToSDNPort']
        controller = self.borderRouter.props['controller']
        wanScope = self.props['wanScope']
        wanScope.addEndpoint(inPort, wanVlan)
        wanScope.addEndpoint(outPort, wanVlan)
        success = True
        for (direction, port1, port2) in [('site_to_hw', inPort, outPort), ('hw_to_site', outPort, inPort)]:
            name = "%s(%d)@%s" % (direction, wanVlan, self.borderRouter.name)
            mod = FlowMod(name=name,scope=wanScope,switch=self.borderRouter)
            mod.props['renderer'] = self
            match = Match(name=name)
            match.props['in_port'] = port1
            match.props['vlan'] = wanVlan
            action = Action(name=name)
            action.props['out_port'] = port2
            action.props['vlan'] = wanVlan
            mod.match = match
            mod.actions = [action]
            wanScope.addFlowMod(mod)
            if not controller.addFlowMod(mod):
                success = False
        return success

    def setBorderRouter(self):
        success = True
        for wanVlan in self.props['wanVlanIndex'].values():
            if not self.stitch(wanVlan):
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

