from org.jgrapht.alg import DijkstraShortestPath
from net.es.enos.api import TopologyFactory
topology = TopologyFactory.instance()
topo = topology.retrieveTopologyProvider("localLayer2")
graph = topo.retrieveTopology()
sites = topo.getSiteLinks()

srcNode = nodes.get("urn:ogf:network:es.net:lbl-mr2")
dstNode = nodes.get("urn:ogf:network:es.net:bnl-mr3")

path = DijkstraShortestPath.findPathBetween(graph, srcNode, dstNode)

print "Node= " + srcNode.getId()

for link in path:
	nodes = nodesByLink.get(link)
	print "Node= " + nodes[0].getId() + " linkId= " + link.getId()
        

print "Node= " + dstNode.getId() 
