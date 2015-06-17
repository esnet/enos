import struct
import jarray
import array

class MACAddress:
    broadcast = None
    size = 6
    def __init__(self, v = [0]):
        if isinstance(v, str):
            self.data = map(lambda x : int(x, 16), v.split(":"))
            return
        self.data = [0] * MACAddress.size
        for i in range(min(len(v), MACAddress.size)):
            self.data[i] = struct.unpack('B', struct.pack('B', v[i]))[0]
    def array(self):
        return array.array('b', struct.pack('%sB' % MACAddress.size, *self.data))
    def jarray(self):
        result = jarray.zeros(MACAddress.size, 'b')
        for i in range(len(result)):
            result[i] = struct.unpack('b', struct.pack('B', self.data[i]))[0]
        return result
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
MACAddress.broadcast = MACAddress([0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF])

