from net.es.enos.api import Dijkstra
from net.es.enos.api import TopologyFactory


topology = TopologyFactory.instance()
topo = topology.retrieveTopologyProvider("localLayer2")
graph = topo.retrieveTopology()

src = "llnl-mr2@es.net"
dst = "bnl-mr3@es.net"

srcNode = topo.getNode(src)
dstNode = topo.getNode(dst)

print Dijkstra.findPath(graph,srcNode, dstNode)