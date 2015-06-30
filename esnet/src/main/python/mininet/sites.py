from array import array
import binascii

from common.intent import ProvisioningRenderer, ProvisioningIntent, ProvisioningExpectation
from common.openflow import ScopeOwner,PacketInEvent, FlowMod, Match, Action, L2SwitchScope, PacketOut, SimpleController
from mininet.enos import TestbedTopology
from mininet.enos import TestbedHost, TestbedNode, TestbedPort, TestbedLink

from net.es.netshell.api import GenericGraph
from common.utils import Logger
from mininet.mac import MACAddress
from common.utils import dump
import threading
broadcastAddress = array('B',[0xFF,0xFF,0xFF,0xFF,0xFF,0xFF])
sites = []
class SiteRenderer(ProvisioningRenderer,ScopeOwner):
    """
    Implements the rendering of provisioning intents on the Site. This class is responsible for pushing the proper
    flowMods that will forward packets between the hosts and the ESnet border router. Typically the topology is

         host(s) <-> siteRouter <-> borderRouter

         Simple vlan/port mach and outport /vlan on siteRouter needs to be set
    """
    debug = False
    lastEvent = None
    instance = None

    def __init__(self, intent):
        """
        Generic constructor. Translate the intent
        :param intent: SiteIntent
        :return:
        """
        ScopeOwner.__init__(self,name=intent.name)
        self.intent = intent
        graph = intent.graph
        self.siteRouter = self.intent.siteRouter
        self.borderRouter = self.intent.borderRouter
        self.macs = {}
        self.active = False
        self.activePorts = {}
        self.flowmods = []
        self.lanVlanIndex = {} # [wanVlan] = lanVlan
        self.wanVlanIndex = {} # [lanVlan] = wanVlan
        SiteRenderer.instance = self

        # Create scope for the site router
        scope = L2SwitchScope(name=intent.name,switch=self.siteRouter,owner=self)
        scope.props['intent'] = self.intent
        self.props['siteScope'] = scope
        for port in self.siteRouter.getPorts():
            self.activePorts[port.name] = port
            port.props['scope'] = scope
        # scope.addEndpoint(port, vlan) later while configuring vpns
        self.siteRouter.props['controller'].addScope(scope)
        # Create scope for the border router
        scope2 = L2SwitchScope(name=intent.name,switch=self.borderRouter,owner=self)
        scope2.props['intent'] = self.intent
        self.props['wanScope'] = scope2
        hwswitch_to_site_port = self.borderRouter.props['toSitePort'].props['enosPort']
        self.activePorts[hwswitch_to_site_port.name] = hwswitch_to_site_port
        hwswitch_to_site_port.props['scope'] = scope2
        scope2.addEndpoint(hwswitch_to_site_port)
        site_to_hwswitch_port = self.borderRouter.props['sitesToHwSwitchPorts'][0].props['enosPort']
        self.activePorts[site_to_hwswitch_port.name] = site_to_hwswitch_port
        site_to_hwswitch_port.props['scope'] = scope2
        scope2.addEndpoint(site_to_hwswitch_port)
        self.props['borderPortToSite'] = hwswitch_to_site_port
        self.props['borderPortToSDN'] = site_to_hwswitch_port
        self.borderRouter.props['controller'].addScope(scope2)
    def addVpn(self, lanVlan, wanVlan):
        self.lanVlanIndex[wanVlan] = lanVlan
        self.wanVlanIndex[lanVlan] = wanVlan
        siteRouter = self.props['siteScope'].switch
        scope = self.props['siteScope']
        toWanPort = siteRouter.props['toWanPort'].props['enosPort']
        for port in siteRouter.getPorts():
            if port == toWanPort:
                scope.addEndpoint(port, wanVlan)
            else:
                # to LAN (Hosts)
                scope.addEndpoint(port, lanVlan)
    def __str__(self):
        desc = "SiteRenderer: " + self.name + "\n"
        desc += "\tSite scope:\n" + str(self.props['siteScope'])
        desc += "\tWAN scope:\n" + str(self.props['wanScope'])
        desc += "\tPorts:\n"
        for (x,port) in self.activePorts.items():
            desc +=  str(port)
        desc += "\n\tWAN port to site:\n" + str(self.props['borderPortToSite'])
        desc += "\n\tWAN port to SDN:\n" + str(self.props['borderPortToSDN'])
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
                if SiteRenderer.debug:
                    print "no VLAN, reject",event
                return
            if SiteRenderer.debug:
                print event
                SiteRenderer.lastEvent = event
            dl_src = event.props['dl_src']
            port = event.props['in_port']
            # switch = port.props['node']
            in_port = self.activePorts[port.name]
            if not in_port.props['type'] in ['ToLAN','ToBorder']:
                # Discard (debug)
                return
            dl_dst = event.props['dl_dst']
            dl_src = event.props['dl_src']
            mac = dl_src
            vlan = event.props['vlan']
            etherType = event.props['ethertype']
            success = True
            #if not mac in self.macs:
            if True:
                # New MAC, install flow entries
                self.macs[mac.str()] = (dl_src, in_port)
                in_port.props['macs'][mac.str()] = dl_src
                # set the flow entry to forward packet to that MAC to this port
                success = self.setMAC(port=in_port,vlan=vlan,mac=dl_src)
                if not success:
                    print "Cannot set MAC %s on %r.%r" % (dl_src, in_port, vlan)
            if dl_dst.isBroadcast():
                success = self.broadcast(vlan=vlan, inPort=in_port,srcMac=dl_src,dstMac=dl_dst,etherType=etherType,payload=event.props['payload'])
                if not success:
                    print  "Cannot send broadcast packet"

    def broadcast(self,vlan,inPort,srcMac,dstMac,etherType,payload) :
        switchController = self.siteRouter.props['controller']
        siteRouterName = inPort.props['node'].name
        scope = inPort.props['scope']
        fromLAN = inPort.props['type'] == 'ToLAN'
        if fromLAN:
            lanVlan = vlan
            wanVlan = self.wanVlanIndex[vlan]
        else:
            lanVlan = self.lanVlanIndex[vlan]
            wanVlan = vlan
        success = True
        for port in self.activePorts.values():
            if port == inPort:
                # no need to send the broadcast back to itself
                continue
            if port.props['type'] == 'ToLAN':
                vlan = lanVlan
                packet = PacketOut(port=port,dl_src=srcMac,dl_dst=dstMac,etherType=etherType,vlan=vlan,scope=scope,payload=payload)
            elif port.props['type'] == 'ToBorder':
                vlan = wanVlan
                packet = PacketOut(port=port,dl_src=srcMac,dl_dst=dstMac,etherType=etherType,vlan=vlan,scope=scope,payload=payload)
            else: #SDNToSite, SiteToSDN
                continue
            if SiteRenderer.debug:
                print packet
            res = switchController.send(packet)
            if not res:
                success = False
        return success


    def setMAC(self, port, vlan, mac):
        if SiteRenderer.debug:
            print "SiteRenderer: Set flow entries for MAC= %r port=%r vlan=%r" % (mac, port, vlan)
        switch = port.props['enosNode']
        scope = port.props['scope']
        controller = switch.props['controller']
        success = True
        fromWan = (port == switch.props['toWanPort'].props['enosPort'])
        if fromWan:
            wanVlan = vlan
            lanVlan = self.lanVlanIndex[wanVlan]
        else:
            lanVlan = vlan
            wanVlan = self.wanVlanIndex[lanVlan]

        name = '%r fr %s.%d' % (mac, port.name, vlan)
        mod = FlowMod(name=name, scope=scope,switch=switch)
        mod.props['renderer'] = self
        match = Match(name=name)
        match.props['dl_dst'] = mac
        action = Action(name=name)
        action.props['out_port'] = port
        action.props['vlan'] = vlan
        mod.match = match
        mod.actions = [action]
        self.flowmods.append(mod)
        if SiteRenderer.debug:
            print "add flowMod",mod
        res = controller.addFlowMod(mod)
        if not res:
            success = False
            print "Cannot push flowmod:\n",mod
        return success

    def setBorderRouter(self):
        if SiteRenderer.debug:
            print "SiteRenderer: setBorderRouter"
        inPort = self.props['borderPortToSite']
        outPort = self.props['borderPortToSDN']
        controller = self.borderRouter.props['controller']
        scope = inPort.props['scope']
        name = ""
        mod = FlowMod(name=name,scope=scope,switch=self.borderRouter)
        mod.props['renderer'] = self
        match = Match(name=name)
        match.props['in_port'] = inPort
        # match.props['vlan'] = inPort.props['vlan']
        action = Action(name=name)
        action.props['out_port'] = outPort
        # action.props['vlan'] = outPort.props['vlan']
        mod.match = match
        mod.actions = [action]
        self.flowmods.append(mod)
        success = controller.addFlowMod(mod)

        tmp = inPort
        inPort = outPort
        outPort = tmp
        name = ""
        mod = FlowMod(name=name,scope=scope,switch=self.borderRouter)
        mod.props['renderer'] = self
        match = Match(name=name)
        match.props['in_port'] = inPort
        # match.props['vlan'] = inPort.props['vlan']
        action = Action(name=name)
        action.props['out_port'] = outPort
        # action.props['vlan'] = outPort.props['vlan']
        mod.match = match
        mod.actions = [action]
        self.flowmods.append(mod)
        success = controller.addFlowMod(mod)

        return success

    def removeFlowEntries(self):
        return False


    def execute(self):
        """
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
    def __init__(self,name,hosts,siteRouter,borderRouter,links):
        """
        Creates a provisioning intent providing a GenericGraph of the logical view of the
        topology that is intended to be created.
        :param topology: TestbedTopology
        :param site: Site
        """
        self.hosts = hosts
        self.siteRouter = siteRouter
        self.borderRouter = borderRouter
        self.links = links
        self.graph = self.buildGraph()
        ProvisioningIntent.__init__(self,name=name,graph=self.graph)


    def buildGraph(self):
        graph = GenericGraph()

        for host in self.hosts:
            graph.addVertex(host)

        graph.addVertex(self.siteRouter)
        graph.addVertex(self.borderRouter)
        for link in self.links:
            node1 = link.getSrcNode()
            node2 = link.getDstNode()
            graph.addEdge(node1,node2,link)

        return graph

