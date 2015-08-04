import random
from common.api import Properties
from common.mac import MACAddress
import threading

class MAT(Properties):
    VERSION = 1
    reserved = 0xFF00 - 1 # Hid after this value are reserved for multicast
    def __init__(self, vid):
        super(MAT, self).__init__(name='MAT[%d]' % vid)
        self.props['vid'] = vid
        self.props['hid'] = {} # [str(mac)] = hid
        self.props['mac'] = {} # [hid] = mac
        self.props['lock'] = threading.Lock()
        self.props['mac'][0xFFFF] = MACAddress("FF:FF:FF:FF:FF:FF")
        self.props['hid']['FF:FF:FF:FF:FF:FF'] = 0xFFFF
        # might support other multicast address in the vid
        # Note: self.props['mac'][0xFF02] = MACAddress("33:33:00:00:00:02")
        # self.props['hid']['33:33:00:00:00:02'] = 0xFF02
        # might be implemented on IPv6Renderer but not here since it's not
        # related to vid
        # ...
        # Note: MAT.reserved might need to be changed if necessary
    def serialize(self):
        obj = {}
        obj['vid'] = self.props['vid']
        obj['hid'] = self.props['hid']
        obj['mac'] = {}
        for (hid, mac) in self.props['mac'].items():
            obj['mac'][hid] = str(mac)
        return obj

    @staticmethod
    def deserialize(obj):
        mat = MAT(obj['vid'])
        mat.props['hid'] = obj['hid']
        for (hid, mac) in obj['mac'].items():
            mat.props['mac'][hid] = MACAddress(mac)
        return mat

    def translate(self, mac):
        if not str(mac) in self.props['hid']:
            with self.props['lock']:
                if not str(mac) in self.props['hid']:
                    hid = random.randint(1, MAT.reserved)
                    while hid in self.props['mac']:
                        hid = random.randint(1, MAT.reserved)
                    self.props['hid'][str(mac)] = hid
                    self.props['mac'][hid] = mac
        trans_mac = MACAddress()
        trans_mac.setVid(self.props['vid'])
        hid = self.props['hid'][str(mac)]
        trans_mac.setHid(hid)
        if hid > MAT.reserved:
            # broadcast MAC address
            trans_mac.data[0] = 0xFF
        return trans_mac
    def reverse(self, hid):
        if not hid in self.props['mac']:
            return None
        return MACAddress(self.props['mac'][hid])
