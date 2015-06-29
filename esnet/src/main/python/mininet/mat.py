import random
from common.api import Properties
from mininet.mac import MACAddress
import threading

class MAT(Properties):
    def __init__(self, vid):
        super(MAT, self).__init__(name='MAT[%d]' % vid)
        self.props['vid'] = vid
        self.props['hid'] = {} # [str(mac)] = hid
        self.props['mac'] = {} # [hid] = mac
        self.props['lock'] = threading.Lock()
    def translate(self, mac):
        # TODO implement a rw locker
        if not str(mac) in self.props['hid']:
            with self.props['lock']:
                if not str(mac) in self.props['hid']:
                    hid = random.randint(1, 65534)
                    while hid in self.props['mac']:
                        hid = random.randint(1, 65534)
                    self.props['hid'][str(mac)] = hid
                    self.props['mac'][hid] = mac
        trans_mac = MACAddress()
        trans_mac.setVid(self.props['vid'])
        trans_mac.setHid(self.props['hid'][str(mac)])
        return trans_mac
    def reverse(self, hid):
        if not hid in self.props['mac']:
            return None
        return self.props['mac'][hid]
