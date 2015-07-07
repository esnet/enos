import net.es.netshell.odl.Controller
from mininet.testbed import TopoBuilder
def main():
    topo = TopoBuilder()

    controller = net.es.netshell.odl.Controller.getInstance()
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