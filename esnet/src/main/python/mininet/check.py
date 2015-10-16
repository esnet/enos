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
from net.es.netshell.odl import Controller
def main():
    try:
        topo = net.builder
    except:
        print "no topo is existed, create a temporary one"
        from mininet.testbed import TopoBuilder
        topo = TopoBuilder()

    controller = Controller.getInstance()

    devices = controller.getNetworkDevices()
    allPass = True
    if len(topo.switches) != len(devices):
        allPass = False
    print 'topo has %d/%d devices' % (len(devices), len(topo.switches))
    for device in devices:
        node = device.getNode()
        nodename = 's%d' % node.getID()
        conns = device.getNodeConnectors()
        numPorts = len(topo.switchIndex[topo.mininetToRealNames[nodename]].props['ports'])
        if numPorts != len(conns):
            allPass = False
        print '%r has %d/%d conns' % (node, len(conns), numPorts)
        it = conns.iterator()
        existed = []
        while it.hasNext():
            conn = it.next()
            connID = conn.getID()
            existed.append(connID)
            portname = '%s-eth%d' % (nodename, connID)
            nodeconn = controller.getNodeConnector(node, portname)
            if not nodeconn:
                print 'FAIL: %r (%s) not found on %r' % (conn, portname, node)
                allPass = False
        for miss in [i for i in range(1, numPorts + 1) if i not in existed]:
            print 'FAIL: %s-eth%d not found on %r' % (nodename, miss, node)
    if allPass:
        print 'PASS'


if __name__ == '__main__':
    main()