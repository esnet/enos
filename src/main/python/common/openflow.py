__author__ = 'lomax'
"""
    This package provides generic type and basic implementation of OpenFlow support. Note tha it currently
    does not provide any level of security, nor it is thread safe. This will have to be addressed in the future.
"""
from utils import generateId

class FlowMod:
    """
    This class uniquely represent a flow mod.
    """
    def __init__(self,matches,actions):
        self.matches = matches
        self.actions = actions
        self.id = generateId()


class OpenFlowSwitch:
    """
    This class represents an OpenFlowSwitch. It contains the list of flowmods that is set on the switch.
    """
    def __init__(self, controller):
        """
        Creates an OpenFlowSwitch instance.
        :param controller (Controller) of this switch
        :return:
        """
        self.controller = controller
        self.flowmods = {}

    def addFlowMod(self,flowMod):
        """
        Adds a FlowMod on this switch. Adds the "switch" dict and adds the "dpid" value into it.
        :param flowMod:
        :return: True if the flowmod was inserted,  False otherwise.
        """
        if 'switch' not in dir(flowMod):
            flowMod.switch = {}
        flowMod.switch['dpid'] = self.dpid
        self.flowmods[flowMod.id] = flowMod
        self.controller.addFlowMod(flowMod)

    def delFlowMod(self,flowMod):
        """
        Deletes the flowMod from the
        :param flowMod:
        :return:
        """
        self.flowmods.pop(flowMod.id)



class Controller:
    """
    This class defined the generic API of the client of an OpenFlow controller.
    API for packet in and out not yet defined.
    """
    def __init__(self,dpid):
        """
        All implementation of Controller must call this.
        :param dpid:
        :return:
        """
        self.dpid = dpid

    def addFlowMod(self, flowMod):
        print "not implemented"

    def delFlowMod(self, flowMod):
        print "not implemented"


