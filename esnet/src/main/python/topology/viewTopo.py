from net.es.enos.api import ModifiedDijkstra
from org.jgrapht.alg import DijkstraShortestPath
from net.es.enos.esnet import GraphViewer
from net.es.enos.api import TopologyFactory
from net.es.enos.api import TopologyProvider
import sys

#
# Created by davidhua on 7/17/14.
#

# Run by calling viewtopo.py in netshell (No arguments); viewtopo.py [path] [source] [dest]; or viewtopo.py [bandwidth] [source] [dest].

topology = TopologyFactory.instance()
topo = topology.retrieveTopologyProvider("localLayer2")

if len(command_args) == 2:
    graph = topo.getGraph(TopologyProvider.WeightType.TrafficEngineering)
    viewer = GraphViewer(graph)
    viewer.init()
elif len(command_args) == 5:
    srcNode = topo.getNode(command_args[3]+"@es.net");
    dstNode = topo.getNode(command_args[4]+"@es.net");
    if command_args[2] == "path":
        graph = topo.getGraph(TopologyProvider.WeightType.TrafficEngineering)
        path = DijkstraShortestPath(graph, srcNode, dstNode)
        thispath = path.getPath()
        viewer = GraphViewer(thispath, graph)
    elif command_args[2] == "bandwidth":
        graph = topo.getGraph(TopologyProvider.WeightType.MaxBandwidth)
        md = ModifiedDijkstra(graph, srcNode, dstNode)
        maxBandwidth = md.getPath()
        viewer = GraphViewer(maxBandwidth, graph)
    viewer.init()
else:
    sys.exit()
