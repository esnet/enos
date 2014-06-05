from org.jgrapht.alg import DijkstraShortestPath
from net.es.enos.api import TopologyFactory
from net.es.enos.esnet import ESnetTopology,OSCARSReservations
from org.joda.time import DateTime
import sys


if len(command_args) != 4:
    # Syntax error
    print "Syntax error: path src@domain dst@domain"
    print "    example: path lbl-mr2@es.net bnl-mr3@es.net"
    sys.exit()


topology = TopologyFactory.instance()
topo = topology.retrieveTopologyProvider("localLayer2")

graph = topo.retrieveTopology()
nodes = topo.getNodes()
nodesByLink = topo.getNodesByLink()
portsByLink = topo.getPortsByLink()

srcNode = topo.getNode(command_args[2]);
dstNode = topo.getNode(command_args[3]);

path = DijkstraShortestPath.findPathBetween(graph, srcNode, dstNode)


start = DateTime.now()
end = start.plusHours(2)
reserved = OSCARSReservations(topo).getReserved(start,end)

print "Start Node= " + srcNode.getId()

maxReservable = -1

for link in path:
	nodes = nodesByLink.get(link)
	ports = portsByLink.get(link)
	port = ports[0] # Assume only one port per link
	portReservation = reserved.get(port)
	if portReservation == None:
		print "No portReservation for link " + link.getId() + " port= " + port.getId()
		continue
	remainTo = portReservation.maxReservable - portReservation.alreadyReserved[0]
	remainFrom = portReservation.maxReservable - portReservation.alreadyReserved[1]
	print "Node= " + nodes[0].getId() + "\tlinkId= " + link.getId()
	if (maxReservable == -1) or (maxReservable > remainTo):
		maxReservable = remainTo;

print "End Node= " + dstNode.getId()
print "Max. reservable= " + str(maxReservable) + " bits/sec"



