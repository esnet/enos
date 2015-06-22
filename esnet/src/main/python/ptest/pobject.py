import array
import struct
import binascii
import jarray
from java.lang import Short
from java.util import LinkedList
from sets import Set
import random
import copy
import net.es.netshell.odl.Controller
import net.es.netshell.odl.PacketHandler

from org.opendaylight.controller.sal.core import Node
from org.opendaylight.controller.sal.packet import Ethernet
from org.opendaylight.controller.sal.packet import IEEE8021Q
from org.opendaylight.controller.sal.packet import RawPacket
from org.opendaylight.controller.sal.packet import PacketResult
from org.opendaylight.controller.sal.utils import EtherTypes

from org.opendaylight.controller.sal.match import Match
from org.opendaylight.controller.sal.match.MatchType import DL_DST
from org.opendaylight.controller.sal.match.MatchType import DL_SRC
from org.opendaylight.controller.sal.match.MatchType import DL_VLAN
from org.opendaylight.controller.sal.match.MatchType import IN_PORT
from org.opendaylight.controller.sal.action import Output
from org.opendaylight.controller.sal.action import SetDlDst
from org.opendaylight.controller.sal.action import SetDlSrc
from org.opendaylight.controller.sal.action import SetVlanId
from org.opendaylight.controller.sal.flowprogrammer import Flow

from mininet.utility import Logger
"""
In Jython world, we use python object as arguments:
PNode, PPort, PLink, ...
PPacket, ...
PMatch, PAction, ...
MACAddress, ...
To translate into Java world:
    mac.jarray()
    port.odl
Customized class includes:
CoreRouter, HwSwitch, SwSwitch, SiteRouter
ServiceVm, Host
WANLink, SDNLink, LANLink, ToWANLink
"""
test = []
class PMAC:
    broadcast = None
    size = 6
    def __init__(self, v = [0]):
        if isinstance(v, PMAC):
            self.data = copy.copy(v.data)
            return
        if isinstance(v, str):
            self.data = map(lambda x : int(x, 16), v.split(":"))
            return
        if isinstance(v, int):
            self.data = []
            for i in range(PMAC.size):
                self.data.append(v & 0xFF)
                v >>= 8
            self.data.reverse()
            return
        self.data = [0] * PMAC.size
        for i in range(min(len(v), PMAC.size)):
            self.data[i] = struct.unpack('B', struct.pack('B', v[i]))[0]
    def isBroadcast(self):
        return self.data[0] == 0xFF and self.getHid() == 0xFFFF
    def getVid(self):
        return (self.data[1] << 16) + (self.data[2] << 8) + self.data[3]
    def setVid(self, vid):
        self.data[1] = vid >> 16
        self.data[2] = (vid >> 8) & 0xFF
        self.data[3] = vid & 0xFF
    def getHid(self):
        return (self.data[4] << 8) + self.data[5]
    def setHid(self, hid):
        self.data[4] = hid >> 8
        self.data[5] = hid & 0xFF
    @staticmethod
    def createBroadcast(vid):
        mac = PMAC(PMAC.broadcast)
        mac.setVid(vid)
        return mac
    def array(self):
        return array.array('b', struct.pack('%sB' % PMAC.size, *self.data))
    def jarray(self):
        result = jarray.zeros(PMAC.size, 'b')
        for i in range(len(result)):
            result[i] = struct.unpack('b', struct.pack('B', self.data[i]))[0]
        return result
    def dpid(self):
        return binascii.hexlify(array.array('B', [0, 0] + self.data))
    def str(self):
        return str.join(":", ("%02X" % i for i in self.data))
    def __repr__(self):
        return self.str()
    def __str__(self):
        return self.str()
    def __eq__(self, other):
        return self.data == other.data
    def __ne__(self, other):
        return self.data != other.data
PMAC.broadcast = PMAC([0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF])

class PObject:
    def __init__(self, name):
        self.name = name
    def __str__(self):
        return self.name
    def __repr__(self):
        return self.name

class PNode(PObject):
    def __init__(self, name, mininetName):
        PObject.__init__(self, name)
        self.mininetName = mininetName
        self.ports = {}
    def getPort(self, num=None):
        if not num:
            num = len(self.ports) + 1
        if not num in self.ports:
            self.ports[num] = PPort("%s-eth%d" % (self.name, num), num, self)
        return self.ports[num]

class PSwitch(PNode):
    dpid = 1
    directory = {}
    # str indexes including:
    #  dpid eg. 0000000000000001
    #  node eg. OF|00:00:00:00:00:00:00:01 (config in testdemo.py)
    def __init__(self, name, mininetName):
        PNode.__init__(self, name, mininetName)
        self.dpid = PMAC(PSwitch.dpid)
        self.controller = None
        self.odl = None
        PSwitch.dpid += 1
        PSwitch.directory[self.dpid.dpid()] = self
    def setController(self, controller):
        self.controller = controller
    def setOdl(self, odldevice):
        self.odl = odldevice.getNode()
        it = odldevice.nodeConnectors.iterator()
        while it.hasNext():
            odlport = it.next()
            port = self.getPort(odlport.getID())
            port.setOdl(odlport)
    def stitch(self, port1, port2):
        self.addFlowMod(PMatch(port=port1), PAction(port=port2))
        self.addFlowMod(PMatch(port=port2), PAction(port=port1))
    def addFlowMod(self, match, action):
        self.controller.addFlowMod(self, match, action)
    def checkPacket(self, packet):
        """
        overrided
        """
        self.addFlowMod(PMatch(dst=packet.getSrc()), PAction(vlan=packet.getVlan(), port=self.getPort(packet.getPortID())))
    def broadcast(self, packet):
        """
        overrided
        """
        for port in self.ports.values():
            if port == self.ports[packet.getPortID()]:
                continue
            self.controller.send(packet, port)
class PSiteRouter(PSwitch):
    def __init__(self, name, mininetName):
        PSwitch.__init__(self, name, mininetName)
        self.wanPort = None
        self.lanVlans = {}
        self.wanVlans = {}
    def setWanPort(self, port):
        self.wanPort = port
    def addVlan(self, lanVlan, wanVlan):
        self.lanVlans[wanVlan] = lanVlan
        self.wanVlans[lanVlan] = wanVlan
    def broadcast(self, packet):
        if self.wanPort.number == packet.getPortID():
            # from WAN
            wanVlan = packet.getVlan()
            lanVlan = self.lanVlans[wanVlan]
            packet.set(vlan=lanVlan)
        else:
            # from LAN
            lanVlan = packet.getVlan()
            wanVlan = self.wanVlans[lanVlan]
            toWan = True
        in_port = self.ports[packet.getPortID()]
        # broadcast to all hosts in LAN
        for port in self.ports.values():
            if port == in_port:
                continue
            if port == self.wanPort:
                continue
            self.controller.send(packet, port)
        if toWan:
            packet.set(vlan=wanVlan)
            self.controller.send(packet, self.wanPort)
class PCoreRouter(PSwitch):
    def __init__(self, name, mininetName):
        PSwitch.__init__(self, name, mininetName)
class PHwSwitch(PSwitch):
    def __init__(self, name, mininetName, pop):
        PSwitch.__init__(self, name, mininetName)
        self.pop = pop
        self.sitePort = None
        self.popPort = {}
        self.vpns = {} # vpns[vlan] = vpn
        self.vlans = {} # vlans[vid] = vlan
    def setSitePort(self, port):
        self.sitePort = port
    def addPopPort(self, pop, port):
        self.popPort[pop.name] = port
    def getPopPort(self, pop):
        if not pop.name in self.popPort:
            Logger().error("next pop %r not found in the ports of %r" % (pop, self))
        return self.popPort[pop.name]
    def addVPN(self, vlan, vpn):
        self.vpns[vlan] = vpn
        self.vlans[vpn.vid] = vlan
    def checkPacket(self, packet):
        in_port = self.getPort(packet.getPortID())
        if self.sitePort == in_port:
            # from LAN: addFlowMod(match=translate MAC, action=reverse, vlan)
            mac = packet.getSrc()
            vlan = packet.getVlan()
            vpn = self.vpns[vlan]
            dst = vpn.translate(self.pop, mac)
            self.addFlowMod(PMatch(dst=dst), PAction(vlan=vlan, dst=mac, port=in_port))
        else:
            # from WAN: addFlowMod(match=reverse translate MAC)
            trans_mac = packet.getSrc()
            vid = trans_mac.getVid()
            vlan = self.vlans[vid]
            vpn = self.vpns[vlan]
            (pop, mac) = vpn.reverse(trans_mac)
            self.addFlowMod(PMatch(dst=mac), PAction(vlan=in_port.getVlan(), dst=trans_mac, port=in_port))
    def broadcast(self, packet):
        in_port = self.getPort(packet.getPortID())
        if self.sitePort == in_port:
            # from LAN: translate MAC, then broadcast to all WANs
            vlan = packet.getVlan()
            if not vlan in self.vpns:
                Logger().warning("vlan %r not found in %r's vpn" % (vlan, self) )
                return
            vpn = self.vpns[vlan]
            mac = packet.getSrc()
            src = vpn.translate(self.pop, mac)
            packet.set(src=src, dst=PMAC.createBroadcast(vpn.vid))
            for pop in vpn.pops:
                if pop == self.pop:
                    continue
                port = self.getPopPort(pop)
                packet.set(vlan=port.getVlan())
                self.controller.send(packet, port)
        else:
            # from WAN: reverse MAC, then forward to site
            trans_mac = packet.getSrc()
            vid = trans_mac.getVid()
            vlan = self.vlans[vid]
            vpn = self.vpns[vlan]
            (pop, mac) = vpn.reverse(trans_mac)
            packet.set(vlan=vlan, src=mac, dst=mac.broadcast)
            self.controller.send(packet, self.sitePort)

class PHost(PNode):
    def __init__(self, name, mininetName):
        PNode.__init__(self, name, mininetName)
        return
class PSDNPop(PObject):
    def __init__(self, name, corename, hwname, mininetCoreName, mininetHwName):
        PObject.__init__(self, name)
        self.core = PCoreRouter(corename, mininetCoreName)
        self.hw = PHwSwitch(hwname, mininetHwName, self)
class PPort(PObject):
    def __init__(self, name, number, node):
        PObject.__init__(self, name)
        self.number = number
        self.links = []
        self.vlans = []
        self.node = node
        self.odl = None
    def addVlan(self, vlan):
        self.vlans.append(vlan)
    def getVlan(self):
        if self.vlans and len(self.vlans) == 1:
            return self.vlans[0]
        Logger().warning("%r.vlans=%r should have only ONE elements" % (self, self.vlans))
        return 0
    def setOdl(self, odl):
        self.odl = odl
    def getNode(self):
        return self.node

class PLink(PObject):
    def __init__(self, node1, node2, name = None, portnum1 = None, portnum2 = None):
        port1 = node1.getPort(portnum1)
        port2 = node2.getPort(portnum2)
        if not name:
            name = '%s:%s' % (port1.name, port2.name)
        PObject.__init__(self, name)
        self.endpoints = [port1, port2]
        port1.links.append(self)
        port2.links.append(self)
        self.vlans = []
    def addVlan(self, vlan):
        self.vlans.append(vlan)
        for p in self.endpoints:
            p.addVlan(vlan)
    def getPort(self, index):
        return self.endpoints[index]
    def getNode(self, index):
        return self.getPort(index).getNode()
class PToWanLink(PLink):
    def __init__(self, site, core, name = None, portnum1 = None, portnum2 = None):
        PLink.__init__(self, site, core, name, portnum1, portnum2)
        site.setWanPort(self.getPort(0))

class PPacket:
    def __init__(self, rawPacket):
        self.rawPacket = rawPacket
        self.odlport = rawPacket.getIncomingNodeConnector()
        self.odlnode = self.odlport.getNode()
        self.l2pkt = net.es.netshell.odl.PacketHandler.getInstance().decodeDataPacket(rawPacket)
        self.etherType = self.l2pkt.getEtherType() & 0xffff # convert to unsigned type
        self.vlanPacket = self.l2pkt.getPayload()
    def ignore(self):
        if self.odlnode.getType() != Node.NodeIDType.OPENFLOW:
            Logger().warning("from unknown node...")
            return True
        if self.l2pkt.__class__  != Ethernet:
            Logger().warning("unknown packet...")
            return True
        return False
    def uninterested(self):
        if self.etherType == EtherTypes.LLDP.shortValue() & 0xffff:
            Logger().debug("ignore LLDP...")
            return True
        if self.etherType != EtherTypes.VLANTAGGED.shortValue() & 0xffff:
            Logger().debug("uninterested packet without vlan...")
            return True
        return False
    def getSwitchString(self):
        return self.odlnode.toString()
    def getPortID(self):
        return self.odlport.getID()
    def getSrc(self):
        return PMAC(self.l2pkt.getSourceMACAddress())
    def getDst(self):
        return PMAC(self.l2pkt.getDestinationMACAddress())
    def getVlan(self):
        return self.vlanPacket.getVid()
    def set(self, vlan=None, src=None, dst=None):
        if src:
            self.l2pkt.setSourceMACAddress(src.jarray())
        if dst:
            self.l2pkt.setDestinationMACAddress(dst.jarray())
        if vlan:
            self.vlanPacket.setVid(vlan)
        self.rawPacket = net.es.netshell.odl.PacketHandler.getInstance().encodeDataPacket(self.l2pkt)
    def isBroadcast(self):
        return self.getDst().isBroadcast()
    def __repr__(self):
        return "packet(src=%r,dst=%r,vlan=%r)" % (self.getSrc(), self.getDst(), self.getVlan())
class PController:
    def __init__(self, name):
        self.debug = True
        self.packets = Set() # used for ignore duplicate only
        self.name = name
        devices = net.es.netshell.odl.Controller.getInstance().getNetworkDevices()
        for device in devices:
            odlnode = device.getNode()
            dpid = PMAC(device.getDataLayerAddress())
            switch = PSwitch.directory[dpid.dpid()]
            switch.setOdl(device)
            PSwitch.directory[odlnode.toString()] = switch
            switch.setController(self)
    def callback(self, packet):
        if self.debug:
            self.lastPacket = packet
        switch = PSwitch.directory[packet.getSwitchString()]
        port = switch.getPort(packet.getPortID())
        if packet.ignore():
            return PacketResult.IGNORED
        if packet.uninterested():
            return PacketResult.KEEP_PROCESSING
        Logger().info("%r recv %r@%r" % (self.name, packet, port))
        switch.checkPacket(packet)
        if packet.isBroadcast():
            switch.broadcast(packet)
        return PacketResult.KEEP_PROCESSING
    def addFlowMod(self, switch, match, action):
        Logger().info("%r addFlowMod(%r,%r)@%r" % (self.name, match, action, switch))
        success = net.es.netshell.odl.Controller.getInstance().addFlow(switch.odl, Flow(match.match, action.action))
        if not success:
            Logger().error("add flow failed!")
    def send(self, packet, port):
        Logger().info("%r send %r fr %r" % (self.name, packet, port))
        packet.rawPacket.setOutgoingNodeConnector(port.odl)
        net.es.netshell.odl.PacketHandler.getInstance().transmitDataPacket(packet.rawPacket)
class PMatch:
    def __init__(self, src=None, dst=None, vlan=None, port=None):
        self.match = Match()
        if src:
            self.match.setField(DL_SRC, src.jarray())
        if dst:
            self.match.setField(DL_DST, dst.jarray())
        if vlan:
            self.match.setField(DL_VLAN, Short(vlan))
        if port:
            self.match.setField(IN_PORT, port.odl)
    def __repr__(self):
        return self.match.__repr__()
class PAction:
    def __init__(self, src=None, dst=None, vlan=None, port=None):
        self.action = LinkedList()
        if src:
            self.action.add(SetDlSrc(src.jarray()))
        if dst:
            self.action.add(SetDlDst(dst.jarray()))
        if vlan:
            self.action.add(SetVlanId(vlan))
        self.repr = self.action.__repr__()
        if port:
            self.action.add(Output(port.odl)) # repr is not implemented
            self.repr = "Action [%r,[OUTPUT[port=%r]]]" % (self.repr[1:-1], port.number)
    def __repr__(self):
        return self.repr

class PVPN:
    def __init__(self, vid, pops):
        self.vid = vid
        self.pops = pops
        self.trans_macs = {} # trans_mac['mac'] = (pop, trans_mac)
        self.reverse_macs = {} # reverse_macs['trans_mac'] = (pop, mac)
        self.occupiedHid = Set()
    def generateRandomHostID(self):
        """
        ff00-ffff: reserved
        """
        found = False
        while not found:
            hid = random.randint(1, 0xff00 - 1)
            if not hid in self.occupiedHid:
                found = True
        self.occupiedHid.add(hid)
        # TODO lock
        return hid
    def translate(self, pop, mac):
        if not str(mac) in self.trans_macs:
            hid = self.generateRandomHostID()
            trans_mac = PMAC()
            trans_mac.setVid(self.vid)
            trans_mac.setHid(hid)
            self.trans_macs[str(mac)] = (pop, trans_mac)
            self.reverse_macs[str(trans_mac)] = (pop, mac)
        return self.trans_macs[str(mac)][1]
    def reverse(self, trans_mac):
        if not str(trans_mac) in self.reverse_macs:
            Logger().warning("trans_mac %r not found in %r.reverse_macs", trans_mac, self)
            return None
        return self.reverse_macs[str(trans_mac)]
    def __repr__(self):
        return "VPN[%r]" % self.vid

