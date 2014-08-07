/*
 * Copyright (c) 2014, Regents of the University of California.
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 * 1. Redistributions of source code must retain the above copyright notice,
 * this list of conditions and the following disclaimer.
 *
 * 2. Redistributions in binary form must reproduce the above copyright notice,
 * this list of conditions and the following disclaimer in the documentation
 * and/or other materials provided with the distribution.
 *
 * 3. Neither the name of the copyright holder nor the names of its contributors
 * may be used to endorse or promote products derived from this software without
 * specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 * DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
 * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
 * CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
 * OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

package net.es.enos.esnet;

import net.es.enos.api.*;
import org.jgrapht.graph.DefaultListenableGraph;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.joda.time.DateTime;

import java.io.*;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Set;


/**
 * Created by lomax on 5/16/14.
 */
public class ESnetTopology  extends TopologyProvider {;
    private final Logger logger = LoggerFactory.getLogger(ESnetTopology.class);

    private HashMap<String, ESnetNode> nodes = new HashMap<String, ESnetNode>();
    private HashMap<String,Node> nodeByLink = new HashMap<String, Node>();
    private HashMap<String,Port> portByLink = new HashMap<String, Port>();
    private HashMap<String, List<Link>> internalLinks = new HashMap<String, List<Link>>();
    private HashMap<String, List<Link>> siteLinks = new HashMap<String, List<Link>>();
    private HashMap<String, List<Link>> domainLinks = new HashMap<String, List<Link>>();
    private HashMap<String, Link> links = new HashMap<String, Link>();

    public ESnetTopology() {
        this.parseTopology();
    }

    public HashMap<String, ESnetNode> getNodes() {
        return nodes;
    }

    /**
     * Returns a HashMap of List of Links that connects ESnet internal node to each other. The map is indexed by
     * the name of the node as found in the topology.
     * @return returns the indexed Map.
     */
    public HashMap<String, List<Link>> getInternalLinks() { return internalLinks; }

    /**
     * Returns a HashMap of the Nodes indexed by Link.
     * @return
     */
    public HashMap<String, Node> getNodeByLink() {
        return nodeByLink;
    }

    public HashMap<String, Port> getPortByLink() {
        return portByLink;
    }

    public HashMap<String, Link> getLinks() {
        return links;
    }

    public HashMap<String, List<Link>> getDomainLinks() {
        return domainLinks;
    }

    public HashMap<String, List<Link>> getSiteLinks() {
        return siteLinks;
    }

    /**
     * Returns the opposite Node of a point to point Link of the provided Node
     * @param l is the link
     * @param n is current end of the link
     * @return
     */
    public Node getOppositeNode (Link l, Node n) {
        if ( ! (l instanceof ESnetLink)) {
            throw new RuntimeException("Link is not an ESnetLink");
        }
        if ( ! (n instanceof ESnetNode)) {
            throw new RuntimeException("Node is not an ESnetNode");
        }
        ESnetLink link = (ESnetLink) l;
        ESnetNode node = (ESnetNode) n;

        // Retrieve the ID of both ends of the link and return the opposite
        if ((link.getId().equals(node.getId()))) {
            return this.nodes.get(link.getRemoteLinkId());
        } else {
            return this.nodes.get(idToUrn(link.getRemoteLinkId(),4));
        }
    }

    /**
     * The topology file is made out of three root elements:
     *  status: status of the JSON query (success or failure)
     *  domains: list of domains.
     *  circuits: list of OSCARS reservations that are either ACTIVE or RESERVED, i.e, list of successful reservation
     *            from now on.
     *  The list of domains contains two domain elements, both related to ESnet topology. The first element is
     *  the translation of the OSCARS NMWG topology. The second domain element is the layer 3 topology. It contain
     *  more information and has information on peering to other domains. This method parses the file, merges nodes
     *  when common between both domains elements.
     */
    private void parseTopology() {
        OSCARSTopologyPublisher publisher = new OSCARSTopologyPublisher();
        ESnetJSONTopology jsonTopology = publisher.toJSON();
        // Retrieve from JSON Domain, Node and Link objects and index them into the various HashMaps
        List<ESnetDomain> domains = jsonTopology.getDomains();
	    HashMap<String, List<ESnetNode>> locationToNode = new HashMap<> ();

        for (ESnetDomain domain : domains) {
            // First index all Nodes.
            List<ESnetNode> nodes = domain.getNodes();
            for (ESnetNode node : nodes) {
                // Nodes in the second domain are set to "ps.es.net". Strip "ps."
                String d = ESnetTopology.idToDomain(node.getId());
                if (d.equals("ps.es.net")) {
                    node.setId(node.getId().replace("ps.es.net","es.net"));
                    // This is the layer3 domain. Retrieve coordinates.
                    if (this.nodes.containsKey(node.getId())) {
                        ESnetNode n = this.nodes.get(node.getId());
                        n.setLongitude(node.getLongitude());
                        n.setLatitude(node.getLatitude());

                    } else {
	                    String nodeName;
	                    String[] nodeList = node.getId().split(":")[4].split("-");
	                    if (nodeList.length == 3) {
		                    nodeName = nodeList[0] + "-" + nodeList[1];
	                    } else {
		                    nodeName = nodeList[0];
	                    }
	                    if (locationToNode.containsKey(nodeName)) {
		                    for (ESnetNode locationNode : locationToNode.get(nodeName)) {
			                    locationNode.setLongitude(node.getLongitude());
			                    locationNode.setLatitude(node.getLatitude());
		                    }
	                    }
                    }
                    // All we need from this node is the coordinates.
                    continue;
                }
	            String[] nodeList = node.getId().split(":")[4].split("-");
	            String nodeName;
	            if (nodeList.length == 3) {
		            nodeName = nodeList[0] + "-" + nodeList[1];
	            } else {
		            nodeName = nodeList[0];
	            }

	            if (nodeName.equals("sacr")) {
		            node.setLongitude(Double.toString(-121.478851));
		            node.setLatitude(Double.toString(38.575764));
	            } else if (nodeName.equals("snll")) {
		            node.setLongitude(Double.toString(-121.768056));
		            node.setLatitude(Double.toString(37.681944));
	            } else if (nodeName.equals("ameslab")) {
		            node.setLongitude(Double.toString(-93.6482));
		            node.setLatitude(Double.toString(42.0305));
	            } else if (nodeName.equals("albq")) {
		            node.setLongitude(Double.toString(-106.6100));
		            node.setLatitude(Double.toString(35.1107));
	            } else if (nodeName.equals("lsvn")) {
		            node.setLongitude(Double.toString(-115.1174));
		            node.setLatitude(Double.toString(36.2365));
	            } else {
		            if (!locationToNode.containsKey(nodeName)) {
			            locationToNode.put(nodeName, new ArrayList<ESnetNode>());
		            }
		            locationToNode.get(nodeName).add(node);
	            }
                this.nodes.put(node.getId(),node);
            }

            // Second, index all Links. Note that all the nodes must be indexed beforehand, so it is not possible
            // to collapse the seemingly identical for loops.
            for (ESnetNode node : this.nodes.values()) {
                List<ESnetPort> ports = node.getPorts();
                for (ESnetPort port : ports) {
                    // Patch the domain name (remove ps.)
                    String d = ESnetTopology.idToDomain(port.getId());
                    if (d.equals("ps.es.net")) {
                        port.setId(port.getId().replace("ps.es.net","es.net"));
                    }
                    // Back reference: it is useful to retrieve the Node object from a port.
                    port.setNode(node);
                    List<ESnetLink> links = port.getLinks();
                    for (ESnetLink link : links) {
                        // Patch the domain name (remove ps.)
                        d = ESnetTopology.idToDomain(link.getId());
                        if (d.equals("ps.es.net")) {
                            link.setId(link.getId().replace("ps.es.net", "es.net"));
                        }
                        d = ESnetTopology.idToDomain(link.getRemoteLinkId());
                        if (d.equals("ps.es.net")) {
                            link.setRemoteLinkId(link.getRemoteLinkId().replace("ps.es.net", "es.net"));
                        }

                        if (this.links.containsKey(link.getId())) {
                            // This is a link that is described in both domain elements. This can only happen
                            // when processing the second domain element. Merge and continue to the next link.
                            ESnetLink l = (ESnetLink) this.links.get(link.getId());
                            continue;
                        }
                        if ( ! this.nodeByLink.containsKey(link.getId())) {
                            // Add the node to the index per Link
                            this.nodeByLink.put(link.getId(), node);
                        }
                        if (! this.portByLink.containsKey(link.getId())) {
                            // Add the port to portbyLink index
                            this.portByLink.put(link.getId(), port);
                        }

                        String localDomain = ESnetTopology.idToDomain(link.getId());
                        String localNode = ESnetTopology.idToName(link.getId());
                        String remoteDomain = ESnetTopology.idToDomain(link.getRemoteLinkId());
                        String remoteNode = null;
                        try {
                            remoteNode = ESnetTopology.idToName(link.getRemoteLinkId());
                        } catch (ArrayIndexOutOfBoundsException e) {
                            // This is a work around for a link that seems to have an incorrect remoteId
                            logger.warn("Cannot parse link= " + link.getId() + " remoteLink= " + link.getRemoteLinkId());
                            continue;
                        }
                        String remoteNodeId = idToUrn(link.getRemoteLinkId(),4);

                        // Add the link to the links HashMap, index it with the port urn.
                        if (this.links.containsKey(idToUrn(link.getId(), 5))) {
                        // if (this.links.containsKey(link.getId())) {
                            continue;
                        }
                        this.links.put(idToUrn(link.getId(),5),link);

                        if (localDomain.equals(remoteDomain)) {
                            // Within the same domain
                            if ( !localNode.equals(remoteNode)) {
                                // Nodes are different, within the same domain: this is an internal link
                                ESnetNode dstNode = this.nodes.get(remoteNodeId);
                                if (dstNode == null) {
                                    throw new RuntimeException("No Node");
                                }
                                this.addLinkToList(this.internalLinks,remoteNode,link);
                            }  else {
                                // This is a link to a site
                                List<Link> list = this.siteLinks.get(remoteNode);
                                if (list == null) {
                                    list = new ArrayList<Link>();
                                }
                                list.add(link);
                                this.siteLinks.put(remoteNode,list);
                            }
                        } else {
                            // This is a link to another domain
                            List<Link> list = this.domainLinks.get(remoteNode);
                            if (list == null) {
                                list = new ArrayList<Link>();
                            }
                            list.add(link);
                            this.domainLinks.put(remoteNode,list);

                        }
                    }
                }
            }
       }
    }

    /**
     * This method returns a Listenable, Directed and Weighted graph of ESnet topology. While ESnet 5 links are
     * to be assumed to be bidirectional, the generic API does not. Therefore, each links are in fact two identical
     * links, but in reverse directions. The weight is directly taken off the traffic engineering metrics as
     * stated in the topology wire format.
     *
     * @return
     */
    @Override
	public DefaultListenableGraph<ESnetNode, ESnetLink> getGraph (DateTime start,
                                                                           DateTime end,
                                                                           WeightType weightType) throws IOException {

        HashMap<ESnetPort, OSCARSReservations.PortReservation> reservations = null;
        if (weightType == WeightType.MaxBandwidth) {
            // Retrieve the reservations only once and cache it
            reservations = (new OSCARSReservations(this)).getReserved(start, end);
        }

		DefaultListenableGraph<ESnetNode,ESnetLink> graph =
                new ESnetTopologyWeightedGraph(ESnetLink.class);

        // First, add all Vertices
        for (ESnetNode node : this.nodes.values()) {
            graph.addVertex(node);
        }
        // Second, add all internal Edges.
        for (List<Link> links : this.internalLinks.values()) {
            for (Link l : links) {
                if ( ! (l instanceof ESnetLink) ) {
                    // This should not happen
                    throw new RuntimeException ("Link is not an ESnetLink");
                }
                ESnetLink link = (ESnetLink) l;
                Node n = this.nodeByLink.get(link.getId());
                if (n == null) {
                    // This should not happen
                    throw new RuntimeException("Link without Nodes " + link.getId());
                }
                if ( ! (n instanceof ESnetNode)) {
                    // This should not happen
                    throw new RuntimeException("Node is not an ESnetNode");
                }
                ESnetNode srcNode = (ESnetNode) n;
                Node r = this.getOppositeNode(link, srcNode);
                if (r == null) {
                    continue;
                }
                if ( ! (r instanceof  ESnetNode)) {
                    throw new RuntimeException("Node is not an ESnetNode " + r.getClass().getCanonicalName());
                }
                ESnetNode dstNode = (ESnetNode) r;
                // Create the Edge
                boolean success = false;
                try {
                    success = graph.addEdge(srcNode,dstNode,link);
                } catch (IllegalArgumentException e) {
                    // TODO: lomax@es.net need to understand why;
                }
                if ( !success ) {
                    // The edge has been ignored by the graph
                    logger.warn("A link has been ignored by the graph: " + link.getId() + " remoteId= " + link.getRemoteLinkId());
                    continue;
                }

                // Add the weight
                long metric = 0;
                if (weightType == WeightType.TrafficEngineering) {
                    metric = link.getTrafficEngineeringMetric();
                    graph.setEdgeWeight(link, metric);
                } else if (weightType == WeightType.MaxBandwidth) {
                    // Retrieve the source port of the link
                    Port port = this.portByLink.get(link.getId());
                    // This is the port of the source Node connected to that Link
                    OSCARSReservations.PortReservation res = reservations.get(port);
                    if (res != null) {
                        // First element of alreadyReserved is the path forward. Compute the available
                        // reservable bandwidth and set it as the weight of the graph.
                        long available = res.maxReservable - res.alreadyReserved[0];
                        metric = available;
                    } else {
                        // The link is not reservable. Set the weight to MAX_VALUE
                        metric = Long.MAX_VALUE;
                    }
                    graph.setEdgeWeight(link, metric);
                }
            }
        }
        return graph;
    }



    private void addLinkToList ( HashMap<String, List<Link>> map, String name, ESnetLink link)  {
        synchronized (map) {
            List<Link> list = map.get(name);
            if (list == null) {
                // This is a new name in tha map. Need to create an new entry in the map
                list = new ArrayList<Link>();
                map.put(name, list);
            }
            // Add the link to the list
            list.add(link);
        }
    }

    public List<Link> getLinksToSite (String destination) {
        return this.siteLinks.get(destination);
    }

    static public String idToUrn (String id, int pos) {
        int endPos=0;
        for (int i=0; i <= pos; ++i) {
            endPos = id.indexOf(":", endPos + 1);
        }
        return id.substring(0,endPos);
    }

    public static void registerToFactory() throws IOException {
        TopologyFactory.instance().registerTopologyProvider(
                ESnetTopology.class.getCanonicalName(),
                TopologyFactory.LOCAL_LAYER2);
    }

    @Override
    public Node getNode(String name) {
        if (name == null) {
            return null;
        }
        // Construct the URN
        String[] tmp = name.split("@");
        if (tmp.length != 2) {
            // Incorrect format.
        }
        String hostname = tmp[0];
        String domain = tmp[1];
        String urn = "urn:ogf:network:" + domain + ":" + hostname;

        return this.nodes.get(urn);
    }

    public static String idToName (String id) {
        return id.split(":")[4];
    }

    public static String idToDomain (String id) {
        return id.split(":")[3];
    }
    public static String idToDescription (String id) {
        return id.split(":")[5];
    }
    public static String idToLinkId (String id) {
        return id.split(":")[6];
    }

    /**
     * Search links for id matching the provided id. Search first for exact match and then for link with
     * linkid of "*".
     * @param id
     * @return
     */
    public ESnetLink searchLink(String id) {

        if (this.links.containsKey(id)) {
            // Exact match
            return (ESnetLink) this.links.get(id);
        }
        String tmpId = id;
        tmpId = tmpId.substring(0,tmpId.lastIndexOf(":")) + "*";
        if (this.links.containsKey(tmpId)) {
            // Match with "*" (any)
            return (ESnetLink) this.links.get(tmpId);
        }
        tmpId = tmpId.substring(0,tmpId.lastIndexOf(":")) + "0";
        if (this.links.containsKey(tmpId)) {
            // Match with "*" (any)
            return (ESnetLink) this.links.get(tmpId);
        }
        return null;
    }
    /**
     * Search links for id matching the provided id. Search first for exact match and then for link with
     * linkid of "*".
     * @param id
     * @return
     */
    public ESnetPort searchPortByLink(String id) {

        if (this.portByLink.containsKey(id)) {
            // Exact match
            return (ESnetPort) this.portByLink.get(id);
        }
        String tmpId = id;
        tmpId = tmpId.substring(0,tmpId.lastIndexOf(":")) + "*";
        if (this.links.containsKey(tmpId)) {
            // Match with "*" (any)
            return (ESnetPort) this.portByLink.get(tmpId);
        }
        tmpId = tmpId.substring(0,tmpId.lastIndexOf(":")) + "0";
        if (this.links.containsKey(tmpId)) {
            // Match with "*" (any)
            return (ESnetPort) this.portByLink.get(tmpId);
        }
        return null;
    }

}
