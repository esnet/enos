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
from net.es.netshell.api import TopologyFactory
from net.es.enos.esnet import OSCARSReservations
from org.joda.time import DateTime

topology = TopologyFactory.instance()
topo = topology.retrieveTopologyProvider("localLayer2")
sites = topo.getSiteLinks()
nodes = topo.getNodes()

links = topo.getLinks()

srcNode = nodes.get("urn:ogf:network:es.net:lbl-mr2")
dstNode = nodes.get("urn:ogf:network:es.net:bnl-mr3")

circuits = OSCARSReservations(topo).retrieveScheduledCircuits()

def setMaxCapacity(c):
	reserved={}

	segments = c.getSegments()
	for segment in segments:
        	ports = segment.getPorts()
        	for port in ports:
                	print port
                	elems = port.split(":")
                	if elems[5] != None:
                        	elems[5] = elems[5].split(".")[0]
                	p =  ":".join(elems)
                	link = links.get(p)
                	if link != None:
                        	routerPort = portsByLink.get(link)[0]
                        	if routerPort.getId() in reserved:
                                	reserved[routerPort.getId()] += long(routerPort.getMaximumReservableCapacity())
                        	else:
                                	reserved[routerPort.getId()] = long(routerPort.getMaximumReservableCapacity())
                	else:   
                        	print "####### NO LINK"

now = DateTime.now()

for circuit in circuits:
	start = circuit.getStartDateTime()
	end = circuit.getEndDateTime()
	if (start >  now):
		print "end= " + end.toString()


for linkid in links.keySet():
	link = links.get(linkid)
	# print linkid + " : " + link.getId() + "   " + link.getRemoteLinkId()




