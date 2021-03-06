#
# ESnet Network Operating System (ENOS) Copyright (c) 2015, The Regents
# of the University of California, through Lawrence Berkeley National
# Laboratory (subject to receipt of any required approvals from the
# U.S. Dept. of Energy).  All rights reserved.
#
# If you have questions about your rights to use or distribute this
# software, please contact Berkeley Lab's Innovation & Partnerships
# Office at IPO@lbl.gov.
#
# NOTICE.  This Software was developed under funding from the
# U.S. Department of Energy and the U.S. Government consequently retains
# certain rights. As such, the U.S. Government has been granted for
# itself and others acting on its behalf a paid-up, nonexclusive,
# irrevocable, worldwide license in the Software to reproduce,
# distribute copies to the public, prepare derivative works, and perform
# publicly and display publicly, and to permit other to do so.
#
from org.opendaylight.controller.sal.packet import Ethernet
from org.opendaylight.controller.sal.packet import IEEE8021Q
from org.opendaylight.controller.sal.utils import EtherTypes
from common.mac import MACAddress
import jarray, struct
def javaByteArray(a):
    b = jarray.zeros(len(a), 'b')
    for i in range(len(a)):
        b[i] = struct.unpack('b', struct.pack('B', a[i]))[0]
    return b
def usage():
    print "usage:"
    print "sim $SRCMAC $DSTMAC $VLAN $SWITCH $PORT $DIR: simulating to send a packet with vlan from src to dst to the port"
    print " MAC: B for broadcast (FF:FF:FF:FF:FF:FF)"
    print " DIR: in/out"
    print " For example, 'sim 1 3 10 lbl.gov 2 in' would send a packet with src=00:00:00:00:00:01, dst=00:00:00:00:00:03, and vlan=10 to the port lbl.gov-eth2"

def parseMac(mac):
    if mac == 'B':
        return MACAddress.createBroadcast()
    try:
        return MACAddress(int(mac))
    except:
        pass
    try:
        return MACAddress(mac)
    except:
        pass
    return None
def main():
    if not 'net' in globals():
        print "Please run demo first"
        return
    if len(sys.argv) < 7:
        usage()
        return
    srcMac = parseMac(sys.argv[1])
    if not srcMac:
        print "srcMac %s can not be parsed" % sys.argv[1]
        return
    dstMac = parseMac(sys.argv[2])
    if not dstMac:
        print "dstMac %s can not be parsed" % sys.argv[2]
        return
    try:
        vlan = int(sys.argv[3])
    except:
        print "vlan %s should be integer" % sys.argv[3]
        return
    try:
        switchName = sys.argv[4]
        switch = net.builder.switchIndex[switchName]
    except:
        try:
            switchIndex = int(sys.argv[4])
            switch = net.builder.switches[switchIndex]
        except:
            print "switch %s can not be found" % sys.argv[4]
            return
    try:
        interfaceIndex = int(sys.argv[5])
        port = switch.props['ports'][interfaceIndex]
    except:
        print "interfaceIndex %s can not be found" % sys.argv[5]
        return
    if sys.argv[6] != 'in' and sys.argv[6] != 'out':
        print "invalid DIR, should be in or out"
        return
    # create a packet
    etherType=2048
    payload=[0]
    odlSwitch = net.controller.findODLSwitch(switch)
    portName = "%s-eth%d" % (switch.props['mininetName'], port.props['interfaceIndex'])
    nodeconn = net.controller.odlController.getNodeConnector(odlSwitch.getNode(), portName)

    # Create the outgoing packet in ODL land.  The outgoing node connector must be set.
    cp = Ethernet()
    cp.setSourceMACAddress(javaByteArray(srcMac.data))
    cp.setDestinationMACAddress(javaByteArray(dstMac.data))
    if vlan == 0:
        cp.setEtherType(etherType)
        cp.setRawPayload(javaByteArray(payload))
    else:
        cvp = IEEE8021Q()
        cvp.setEtherType(etherType)
        cvp.setVid(vlan)
        cvp.setRawPayload(javaByteArray(payload))
        cp.setPayload(cvp)
        cp.setEtherType(EtherTypes.VLANTAGGED.shortValue())
    rp = net.controller.odlPacketHandler.encodeDataPacket(cp)
    if sys.argv[6] == 'in':
        rp.setIncomingNodeConnector(nodeconn)
        net.controller.callback(rp)
    else:
        rp.setOutgoingNodeConnector(nodeconn)
        net.controller.odlPacketHandler.transmitDataPacket(rp)

if __name__ == '__main__':
    main()
