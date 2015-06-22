import struct
import array
import binascii
"""
this python script will be invoked in the generic python (mininet) instead of jython (netshell)
"""
def int2dpid(dpid):
    return binascii.hexlify(array.array('B',struct.unpack("8B", struct.pack("!Q", dpid))))

class MininetNode:
    def __init__(self, name, mininetName):
        self.name = name
        self.mininetName = mininetName
        self.ports = {}
    def stitch(self, port1, port2):
        pass
    def getPort(self, num=None):
        if not num:
            num = len(self.ports) + 1
        if not num in self.ports:
            self.ports[num] = MininetPort(None, num, self)
        return self.ports[num]

class MininetSwitch(MininetNode):
    dpid = 1
    def __init__(self, name, mininetName):
        MininetNode.__init__(self, name, mininetName)
        self.dpid = int2dpid(MininetSwitch.dpid)
        MininetSwitch.dpid += 1

class MininetSiteRouter(MininetSwitch):
    def setWanPort(self, port):
        pass
    def addVlan(self, lanVlan, wanVlan):
        pass
class MininetCoreRouter(MininetSwitch):
    pass
class MininetHwSwitch(MininetSwitch):
    def setSitePort(self, port):
        pass
    def addPopPort(self, pop, port):
        pass
    def addVPN(self, vlan, vpn):
        pass

class MininetSDNPop:
    def __init__(self, name, corename, hwname, mininetCoreName, mininetHwName):
        self.name = name
        self.core = MininetCoreRouter(corename, mininetCoreName)
        self.hw = MininetHwSwitch(hwname, mininetHwName)

class MininetHost(MininetNode):
    def __init__(self, name, mininetName):
        MininetNode.__init__(self, name, mininetName)
        return

class MininetPort:
    def __init__(self, name, number, node):
        self.number = number
        self.node = node

class MininetLink:
    def __init__(self, node1, node2, name = None, portnum1 = None, portnum2 = None):
        port1 = node1.getPort(portnum1)
        port2 = node2.getPort(portnum2)
        self.endpoints = [port1, port2]
    def getPort(self, index):
        return self.endpoints[index]
    def addVlan(self, vlan):
        pass

class MininetVPN:
    def __init__(self, vid, pops):
        pass