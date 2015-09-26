#
# ENOS, Copyright (c) 2015, The Regents of the University of California,
# through Lawrence Berkeley National Laboratory (subject to receipt of any
# required approvals from the U.S. Dept. of Energy).  All rights reserved.
#
# If you have questions about your rights to use or distribute this software,
# please contact Berkeley Lab's Technology Transfer Department at TTD@lbl.gov.
#
# NOTICE.  This software is owned by the U.S. Department of Energy.  As such,
# the U.S. Government has been granted for itself and others acting on its
# behalf a paid-up, nonexclusive, irrevocable, worldwide license in the Software
# to reproduce, prepare derivative works, and perform publicly and display
# publicly.  Beginning five (5) years after the date permission to assert
# copyright is obtained from the U.S. Department of Energy, and subject to
# any subsequent five (5) year renewals, the U.S. Government is granted for
# itself and others acting on its behalf a paid-up, nonexclusive, irrevocable,
# worldwide license in the Software to reproduce, prepare derivative works,
# distribute copies to the public, perform publicly and display publicly, and
# to permit others to do so.
#
import struct
import array, jarray
import sys
import inspect
import binascii
import threading
from layer2.common.mac import MACAddress
from layer2.common.utils import Logger

from java.lang import Short
from java.lang import Long
from java.util import LinkedList
from java.nio import ByteBuffer

from layer2.common.openflow import SimpleController, PacketInEvent

from org.opendaylight.controller.sal.core import Node

from net.es.netshell.odl import Controller
from net.es.netshell.odl import PacketHandler

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

class ODLClient(SimpleController,PacketHandler.Callback):
    """
    Class that is an interface to the ENOS OpenDaylight client.
    The real client functionality is the Controller
    class (in Java).
    :param topology layer2.testbed.topology.TestbedTopology
    """
    topology = None
    logger = Logger('ODLClient')

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
        self.odlController = Controller.getInstance()
        self.odlPacketHandler = PacketHandler.getInstance()
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
        for switch in ODLClient.topology.builder.switchIndex.values():
            if 'dpid' in switch.props:
                dpid = binascii.hexlify(switch.props['dpid'][-6:])
                index[dpid] = switch
        for odlSwitch in self.odlController.getNetworkDevices():
            nodeID = odlSwitch.getNode().getID()
            dpid = binascii.hexlify(odlSwitch.getDataLayerAddress())
            if not dpid in index:
                ODLClient.logger.warning('an OdlSwitch with %r not found in topology' % dpid)
                continue
            self.odlSwitchIndex[dpid] = odlSwitch
            self.switchIndex[nodeID] = index[dpid]
        self.odlPacketHandler.setPacketInCallback(self)
    def getSwitch(self, nodeID):
        if not nodeID in self.switchIndex:
            ODLClient.logger.error('nodeID %r not found in %r.switchIndex' % (nodeID, self))
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
            ODLClient.logger.warning('could not found dpid %r in %r.findODLSwitch' % (dpid, self))
            return None
        return self.odlSwitchIndex[dpid]

    def getNodeConn(self, odlNode, switch, port):
        # Retrieve the name of the switch. We then need to look this up in the ODL SwitchManager,
        # but that requires a pointer to the ODL Node.
        portName =  port.name
        nodeconn = self.odlController.getNodeConnector(odlNode, portName)
        if not nodeconn:
            ODLClient.logger.warning('%s not found at %r' % (portName, odlNode))
            return None
        return nodeconn

    def makeODLFlowEntry(self, flowMod, odlNode):
        """
        Given a FlowMod object, turn it into a Flow suitable for passing to ODL.

        Encapsulates a bunch of common sense about the order in which flow actions
        should be applied.

        :param flowMod: ENOS FlowMod
        :param odlNode: OpenDaylight Node object
        :return: False if error occurs
        """

        # Compose match object                                                     `
        match = Match()
        if 'in_port' in flowMod.match.props:
            # Compose the port name
            portName = flowMod.match.props['in_port'].name
            nodeconn = self.odlController.getNodeConnector(odlNode, portName)
            if not nodeconn:
                ODLClient.logger.warning('%s not found at %r' % (portName, odlNode))
                return False
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
        noOutPort = True
        for action in flowMod.actions:
            if 'dl_dst' in action.props:
                actionList.add(SetDlDst(self.javaByteArray(action.props['dl_dst'].data)))
            if 'dl_src' in action.props:
                actionList.add(SetDlSrc(self.javaByteArray(action.props['dl_src'].data)))
            if 'vlan' in action.props:
                actionList.add(SetVlanId(action.props['vlan']))
            if 'out_port' in action.props:
                p = action.props['out_port']
                nodeconn = self.getNodeConn(odlNode, flowMod.switch, p)
                actionList.add(Output(nodeconn))
                noOutPort = False
            elif 'out_ports' in action.props:
                for p in action.props['out_ports']:
                    nodeconn = self.getNodeConn(odlNode, flowMod.switch, p)
                    actionList.add(Output(nodeconn))
                noOutPort = False
        if noOutPort:
            # This implementation requires all actions to contain a port_out
            ODLClient.logger.warning("no out_port or out_ports in flowMod")
            return None

        # compose flow
        flow = Flow(match, actionList)
        flow.priority = flowMod.props['priority']
        return flow

    def addFlowMod(self, flowMod):
        """
        Implementation of addFlowMod for use with OpenDaylight.
        Uses the Controller.
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
                ODLClient.logger.warning("Cannot push flowmond onto %r" % flowMod.switch)
                return False
            # go to the controller
            ODLClient.logger.info('addFlow %r' % flow)
            res = self.odlController.addFlow(sw.node, flow)
            return res.isSuccess()
        else:
            print 'flowMod %r is not valid' % flowMod
        return False
    def modifyFlowMod(self, oldFlowMod, newFlowMod):
        if self.isFlowModValid(newFlowMod):
            sw = self.findODLSwitch(flowMod.switch)
            # print "flowMod.switch of type ", str(type(flowMod.switch))
            if sw == None:
                print flowMod,"cannot be pushed because the switch is not in inventory"
                return False
            newFlow = self.makeODLFlowEntry(flowMod=newFlowMod, odlNode=sw.node)
            if not newFlow:
                ODLClient.logger.warning("Cannot push flowmond onto %r" % newFlowMod.switch)
                return False
            # go to the controller
            ODLClient.logger.info('addFlow %r' % flow)
            res = self.odlController.modifyFlow(sw.node, oldFlow, newFlow)
            return res.isSuccess()
        else:
            print 'flowMod %r is not valid' % newFlowMod
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
            portName = packet.port.name
            nodeconn = self.odlController.getNodeConnector(sw.getNode(), portName)
            if nodeconn == None:
                ODLClient.logger.warning('can not send %r because the port %s on %r is invalid' % (packet, portName, sw.getNode()))
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
            ODLClient.logger.info("send %r@%r" %(packet, nodeconn))
            self.odlPacketHandler.transmitDataPacket(rp)
            return True
        ODLClient.logger.warning("Packet %r is not valid" % packet)
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
            ODLClient.logger.info('del %r' % flow)
            success = self.odlController.removeFlow(sw.node, flow)
            return success.isSuccess()
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
            ODLClient.logger.error("%r %r" % (exc[0], exc[1]))
            tb = exc[2]
            while tb:
                ODLClient.logger.error("%r %r" % (tb.tb_frame.f_code, tb.tb_lineno))
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
            # SwitchManager.getNodeConnector().
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
