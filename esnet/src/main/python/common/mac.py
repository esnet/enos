import struct
import jarray
import array
import copy
from common.mac import MACAddress as ParentMACAddress
class MACAddress(ParentMACAddress):
    def __init__(self, v = [0]):
        super(MACAddress, self).__init__(v)
    def jarray(self):
        result = jarray.zeros(MACAddress.size, 'b')
        for i in range(len(result)):
            result[i] = struct.unpack('b', struct.pack('B', self.data[i]))[0]
        return result
    @staticmethod
    def createBroadcast(vid = 0xFFFFFF):
        mac = MACAddress([255]*6)
        mac.setVid(vid)
        return mac
