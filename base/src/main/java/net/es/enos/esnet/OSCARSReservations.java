package net.es.enos.esnet;

import net.es.enos.api.ISODateTime;
import net.es.enos.api.Link;
import net.es.enos.api.Node;
import net.es.enos.api.Port;
import org.jgrapht.Graph;
import org.jgrapht.GraphPath;
import org.jgrapht.graph.ListenableDirectedGraph;
import org.joda.time.DateTime;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import java.util.HashMap;

import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;

/**
 * Created by lomax on 5/28/14.
 */
public class OSCARSReservations {

    private final Logger logger = LoggerFactory.getLogger(OSCARSReservations.class);
    private ESnetTopology topology;
    private List<ESnetCircuit> circuits;
    private ListenableDirectedGraph topoGraph;

    public class PortReservation {
        public long maxReservable;
        public long[] alreadyReserved = new long[2]; // Path forward and back
        public PortReservation (long maxReservable) {
            this.maxReservable = maxReservable;
        }
    }
    /**
     * Returns the list of ACTIVE or RESERVED OSCARS circuits.
     * @return  a list of circuits.
     * @throws IOException
     */
    public  List<ESnetCircuit> retrieveScheduledCircuits() throws IOException {
        return this.topology.retrieveJSONTopology().getCircuits();
    }

    public OSCARSReservations(ESnetTopology topology) throws IOException {
        this.topology = topology;
        this.topology = topology;
        this.circuits = this.retrieveScheduledCircuits();
        this.topoGraph = topology.retrieveTopology ();
    }

    public long getMaxReservableBandwidth (GraphPath<Node,Link> path, DateTime start,DateTime end) throws IOException {

	    HashMap<Link, List<Port>> portsByLink = topology.getPortsByLink();

	    // First compute the overall reserved bandwidth on the overall topology
	    HashMap<ESnetPort, PortReservation> reserved = this.getReserved(start, end);

	    long maxReservable = -1;
	    long remainTo;

	    // Then compute max reservable for each link.
	    for (Link link : path.getEdgeList()) {
		    List<Port> ports = portsByLink.get(link);
		    Port port = ports.get(0); // Assume one port per link
		    reserved.get(port);
		    PortReservation portReservation = reserved.get(port);
		    if (portReservation == null) {
			    continue;
		    }
		    remainTo = portReservation.maxReservable - portReservation.alreadyReserved[0];
		    if (maxReservable == -1 || maxReservable > remainTo) {
			    maxReservable = remainTo;
		    }
	    }
	    return maxReservable;
    }


    public ListenableDirectedGraph getTopoGraph() {
        return topoGraph;
    }


    /**
     * Reads all the reservations that are active within the specified time range and
     * aggregates, per port, the bandwidth that is already reserved. The method returns
     * the data in the form of HashMap of PortReservation, index by Port. PortReservation
     * contains both the reservation that has already been made and the maximum bandwidth
     * that is allowed on this port.
     * @param start time of the query
     * @param end time of the query
     * @return  an HashMap of PortReservation indexed by ESnetPort
     */
    public HashMap<ESnetPort, PortReservation> getReserved (DateTime start, DateTime end) {

        HashMap<String,Link> links = topology.getLinks();
        HashMap<Link,List<Port>> portsByLink = topology.getPortsByLink();

        HashMap<ESnetPort,PortReservation> reserved = new HashMap<ESnetPort, PortReservation>();
        List<ESnetCircuit> reservations = topology.retrieveJSONTopology().getCircuits();
        for (ESnetCircuit reservation : reservations) {
            if (! reservation.isActive(start,end))  {
                // This reservation is not active withing the query time frame, ignore
                continue;
            }
            List<ESnetSegment> segments = reservation.getSegments();
            int segmentCounter = 0;
            for (ESnetSegment segment : segments) {
                List<String> portNames = segment.getPorts();
                for (String portName : portNames) {
                    // String the VLAN off the port name, if any.
                    String[] tmp = portName.split(":");
                    String[] tmp2 = tmp[5].split(".");
                    if (tmp[5].indexOf(".") > 0) {
                        tmp[5] = tmp[5].substring(0,tmp[5].indexOf("."));
                        continue;
                    }
                    portName = "";
                    for (String s : tmp) {
                        portName += s + ":";
                    }
                    portName = portName.substring(0,portName.length() -1);

                    // Retrieve port from topology.
                    Link link = links.get(portName);
                    if (link == null) {
                        logger.warn("No link in topology that matches OSCARS path element " + portName);
                        continue;
                    }
                    List<Port> ports = portsByLink.get(link);
                    if (ports.size() < 1) {
                        throw new RuntimeException("No port in topology that matches OSCARS path element " + portName);
                    }
                    Port p = ports.get(0); // Assume first port
                    if ( ! (p instanceof ESnetPort)) {
                        // This implementation relies on ESnet types
                        throw new RuntimeException("Unexpected type " + p.getClass().getCanonicalName());
                    }
                    ESnetPort port = (ESnetPort) p;
                    if (reserved.containsKey(port)) {
                        PortReservation portReservation = reserved.get(port);

                        portReservation.alreadyReserved[segmentCounter] = portReservation.alreadyReserved[segmentCounter]
                                                            + Long.parseLong(reservation.getCapacity());

                    } else {
                        // First time this port is seen. Create a PortReservation
                        PortReservation portReservation =
                                new PortReservation(Long.parseLong(port.getMaximumReservableCapacity()));
                        portReservation.alreadyReserved[segmentCounter] = Long.parseLong(reservation.getCapacity());
                        reserved.put(port, portReservation);
                    }
                }
                ++segmentCounter;
            }
        }
        return reserved;
    }
}
