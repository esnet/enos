from org.jgrapht.alg import DijkstraShortestPath
from net.es.netshell.api import TopologyFactory,TopologyProvider
from net.es.enos.esnet import OSCARSReservations
from org.joda.time import DateTime
import sys


if len(command_args) != 4:
    # Syntax error
    print "Syntax error: path src@domain dst@domain"
    print "    example: path lbl-mr2@es.net bnl-mr2@es.net"
    sys.exit()


topology = TopologyFactory.instance()
topo = topology.retrieveTopologyProvider("localLayer2")

graph = topo.getGraph(TopologyProvider.WeightType.TrafficEngineering)

nodes = topo.getNodes()

srcNode = topo.getNode(command_args[2]);
dstNode = topo.getNode(command_args[3]);

path = DijkstraShortestPath.findPathBetween(graph, srcNode, dstNode)
if path == None:
        print "No path between " + srcNode.getId() + " and " + dstNode.getId()
        sys.exit()

start = DateTime.now()
end = start.plusHours(2)
reserved = OSCARSReservations(topo).getReserved(start,end)

print "Start Node= " + srcNode.getId()

maxReservable = -1

for link in path:
    node = topo.getNodeByLink(link.getId())
    port = topo.getPortByLink(link.getId())

    portReservation = reserved.get(port)
    if portReservation == None:
        print "No portReservation for link " + link.getId() + " port= " + port.getId()
        continue
    remainTo = portReservation.maxReservable - portReservation.alreadyReserved[0]
    remainFrom = portReservation.maxReservable - portReservation.alreadyReserved[1]
    print "Node= " + node.getId() + "\tlinkId= " + link.getId()
    if (maxReservable == -1) or (maxReservable > remainTo):
        maxReservable = remainTo;

print "End Node= " + dstNode.getId()
print "Max. reservable= " + str(maxReservable) + " bits/sec"



