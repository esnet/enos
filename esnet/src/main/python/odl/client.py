import struct
from java.util import LinkedList

from common.openflow import SimpleController
from common.utils import singleton

from org.opendaylight.controller.sal.core import Node

import net.es.netshell.odl.Controller

import org.opendaylight.controller.sal.match
import org.opendaylight.controller.sal.action
import org.opendaylight.controller.sal.flowprogrammer

class ODLClient(SimpleController):
    """
    Class that is an interface to the ENOS OpenDaylight client.
    The real client functionality is the net.es.netshell.odl.Controller
    class (in Java).
    """

    def __init__(self):
        self.__class__ = SimpleController
        #super(ODLClient,self).__init__()
        SimpleController.__init__(self)
        self.__class__ = ODLClient
        self.odlController = net.es.netshell.odl.Controller.getInstance()

    def makeODLFlowEntry(self, flowMod):
        """
        Given a FlowMod object, turn it into a Flow suitable for passing to ODL

        Encapsulates a bunch of common sense about the order in which flow actions
        should be applied.

        :param flowMod:
        :return:
        """

        # Compose match object                                                     `
        match = org.opendaylight.controller.sal.match.Match()
        if 'in_port' in flowMod.match.props:
            match.setField(org.opendaylight.controller.sal.match.MatchType.IN_PORT, flowMod.match.props['in_port'][3:])
        if 'dl_src' in flowMod.match.props:
            match.setField(org.opendaylight.controller.sal.match.MatchType.DL_SRC, flowMod.match.props['dl_src'])
        if 'dl_dst' in flowMod.match.props:
            match.setField(org.opendaylight.controller.sal.match.MatchType.DL_DST, flowMod.match.props['dl_dst'])
        if 'vlan' in flowMod.match.props:
            match.setField(org.opendaylight.controller.sal.match.MatchType.DL_VLAN, flowMod.match.props['vlan'])

        # Compose action.
        # We do the data-link and VLAN translations first.  Other types of
        # translations would happen here as well.  Then any action to forward
        # packets.
        actionList = LinkedList()

        if 'dl_dst' in flowMod.actions.props:
            actionList.add(org.opendaylight.controller.sal.actionSetDlDst(flowMod.actions.props['dl_dst']))
        if 'dl_src' in flowMod.actions.props:
            actionList.add(org.opendaylight.controller.sal.actionSetDlSrc(flowMod.actions.props['dl_src']))
        if 'vlan'in flowMod.actions.props:
            actionList.add(org.opendaylight.controller.sal.actionPopVlan())
            actionList.add(org.opendaylight.controller.sal.actionPushVlan(flowMod.actions.props['vlan']))
        if 'out_port' in flowMod.actions.props:
            val = flowMod.actions.props['out_port']
            if val != None:
                for p in val:
                    actionList.add(Output(p[3:]))

        # compose flow
        flow = org.opendaylight.controller.sal.flowprogrammer.Flow(match, actionList)

        return flow

    def addFlowMod(self, flowMod):
        """
        Implementation of addFlowMod for use with OpenDaylight.
        Uses the net.es.netshell.odl.Controller.
        :param flowMod:
        :return:
        """
        # check scope
        if self.isFlowModValid(flowMod):

            # Find switch
            # XXX I bet this operation is expensive.  Maybe we should think about putting in
            # a one-deep cache of the switch lookup.
            switches = self.odlController.getNetworkDevices()
            sw = None
            # Its seems that ODL returns 6 bytes DPID instead of 8.
            dpid = flowMod.switch.props['dpid'][-6:]
            for s in switches:
                # Find the switch that has the same DPID as the one we want to talk to.
                # Note that we also have the mininet switch name in flowMod.switch.props['mininetName']
                if s.dataLayerAddress == dpid: # Representation of DPID?
                    sw = s
                    break
            if sw == None:
                return False

            flow = self.makeODLFlowEntry(flowMod)
            # go to the controller
            self.odlController.addFlow(sw.node, flow)

            # get result
            return True
        return False




    def delFlowMod(self, flowMod):

        return False

# Creates an instance of ODLClient
instance = ODLClient()
def getODLClient():
    return instance

