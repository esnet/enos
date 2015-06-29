import struct
import array
import copy

class MACAddress(object):
    size = 6
    def __init__(self, v = [0]):
        """
        self.data = a list of 6 numbers
        :param v: constructor argument
        """
        if isinstance(v, MACAddress):
            self.data = copy.copy(v.data)
            return
        if isinstance(v, str):
            # format: 01:02:03:04:05:06
            self.data = map(lambda x : int(x, 16), v.split(":"))
            return
        if isinstance(v, int):
            # 1 => 00:00:00:00:00:01 
            self.data = []
            for i in range(MACAddress.size):
                self.data.append(v & 0xFF)
                v >>= 8
            self.data.reverse()
            return
        # v could be list, array, jarray, ... which support operator[]
        self.data = [0] * MACAddress.size
        for i in range(min(len(v), MACAddress.size)):
            self.data[i] = struct.unpack('B', struct.pack('B', v[i]))[0]
    def isBroadcast(self):
        return self.data[0] == 0xFF and self.getHid() == 0xFFFF
    def getVid(self):
        return (self.data[1] << 16) + (self.data[2] << 8) + self.data[3]
    def setVid(self, vid):
        self.data[1] = vid >> 16
        self.data[2] = (vid >> 8) & 0xFF
        self.data[3] = vid & 0xFF
    def getHid(self):
        return (self.data[4] << 8) + self.data[5]
    def setHid(self, hid):
        self.data[4] = hid >> 8
        self.data[5] = hid & 0xFF
    @staticmethod
    def createBroadcast(vid = 0xFFFFFF):
        mac = MACAddress([255]*6)
        mac.setVid(vid)
        return mac
    def array(self):
        return array.array('b', struct.pack('%sB' % MACAddress.size, *self.data))
    def str(self):
        return str.join(":", ("%02X" % i for i in self.data))
    def __repr__(self):
        return self.str()
    def __str__(self):
        return self.str()
    def __eq__(self, other):
        return self.data == other.data
    def __ne__(self, other):
        return self.data != other.data