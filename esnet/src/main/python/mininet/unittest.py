import unittest
from mininet.mac import MACAddress
from mininet.mat import MATManager
import random
import copy
class TestMAT(unittest.TestCase):
    def testMAC(self):
        mac1 = MACAddress()
        self.assertEqual(mac1.str(), "00:00:00:00:00:00")
        mac2 = MACAddress([1,2,16,17,254,255])
        self.assertEqual(mac2.str(), "01:02:10:11:FE:FF")
        self.assertNotEqual(mac1, mac2)
        mac3 = MACAddress([-1]*6)
        self.assertEqual(mac3, MACAddress.broadcast)
        mac4 = copy.deepcopy(mac2)
        self.assertEqual(mac2, mac4)
        self.assertEqual(mac2.jarray(), mac4.jarray())
        self.assertEqual(mac2.array(), mac4.array())

    def testMAT(self):
        # public method: reset, generateRandomVPNID, setVid, getVid, MAT
        MATManager.reset()
        vid = MATManager.generateRandomVPNID()
        self.assertTrue(vid >= 1 and vid < (1 << 24))
        MATManager.setVid('s0-eth0', 10, vid)
        MATManager.setVid('s0-eth1', 11, vid)
        self.assertEqual(MATManager.getVid('s0-eth0', 10), vid)
        self.assertEqual(MATManager.getVid('s0-eth1', 11), vid)
        self.assertEqual(MATManager.getVid('s0-eth0', 11), 0) # non-exist
        src_mac = MACAddress([0x00, 0x01, 0x02, 0x03, 0x04, 0x05])
        trans_mac = MATManager.MAT(src_mac, 's0-eth0', 10)
        # since they are in the same vpn (same vid), the same mac should be transfered 
        self.assertEqual(MATManager.MAT(src_mac, 's0-eth1', 11), trans_mac)
        self.assertEqual(MATManager.restoreMAT(trans_mac), src_mac)

if __name__ == '__main__':
    unittest.main()