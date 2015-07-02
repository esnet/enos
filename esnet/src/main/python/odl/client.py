import struct
import array, jarray
import sys
import inspect
import binascii
import threading
from common.mac import MACAddress
from common.utils import Logger

from java.lang import Short
from java.lang import Long
from java.util import LinkedList
from java.nio import ByteBuffer

from common.openflow import SimpleController, PacketInEvent

from org.opendaylight.controller.sal.core import Node

import net.es.netshell.odl.Controller
import net.es.netshell.odl.PacketHandler

from org.opendaylight.controller.sal.core import Node

from org.opendaylight.controller.sal.match import Match
from org.opendaylight.controller.sal.match.MatchType import DL_DST
from org.opendaylight.controller.sal.match.MatchType import DL_SRC
from org.opendaylight.controller.sal.match.MatchType import DL_VLAN
from org.opendaylight.controller.sal.match.MatchType import IN_PORT

from org.opendaylight.controller.sal.action import Output
from org.opendaylight.controller.sal.action import SetDlDst
from org.opendaylight.controller.sal.action import SetDlSrc
from org.opendaylight.controller.sal.action import SetVlanId

from org.opendaylight.controller.sal.packet import Packet
from org.opendaylight.controller.sal.packet import Ethernet
from org.opendaylight.controller.sal.packet import IEEE8021Q
from org.opendaylight.controller.sal.packet.LinkEncap import ETHERNET
from org.opendaylight.controller.sal.packet import RawPacket
from org.opendaylight.controller.sal.packet import PacketResult

from org.opendaylight.controller.sal.flowprogrammer import Flow

from org.opendaylight.controller.sal.utils import EtherTypes
class ODLClient(SimpleController,net.es.netshell.odl.PacketHandler.Callback):
    """
    Class that is an interface to the ENOS OpenDaylight client.
    The real client functionality is the net.es.netshell.odl.Controller
    class (in Java).
    :param topology mininet.enos.TestbedTopology
    """
    topology = None

    def __init__(self,topology):
        """
        Note: topology might not be ready at this moment,
        so you are not allowed to access anything related to topology.builder here.
        However, you could do it later in method init(self).
        :param topology: TestbedTopology whose builder is not ready yet
        """
        self.__class__ = SimpleController
        #super(ODLClient,self).__init__()
        SimpleController.__init__(self)
        self.__class__ = ODLClient
        self.odlController = net.es.netshell.odl.Controller.getInstance()
        self.odlPacketHandler = net.es.netshell.odl.PacketHandler.getInstance()
        ODLClient.topology = topology
        self.debug = 0
        self.dropLLDP = True
        self.odlSwitchIndex = {} # [key=dpid]
        self.switchIndex = {} # [key=odlNode.getID()]
    def init(self):
        """
        Index odlSwitchIndex and switchIndex to speed up getSwitch() and findODLSwitch()
        """
        # index odl node and port(connector)
        index = {} # [dpid] = switch
        for switch in ODLClient.topology.builder.switches:
            if 'dpid' in switch.props:
                dpid = binascii.hexlify(switch.props['dpid'][-6:])
                index[dpid] = switch
        for odlSwitch in self.odlController.getNetworkDevices():
            nodeID = odlSwitch.getNode().getID()
            dpid = binascii.hexlify(odlSwitch.getDataLayerAddress())
            if not dpid in index:
                Logger().warning('an OdlSwitch with %r not found in topology' % dpid)
                continue
            self.odlSwitchIndex[dpid] = odlSwitch
            self.switchIndex[nodeID] = index[dpid]
        self.odlPacketHandler.setPacketInCallback(self)
    def getSwitch(self, nodeID):
        if not nodeID in self.switchIndex:
            Logger().error('nodeID %r not found in %r.switchIndex' % (nodeID, self))
            return None
        return self.switchIndex[nodeID]

    def startCallback(self):
        self.odlPacketHandler.setPacketInCallback(self)

    def stopCallback(self):
        self.odlPacketHandler.setPacketInCallback(None)

    def findODLSwitch(self, switch):
        """
        Given the switch in the ENOS (Python) world, find the switch in the
        ODL (Java) world.
        :param switch: common.api.Node
        :return: org.opendaylight.controller.switchmanager.Switch (None if not found)
        """
        dpid = binascii.hexlify(switch.props['dpid'][-6:])
        if not dpid in self.odlSwitchIndex:
            Logger().warning('could not found dpid %r in %r.findODLSwitch' % (dpid, self))
            return None
        return self.odlSwitchIndex[dpid]

    def makeODLFlowEntry(self, flowMod, odlNode):
        """
        Given a FlowMod object, turn it into a Flow suitable for passing to ODL.

        Encapsulates a bunch of common sense about the order in which flow actions
        should be applied.

        :param flowMod: ENOS FlowMod
        :param odlNode: OpenDaylight Node object
        :return:
        """

        # Compose match object                                                     `
        match = Match()
        if 'in_port' in flowMod.match.props:
            # Compose the port name
            portName = flowMod.switch.props['mininetName'] + '-' + flowMod.match.props['in_port'].name.split("-")[-1]
            nodeconn = self.odlController.getNodeConnector(odlNode, portName)
            match.setField(IN_PORT, nodeconn)
        if 'dl_src' in flowMod.match.props:
            match.setField(DL_SRC, self.javaByteArray(flowMod.match.props['dl_src'].data))
        if 'dl_dst' in flowMod.match.props:
            match.setField(DL_DST, self.javaByteArray(flowMod.match.props['dl_dst'].data))
        if 'vlan' in flowMod.match.props:
            match.setField(DL_VLAN, Short(flowMod.match.props['vlan']))

        # Compose action.
        # We do the data-link and VLAN translations first.  Other types of
        # translations would happen here as well.  Then any action to forward
        # packets.
        actionList = LinkedList()

        # Current code assumes there is only one action
        if len(flowMod.actions) != 1:
            # This implementation only supports a single action
            return False

        action = flowMod.actions[0]
        if 'dl_dst' in action.props:
            actionList.add(SetDlDst(self.javaByteArray(action.props['dl_dst'].data)))
        if 'dl_src' in action.props:
            actionList.add(SetDlSrc(self.javaByteArray(action.props['dl_src'].data)))
        if 'vlan' in action.props:
            actionList.add(SetVlanId(action.props['vlan']))
        if 'out_port' in action.props:
            p = action.props['out_port']
            # Compose the port name, which comes from the mininet switch name ("s2") and our
            # port name ("eth1").  We then need to look this up in the ODL SwitchManager,
            # but that requires a pointer to the ODL Node.
            portName = flowMod.switch.props['mininetName'] + "-" + p.name.split("-")[-1]
            nodeconn = self.odlController.getNodeConnector(odlNode, portName)
            actionList.add(Output(nodeconn))
        else:
            # This implementation requires all actions to contain a port_out
            return False

        # compose flow
        flow = Flow(match, actionList)
        return flow

    def addFlowMod(self, flowMod):
        """
        Implementation of addFlowMod for use with OpenDaylight.
        Uses the net.es.netshell.odl.Controller.
        :param flowMod:
        :return: True if successful, False if not
        """
        # check scope
        if self.isFlowModValid(flowMod):
            sw = self.findODLSwitch(flowMod.switch)
            # print "flowMod.switch of type ", str(type(flowMod.switch))
            if sw == None:
                print flowMod,"cannot be pushed because the switch is not in inventory"
                return False

            flow = self.makeODLFlowEntry(flowMod=flowMod, odlNode=sw.node)
            if not flow:
                print "Cannot push flowmond onto",flowMod.switch
            # go to the controller
            success = self.odlController.addFlow(sw.node, flow)
            # if success.isSuccess():
            #     flowMod.switch.props['openFlowSwitch'].flowMods[flowMod] = flowMod

            # get result
            return True
        else:
            print 'flowMod %r is not valid' % flowMod
        return False


    def send(self,packet):
        """
        Send a packet via a PACKET_OUT OpenFlow message

        :param packet: common.openflow.PacketOut
        :return:  True if successful, False if not
        """
        if self.isPacketOutValid(packet):
            # Get the switch (Node in the ODL world) and port (NodeConnector in the ODL world)
            sw = self.findODLSwitch(packet.scope.switch)
            if sw == None:
                print packet, "cannot be sent because the switch is not in inventory"
                return False
            portName = packet.scope.switch.props['mininetName'] + '-' + packet.port.name.split("-")[-1]
            nodeconn = self.odlController.getNodeConnector(sw.getNode(), portName)
            if nodeconn == None:
                print packet, "cannot be sent because the port is invalid"
                return False

            # Create the outgoing packet in ODL land.  The outgoing node connector must be set.
            cp = Ethernet()
            cp.setSourceMACAddress(self.javaByteArray(packet.dl_src.data))
            cp.setDestinationMACAddress(self.javaByteArray(packet.dl_dst.data))
            if packet.vlan == 0:
                cp.setEtherType(packet.etherType)
                if isinstance(packet.payload, Packet):
                    cp.setPayload(packet.payload)
                else:
                    cp.setRawPayload(self.javaByteArray(packet.payload))
            else:
                cvp = IEEE8021Q()
                cvp.setEtherType(packet.etherType)
                cvp.setVid(packet.vlan)
                if isinstance(packet.payload, Packet):
                    cvp.setPayload(packet.payload)
                else:
                    cvp.setRawPayload(self.javaByteArray(packet.payload))
                cp.setPayload(cvp)
                cp.setEtherType(EtherTypes.VLANTAGGED.shortValue())
            rp = self.odlPacketHandler.encodeDataPacket(cp)
            rp.setOutgoingNodeConnector(nodeconn)

            self.odlPacketHandler.transmitDataPacket(rp)
            return True
        else:
            print 'Packet %r is not valid' % packet
        return False

    def delFlowMod(self, flowMod):
        """
        Implementation of delFlowMod for use with OpenDaylight.
        :param flowMod:
        :return: True if successful, False if not
        """
        # check scope
        if self.isFlowModValid(flowMod):
            sw = self.findODLSwitch(flowMod.switch)
            if sw == None:
                print flowMod,"cannot be removed because the switch is not in inventory"
                return False

            flow = self.makeODLFlowEntry(flowMod=flowMod, odlNode=sw.node)
            if not flow:
                print "Cannot remove flowmod from",flowMod.switch
            # go to the controller
            success = self.odlController.removeFlow(sw.node, flow)
            print success
            # get result
            return True
        else:
            print 'flowMod %r is not valid' % flowMod
        return False

    def delAllFlowMods(self, switch):
        """
        Implementation of delAllFlowMods for OpenDaylight
        :param sw: common.api.Node (switch to be nuked)
        :return:
        """
        odlSwitch = self.findODLSwitch(switch)
        if (odlSwitch):
            success = self.odlController.removeAllFlows(odlSwitch.getNode())
            print success
            switch.flowMods = {}
            return True
        else:
            print "Cannot find ", switch
            return False

    def unsignedByteArray(self, a):
        """
        Make an unsigned byte array from a signed byte array.
        Useful for getting arrays of bytes from Java, which doesn't have an unsigned byte
        type.
        :param a: array of signed bytes
        :return: array of unsigned bytes
        """
        b = array.array('B')
        for i in a:
            b.append(i & 0xff)
        return b

    def javaByteArray(self, a):
        """
        Make a Java array of bytes from unsigned bytes in Python.  Note that Java
        bytes are signed, whereas in Python they may be either signed or unsigned.
        :param a:
        :return:
        """
        b = jarray.zeros(len(a), 'b')
        for i in range(len(a)):
            b[i] = struct.unpack('b', struct.pack('B', a[i]))[0]
        return b

    def strByteArray(self, a):
        """
        Return a colon-separated string representation of a byte array
        :param a: array of unsigned bytes
        :return: string representation
        """
        return str.join(":", ("%02x" % i for i in a))

    def callback(self, rawPacket):
        try:
            self.tryCallback(rawPacket)
        except:
            exc = sys.exc_info()
            tid = threading.current_thread().ident
            print '[%d]%r %r' % (tid, exc[0], exc[1])
            tb = exc[2]
            while tb:
                print '[%d]%r %r' % (tid, tb.tb_frame.f_code, tb.tb_lineno)
                tb = tb.tb_next
    def tryCallback(self, rawPacket):
        """
        And this is the callback itself.  Everything that touches an ODL-specific
        data structure needs to go in here...above this layer it's all generic
        OpenFlow.

        :param rawPacket an instance of org.opendaylight.controller.sal.packet.RawPacket
        """
        # Find out where the packet came from (ingress port).  First find the node and connector
        # in the ODL/Java world.
        ingressConnector = rawPacket.getIncomingNodeConnector()
        ingressNode = ingressConnector.getNode()

        # Make sure this is an OpenFlow switch.  If not, ignore the packet.
        if ingressNode.getType() == Node.NodeIDType.OPENFLOW:

            # Need to get the ENOS/Python switch that corresponds to this ingressNode.
            switch = self.getSwitch(ingressNode.getID())

            # This part is harder.  Need to figure out the ENOS port from the
            # NodeConnector object.  We also have the ENOS switch.
            #
            # This is very difficult because ODL does not let us retrieve the name of
            # a node connector (the last argument that would be passed to
            # SwitchManager.getNodeConnector().  The ID of a node connector appears to
            # be a small integer X that corresponds to the "ethX" port name in ENOS
            # (and sY-ethX in mininet)
            portno = ingressConnector.getID()
            port = switch.props['ports'][portno]
            if self.debug and not self.dropLLDP:
                print "PACKET_IN from port %r in node %r" % (port, ingressNode)

            # Try to decode the packet.
            l2pkt = self.odlPacketHandler.decodeDataPacket(rawPacket)

            if l2pkt.__class__  == Ethernet:
                srcMac = MACAddress(l2pkt.getSourceMACAddress())
                destMac = MACAddress(l2pkt.getDestinationMACAddress())
                etherType = l2pkt.getEtherType() & 0xffff # convert to unsigned type
                vlanTag = 0
                if l2pkt.getPayload():
                    payload = l2pkt.getPayload()
                else:
                    payload = l2pkt.getRawPayload()

                # Possibly drop LLDP frames
                if self.dropLLDP:
                    if etherType == EtherTypes.LLDP.shortValue() & 0xffff:
                        return PacketResult.KEEP_PROCESSING
                # Strip off IEEE 802.1q VLAN and set VLAN if present
                if etherType == EtherTypes.VLANTAGGED.shortValue() & 0xffff:
                    # If we get here, then l2pkt.payload is an object of type
                    # org.opendaylight.controller.sal.packet.IEEE8021Q
                    vlanPacket = l2pkt.getPayload()
                    vlanTag = vlanPacket.getVid()
                    etherType = vlanPacket.getEtherType() & 0xffff # convert to unsigned
                    if vlanPacket.getPayload():
                        payload = vlanPacket.getPayload()
                    else:
                        payload = vlanPacket.getRawPayload()
                else:
                    return PacketResult.KEEP_PROCESSING
                packetIn = PacketInEvent(inPort = port,srcMac=srcMac,dstMac=destMac,vlan=vlanTag,payload=payload)
                packetIn.props['ethertype'] = etherType

                if self.debug:
                    print "  Ethernet frame " + srcMac.str() + " -> " + destMac.str() + " Ethertype " + "%04x" % etherType + " VLAN " + "%04x" % vlanTag
                self.dispatchPacketIn(packetIn)
                return PacketResult.KEEP_PROCESSING

            else:
                if self.debug:
                    print "  Unknown frame type"

                return PacketResult.IGNORED

        else:
            if self.debug:
                print "PACKET_IN from Non-OpenFlow Switch"
            return PacketResult.IGNORED
