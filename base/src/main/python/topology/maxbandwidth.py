from net.es.enos.api import ModifiedDijkstra
from net.es.enos.api import TopologyFactory
from net.es.enos.esnet import OSCARSReservations
from org.joda.time import DateTime

topology = TopologyFactory.instance()
topo = topology.retrieveTopologyProvider("localLayer2")
graph = topo.retrieveBandwidthTopology()
portsByLink = topo.getPortsByLink()

src = "lbl-mr2@es.net"
dst = "bnl-mr3@es.net"

srcNode = topo.getNode(src)
dstNode = topo.getNode(dst)

start = DateTime.now()
end = start.plusHours(2)
reserved = OSCARSReservations(topo).getReserved(start,end)

maxReservable = -1

temp = ModifiedDijkstra(graph, srcNode, dstNode)

for link in temp.getBandwidth():
    print link.getId()
    ports = portsByLink.get(link)
    port = ports[0] # Assume only one port per link
    portReservation = reserved.get(port)
    if portReservation == None:
        continue
    remainTo = portReservation.maxReservable - portReservation.alreadyReserved[0]
    remainFrom = portReservation.maxReservable - portReservation.alreadyReserved[1]
    if (maxReservable == -1) or (maxReservable > remainTo):
        maxReservable = remainTo;

print "Max. reservable= " + str(maxReservable) + " bits/sec"

# for node in temp.getBandwidth():
    # print node.getId()

# Interestingly, but unrelated, if a comment is the last line of the code, Jython will give an error.
# However, if the file ends with a newline, then the error will not appear.

