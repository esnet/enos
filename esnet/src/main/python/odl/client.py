from java.util import LinkedList

from common.openflow import SimpleController
from common.utils import singleton

from org.opendaylight.controller.sal.core import Node

import net.es.netshell.odl.Controller

from org.opendaylight.controller.sal.match import Match
from org.opendaylight.controller.sal.match import MatchType

from org.opendaylight.controller.sal.action import SetDlDst
from org.opendaylight.controller.sal.action import SetDlSrc
from org.opendaylight.controller.sal.action import PopVlan
from org.opendaylight.controller.sal.action import PushVlan
from org.opendaylight.controller.sal.action import Output

from org.opendaylight.controller.sal.flowprogrammer import Flow

@singleton
class ODLClient(SimpleController):
    """
    Class that is an interface to the ENOS OpenDaylight client.
    The real client functionality is the net.es.netshell.odl.Controller
    class (in Java).
    """
    def __init__(self):
        #SimpleController.__init__(self)
        self.odlController = net.es.netshell.odl.Controller.getInstance()

    def makeODLFlowEntry(self, flowMod):
        """
        Given a FlowMod object, turn it into a Flow suitable for passing to ODL

        Encapsulates a bunch of common sense about the order in which flow actions
        should be applied.

        :param flowMod:
        :return:
        """

        # Compose match object
        match = org.opendaylight.controller.sal.match.Match()

        val = flowMod.match.props['in_port']
        if val != None:
            match.setField(MatchType.IN_PORT, val[3:])
        val = flowMod.match.props['dl_src']
        if val != None:
            match.setField(MatchType.DL_SRC, val)
        val = flowMod.match.props['dl_dst']
        if val != None:
            match.setField(MatchType.DL_DST, val)
        val = flowMod.match.props['vlan']
        if val != None:
            match.setField(MatchType.DL_VLAN, val)

        # Compose action.
        # We do the data-link and VLAN translations first.  Other types of
        # translations would happen here as well.  Then any action to forward
        # packets.
        actionList = LinkedList()

        val = flowMod.actions.props['dl_dst']
        if val != None:
            actionList.add(SetDlDst(val))
        val = flowMod.actions.props['dl_src']
        if val != None:
            actionList.add(SetDlSrc(val))
        val = flowMod.actions.props['vlan']
        if val != None:
            actionList.add(PopVlan())
            actionList.add(PushVlan(val))
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
        if flowMod.scope.isValidFlowMod(flowMod):

            # Find switch
            # XXX I bet this operation is expensive.  Maybe we should think about putting in
            # a one-deep cache of the switch lookup.
            switches = self.odlController.getNetworkDevices()
            sw = None
            for s in switches:
                # Find the switch that has the same DPID as the one we want to talk to.
                # Note that we also have the mininet switch name in flowMod.switch.props['mininetName']
                if s.dataLayerAddress == flowMod.switch.props['dpid']: # Representation of DPID?
                    sw = s
                    break
            if sw == None:
                return False

            flow = self.makeODLFlowEntry(self, flowMod)

            # go to the controller
            self.odlController.addFlow(sw.node, flow)

            # get result
            return True

        return False

    def delFlowMod(self, flowMod):

        return False

