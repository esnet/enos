from org.jgrapht.alg import DijkstraShortestPath

from net.es.enos.esnet import ESnetLink
from net.es.enos.api import TopologyFactory

#
# Created by davidhua on 6/10/14.
#

offset = 23 # Remove "urn:ogf:network:es.net:" from router address
endingString = "@es.net" # Append address with @es.net
nodeCounter = 0
lengthCounter = 0
Nonetypecounter = 0
weightCounter = 0
goodpaths = 0
node_dict = {} # Store the path hop where the paths begin to diverge
completedList = {} # Stores paths already computed
nonetype = {}
problem_dict = {}
weight_dict = {}
arrow = " -> " # Arrow for output data. Replace with single space for easy copying into path.py prompt.


# Copied over from path.py-- initializes and fetches topology and list of nodes
topology = TopologyFactory.instance()
topo = topology.retrieveTopologyProvider("localLayer2")
graph = topo.retrieveTopology()
nodes = topo.getNodes()
listOfLinks = topo.getLinks()

# Run loop through every node pair in network
for destNode in nodes:
    destNodeString = str(destNode) # Convert node into string
    destNodeString = destNodeString[offset:]

    destNodeString = destNodeString + endingString # Chop off offset and insert ending string for graph operations
    destNodeGraph = topo.getNode(destNodeString)

    for ordNode in nodes:

        # If origin node and destination node are the same, skip.
        if ordNode == destNode:
            continue
        reversePath = [] # Reverse the hops taken by the reverse route
        orgpath = [] # Store shortest path info in an array
        destpath = [] # Store shortest path info in an array
        orgId = []
        destId = []
        revDestId = []
        orgWeight = []
        destWeight = []
        revDestWeight = []


        ordNodeString = str(ordNode)
        ordNodeString = ordNodeString[offset:]

        ordNodeString = ordNodeString + endingString
        ordNodeGraph = topo.getNode(ordNodeString)

        # Compute paths forwards and backwards
        firstShort = DijkstraShortestPath(graph, ordNodeGraph, destNodeGraph)
        firstpath = firstShort.getPathEdgeList()
        firstweight = firstShort.getPathLength()
        secondShort = DijkstraShortestPath(graph, destNodeGraph, ordNodeGraph)
        secondpath = secondShort.getPathEdgeList()
        secondWeight = secondShort.getPathLength()

        # Skip paths that give us a NoneType, but record into nonetype dictionary and increment counter
        if firstpath == None:
            Nonetypecounter += 1
            # Create entry if not in dictionary, else increment value
            nonetype[ordNodeString.encode("ascii")] = nonetype.get(ordNodeString, 0) + 1
            nonetype[destNodeString.encode("ascii")] = nonetype.get(destNodeString, 0) + 1
            continue
        if secondpath == None:
            nonetype[ordNodeString.encode("ascii")] = nonetype.get(ordNodeString, 0) + 1
            nonetype[destNodeString.encode("ascii")] = nonetype.get(destNodeString, 0) +1
            Nonetypecounter += 1
            continue

            #if len(firstpath) >= 2:
            #continue
        if firstweight == secondWeight:
            continue

        # Don't repeat paths that have already been run
        completed = destNodeString + arrow + ordNodeString
        if completedList.has_key(completed):
            continue
        completedList[completed.encode("ascii")] = completedList.get(completed, 1)

        completed = ordNodeString + arrow + destNodeString
        if completedList.has_key(completed):
            continue
        completedList[completed.encode("ascii")] = completedList.get(completed, 1)


        # Ignore hops within the same location to different routers-- not sure if we want this /
        # since going through different routers means a different path is taken, which is undesirable (@bmah)
        duplicateLink  = '' # Store the previous node in hop

        for link in firstpath:
            print "capacity: ", link.getMinimumReservableCapacity()
            # Remove everything in router address except location (ex lbl)
            # Remove ".split("-"[0]" to remove everything in router address except location-routerName (ex lbl-mr2)
            temp1 = (nodesByLink.get(link))[0].getId()[23:].split("-")[0]
            #print temp1, (nodesByLink.get(link))[6].getId()[23:].split("-")[0]
            orgpath.append(temp1)

            orgId.append(link.getId())
            orgWeight.append(link.getTrafficEngineeringMetric())
            duplicateLink = temp1
        print orgpath
        print "ENDLINE"
        orgpath.append(str(destNode)[offset:].split("-")[0])

        duplicateLink = '' # Reset duplicate field
        for link in secondpath:
            temp2 = (nodesByLink.get(link))[0].getId()[23:].split("-")[0]
            #print temp2, (nodesByLink.get(link))[6].getId()[23:].split("-")[0]
            destpath.append(temp2)
            destId.append(link.getId())
            destWeight.append(link.getTrafficEngineeringMetric())
            duplicateLink = temp2
            #for link2 in nodesByLink.get(link):
            #print link2.getId()[23:]
        destpath.append(str(ordNode)[offset:].split("-")[0])
        print destpath
        print "ENDLINE"



        # Reverse the second path to try to match with the first path
        for index, ignore in reversed(list(enumerate(destpath))):
            reversePath.append(destpath[index])
        for index, ignore in reversed(list(enumerate(destId))):
            revDestId.append(destId[index])
        for index, ignore in reversed(list(enumerate(destWeight))):
            revDestWeight.append(destWeight[index])

            # Check to see if lengths of paths are the same
            counter = 0
        if len(reversePath) != len(orgpath):
            #Find out which path is shorter
            length = min(len(reversePath), len(orgpath))
            for i in range(0, length-1):
                # If the two paths differ before the lengths differ, then log where they start to differ
                if orgpath[i+1] != reversePath[i+1]:
                    route = str(orgpath[i])+ arrow + str(orgpath[i+1])
                    node_dict[route.encode("ascii")] = node_dict.get(route, 0) + 1

                    route = str(reversePath[i])+ arrow + str(reversePath[i+1])
                    node_dict[route.encode("ascii")] = node_dict.get(route, 0) + 1

                if counter != 1:
                    problem_dict[reversePath[i].encode("ascii")] = problem_dict.get(reversePath[i], 0) + 1
                    counter = 1
                    continue
        if counter == 1:
            print "path " + ordNodeString + arrow + destNodeString +  " appears to be asymmetrical(length)"
            for i in range(length-1):
                print orgpath[i+1], " <-> ", reversePath[i+1]
            for i in range(length-1, max(len(reversePath), len(orgpath))-1):
                if (len(reversePath) < len(orgpath)):
                    print orgpath[i+1] + " <->"
                else:
                    print "     <-> ", reversePath[i+1]
                lengthCounter += 1 # Increment length counter
            print ""
            break

            # If lengths are the same, check to see if the paths take the same route
            counter = 0
        for i in range(len(orgpath)-1):
            if orgpath[i+1] != reversePath[i+1]:
                # If paths are not the same, store the hop where they begin to differ
                route = str(orgpath[i])+ arrow + str(orgpath[i+1])
                node_dict[route.encode("ascii")] = node_dict.get(route, 0) + 1

                route = str(reversePath[i])+ arrow + str(reversePath[i+1])
                node_dict[route.encode("ascii")] = node_dict.get(route, 0) + 1

            if counter != 1:
                problem_dict[reversePath[i].encode("ascii")] = problem_dict.get(reversePath[i], 0) + 1
                counter = 1
                nodeCounter += 1 # Increment node counter
                continue
        if counter == 1:
            print "path " + ordNodeString + arrow + destNodeString +  " appears to be asymmetrical"
            for i in range(len(orgpath)):
                print orgpath[i], " <-> ", reversePath[i]
            print ""

# Output info, comment out anything that you don't need

print ""
# Outputs numerical results
print "Numerical results:"
print ("Asymmetric paths counter (includes mismatched weights): " , nodeCounter)
print ("Mismatched length counter: " , lengthCounter)
print ("Nonetype counter: " , Nonetypecounter)

print ""
print "Problem hops:"
#Output mismatched paths, sorted alphabetical
for key, value in sorted(node_dict.iteritems(), key=lambda (k,v): (v,k)):
    print (key, value)


print ""
print "Problem nodes:"
# Output node where problems began, sorted reverse numerical by number of problems at that router
for key, value in sorted(problem_dict.iteritems(), key=lambda (k,v): (v,k)):
    print (key, value)


print ""
print "Nonetype: "
# Outputs which routers are causing Nonetype issues, sorted reverse numerical
for key, value in sorted(nonetype.iteritems(), key=lambda (k,v): (v,k)):
    print (key, value)
