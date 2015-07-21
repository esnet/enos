#
# ENOS, Copyright (c) 2015, The Regents of the University of California,
# through Lawrence Berkeley National Laboratory (subject to receipt of any
# required approvals from the U.S. Dept. of Energy).  All rights reserved.
#
# If you have questions about your rights to use or distribute this software,
# please contact Berkeley Lab's Technology Transfer Department at TTD@lbl.gov.
#
# NOTICE.  This software is owned by the U.S. Department of Energy.  As such,
# the U.S. Government has been granted for itself and others acting on its
# behalf a paid-up, nonexclusive, irrevocable, worldwide license in the Software
# to reproduce, prepare derivative works, and perform publicly and display
# publicly.  Beginning five (5) years after the date permission to assert
# copyright is obtained from the U.S. Department of Energy, and subject to
# any subsequent five (5) year renewals, the U.S. Government is granted for
# itself and others acting on its behalf a paid-up, nonexclusive, irrevocable,
# worldwide license in the Software to reproduce, prepare derivative works,
# distribute copies to the public, perform publicly and display publicly, and
# to permit others to do so.
#
from org.opendaylight.controller.sal.packet import Ethernet
from org.opendaylight.controller.sal.packet import IEEE8021Q
from org.opendaylight.controller.sal.utils import EtherTypes
import jarray, struct
def javaByteArray(a):
    b = jarray.zeros(len(a), 'b')
    for i in range(len(a)):
        b[i] = struct.unpack('b', struct.pack('B', a[i]))[0]
    return b
def usage():
    print "usage:"
    print "sim $SRCMAC $DSTMAC $VLAN $SWITCH $PORT: simulating to send a packet with vlan from src to dst to the port"
    print " MAC: B for broadcast (FF:FF:FF:FF:FF:FF)"
    print " For example, sim 1 3 10 lbl.gov 2 would send a packet with src=00:00:00:00:00:01, dst=00:00:00:00:00:03, and vlan=10 to the port lbl.gov-eth2"

def parseMac(mac):
    try:
        return MACAddress(int(mac))
    except:
        pass
    try:
        return MACAddress(mac)
    except:
        pass
    if mac == 'B':
        return MACAddress.createBroadcast()
    return None
def main():
    if not 'net' in globals():
        print "Please run demo first"
        return
    if len(command_args) < 7:
        usage()
        return
    srcMac = parseMac(command_args[2])
    if not srcMac:
        print "srcMac %s can not be parsed" % command_args[2]
        return
    dstMac = parseMac(command_args[3])
    if not dstMac:
        print "dstMac %s can not be parsed" % command_args[3]
        return
    try:
        vlan = int(command_args[4])
    except:
        print "vlan %s should be integer" % command_args[4]
        return
    try:
        switchName = command_args[5]
        switch = net.builder.switchIndex[switchName]
    except:
        try:
            switchIndex = int(command_args[5])
            switch = net.builder.switches[switchIndex]
        except:
            print "switch %s can not be found" % command_args[5]
            return
    try:
        interfaceIndex = int(command_args[6])
        port = switch.props['ports'][interfaceIndex]
    except:
        print "interfaceIndex %s can not be found" % command_args[6]
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
    rp.setIncomingNodeConnector(nodeconn)
    net.controller.callback(rp)

if __name__ == '__main__':
    main()