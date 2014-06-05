from net.es.enos.api import TopologyFactory
from net.es.enos.esnet import OSCARSReservations
from org.joda.time import DateTime

topology = TopologyFactory.instance()
topo = topology.retrieveTopologyProvider("localLayer2")
graph = topo.retrieveTopology()
sites = topo.getSiteLinks()
nodes = topo.getNodes()
nodesByLink = topo.getNodesByLink()
portsByLink = topo.getPortsByLink()

links = topo.getLinks()

srcNode = nodes.get("urn:ogf:network:es.net:lbl-mr2")
dstNode = nodes.get("urn:ogf:network:es.net:bnl-mr3")

circuits = OSCARSReservations.retrieveScheduledCircuits()

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




