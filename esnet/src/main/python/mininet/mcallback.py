import net.es.netshell.odl.Controller
import net.es.netshell.odl.PacketHandler
import struct, array, jarray
from java.lang import Short
from java.util import LinkedList


from org.opendaylight.controller.sal.core import Node
from org.opendaylight.controller.sal.packet import Ethernet
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

import logging
import sys

logger = logging.getLogger()
logger.setLevel(logging.INFO)
if len(logger.handlers) == 0:
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
# using logger.setLevel(logging.DEBUG) to open debug information

class MiniCallback(net.es.netshell.odl.PacketHandler.Callback):
    version = 6
    # topo: h1-eth0 <-> s1-eth1, s1-eth2 <-> s2-eth2, s2-eth1 <-> h2-eth0
    # vlan:          10                   11                   10
    vlan_lan = 10
    vlan_wan = 11
    vlan_trans = {10:11, 11:10}
    topo = {}
    def __init__(self):
        self.odlController = net.es.netshell.odl.Controller.getInstance()
        self.devices = self.odlController.getNetworkDevices()
        if len(self.devices) != 2:
            logger.warning("more than 2 devices, out of the controller's capability...")
            return
        self.odlPacketHandler = net.es.netshell.odl.PacketHandler.getInstance()
        self.odlPacketHandler.setPacketInCallback(self)
        self.macs = [ array.array('b', [0,0,0,0,0,1]), array.array('b', [0,0,0,0,0,2]), array.array('b', [-1,-1,-1,-1,-1,-1]) ]
    def startCallback(self):
        self.odlPacketHandler.setPacketInCallback(self)

    def stopCallback(self):
        self.odlPacketHandler.setPacketInCallback(None)

    def javaByteArray(self, parr):
        jarr = jarray.zeros(len(parr), 'b')
        for i in range(len(jarr)):
            jarr[i] = struct.unpack('b', struct.pack('B', parr[i]))[0]
        return jarr
       
    def callback(self, rawPacket):
        logger.debug("Hello, callback" + str(MiniCallback.version))
        ingressConnector = rawPacket.getIncomingNodeConnector() # OF|2@OF|00:...:01
        ingressNode = ingressConnector.getNode() # OF|00:...:02
        if ingressNode.getType() != Node.NodeIDType.OPENFLOW:
            logger.warning("from node with unknown type...")
            return PacketResult.IGNORED
        l2pkt = self.odlPacketHandler.decodeDataPacket(rawPacket)
        if l2pkt.__class__  != Ethernet:
            logger.warning("unknown packet...")
            return PacketResult.IGNORED
        if not l2pkt.getSourceMACAddress() in self.macs or not l2pkt.getDestinationMACAddress() in self.macs:
            logger.debug("packet from uninterested src... Goodbye, callback")
            return PacketResult.KEEP_PROCESSING
        etherType = l2pkt.getEtherType() & 0xffff # convert to unsigned type
        if etherType != EtherTypes.VLANTAGGED.shortValue() & 0xffff:
            logger.info("uninterested packet without vlan... Goodbye, callback")
            return PacketResult.KEEP_PROCESSING
        vlanPacket = l2pkt.getPayload()
        vlanTag = vlanPacket.getVid()
        if vlanTag != MiniCallback.vlan_lan and vlanTag != MiniCallback.vlan_wan:
            logger.warning("uninterested vlan... Goodbye, callback")
            return PacketResult.KEEP_PROCESSING

        if ingressNode.getID() == 1L:
            assert(vlanTag == MiniCallback.vlan_lan)
            dst = self.javaByteArray(l2pkt.getSourceMACAddress())
            it = self.devices[1].nodeConnectors.iterator()
            in_port = it.next()
            out_port = it.next()
            match = Match()
            # match.setField(IN_PORT, in_port)
            match.setField(DL_DST, dst)
            match.setField(DL_VLAN, Short(MiniCallback.vlan_wan))
            actionList = LinkedList()
            # MAC translation
            # actionList.add(SetDlDst(self.javaByteArray(action.props['dl_dst'])))
            # actionList.add(SetDlSrc(self.javaByteArray(action.props['dl_src'])))
            actionList.add(SetVlanId(MiniCallback.vlan_lan))
            actionList.add(Output(out_port))
            flow = Flow(match, actionList)
            self.odlController.addFlow(ingressNode, flow)

            it = self.devices[0].nodeConnectors.iterator()
            in_port = it.next()
            out_port = it.next()
            match = Match()
            # match.setField(IN_PORT, in_port)
            match.setField(DL_DST, dst)
            match.setField(DL_VLAN, Short(MiniCallback.vlan_lan))
            actionList = LinkedList()
            # MAC translation
            # actionList.add(SetDlDst(self.javaByteArray(action.props['dl_dst'])))
            # actionList.add(SetDlSrc(self.javaByteArray(action.props['dl_src'])))
            actionList.add(SetVlanId(MiniCallback.vlan_wan))
            actionList.add(Output(out_port))
            flow = Flow(match, actionList)
            self.odlController.addFlow(self.devices[0].node, flow)

            # broadcast
            for nodeconn in self.devices[1].nodeConnectors:
                if nodeconn == ingressConnector:
                    continue
                rawPacket.setOutgoingNodeConnector(nodeconn)
                self.odlPacketHandler.transmitDataPacket(rawPacket)
        else:
            assert(vlanTag == MiniCallback.vlan_lan)
            dst = self.javaByteArray(l2pkt.getSourceMACAddress())
            it = self.devices[0].nodeConnectors.iterator()
            out_port = it.next()
            in_port = it.next()
            match = Match()
            # match.setField(IN_PORT, in_port)
            match.setField(DL_DST, dst)
            match.setField(DL_VLAN, Short(MiniCallback.vlan_wan))
            actionList = LinkedList()
            # MAC translation
            # actionList.add(SetDlDst(self.javaByteArray(action.props['dl_dst'])))
            # actionList.add(SetDlSrc(self.javaByteArray(action.props['dl_src'])))
            actionList.add(SetVlanId(MiniCallback.vlan_lan))
            actionList.add(Output(out_port))
            flow = Flow(match, actionList)
            self.odlController.addFlow(ingressNode, flow)

            it = self.devices[1].nodeConnectors.iterator()
            out_port = it.next()
            in_port = it.next()
            match = Match()
            # match.setField(IN_PORT, in_port)
            match.setField(DL_DST, dst)
            match.setField(DL_VLAN, Short(MiniCallback.vlan_lan))
            actionList = LinkedList()
            # MAC translation
            # actionList.add(SetDlDst(self.javaByteArray(action.props['dl_dst'])))
            # actionList.add(SetDlSrc(self.javaByteArray(action.props['dl_src'])))
            actionList.add(SetVlanId(MiniCallback.vlan_wan))
            actionList.add(Output(out_port))
            flow = Flow(match, actionList)
            self.odlController.addFlow(self.devices[1].node, flow)

            # broadcast
            for nodeconn in self.devices[0].nodeConnectors:
                if nodeconn == ingressConnector:
                    continue
                rawPacket.setOutgoingNodeConnector(nodeconn)
                self.odlPacketHandler.transmitDataPacket(rawPacket)
        return PacketResult.KEEP_PROCESSING
