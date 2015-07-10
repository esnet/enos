#
# ENOS, Copyright (c) 2015, The Regents of the University of California,
# through Lawrence Berkeley National Laboratory (subject to receipt of any
# required approvals from the U.S. Dept. of Energy).  All rights reserved.
#
# If you have questions about your rights to use or distribute this software,
# please contact Berkeley Lab's Technology Transfer Department at TTD@lbl.gov.
#
# NOTICE.  This software is owned by the U.S. Department of Energy.  As such,
# the U.S. Government has been granted for itself and others acting on its
# behalf a paid-up, nonexclusive, irrevocable, worldwide license in the Software
# to reproduce, prepare derivative works, and perform publicly and display
# publicly.  Beginning five (5) years after the date permission to assert
# copyright is obtained from the U.S. Department of Energy, and subject to
# any subsequent five (5) year renewals, the U.S. Government is granted for
# itself and others acting on its behalf a paid-up, nonexclusive, irrevocable,
# worldwide license in the Software to reproduce, prepare derivative works,
# distribute copies to the public, perform publicly and display publicly, and
# to permit others to do so.
#
from net.es.netshell.api import TopologyFactory
from net.es.netshell.api import TopologyProvider

#
# Created by davidhua on 6/13/14.
#

# Iterates through all links to see if traffic metrics are the same in both directions

# Copied over from path.py-- initializes and fetches topology and list of nodes
topology = TopologyFactory.instance()
topo = topology.retrieveTopologyProvider("localLayer2")
listOfLinks = topo.getInternalLinks()
linkset = listOfLinks.values()
counter = 0

completedList = {}

graph = topo.getGraph(TopologyProvider.WeightType.TrafficEngineering)

# Iterate through links
for linked in graph.edgeSet():
    #for linked in linkk:
    forwardSuccess = 0
    backwardSuccess = 0

    # Normalize links

    linkSplit = linked.getId().split(":")
    if linkSplit[3] != "es.net":
        continue;
    sourceNode = linkSplit[4] + "@" + linkSplit[3];
    source = topo.getNode(sourceNode)

    # Get remote link and normalize
    remoteSplit = linked.getRemoteLinkId().split(":");

    if remoteSplit[3] != "es.net":
        continue;
    targetNode = remoteSplit[4] + "@" + remoteSplit[3]
    #print remoteSplit[4]
    target = topo.getNode(targetNode)


    # Find forwards and backwards edge
    forwards = graph.getAllEdges(source, target)
    backwards = graph.getAllEdges(target, source)
    if forwards.isEmpty():
        continue
    if backwards.isEmpty():
        continue

    for forward in forwards:
        if forward.equals(linked):
            forwardSuccess = 1
            realForward = forward

    if forwardSuccess == 1:
        reverse = realForward.getRemoteLinkId()
    else:
        continue


    for backward in backwards:
        if backward.getId() == (reverse):
            realBackward = backward
            backwardSuccess = 1
    if backwardSuccess != 1:
        continue
    forwards = realForward
    backwards = realBackward
    # Skip invalid edges for now
    if completedList.has_key(forwards):
        continue
    completedList[forwards] = completedList.get(forwards, 1)

    if completedList.has_key(backwards):
        continue

    completedList[backwards] = completedList.get(backwards, 1)
    counter+=1
    # Check to see if metrics are the same
    if forwards.getTrafficEngineeringMetric() != backwards.getTrafficEngineeringMetric():
        print sourceNode, " and ", targetNode, " metrics possibly do not match"
        print forwards.getId(), forwards.getTrafficEngineeringMetric()
        print backwards.getId(), backwards.getTrafficEngineeringMetric()
        #print ""

    if forwards.getInterfaceMTU() != backwards.getInterfaceMTU():
        print ""
        print sourceNode, " and ", targetNode, " MTUs possibly do not match"
