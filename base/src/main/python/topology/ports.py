from net.es.enos.api import TopologyFactory


#
# Created by davidhua on 6/13/14.
#

# Iterates through all links to see if traffic metrics are the same in both directions

# Copied over from path.py-- initializes and fetches topology and list of nodes
topology = TopologyFactory.instance()
topo = topology.retrieveTopologyProvider("localLayer2")
graph = topo.retrieveTopology()
nodes = topo.getNodes()
nodesByLink = topo.getNodesByLink()
links = topo.getPortsByLink()
listOfLinks = topo.getLinks()
linkset = listOfLinks.values()

# Iterate through links
for linkset in listOfLinks:
    # Normalize links
    linked = listOfLinks.get(linkset)
    linkSplit = linked.getId().split(":")
    if linkSplit[3] != "es.net":
        continue;
    sourceNode = linkSplit[4] + "@" + linkSplit[3];
    source = topo.getNode(sourceNode)

    # Get remote link and normalize
    remoteSplit = listOfLinks.get(linkset).getRemoteLinkId().split(":");
    if remoteSplit[3] != "es.net":
        continue;
    targetNode = remoteSplit[4] + "@" + remoteSplit[3]
    target = topo.getNode(targetNode)

    # Find forwards and backwards edge
    forwards = graph.getEdge(source, target)
    backwards = graph.getEdge(target, source)

    # Skip invalid edges for now
    if forwards is None:
        continue
    if backwards is None:
        continue

    # Check to see if metrics are the same
    if forwards.getTrafficEngineeringMetric() != backwards.getTrafficEngineeringMetric():
        print sourceNode, " and ", targetNode, " metrics possibly do not match"

        #print ""
        #
        #if forwards.getInterfaceMTU() != backwards.getInterfaceMTU():
        #print sourceNode, " and ", targetNode, " MTUs possibly do not match"
