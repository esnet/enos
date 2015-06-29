__author__ = 'lomax'
"""
    This package provides generic type and basic implementation of OpenFlow support. Note tha it currently
    does not provide any level of security, nor it is thread safe. This will have to be addressed in the future.
"""
from array import array

from common.utils import generateId
from common.api import Properties, Node

from mininet.mac import MACAddress
from common.utils import Logger

import binascii
import sys

debug = False
def setDebug(val):
    global debug
    debug = val

class Match(Properties):
    """
    This is the class defining an OpenFlow match. It is a wrapper of Properties.
    The base class defines the following key / values:

    Layer2:
        "in_port": Port ingress port on the swith
        "dl_src" : array('B') source MAC
        "dl_dst" : array('B') destination MAC
        "vlan"   : int VLAN

    Other layers are TBD

    """
    def __init__(self,name=None,props={}):
        Properties.__init__(self,name,props)

    def __str__(self):
        global debug
        if not debug:
            return self.name
        desc = "Match: "
        if 'in_port' in self.props:
            desc += " in_port= " + self.props['in_port'].name
        if 'dl_src' in self.props:
            desc += " dl_src= %s" % self.props['dl_src']
        if 'dl_dst' in self.props:
            desc += " dl_dst= %s" % self.props['dl_dst']
        if 'vlan' in self.props:
            desc += " vlan= " + str(self.props['vlan'])
        return desc

    def __repr__(self):
        return self.__str__()

class Action(Properties):
    """
    This class is the class defining an OpenFlow action. It is a wrapper of Properties.
    The base class defines the following key / values:

    Layer 2:
        "dl_src": array('B') rewrite the source MAC with the provided MAC
        "dl_dst": array('B') rewrite the destination MAC with the provided MAC
        "vlan": int rewrite the VLAN with the provided vlan
        "out_port": Port egress ports

    Other layers are TBD
    """
    def __init__(self,name=None,props={}):
        Properties.__init__(self,name,props)

    def __str__(self):
        global debug
        if not debug:
            return self.name
        desc = "action " + self.name
        if 'out_port' in self.props:
            desc += " out_port= " + self.props['out_port'].name
        if 'dl_src' in self.props:
            desc += " dl_src= %s" % self.props['dl_src']
        if 'dl_dst' in self.props:
            desc += " dl_dst= %s" % self.props['dl_dst']
        if 'vlan' in self.props:
            desc += " vlan= " + str(self.props['vlan'])
        desc += "\n"
        return desc

    def __repr__(self):
        return self.__str__()



class FlowMod(Properties):
    """
    This class uniquely represent a flow mod.
    """
    def __init__(self,scope,switch,match=None,name="",actions=[]):
        """
        :param scope: Scope owner
        :param switch: common.api.Node
        :param match: Match
        :param actions: Action
        """
        Properties.__init__(self,name)
        self.scope = scope
        self.scopeowner = scope.owner
        self.switch = switch
        self.actions = actions
        self.match = match
        self.id = generateId()

    def __str__(self):
        global debug
        if not debug:
            return self.name
        desc ="FlowMod: " + self.name
        desc += " \n\tid= " + str(self.id) + " scope= " + self.scope.name + " switch= " + self.switch.name
        desc += "\n\t" + str(self.match)
        desc += "\n\tActions:\n"
        for action in self.actions:
            desc += "\t\t" + str(action)
        desc += "\n"
        return desc

    def __repr__(self):
        return self.__str__()

class Scope(Properties):
    """
    This class is a Properties wrapper. The key/value pairs in the property is used to define the scope of control
    an application wishes to have on a given network element.
    """
    def __init__(self,name,switch,owner,props={}):
        """
        :param name: str human readable name of the scope
        :param switch: common.api.Node
        :param owner: ScopeController controller that owns this scope
        :param props: dict optional properties of the scope, such as ports, vlan, etc. See Layer2Scope for example.
        """
        Properties.__init__(self,name,props)
        self.owner = owner
        self.id = generateId()
        self.switch = switch

    def overlaps(self, scope):
        """
        Check if this scopes overlaps with the provided scope. It is expected that Scope implements will overwrite
         this method.
        :param scope: Scope
        :returns True if scopes overlap, False otherwise
        """
        return True

    def isValidFlowMod(self, flowMod):
        """
        Verifies if a flowMod is valid within the scope
        :param flowMod: FlowMod
        """
        return False

    def includes(self,port):
        """
        Returns True if the provided port is within the Scope. False otherwise
        :param port: Port
        :returns boolean
        """
        return False


    def __str__(self):
        desc = "Scope: " + self.name  + " id= " + str(self.id)
        if self.switch:
            desc += " switch= " + self.switch.name
        else:
            desc += " no switch"
        if self.owner:
            desc += " owner= " + str(self.owner)
        else:
            desc += " no owner"
        return desc

    def __repr__(self):
        return self.__str__()



class ScopeEvent(Properties):
    """
    This class define an event related to a scope sent by the controller to the application. Scope implementation
    are responsible for implementing ScopeEvent as well. A ScopeEvent is a Properties, i.e. a dict of objects.
    For instance, an OpenFlow event could countain a key "packet-in" matching an object containing the relevant
    data. Implementing scopes freely define their own key/value pairs. All keys must be strings.

    This base class defines basic keys as well as their meaning. Value definition is let to the implementation.
    However the semantic of the key must be followed. This allow the consumer of the
    event to understand what the event means without understand the actual details, or the opposite.

        "closed": the scope has closed. If there is no "error" key/value in the event, the scope is gracefully closed.
        "error": the event is the result of an error that affected the scope.
        "changed": something has changed in the scope.
    """
    def __init__(self,name,scope,props={}):
        """
        :param name: str  human readable name of the event
        :param scope: Scope scope that is generating the event
        :param props: properties of the event
        """
        Properties.__init__(self,name,props={})
        self.id = generateId()

class PacketInEvent(ScopeEvent):
    """
    This class defines a PACKET_IN event. It adds the following key / value's to the ScopeEvent

        "in_port": str ingress port
        "payload": opaque type, payload of the packet (Ethernet payload, minus Ethernet and 802.1q headers)
    Layer 2
        "dl_src": str source MAC
        "dl_dst": str destination MAC
        "vlan" ": int VLAN

    Although the payload is an opaque object, it is (in the common case) an object of a subclass of
    org.opendaylight.controller.sal.packet.Packet or (if the higher layers cannot be parsed) an array
    of unsigned bytes.

     Other layers are TBD
    """

    def __init__(self,inPort=None,srcMac=None,dstMac=None,vlan=0,payload=None,name=""):
        Properties.__init__(self,name)
        self.props['in_port'] = inPort
        self.props['dl_src'] = srcMac
        self.props['dl_dst'] = dstMac
        self.props['vlan'] = vlan
        if payload:
            self.props['payload'] = payload

    def __str__(self):
        global debug
        if not debug:
            return self.name
        desc = "PacketIn: " + self.name + "\n"
        desc += "\tin_port:" + str(self.props['in_port']) + "\n"
        desc += "\tdl_src: " + str(self.props['dl_src']) + "\n"
        desc += "\tdl_dst: " + str(self.props['dl_dst']) + "\n"
        if 'vlan' in self.props:
            desc += "\tvlan: " + str(self.props['vlan']) + "\n"
        if 'payload' in self.props:
            desc += "\tpayload: " + str(self.props['payload'])
        desc += "\n"
        return desc

    def __repr__(self):
        return 'PacketInEvent(inPort=%r,srcMac=%r,dstMac=%r,vlan=%r)' % (self.props['in_port'], self.props['dl_src'], self.props['dl_dst'], self.props['vlan'])


class PacketOut(Properties):
    """
    This class implements a packet out.
    """
    def __init__(self, scope, port, dl_src, dl_dst, etherType, vlan, payload, name=""):
        """
        :param scope: Scope
        :param port: Port
        :param vlan: int
        :param payload: opaque type, contents starting from the Ethernet frame payload (not including Ethernet or 802.1q headers)

        In reality, payload is either an array of unsigned bytes or a subclass of
        org.opendaylight.controller.sal.packet.Packet.
        """
        super(PacketOut, self).__init__(name)
        self.scope = scope
        self.port = port
        self.dl_src = dl_src
        self.dl_dst = dl_dst
        self.etherType = etherType
        self.vlan = vlan
        self.payload = payload

    def __str__(self):
        global debug
        if not debug:
            return self.name
        desc = "PacketOut: " + self.name
        if self.port:
            desc += " port= " + self.port.name
            if 'switch' in self.port.props:
                desc += " switch= " + self.port.props['switch'].name
        if self.vlan:
            desc += " vlan= " + str(self.vlan)
        if self.scope:
            desc += "\n\tScope: " + str(self.scope) + "\n"

        if self.payload:
            desc += "\tPayload:\n\t\t"
        if isinstance(self.payload, array):
            desc += binascii.hexlify(self.payload)
        else:
            desc += str(self.payload.__class__)
        desc += "\n"
        return desc

    def __repr__(self):
        return 'PacketOut(scope=%r,port=%r,src=%r,dst=%r,etherType=%r,vlan=%r)' % (self.scope, self.port, self.dl_src, self.dl_dst, self.etherType, self.vlan)

class ScopeOwner(Properties):
    """
    This class must be extended by any application that controls a scope.
    """
    def __init__(self,name="",props={}):
        Properties.__init__(self,name,props)
        self.controller = None # The controller will set it ip

    def eventListener(self,event):
        """
        The implementation of this class is expected to overwrite this method if it desires
        to receive events from the controller such as PACKET_IN
        :param event: ScopeEvent
        """
    def __str__(self):
        return self.name

    def __repr__(self):
        return self.__str__()

class L2SwitchScope(Scope):
    """
    This class is the base class of any Scope that defines a layer 2 switch
    """
    def __init__(self,name,switch,owner,props={},endpoints={}):
        """
        Creates a Layer2Scope. The optional endpoint parameter is a list that contains tuples. Tuples are expected
        to be (port,vlans), where port is a string and vlans is a list of integers. The following are valid examples:
            ("eth10",[12]) port eth10, VLAN 12
            ("eth10",[])  the whole eth10 port (any VLAN)
            ("eth10",[1,2,10]) VLAN 1, 2 and 10 on port eth10
        If no endpoint is provided, then the scope represents all VLAN on all ports
        """
        Scope.__init__(self,name,switch,owner,props)
        self.props['endpoints'] = endpoints # ['portname'] = [vlans]

    def __str__(self):
        global debug
        if not debug:
            return self.name
        desc = "Scope " + self.name + " switch= " + self.switch.name
        desc += "\n\tEndpoints:"
        for (portname, vlans) in self.props['endpoints'].items():
            desc += "\n\t\t" + portname + " vlans= "
            for vlan in vlans:
                desc += str(vlan)
        desc += "\n"
        return desc

    def __repr__(self):
        return self.__str__()

    def includes(self,packetIn):
        name = packetIn.props['in_port'].name
        vlan = packetIn.props['vlan']
        if not name in self.props['endpoints']:
            return False
        vlans = self.props['endpoints'][name]
        if not vlans or vlan in vlans:
            return True
        return False

    def overlaps(self, scope):
        endpoints1 = self.props['endpoints']
        if not 'endpoints' in scope.props:
            # not a L2SwitchScope
            print "No endpoints"
            return False
        endpoints2 = scope.props['endpoints']
        # If not the same switch, they don't overlap
        if self.switch != scope.switch:
            return False
        # If either set of endpoints is empty, they trivially overlap
        if len(endpoints1) == 0 or len(endpoints2) == 0:
            return True
        for (port, vlans1) in endpoints1.items():
            if not port in endpoints2:
                continue
            vlans2 = endpoints2[port]
            if not vlans1 or not vlans2:
                return True
            if set(vlans1).intersection(vlans2):
                return True
        return False

    def isValidPacketOut(self,packet):
        endpoints = self.props['endpoints']
        if packet.port.name in endpoints:
            vlans = endpoints[packet.port.name]
            return not vlans or packet.vlan in vlans
        print  packet,"is not within this scope:",self
        return False

    def isValidFlowMod(self, flowMod):
        """
        Check to see if a flow is contained within this scope
        """
        flowModMatch = flowMod.match
        flowModActions = flowMod.actions
        flowModSwitch = flowMod.switch

        flowModEndpoints = self.props['endpoints']
        # See if it's for the same switch.  If not, it can't be valid.
        if flowModSwitch != self.switch:
            print flowMod,"flowmod is for a different switch than this scope's switch",self.switch,"was",flowMod.switch
            return False

        # If no endpoints, then the scope includes all VLANs and ports and the flow must be valid.
        if len(flowModEndpoints) == 0:
            return True

        """"
        This code is currently disabled: SDNPropsRenderer is simplified and currently needs to have a generic
        flow mod, i.e, without any other match than dl_dst. This will have to be fixed

        if not 'in_port' in match.props:
            # This controller rejects matches that do not include an in_port"
            print flowMod,"does not include an in_port in the macth. Not supported."
            return False

        in_port = match.props['in_port'].name
        in_vlan = match.props['vlan']
        valid = False
        # checks match
        for endpoint in endpoints:
            port = endpoint[0]
            if port != in_port:
                continue
            vlans = endpoint[1]
            for vlan in vlans:
                if vlan == in_vlan:
                    # authorized vlan
                    valid = True
                    break
        if not valid:
            print flowMod,"contains at least one match in_port/vlan that is not contained in this scope:",self
            return False
        """""

        # check actions
        for action in flowModActions:
            out_port = action.props['out_port'].name
            out_vlan = action.get('vlan')
            valid = False
            for (port, vlans) in flowModEndpoints.items():
                if port != out_port:
                    continue
                if vlans and out_vlan and not out_vlan in vlans:
                    print flowMod,"VLAN is not included in this scope",self
                    return False
                else:
                    valid = True
                    break
            if not valid:
                print flowMod,"contains at least one action out_port/vlan that is not contained in this scope:",self
                return False
        return True

    def addEndpoint(self, port, vlans):
        if not port.name in self.props['endpoints']:
            self.props['endpoints'][port.name] = []
        self.props['endpoints'][port.name].extend(vlans)
        port.props['enosNode'].props['controller'].addScopeIndex(self, port, vlans)

class OpenFlowSwitch(Node):
    """
    This class represents an OpenFlowSwitch. It contains the list of flowmods that is set on the switch.
    """
    def __init__(self, name, dpid, controller = None, builder = None, props = {}):
        """
        Creates an OpenFlowSwitch instance.
        :param controller (Controller) of this switch
        :return:
        """
        Node.__init__(self, name, builder, props)
        self.dpid = dpid
        self.controller = controller
        self.props['controller'] = controller
        self.flowMods = {}
        self.scopes = {}


class Controller(object):
    """
    This class defined the generic API of the client of an OpenFlow controller.
    API for packet in and out not yet defined.
    """
    def __init__(self):
        return

    def requestControl(self,scope):
        """
        Request the control over the specified scope.
        :param scope:
        :return: True up success, False otherwise
        """
        return False

    def addFlowMod(self, flowMod):
        print "not implemented"

    def delFlowMod(self, flowMod):
        print "not implemented"

    def send(selfs,packet):
        """
        :param packet: PacketOut
        """


class SimpleController(Controller):
    """
    This class implements a simple controller. It implements some basic controller function but does not
    implement the actual interaction with the switch or controller.
    IMPORTANT: this currentl implementation relies on having static state. In otherwords, only one
    controller extending SimpleController may run at the same time. This limitation should be fixed later.
    """

    scopes = None
    forbiddenScopes = None
    switches = None
    id = None
    instance = None

    def __init__(self):
        super(SimpleController,self).__init__()
        if not SimpleController.id:
            # First time SimpleController is instanciated. Initialize globals
            SimpleController.scopes ={}
            SimpleController.forbiddenScopes = {}
            SimpleController.switches = {}
            SimpleController.id = generateId()
            SimpleController.instance = self
            self.scopeIndex = {}

    def addSwitch(self,switch):
        """
        Adds a switch to the list of switches this controller can manage
        :param switch: OpenFlowSwitch
        :return:
        """
        SimpleController.switches[switch.dpid] = switch

    def removeSwitch(self,switch):
        self.switches.pop(switch)
        # Remove all flow mods on that switch
        SimpleController.scopes = {}
        for flowMod in switch.flowMods():
            SimpleController.delFlowMod(flowMod)

    def addScope(self, scope):
        """
        Adds the scopes to the authorized set of scopes. In order to be accepted, a scope must not overlap
        with any of the forbiden scopes, and not overlap with any of existing, authorized, scopes.
        :param scope:
        :return:
        """
        for (x,s) in SimpleController.forbiddenScopes.items():
            if s.overlaps(scope):
                print "addScope error:  ", scope
                print "Overlaps with a forbidden port/vlan:"
                print s
                return False
        for (x,s) in SimpleController.scopes.items():
            if s.overlaps(scope):
                print "addScope error:  ", scope
                print "Overlaps with a port/vlan that is already in another scope:"
                print s
                return False
        if scope.id in SimpleController.scopes.keys():
            print "addScope error:  ", scope
            print "this scope has been already added"
            return False
        SimpleController.scopes[scope.id] = scope
        return True
    def removeScope(self,scope):
        SimpleController.scopes.pop(scope)
        for (portname, vlans) in scope.props['endpoints']:
            del SimpleController.scopesIndex[portname]

    def addForbiddenScope(self,scope):
        """
        Adds a scope that is forbidden to authorize any request
        :param scope:
        :return:
        """
        print "not implemented yet"

    def removeForbiddenScope(self,scope):
        """
        Adds a scope that is forbidden scope
        :param scope:
        :return:
        """
        print "not implemented yet"

    def isFlowModValid(self, flowMod):
        scopeId = flowMod.scope.id
        if not scopeId in SimpleController.scopes:
            print "Provided scope is not authorized"
            print "Authorized scopes are"
            for sid in SimpleController.scopes:
                print "\t" + str(sid)
            return False
        scope = SimpleController.scopes[scopeId]
        return scope.isValidFlowMod(flowMod)

    def isPacketOutValid(self,packet):
        scopeId = packet.scope.id
        if not scopeId in SimpleController.scopes:
            print "PacketOut",packet,"scope is not authorized"
            return False
        scope = SimpleController.scopes[scopeId]
        return scope.isValidPacketOut(packet)

    def addFlowMod(self, flowMod):
        """
        Implementation of SimpleController must implement this method
        :param flowMod:
        :return:
        """
        return False

    def delFlowMod(self, flowMod):
        """
        Implementation of SimpleController must implement this method
        :param flowMod:
        :return:
        """
        return False

    def send(self,packet):
        """
        Implementation of SimpleController must implement this method
        :param self:
        :param packet:
        :return:
        """
        return False

    def getScope(self, port, vlan):
        key = '%s.%d' % (port.name, vlan)
        if not key in self.scopeIndex:
            # try without vlan
            key = port.name
        if not key in self.scopeIndex:
            Logger().error('%s.%d not found in %r.scopeIndex' % (port.name, vlan, self))
            return None
        return self.scopeIndex[key]

    def addScopeIndex(self, scope, port, vlans = []):
        if not vlans:
            self.scopeIndex['%s' % port.name] = scope
        else:
            for vlan in vlans:
                self.scopeIndex['%s.%d' % (port.name, vlan)] = scope

    def dispatchPacketIn(self,packetIn):
        """
        :param packetIn:  PacketIn
        :return:
        """
        port = packetIn.props['in_port'].props['enosPort']
        vlan = packetIn.props['vlan']
        if vlan == 0:
            Logger().debug('vlan == 0 not interested...')
            return
        Logger().info('recv packet %r' % packetIn)
        scope = self.getScope(port, vlan)
        if scope and scope.switch == port.get('enosNode') and scope.includes(packetIn):
            scope.owner.eventListener(packetIn)
        else:
            Logger().error('No scope for %r', packetIn)

    @staticmethod
    def makeL2FlowMod(scope, switch, inPort, inVlan, outPort, outVlan):
        """
        Convenience method to make a flow entry for Layer 2 / VLAN translation.
        Note that the returned flow entry only handles one direction of
        translation / forwarding; for use in a bidirectional circuit (i.e.
        OSCARS semantics), two of these are required.
        :param switch: the switch to which this flow entry applies
        :param inPort: input port
        :param inVlan: input VLAN tag
        :param outPort: output port
        :param outVlan: output VLAN tag
        :return: FlowMod
        """
        match = Match()
        match.props['in_port'] = inPort
        match.props['vlan'] = inVlan

        actions = Action()
        actions.props['vlan'] = outVlan
        actions.props['out_port'] = { outPort }

        flow = FlowMod(scope=scope, switch=switch, match=match, actions=actions)
        return flow







