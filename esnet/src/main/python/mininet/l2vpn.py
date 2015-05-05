from array import array
import binascii

from common.intent import ProvisioningRenderer, ProvisioningIntent
from common.api import Site, Properties
from common.openflow import ScopeOwner,PacketInEvent, FlowMod, Match, Action, L2SwitchScope, PacketOut, SimpleController
from odl.client import ODLClient

from mininet.enos import TestbedTopology

from net.es.netshell.api import GenericGraph, GenericHost

broadcastAddress = array('B',[0xFF,0xFF,0xFF,0xFF,0xFF,0xFF])

class SDNPopsRenderer(ProvisioningRenderer,ScopeOwner):
    debug = True
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
        self.pops = intent.pops

        self.macs = {}
        self.active = False
        self.activePorts = {}
        self.flowmods = []
        self.links = self.intent.links
        self.linkByPort = {}

        SDNPopsRenderer.instance = self
        self.scopes = {}

        for pop in self.pops:
            coreRouter = pop.props['coreRouter']
            hwSwitch = pop.props['hwSwitch']
            swSwitch = pop.props['swSwitch']
            hwSwitchScope = L2SwitchScope(name=self.name,switch=hwSwitch,owner=self,endpoints=[])
            swSwitchScope = L2SwitchScope(name=self.name,switch=swSwitch,owner=self,endpoints=[])
            for link in self.links:
                dstNode = link.getDstNode()
                dstPort = link.getDstPort()
                srcNode = link.getSrcNode()
                srcPort = link.getSrcPort()
                self.linkByPort[dstPort] = link
                self.linkByPort[srcPort] = link

                vlans = link.props['vpnVlans']
                for vlan in vlans:
                    if srcNode.getResourceName() == hwSwitch.name:
                        hwSwitchScope.addEndpoint((srcPort.name,[vlan]))
                        self.activePorts[hwSwitch.name + ":" + srcPort.name + ":" + str(vlan)] = (srcPort,hwSwitch,hwSwitchScope)
                    if dstNode.getResourceName() == hwSwitch.name:
                        hwSwitchScope.addEndpoint((dstPort.name,[vlan]))
                        self.activePorts[hwSwitch.name + ":" +dstPort.name + ":" + str(vlan)] = (dstPort,hwSwitch,hwSwitchScope)
                    if srcNode.getResourceName() == swSwitch.name:
                        swSwitchScope.addEndpoint((srcPort.name,[vlan]))
                        self.activePorts[swSwitch.name + ":" +srcPort.name + ":" + str(vlan)] = (srcPort,swSwitch,swSwitchScope)
                    if dstNode.getResourceName() == swSwitch.name:
                        swSwitchScope.addEndpoint((dstPort.name,[vlan]))
                        self.activePorts[swSwitch.name + ":" +dstPort.name + ":" + str(vlan)] = (dstPort,swSwitch,swSwitchScope)
            self.scopes[hwSwitch] = hwSwitchScope
            self.scopes[swSwitch] = swSwitchScope


    def __str__(self):
        desc = "SDNPopsRenderer: " + self.name + "\n"
        desc += "\tPorts:\n"
        for (x,port) in self.activePorts.items():
            desc +=  str(port)
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
                if SDNPopsRenderer.debug:
                    print "no VLAN, reject",event
                return
            if SDNPopsRenderer.debug:
                print self.name
                print event
            dl_src = event.props['dl_src']
            mac = binascii.hexlify(dl_src)
            port = event.props['in_port']
            switch = TestbedTopology().nodes[port.props['node']]
            vlan = event.props['vlan']
            in_port,switch,scope = self.activePorts[switch.name + ":" + port.name + ":" + str(vlan)]
            dl_dst = event.props['dl_dst']
            dl_src = event.props['dl_src']
            mac = binascii.hexlify(dl_src)
            etherType = event.props['ethertype']
            success = True
            #if not mac in self.macs:
            if True:
                self.macs[mac] = (dl_src,in_port)
                # set the flow entry to forward packet to that MAC to this port
                success = self.setMAC(port=in_port,switch=switch,scope=scope,vlan=vlan,mac=dl_src)
                if not success:
                    print "Cannot set MAC",binascii.hexlify(dl_src),"on", + ":" +in_port.name + "." + str(vlan)
            global broadcastAddress
            if not 'node' in in_port.props:
                print "L2VPN no swict",in_port,in_port.props
                #in_port.props['switch'] = switch
            if dl_dst == broadcastAddress:
                success = self.broadcast(inPort=in_port,switch=switch,scope=scope,inVlan=vlan,srcMac=dl_src,etherType=etherType,payload=event.props['payload'])
                if not success:
                    print  "Cannot send broadcast packet"


    def broadcast(self,inPort,inVlan,srcMac,etherType,payload,switch,scope) :

        switchController = switch.props['controller']
        success = True
        endpoints = scope.props['endpoints']

        for endpoint in endpoints:
            vlan = endpoint[1][0]
            outPort,outSwitch,outScope = self.activePorts[switch.name+":"+endpoint[0]+":"+str(vlan)]
            # Check that outScope is the sacme as scope
            if scope != outScope:
                print "Wrong scope", outScope
                continue
            if outPort.name == inPort.name:
                # no need to rebroadcast on in_port
                continue

            if inVlan >= 1000 and vlan >= 1000:
                continue
            packet = PacketOut(port=outPort,dl_src=srcMac,dl_dst=broadcastAddress,etherType=etherType,vlan=vlan,scope=outScope,payload=payload)
            if SDNPopsRenderer.debug:
                print packet
                #print "PacketOut out-switch",outSwitch.name,"out-port",outPort.name,"scope",outScope.switch.name
            res = switchController.send(packet)
            res = True
            if not res:
                success = False

        return success


    def setMAC(self,port,vlan, mac,switch,scope):
        if SDNPopsRenderer.debug:
            print "SDNPopsRenderer: Set flow entries for MAC= " + str(mac)+ " switch=" + switch.name + " port= " + port.name + " vlan= " + str(vlan)

        controller = switch.props['controller']
        success = True

        mod = FlowMod(name=scope.name,scope=scope,switch=switch)
        mod.props['renderer'] = self
        match = Match(name=scope.name)
        match.props['dl_dst'] = mac
        action = Action(name=scope.name)
        action.props['out_port'] = port
        action.props['vlan'] = vlan
        mod.match = match
        mod.actions = [action]
        self.flowmods.append(mod)
        if SDNPopsRenderer.debug:
            print "add flowMod",mod
        success = controller.addFlowMod(mod)
        if not success:
            print "Cannot push flowmod:\n",mod

        return success

    def execute(self):
        """
        Renders the intent.
        :return: Expectation when succcessful, None otherwise
        """
        # Add scopes to the controller
        for (switch,scope) in self.scopes.items():
            if not switch.props['enosNode'].props['controller'].addScope(scope):
                print "Cannot add",scope
                return False
        self.active = True
        return True


    def destroy(self):
        """
        Destroys or stop the rendering of the intent.
        :return: True if successful
        """
        self.active = False
        return




class SDNPopsIntent(ProvisioningIntent):
    def __init__(self,name,pops,hosts,links):
        """
        Creates a provisioning intent providing a GenericGraph of the logical view of the
        topology that is intended to be created.
        :param topology: TestbedTopology
        :param site: Site
        """
        self.pops = pops
        self.links = links
        self.hosts = []
        for host in hosts:
            if not 'enosNode' in host.props:
                # This is already a GenericNode object
                self.hosts.append(host)
            else:
                self.hosts.append(host.props['enosNode'])

        self.graph = self.getGraph()
        ProvisioningIntent.__init__(self,name=name,graph=self.graph)


    def getGraph(self):
        graph = GenericGraph()

        for host in self.hosts:
            graph.addVertex(host)

        for link in self.links:
            node1 = link.getSrcNode()
            node2 = link.getDstNode()
            graph.addEdge(node1,node2,link)
        return graph


