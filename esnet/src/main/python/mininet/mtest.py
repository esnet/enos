import net.es.netshell.odl.Controller
import net.es.netshell.odl.PacketHandler
from java.lang import Short
from java.util import LinkedList

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


from mininet.mac import MACAddress
from mininet.mat import MATManager
from mininet.utility import Logger

class MiniTopo():
    def __init__(self):
        # $ sudo mn --topo linear,2 --controller remote
        # construct the simple topology
        # single VPN
        # topo: h1-eth0 <-> s1-eth1, s1-eth2 <-> s2-eth2, s2-eth1 <-> h2-eth0
        # vlan:          10                   11                   10                       
        #                   conn[1]  conn[0]     conn[1]  conn[0]
        #                       device[1]            device[0]
        #                       ID = 2               ID = 1
        self.vlans = {}
        self.ports = {}
        self.nodes = {}
        self.ports_name = {}
        self.nodes_name = {}

        devices = net.es.netshell.odl.Controller.getInstance().getNetworkDevices()
        
        vid = MATManager.generateRandomVPNID()
        self.vlans[vid] = {"s1-eth1": 10, "s1-eth2":11, "s2-eth2":11, "s2-eth1":10}
        for vlan in self.vlans[vid].items():
            MATManager.setVid(vlan[0], vlan[1], vid) # eg. setVid("s1-eth1", 10, vid)

        it = devices[1].nodeConnectors.iterator()
        self.ports["s1-eth2"] = it.next()
        self.ports["s1-eth1"] = it.next()

        it = devices[0].nodeConnectors.iterator()
        self.ports["s2-eth1"] = it.next()
        self.ports["s2-eth2"] = it.next()
        self.nodes["s1"] = devices[1].getNode()
        self.nodes["s2"] = devices[0].getNode()

        for port in self.ports.items():
            self.ports_name[port[1]] = port[0]
        for node in self.nodes.items():
            self.nodes_name[node[1]] = node[0]

class MiniTest(net.es.netshell.odl.PacketHandler.Callback):
    version = 10
    def __init__(self):
        self.odlController = net.es.netshell.odl.Controller.getInstance()
        self.odlPacketHandler = net.es.netshell.odl.PacketHandler.getInstance()
        self.odlPacketHandler.setPacketInCallback(self)
        self.topo = MiniTopo()

    def startCallback(self):
        self.odlPacketHandler.setPacketInCallback(self)

    def stopCallback(self):
        self.odlPacketHandler.setPacketInCallback(None)
        
    def callback(self, rawPacket):
        Logger().debug("Hello, callback " + str(MiniTest.version))
        ingressConnector = rawPacket.getIncomingNodeConnector() # OF|2@OF|00:...:01
        ingressNode = ingressConnector.getNode() # OF|00:...:02
        if ingressNode.getType() != Node.NodeIDType.OPENFLOW:
            Logger().warning("from node with unknown type...")
            return PacketResult.IGNORED
        l2pkt = self.odlPacketHandler.decodeDataPacket(rawPacket)
        if l2pkt.__class__  != Ethernet:
            Logger().warning("unknown packet...")
            return PacketResult.IGNORED
        etherType = l2pkt.getEtherType() & 0xffff # convert to unsigned type
        if etherType != EtherTypes.VLANTAGGED.shortValue() & 0xffff:
            Logger().debug("uninterested packet without vlan... Goodbye, callback")
            return PacketResult.KEEP_PROCESSING
        vlanPacket = l2pkt.getPayload()
        vlanTag = vlanPacket.getVid()
        # input: switch, port, vlan, mac
        port_name = self.topo.ports_name[ingressConnector]
        if port_name[-1] == '1':
            # the packet is from host
            mac = MACAddress(l2pkt.getSourceMACAddress())
            # output: trans_mac (fr vid(fr port and vlan) and mac) as list
            trans_mac = MATManager.MAT(mac, port_name, vlanTag)
            # add flowmod: match: to mac; action: vlan, port, trans_mac
            match = Match()
            match.setField(DL_DST, trans_mac.jarray())
            actionList = LinkedList()
            actionList.add(SetDlDst(mac.jarray()))
            actionList.add(SetVlanId(vlanTag))
            actionList.add(Output(ingressConnector))
            flow = Flow(match, actionList)
            Logger().info("fr site: add flow match={{dst:{}}}, action={{dst:{},vlan:{},port:{}}}".format(trans_mac, mac, vlanTag, port_name))
            self.odlController.addFlow(ingressNode, flow)
            # if fr host && broadcast: packetout with trans_mac and trans_vlan (fr vid(fr port and vlan) and out_port)
            if MACAddress(l2pkt.getDestinationMACAddress()) == MACAddress.broadcast:
                vid = MATManager.getVid(port_name, vlanTag)
                for port in self.topo.ports.items():
                    if port[1] == ingressConnector:
                        continue
                    trans_vlan = self.topo.vlans[vid][port[0]]
                    l2pkt_out = Ethernet()
                    l2pkt_out.setSourceMACAddress(trans_mac.array())
                    l2pkt_out.setDestinationMACAddress(l2pkt.getDestinationMACAddress())
                    vlanpkt_out = IEEE8021Q()
                    vlanpkt_out.setVid(trans_vlan)
                    vlanpkt_out.setEtherType(vlanPacket.getEtherType())
                    vlanpkt_out.setPayload(vlanPacket.getPayload())
                    l2pkt_out.setPayload(vlanpkt_out)
                    l2pkt_out.setEtherType(EtherTypes.VLANTAGGED.shortValue())
                    rawpkt_out = self.odlPacketHandler.encodeDataPacket(l2pkt_out)
                    rawpkt_out.setOutgoingNodeConnector(port[1])
                    self.odlPacketHandler.transmitDataPacket(rawpkt_out)
        else:
            # the packet is from controller (broadcast)
            trans_mac = MACAddress(l2pkt.getSourceMACAddress())
            # output: trans_mac (fr vid(fr port and vlan) and mac) as list
            mac = MATManager.restoreMAT(trans_mac)
            # add flowmod: match: to mac; action: vlan, port, trans_mac
            match = Match()
            match.setField(DL_DST, mac.jarray())
            actionList = LinkedList()
            actionList.add(SetDlDst(trans_mac.jarray()))
            actionList.add(SetVlanId(vlanTag))
            actionList.add(Output(ingressConnector))
            flow = Flow(match, actionList)
            Logger().info("fr ctrl: add flow match={{dst:{}}}, action={{dst:{},vlan:{},port:{}}}".format(mac, trans_mac, vlanTag, port_name))
            self.odlController.addFlow(ingressNode, flow)
        return PacketResult.KEEP_PROCESSING
