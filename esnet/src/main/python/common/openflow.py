__author__ = 'lomax'
"""
    This package provides generic type and basic implementation of OpenFlow support. Note tha it currently
    does not provide any level of security, nor it is thread safe. This will have to be addressed in the future.
"""
from commom.utils import generateId
from common.api import Properties


class FlowMod:
    """
    This class uniquely represent a flow mod.
    """
    def __init__(self,switch,matches,actions):
        self.switch =  switch
        self.matches = matches
        self.actions = actions
        self.id = generateId()


class ScopeEvent(Properties):
    """
    This class define an event related to a scope sent by the controller to the application
    """
    def __init__(self,name,scope):
        """
        :param name: str  human readable name of the event
        :param scope: Scope scope that is generating the event
        :param props:
        """
        Properties.__init__(self,name)
        self.id = generateId()

class ScopeController():
    """
    This class must be extended by any application that controls a scope.
    """
    def __init__(self):
        self.controller = None # The controller will set it ip

    def eventListener(self,event):
        """
        The implementation of this class is expected to overwrite this method if it desires
        to receive events from the controller such as PACKET_IN
        :param event: ScopeEvent
        """


class Scope(Properties):
    """
    This class is a Properties wrapper. The key/value pairs in the property is used to define the scope of control
    an application wishes to have on a given network element.
    """
    def __init__(self,name,dpid,props={}):
        Properties.__init__(self,name,props)
        self.props['dpid'] = dpid

class Layer2Scope(Scope):
    def __init__(self,name,dpid,port,vlan):
        Properties.__init__(self,name)
        self.props['port'] = port
        self.props['vlan'] = vlan



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
        self.scopes = {}




class Controller:
    """
    This class defined the generic API of the client of an OpenFlow controller.
    API for packet in and out not yet defined.
    """
    def requestControl(self,scope,listener=None):
        """
        Request the control over the specified scope.
        :param scope:
        :param listener: ScopeListener
        :return: True up success, False otherwise
        """
        return False

    def addFlowMod(self, flowMod):
        print "not implemented"

    def delFlowMod(self, flowMod):
        print "not implemented"


class SimpleController(Controller):
    """
    This class implements a simple controller. It implements some basic controller function but does not
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        """
        Implements a singleton
        """
        if not cls._instance:
            cls._instance = super(SimpleController, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        self.scopes = {}
        self.blackListedScopes = {}
        self.switches = {}

    def addSwitch(self,switch):
        """
        Adds a switch to the list of switches this controller can manage
        :param switch: OpenFlowSwitch
        :return:
        """
        self.switches[switch.dpid] = switch

    def removeSwitch(self,switch):
        self.switches.pop(switch)








