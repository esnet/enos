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
import layer2.testbed.dpid

from net.es.netshell.controller.core import Controller
from net.es.netshell.controller.core.Controller import L2Translation
from net.es.netshell.controller.core.Controller.L2Translation import L2TranslationOutput
from net.es.netshell.odlmdsal.impl import OdlMdsalImpl
from net.es.netshell.odlmdsal.impl import EthernetFrame
from org.opendaylight.yang.gen.v1.urn.opendaylight.inventory.rev130819.node import NodeConnector
from org.opendaylight.yang.gen.v1.urn.opendaylight.inventory.rev130819.node import NodeConnectorKey
from org.opendaylight.yang.gen.v1.urn.opendaylight.inventory.rev130819.nodes import Node
from org.opendaylight.yang.gen.v1.urn.opendaylight.inventory.rev130819.nodes import NodeKey
from org.opendaylight.yang.gen.v1.urn.opendaylight.flow.inventory.rev130819 import FlowCapableNode
from org.opendaylight.yang.gen.v1.urn.opendaylight.flow.inventory.rev130819 import FlowCapableNodeConnector

from org.opendaylight.yang.gen.v1.urn.ietf.params.xml.ns.yang.ietf.yang.types.rev100924 import MacAddress

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
            # e.g. "020100616f666101"
            if 'dpid' in switch.props:
                dpid = binascii.hexlify(switch.props['dpid'][-8:])
                index[dpid] = switch
        devices = self.odlController.getNetworkDevices()
        if devices:
            for odlSwitch in devices:
                nodeID = odlSwitch.getId()
                # Given the ID, strip off "openflow:", what's left is the DPID in decimal ASCII
                # Convert this to a hex string.
                dpidDecimal = long(nodeID.getValue().replace("openflow:", ""))
                dpid = '%016x' % dpidDecimal

                if not dpid in index:
                    ODLClient.logger.warning('an OdlSwitch with %r not found in topology' % dpid)
                    continue
                self.odlSwitchIndex[dpid] = odlSwitch
                self.switchIndex[nodeID.getValue()] = index[dpid]
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

    def makeL2Translation(self, flowMod):
        """
        From the input FlowMod object, create a L2Translation object.
        This doesn't work in the general case because a FlowMod is more expressive than
        L2Translation, but within the context of the multipoint VPN we should be able
        to do a translation.
        :param flowMod: layer2.common.openflow.FlowMod
        :return: net.es.netshell.controller.core.Controller.L2Translation
        """

        # Create a L2Translation object and fill in its fields
        l2t = L2Translation()
        l2t.dpid = self.javaByteArray(flowMod.switch.props['dpid'])
        l2t.priority = flowMod.props['priority']
        # l2t.c uses default value
        l2t.inPort = flowMod.match.props['in_port'].name
        l2t.vlan1 = flowMod.match.props['vlan']
        # convert from common.mac.MACAddress to
        # org.opendaylight.yang.gen.v1.urn.ietf.params.xml.ns.yang.ietf.yang.types.rev100924.MacAddress
        # MACAddress vs. MacAddress, what could possibly go wrong with this?
        l2t.dstMac1 = MacAddress(flowMod.match.props['dl_dst'].str())
        # There are some uses cases where we need to push a flow to the software
        # switch that has a match on dl_src.
        if 'dl_src' in flowMod.match.props and flowMod.match.props['dl_src'] != None:
            l2t.srcMac1 = MacAddress(flowMod.match.props['dl_src'].str())

        l2toutseq = []
        for action in flowMod.actions:
            l2tout = L2TranslationOutput()
            if 'out_port' in action.props:
                l2tout.outPort = action.props['out_port'].name
            if 'vlan' in action.props:
                l2tout.vlan = action.props['vlan']
            if 'dl_dst' in action.props:
                l2tout.dstMac = MacAddress(action.props['dl_dst'].str())
            # We appear not to have any circumstances that would set action.props['dl_src'],
            # even though there's support for this in the AD-SAL version of client.py.
            l2toutseq.append(l2tout)
        l2t.outputs = jarray.array(l2toutseq, L2TranslationOutput)

        # l2t.pcp uses default value
        # XXX l2t.queue?
        # XXX set meter appropriately...use all green for now.  This needs to take a parameter
        # from somewhere to appropriately set QOS
        l2t.meter = 5L

        return l2t

    def addFlowMod(self, flowMod):
        """
        Add a flow described by a FlowMod.
        This is is something of a hack because the FlowMod object is fairly low-level
        (OpenFlow specific) and we're converting to a higher-level object, i.e. a
        L2Translation, expected by installL2ForwardingRule.  As a side effect,
        saves the FlowRef object for the installed flow as a property in the FlowMod
        object, for use in delFlowMod.
        :param flowMod: layer2.common.openflow.FlowMod
        :return: True if successful, False if not
        """
        l2t = self.makeL2Translation(flowMod)
        self.installL2ForwardingRule(l2t)
        flowMod.props['flowRef'] = l2t.flowRef
        return True

    def delFlowMod(self, flowMod):
        """
        Delete a flow described by a FlowMod object.
        Also a bit of a hack...we get rid of a flow when given a FlowRef, passed in
        the FlowMod.
        :param flowMod: layer2.common.openflow.FlowMod
        :return: True if successful, False if not
        """

        # If there's no flowRef object, we can't do anything.
        if flowMod.props['flowRef'] == None:
            return False
        self.deleteFlow(flowMod.switch.props['dpid'], flowMod.props['flowRef'])

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

    def initQos(self, switch):
        """
        Initialize the per-switch QOS parameters on a switch
        These are tied pretty tightly to a specific QOS configuration for SC15.
        We need to eventually figure out a better way to do this.
        :param switch: ENOS node
        :return:
        """
        switchDpid = switch.props['dpid']
        (vendor, role, location, id) = layer2.testbed.dpid.decodeDPID(switchDpid)
        if vendor == layer2.testbed.dpid.Vendors.Corsa:

            odlSwitch = self.findODLSwitch(switch)

            # Don't bother saving the MeterRefs from these calls because we never
            # delete the meters.
            self.odlCorsaImpl.createGreenMeter(odlSwitch, 5L)
            self.odlCorsaImpl.createGreenMeter(odlSwitch, 4L)
            self.odlCorsaImpl.createGreenYellowMeter(odlSwitch, 3L, 500000L, 50000000L)

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
        # in the ODL/Java world (ingressNode and ingressNodeConnector)
        nodeConnectorRef = notification.getIngress() # XXX need to turn this into a NodeConnector object

        # String nodeId = ingress.getValue().firstIdentifierOf(Node.class).firstKeyOf(Node.class, NodeKey.class).getId().getValue();
        ingressNodeId = nodeConnectorRef.getValue().firstIdentifierOf(Node).firstKeyOf(Node, NodeKey).getId().getValue()
        switch = self.getSwitch(ingressNodeId) # ENOS switch
        ingressNode = self.findODLSwitch(switch) # ODL switch corresponding to it

        # String ncId = ncRef.getValue().firstIdentifierOf(NodeConnector.class).firstKeyOf(NodeConnector.class, NodeConnectorKey.class).getId().getValue();
        ingressNodeConnectorId = nodeConnectorRef.getValue().firstIdentifierOf(NodeConnector).firstKeyOf(NodeConnector, NodeConnectorKey).getId().getValue()

        # Make sure this is an OpenFlow switch.  If not, ignore the packet.
        if ingressNode.getAugmentation(FlowCapableNode) is not None:

            # This part is harder.  Need to figure out the ENOS port from the
            # NodeConnector object.  We also have the ENOS switch.
            # ingressNodeConnectorId is of the form u'openflow:72620962556436737:3',
            # but we need to get to an ENOS port from that (which has the form "eth13"
            # (for OVS) or "1" (for Corsa).  The ENOS port name for
            # NodeConnectorId can be gotten from the FlowCapableNodeConnector
            # augmentation for the NodeConnector.
            # We iterate over the Node's connectors to try to find the correct
            # NodeConnector...it's sort of the opposite of OdlMdsalImpl.getNodeConnector
            # (and this implies that we should probably make this into a Java function
            # someday.
            # XXX Would replacing this with something that just reads the NodeConnector
            # from the data store be more efficient?  It would avoid the loop, but by time
            # we get here we've already queried the data store for the Node anyway.
            ncs = self.odlMdsalImpl.getNodeConnectors(ingressNode)
            IngressNodeConnector = None
            portName = None
            for nc in ncs:
                if nc.getId().getValue() == ingressNodeConnectorId:
                    IngressNodeConnector = nc
                    fcnc = nc.getAugmentation(FlowCapableNodeConnector)
                    portName = fcnc.getName()
                    break

            # Complain if we can't figure out the ENOS port name
            if portName == None:
                ODLClient.logger.error("Can't determine port name for NodeConnector %r on node %r" % (ingressNodeConnectorId, ingressNodeId))
                return

            port = switch.props['ports'][portName]

            # Complain if we can't find the port, even though we have its name
            if port == None:
                ODLClient.logger.error("Can't find port %r on node %r" % (portName, ingressNodeId))
                return

            if self.debug and not self.dropLLDP:
                print "PACKET_IN from port %r in node %r" % (port, ingressNodeId)

            # Try to decode the packet.  First get the payload bytes and parse them.
            l2pkt = notification.getPayload()
            ethernetFrame = EthernetFrame.packetToFrame(l2pkt)

            if ethernetFrame != None:

                srcMac = MACAddress(ethernetFrame.getSrcMac())
                destMac = MACAddress(ethernetFrame.getDstMac())
                etherType = ethernetFrame.getEtherType() & 0xffff # convert to unsigned type
                vlanTag = ethernetFrame.getVid()
                payload = ethernetFrame.getPayload()

                # Possibly drop LLDP frames
                if self.dropLLDP:
                    if etherType == EthernetFrame.ETHERTYPE_LLDP:
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
