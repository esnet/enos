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
        for host in intent.hosts:
            if host.props['role'] == "CoreRouter":
                self.borderRouter = host
                continue
            if host.props['role'] == "HwSwitch":
                self.hwSwitch = host
                continue
            if host.props['role'] == "SwSwitch":
                self.swSwitch = host
                continue
            if host.props['role'] == "ServiceVm":
                self.service = host
                continue

        self.macs = {}
        self.active = False
        self.activePorts = {}
        self.flowmods = []

        SDNPopsRenderer.instance = self
        self.hwSwitchScope = L2SwitchScope(name=self.name,switch=self.hwSwitch,owner=self)
        SDNPopsRenderer.instance = self
        self.swSwitchScope = L2SwitchScope(name=self.name,switch=self.swSwitch,owner=self)

        for link in self.intent.links:
            dstNode = link.getDstNode()
            dstPort = link.getDstPort()
            srcNode = link.getSrcNode()
            srcPort = link.getSrcPort()
            vlan = link.props['vpnVlan']
            if srcNode.getResourceName() == self.hwSwitch.name:
                self.hwSwitchScope.addEndpoint((srcPort.name,[vlan]))
                self.activePorts[self.hwSwitch.name + ":" + srcPort.name + ":" + str(vlan)] = srcPort
            if dstNode.getResourceName() == self.hwSwitch.name:
                self.hwSwitchScope.addEndpoint((dstPort.name,[vlan]))
                self.activePorts[self.hwSwitch.name + ":" +dstPort.name + ":" + str(vlan)] = dstPort
            if srcNode.getResourceName() == self.swSwitch.name:
                self.swSwitchScope.addEndpoint((srcPort.name,[vlan]))
                self.activePorts[self.swSwitch.name + ":" +srcPort.name + ":" + str(vlan)] = srcPort
            if dstNode.getResourceName() == self.swSwitch.name:
                self.swSwitchScope.addEndpoint((dstPort.name,[vlan]))
                self.activePorts[self.swSwitch.name + ":" +dstPort.name + ":" + str(vlan)] = dstPort
        print self.activePorts

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
            switch = port.props['switch']
            vlan = event.props['vlan']
            in_port = self.activePorts[switch.name + ":" + port.name + ":" + str(vlan)]
            dl_dst = event.props['dl_dst']
            dl_src = event.props['dl_src']
            mac = binascii.hexlify(dl_src)
            etherType = event.props['ethertype']
            success = True
            if not mac in self.macs:
                # New MAC, install flow entries
                self.macs[mac] = (dl_src,in_port)
                in_port.props['macs'][mac] = dl_src
                # set the flow entry to forward packet to that MAC to this port
                success = self.setMAC(port=in_port,vlan=vlan,mac=dl_src)
                if not success:
                    print "Cannot set MAC",binascii.hexlify(dl_src),"on",in_port.props['switch'].name + ":" +in_port.name + "." + str(vlan)
                else:
                    if SDNPopsRenderer.debug:
                        print self.name,"Learned new MAC",binascii.hexlify(dl_src)
            global broadcastAddress

            if dl_dst == broadcastAddress:
                success = self.broadcast(inPort=in_port,inVlan=vlan,srcMac=dl_src,etherType=etherType,payload=event.props['payload'])
                if not success:
                    print  "Cannot send broadcast packet"

    def broadcast(self,inPort,inVlan,srcMac,etherType,payload) :
        switchController = self.hwSwitch.props['controller']
        success = True

        for (name,port) in self.activePorts.items():
            vlan = int(name.split(":")[2])
            if (port,vlan) == (inPort,inVlan):
                # no need to send the broadcast back to itself
                print "DROP A",port.name,vlan
                continue
            if port.props['node'] != self.hwSwitch.name:
                print "DROP B",port.name,vlan
                continue
            scope = self.hwSwitchScope
            if not 'switch' in port.props:
                port.props['switch'] = self.hwSwitch
            packet = PacketOut(port=port,dl_src=srcMac,dl_dst=broadcastAddress,etherType=etherType,vlan=vlan,scope=scope,payload=payload)
            if SDNPopsRenderer.debug:
                #print packet
                print "PACKETOUT",port.name,vlan
            res = switchController.send(packet)
            if not res:
                print "FAILED",port.name,vlan
                success = False
        return success


    def setMAC(self,port,vlan, mac):
        success = False
        # To be implemented
        return success

    def execute(self):
        """
        Renders the intent.
        :return: Expectation when succcessful, None otherwise
        """
        # Add scopes to the controller
        if not self.hwSwitch.props['controller'].addScope(self.hwSwitchScope):
            print "Cannot add",self.hwSwitchScope
            return False
        if not self.swSwitch.props['controller'].addScope(self.swSwitchScope):
            print "Cannot add",self.swSwitchScope
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
            graph.addVertex(host)

        for link in self.links:
            node1 = link.getSrcNode()
            node2 = link.getDstNode()
            graph.addEdge(node1,node2,link)
        return graph


