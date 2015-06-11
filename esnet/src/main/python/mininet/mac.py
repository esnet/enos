import struct

class MACAddress:
    broadcast = MACAddress([0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF])
    def __init__(self, v = [0]):
        self.data = [0] * 6
        for i in range(min(len(v), 6)):
            self.data[i] = struct.unpack('B', struct.pack('B', v[i]))[0]
    def str(self):
        return str.join(":", ("%02X" % i for i in self.data))
    def __str__(self):
        return self.str()
    def __eq__(self, other):
        return self.data == other.data
    def __ne__(self, other):
        return self.data != other.data

