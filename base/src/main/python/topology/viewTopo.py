from net.es.enos.esnet import TopologyViewer
from net.es.enos.api import TopologyFactory
from net.es.enos.api import TopologyProvider

#
# Created by davidhua on 7/17/14.
#

# Run by calling viewtopo.py in enos (No arguments).

topology = TopologyFactory.instance()
topo = topology.retrieveTopologyProvider("localLayer2")
graph = topo.getGraph(TopologyProvider.WeightType.TrafficEngineering)

topo = TopologyViewer(graph)
topo.init()

