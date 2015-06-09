import net.es.netshell.odl.Controller
import net.es.netshell.odl.PacketHandler
import array

from org.opendaylight.controller.sal.core import Node
from org.opendaylight.controller.sal.packet import Ethernet
from org.opendaylight.controller.sal.packet import RawPacket
from org.opendaylight.controller.sal.packet import PacketResult
from org.opendaylight.controller.sal.utils import EtherTypes

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
    version = 5
    def __init__(self):
        self.odlController = net.es.netshell.odl.Controller.getInstance()
        self.odlPacketHandler = net.es.netshell.odl.PacketHandler.getInstance()
        self.odlPacketHandler.setPacketInCallback(self)
        self.macs = [ array.array('b', [0,0,0,0,0,1]), array.array('b', [0,0,0,0,0,2]), array.array('b', [-1,-1,-1,-1,-1,-1]) ]
    def startCallback(self):
        self.odlPacketHandler.setPacketInCallback(self)

    def stopCallback(self):
        self.odlPacketHandler.setPacketInCallback(None)

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
        self.l2pkt = l2pkt        
        vlanPacket = l2pkt.getPayload()
        vlanTag = vlanPacket.getVid()
        etherType = vlanPacket.getEtherType() & 0xffff # convert to unsigned
        if vlanPacket.getPayload():
            payload = vlanPacket.getPayload()
        else:
            payload = vlanPacket.getRawPayload()
        out = "srcMac:" + l2pkt.getSourceMACAddress().__str__() + ";"
        out += "dstMac:" + l2pkt.getDestinationMACAddress().__str__() + ";"
        out += "vlan:" + str(vlanTag) + ";"
        logger.info(out)
        logger.debug("Goodbye, callback")
        return PacketResult.KEEP_PROCESSING
