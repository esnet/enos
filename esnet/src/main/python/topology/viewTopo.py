#
# ESnet Network Operating System (ENOS) Copyright (c) 2015, The Regents
# of the University of California, through Lawrence Berkeley National
# Laboratory (subject to receipt of any required approvals from the
# U.S. Dept. of Energy).  All rights reserved.
#
# If you have questions about your rights to use or distribute this
# software, please contact Berkeley Lab's Innovation & Partnerships
# Office at IPO@lbl.gov.
#
# NOTICE.  This Software was developed under funding from the
# U.S. Department of Energy and the U.S. Government consequently retains
# certain rights. As such, the U.S. Government has been granted for
# itself and others acting on its behalf a paid-up, nonexclusive,
# irrevocable, worldwide license in the Software to reproduce,
# distribute copies to the public, prepare derivative works, and perform
# publicly and display publicly, and to permit other to do so.
#

from net.es.netshell.api import ModifiedDijkstra
from org.jgrapht.alg import DijkstraShortestPath
from net.es.enos.esnet import GraphViewer
from net.es.netshell.api import TopologyFactory
from net.es.netshell.api import TopologyProvider
import sys

#
# Created by davidhua on 7/17/14.
#

# Run by calling viewtopo.py in netshell (No arguments); viewtopo.py [path] [source] [dest]; or viewtopo.py [bandwidth] [source] [dest].

topology = TopologyFactory.instance()
topo = topology.retrieveTopologyProvider("localLayer2")

command_args = sys.argv

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
