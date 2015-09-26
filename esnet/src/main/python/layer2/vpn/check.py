from net.es.netshell.layer2.odl import Controller
from layer2.testbed.builder import TopoBuilder
def main():
    try:
        builder = topo.builder
    except:
        print "no topo is existed, create a temporary one"
        builder = TopoBuilder()

    controller = Controller.getInstance()

    devices = controller.getNetworkDevices()
    allPass = True
    if len(builder.switchIndex.values()) != len(devices):
        allPass = False
    print 'builder has %d/%d devices' % (len(devices), len(builder.switchIndex.values()))
    for device in devices:
        node = device.getNode()
        nodename = 's%d' % node.getID()
        conns = device.getNodeConnectors()
        numPorts = len(builder.switchIndex[nodename].props['ports'])
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