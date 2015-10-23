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
import binascii
from layer2.common.mac import MACAddress
from layer2.common.utils import Logger

from layer2.common.openflow import SimpleController, PacketInEvent

from net.es.netshell.controller.core import Controller
from net.es.netshell.odlmdsal.impl import OdlMdsalImpl
from net.es.netshell.odlmdsal.impl import EthernetFrame
from org.opendaylight.yang.gen.v1.urn.opendaylight.flow.inventory.rev130819 import FlowCapableNode


class ODLClient(SimpleController, OdlMdsalImpl.Callback):
    """
    Class that is an interface to the ENOS OpenDaylight client.
    The real client functionality is the Controller
    class (in Java).
    :param topology layer2.testbed.topology.TestbedTopology
    """
    topology = None
    logger = Logger('ODLClient')

    def __init__(self, topology):
        """
        Note: topology might not be ready at this moment,
        so you are not allowed to access anything related to topology.builder here.
        However, you could do it later in method init(self).
        :param topology: TestbedTopology whose builder is not ready yet
        """
        self.__class__ = SimpleController
        SimpleController.__init__(self)
        self.__class__ = ODLClient

        self.odlController = Controller.getInstance()
        self.odlMdsalImpl = self.odlController.getOdlMdsalImpl()
        self.odlCorsaImpl = self.odlController.getOdlCorsaImpl()

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
            # DPIDs from the builder are arrays of 8 bytes...get those as a hex string
            if 'dpid' in switch.props:
                dpid = binascii.hexlify(switch.props['dpid'][-8:])
                index[dpid] = switch
        devices = self.odlController.getNetworkDevices()
        if devices:
            for odlSwitch in self.odlController.getNetworkDevices():
                nodeID = odlSwitch.getID()
                # Given the ID, strip off "openflow:", what's left is the DPID in decimal ASCII
                # Convert this to a hex string.
                dpidDecimal = long(nodeID.replace("openflow:", ""))
                dpid = '%08x' % dpidDecimal

                if not dpid in index:
                    ODLClient.logger.warning('an OdlSwitch with %r not found in topology' % dpid)
                    continue
                self.odlSwitchIndex[dpid] = odlSwitch
                self.switchIndex[nodeID] = index[dpid]
        self.odlMdsalImpl.setPacketInCallback(self)

    def getSwitch(self, nodeID):
        if not nodeID in self.switchIndex:
            ODLClient.logger.error('nodeID %r not found in %r.switchIndex' % (nodeID, self))
            return None
        return self.switchIndex[nodeID]

    def startCallback(self):
        self.odlMdsalImpl.setPacketInCallback(self)

    def stopCallback(self):
        self.odlMdsalImpl.setPacketInCallback(None)

    def findODLSwitch(self, switch):
        """
        Given the switch in the ENOS (Python) world, find the switch in the
        ODL (Java) world.
        :param switch: common.api.Node
        :return: org.opendaylight.controller.switchmanager.Switch (None if not found)
        """
        dpid = binascii.hexlify(switch.props['dpid'][-8:])
        if not dpid in self.odlSwitchIndex:
            ODLClient.logger.warning('could not found dpid %r in %r.findODLSwitch' % (dpid, self))
            return None
        return self.odlSwitchIndex[dpid]

    def getNodeConn(self, odlNode, switch, port):
        # Retrieve the name of the switch. We then need to look this up in the ODL SwitchManager,
        # but that requires a pointer to the ODL Node.
        portName = port.name
        nodeconn = self.odlController.getNodeConnector(odlNode, portName)
        if not nodeconn:
            ODLClient.logger.warning('%s not found at %r' % (portName, odlNode))
            return None
        return nodeconn

    def installL2ForwardingRule(self, translation):
        """
        Push a L2 forwarding rule to a switch
        :param translation: net.es.netshell.controller.core.Controller.L2Translation
        :return: FlowRef
        """
        return self.odlController.installL2ForwardingRule(translation)

    def installL2ControllerRule(self, translation):
        """
        Install a "send to controller" rule for an L2 translation's match
        :param translation: net.es.netshell.controller.core.Controller.L2Translation
        :return: FlowRef
        """
        return self.odlController.installL2ControllerRule(translation)

    def deleteFlow(self, dpid, flowRef):
        """
        Delete a flow
        :param dpid: DPID of the switch (array of bytes)
        :param flowRef: FlowRef
        :return: boolean indicating success
        """
        return self.odlController.deleteFlow(dpid, flowRef)

    def send(self, packet):

        """
        Send a packet via a PACKET_OUT OpenFlow message.  We use the PacketOut members
        and use net.es.netshell.odlmdsal.impl.EthernetFrame to help us put a VLAN
        header on the front

        :param packet: common.openflow.PacketOut
        :return:  True if successful, False if not
        """
        if self.isPacketOutValid(packet):
            # Get the switch (Node in the ODL world) and port (NodeConnector in the ODL world)
            sw = self.findODLSwitch(packet.scope.switch)
            dpid = packet.scope.switch.props['dpid'][-8:]
            if sw == None:
                print packet, "cannot be sent because the switch is not in inventory"
                return False
            portName = packet.port.name
            nodeconn = self.odlController.getNodeConnector(sw.getNode(), portName)
            if nodeconn == None:
                ODLClient.logger.warning('can not send %r because the port %s on %r is invalid' % (packet, portName, sw.getNode()))
                return False

            # Create the outgoing packet in ODL land.  The outgoing node connector must be set.
            frame = EthernetFrame()
            frame.setDstMac(self.javaByteArray(packet.dl_dst.data))
            frame.setSrcMac(self.javaByteArray(packet.dl_src.data))
            frame.setEtherType(packet.etherType)
            frame.setVid(packet.vlan)
            frame.setPayload(packet.payload)

            self.odlController.transmitDataPacket(dpid, portName, frame.toPacket())

            return True
        ODLClient.logger.warning("Packet %r is not valid" % packet)
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

    def callback(self, notification):
        """
        Receives PacketReceived notification via OdlMdsalImpl.onPacketReceived().
        Catch any errors that might be thrown by the "real" callback.
        :param notification: org.opendaylight.yang.gen.v1.urn.opendaylight.packet.service.rev130709.PacketReceived
        :return: none
        """
        try:
            self.tryCallback(notification)
        except:
            exc = sys.exc_info()
            ODLClient.logger.error("%r %r" % (exc[0], exc[1]))
            tb = exc[2]
            while tb:
                ODLClient.logger.error("%r %r" % (tb.tb_frame.f_code, tb.tb_lineno))
                tb = tb.tb_next

    def tryCallback(self, notification):

        """
        And this is the callback itself.  Everything that touches an ODL-specific
        data structure needs to go in here...above this layer it's all generic
        OpenFlow.

        :param notification org.opendaylight.yang.gen.v1.urn.opendaylight.packet.service.rev130709.PacketReceived
        """
        # Find out where the packet came from (ingress port).  First find the node and connector
        # in the ODL/Java world.
        nodeConnectorRef = notification.getIngress() # XXX need to turn this into a NodeConnector object
        ingressConnector = rawPacket.getIncomingNodeConnector()
        ingressNode = ingressConnector.getNode()

        # Make sure this is an OpenFlow switch.  If not, ignore the packet.
        if ingressNode.getAugmentation(FlowCapableNode) != None:

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

            # Try to decode the packet.  First get the payload bytes and parse them.
            l2pkt = notification.getPayload()
            ethernetFrame = EthernetFrame.packetToFrame(l2pkt);

            if ethernetFrame != None:

                srcMac = MACAddress(ethernetFrame.getSrcMac())
                destMac = MACAddress(ethernetFrame.getDstMac())
                etherType = ethernetFrame.getEtherType() & 0xffff # convert to unsigned type
                vlanTag = ethernetFrame.getVid()
                payload = ethernetFrame.getPayload()

                # Possibly drop LLDP frames
                if self.dropLLDP:
                    if etherType == net.es.netshell.odlmdsal.impl.EthernetFrame.ETHERTYPE_LLDP:
                        return

                packetIn = PacketInEvent(inPort = port, srcMac=srcMac, dstMac=destMac, vlan=vlanTag, payload=payload)
                packetIn.props['ethertype'] = etherType

                if self.debug:
                    print "  Ethernet frame " + srcMac.str() + " -> " + destMac.str() + " Ethertype " + "%04x" % etherType + " VLAN " + "%04x" % vlanTag
                self.dispatchPacketIn(packetIn)

            else:
                if self.debug:
                    print "  Unknown frame type"

        else:
            if self.debug:
                print "PACKET_IN from Non-OpenFlow Switch"
