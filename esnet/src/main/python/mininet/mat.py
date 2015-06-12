import random
import array
from mininet.mac import MACAddress

class MATManager:
    occupiedHostID = {}
    occupiedVPNID = {}
    VPNID = {}
    HostID = {}
    HostMAC = {}
    @staticmethod
    def reset():
        MATManager.occupiedHostID = {}
        MATManager.occupiedVPNID = {}
        MATManager.VPNID = {}
        MATManager.HostID = {}
        MATManager.HostMAC = {}
    @staticmethod
    def generateRandomVPNID():
        found = False
        while not found:
            vid = random.randint(1, 256 * 256 * 256 - 1)
            if not vid in MATManager.occupiedVPNID:
                found = True
        MATManager.occupiedVPNID[vid] = True
        return vid
    @staticmethod
    def generateRandomHostID():
        found = False
        while not found:
            hid = random.randint(1, 65535)
            if not hid in MATManager.occupiedHostID:
                found = True
        MATManager.occupiedHostID[hid] = True
        return hid
    @staticmethod
    def setVid(port, vlan, vid):
        if not port in MATManager.VPNID:
            MATManager.VPNID[port] = {}
        MATManager.VPNID[port][vlan] = vid
    @staticmethod
    def getVid(port, vlan):
        """
        :param port: (type: unique string)
        :param vlan: (type: int)
        :return: VPN instance ID (type: int range from 1 to 2^24)
        """
        # the information should be managed by a centralized controller
        if not port in MATManager.VPNID:
            return 0
        if not vlan in MATManager.VPNID[port]:
            return 0
        return MATManager.VPNID[port][vlan]
    @staticmethod
    def getHid(vid, mac):
        """
        :param vid: VPN instance ID (type: int range from 1 to 2^24)
        :param mac: original MAC address (type: str)
        :return: host ID
        """
        # the information should be managed by a centralized controller
        if not vid in MATManager.HostID:
            MATManager.HostID[vid] = {}
        if not mac in MATManager.HostID[vid]:
            hid = MATManager.generateRandomHostID()
            MATManager.HostID[vid][mac] = hid
        return MATManager.HostID[vid][mac]
    @staticmethod
    def MAT(mac, port, vlan):
        """
        MAC address translation
        :param mac: original MAC address (type: MACAddress)
        :param port: the corresponding port to the MAC address (str)
        :param vlan: vlan (int)
        :return: translated MAC address (type: MACAddress)
        """
        # format: reserved | broadcast (1 bytes), VPN instance id (3 bytes), host id (2 bytes)
        # TODO not implement broadcast yet
        manage_byte = 0 # bit 1: local administered; bit 0: unicast/multicast
        vid = MATManager.getVid(port, vlan)
        hid = MATManager.getHid(vid, mac.str())
        trans_mac = MACAddress([manage_byte, vid >> 16, (vid >> 8) & 0xFF, vid & 0xFF, hid >> 8, hid & 0xFF])
        MATManager.HostMAC[trans_mac.str()] = mac
        return trans_mac
    @staticmethod
    def restoreMAT(mac):
        """
        restore the translated MAC address to original MAC address
        :param mac: the translated MAC (get from MAT)
        :return: original MAC address (type: str)
        """
        # TODO implement a MACAddress class
        return MATManager.HostMAC[mac.str()]