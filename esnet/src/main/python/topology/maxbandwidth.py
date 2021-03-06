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
from net.es.netshell.api import TopologyFactory
from net.es.enos.esnet import OSCARSReservations
from net.es.netshell.api import TopologyProvider
from org.joda.time import DateTime

# Create graph with bandwidth weights rather than network metrics
topology = TopologyFactory.instance()
topo = topology.retrieveTopologyProvider("localLayer2")

src = raw_input("src: ")
dst = raw_input("dst: ")
srcNode = topo.getNode(src+"@es.net");
dstNode = topo.getNode(dst+"@es.net");

start = DateTime.now()
end = start.plusHours(2)
reserved = OSCARSReservations(topo).getReserved(start,end)

maxReservable = -1

# Calculate max bandwidth possible from source to destination

tgraph = topo.getGraph(start, end, TopologyProvider.WeightType.MaxBandwidth)

md = ModifiedDijkstra(tgraph, srcNode, dstNode)
maxBandwidth = md.getBandwidth()

# iterate through path to calculate what is the max bandwidth available and the path corresponding
for link in maxBandwidth:
    print "link: " , link.getId()
    port = topo.getPortByLink(link.getId())
    portReservation = reserved.get(port)
    if portReservation == None:
        continue
    remainTo = portReservation.maxReservable - portReservation.alreadyReserved[0]
    print "reservable: ", remainTo
    if (maxReservable == -1) or (maxReservable > remainTo):
        maxReservable = remainTo;

print "Max. reservable= " + str(maxReservable) + " bits/sec"

# Interestingly, but unrelated, if a comment is the last line of the code, Jython will give an error.
# However, if the file ends with a newline, then the error will not appear.

