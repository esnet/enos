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

import com.sun.jersey.api.client.Client;

import com.sun.jersey.api.client.ClientResponse;
import com.sun.jersey.api.client.WebResource;
import com.sun.jersey.api.client.config.ClientConfig;
import com.sun.jersey.api.client.config.DefaultClientConfig;

import com.sun.jersey.api.json.JSONConfiguration;
import com.sun.jersey.client.urlconnection.HTTPSProperties;
import net.es.enos.api.*;
import org.codehaus.jackson.JsonGenerationException;
import org.codehaus.jackson.map.JsonMappingException;
import org.codehaus.jackson.map.ObjectMapper;
import org.codehaus.jackson.type.TypeReference;
import org.codehaus.jettison.json.JSONException;
import org.codehaus.jettison.json.JSONObject;
import org.jgrapht.Graph;
import org.jgrapht.GraphPath;
import org.jgrapht.graph.GraphPathImpl;
import org.jgrapht.graph.ListenableDirectedGraph;
import org.jgrapht.graph.ListenableDirectedWeightedGraph;
import org.python.modules.synchronize;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import javax.net.ssl.*;
import java.io.*;
import java.security.cert.CertificateException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;


/**
 * Created by lomax on 5/16/14.
 */
public class ESnetTopology implements TopologyProvider {
    public static final String ESNET_DEFAULT_URL = "https://oscars.es.net/topology-publisher";
    private final Logger logger = LoggerFactory.getLogger(ESnetTopology.class);
    private String wireFormatTopology;
    private ESnetJSONTopology jsonTopology;
    private String url;

    private HashMap<String, ESnetNode> nodes = new HashMap<String, ESnetNode>();
    private HashMap<Link,List<Node>> nodesByLink = new HashMap<Link, List<Node>>();
    private HashMap<Link,List<Port>> portsByLink = new HashMap<Link, List<Port>>();
    private HashMap<String, List<Link>> internalLinks = new HashMap<String, List<Link>>();
    private HashMap<String, List<Link>> siteLinks = new HashMap<String, List<Link>>();
    private HashMap<String, List<Link>> peeringLinks = new HashMap<String, List<Link>>();
    private HashMap<String, Link> links = new HashMap<String, Link>();
    private boolean isWeighted = true;

    public class TopologyTrustManager implements X509TrustManager {

        @Override
        public void checkClientTrusted(java.security.cert.X509Certificate[] x509Certificates, String s) throws CertificateException {

        }

        @Override
        public void checkServerTrusted(java.security.cert.X509Certificate[] x509Certificates, String s) throws CertificateException {

        }

        @Override
        public java.security.cert.X509Certificate[] getAcceptedIssuers() {
            return new java.security.cert.X509Certificate[0];
        }
    }

    public ESnetTopology() {
        this.init();
    }

    public ESnetTopology(boolean isWeighted) {
        this.isWeighted = isWeighted;
        this.init();
    }

    /**
     * This constructor reads the provided file to load the topology in the wire format, instead of
     * downloading it from the topology service. This is useful when network is not available and only
     * a cached version of the topology can be used.
     * @param filename  of the file containing the topology in wire format
     * @throws IOException
     */
    public ESnetTopology(String filename) throws IOException {
        InputStream in = new FileInputStream(filename);
        StringBuffer stringbuffer = new StringBuffer();
        byte[] buffer = new byte[4096];
        while (true) {
            int r = in.read(buffer);
            if (r <= 0) {
                // EOF
                break;
            }
            new String(buffer,0, r);
            stringbuffer.append(new String(buffer,0, r));
        }
        this.wireFormatTopology = stringbuffer.toString();
        this.jsonTopology = this.wireFormatToJSON(this.wireFormatTopology);
    }

    public String loadTopology() {

        try {
            ClientConfig clientConfig = new DefaultClientConfig();


            SSLContext sslcontext = null;
            TrustManager[] trustAllCerts = new TrustManager[]{new TopologyTrustManager()};

            HTTPSProperties httpsProperties = new HTTPSProperties(
                    new HostnameVerifier() {
                        @Override
                        public boolean verify( String s, SSLSession sslSession ) {
                            // whatever your matching policy states
                            logger.info("Verifying SSL Session");
                            return true;
                        }
                    }
            );

            clientConfig.getProperties().put(HTTPSProperties.PROPERTY_HTTPS_PROPERTIES, httpsProperties);
            sslcontext = httpsProperties.getSSLContext();
            sslcontext.init(null, trustAllCerts, null);
            Client client = Client.create(clientConfig);
            clientConfig.getFeatures().put(JSONConfiguration.FEATURE_POJO_MAPPING, Boolean.TRUE);

            WebResource webResource = client.resource(ESnetTopology.ESNET_DEFAULT_URL);

            ClientResponse response = webResource.accept("application/json").get(ClientResponse.class);
            if (response.getStatus() != 200) {
                throw new RuntimeException("Failed : HTTP error code : "
                        + response.getStatus());
            }

            String output = response.getEntity(String.class);
            logger.info("Retrieved ESnet topology");
            output = this.normalize(output);
            return output;

        } catch (Exception e) {

            e.printStackTrace();
            return null;
        }
    }

    public HashMap<String, ESnetNode> getNodes() {
        return nodes;
    }

    /**
     * Returns a HashMap of List of Links that connects to or from a Site to ESnet. The map is indexed by
     * the name of the site as found in the topology.
     * @return returns the indexed Map.
     */
    public HashMap<String, List<Link>> getSiteLinks() {
        return siteLinks;
    }

    /**
     * Returns a HashMap of List of Links that connects to or from another Domain (OSCARS peering) to ESnet. The map is indexed by
     * the name of the domain as found in the topology.
     * @return returns the indexed Map.
     */
    public HashMap<String, List<Link>> getPeeringLinks() {
        return peeringLinks;
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
    public HashMap<Link, List<Node>> getNodesByLink() {
        return nodesByLink;
    }

    public HashMap<Link, List<Port>> getPortsByLink() {
        return portsByLink;
    }

    public HashMap<String, Link> getLinks() {
        return links;
    }

    private void init() {
        this.wireFormatTopology = this.loadTopology();
        this.jsonTopology = this.wireFormatToJSON(this.wireFormatTopology);
    }

    public ESnetJSONTopology retrieveJSONTopology() {
        if (this.jsonTopology == null) this.init();
        return this.jsonTopology;
    }

    public ESnetJSONTopology wireFormatToJSON (String topology) {
        ObjectMapper mapper = new ObjectMapper();

        try {
            JSONObject jsonObj = new JSONObject(topology);
            ESnetJSONTopology jsonTopology = mapper.readValue(jsonObj.toString(), new TypeReference<ESnetJSONTopology>()
            {
            });
            return jsonTopology;
        } catch (JsonGenerationException e) {

            e.printStackTrace();

        } catch (JsonMappingException e) {

            e.printStackTrace();

        } catch (IOException e) {

            e.printStackTrace();

        } catch (JSONException e) {
            e.printStackTrace();
        }
        return null;
    }

    /**
     * ESnet esnet uses two different format in ID:
     *    1) urn:ogf:network:domain=es.net:node=sunn-cr5:port=to_sunn-ixia-mgmt:link=*
     *    2) urn:ogf:network:es.net:sunn-cr5:to_sunn-ixia-mgmt:*
     */
    public String normalize(String wireformat) {
        wireformat = wireformat.replaceAll("(?:domain=)","");
        wireformat = wireformat.replaceAll("(?:node=)","");
        wireformat = wireformat.replaceAll("(?:link=)","");
        wireformat = wireformat.replaceAll("(?:port=)","");
        return wireformat;
    }

    public ListenableDirectedGraph retrieveTopology () {
        if (this.jsonTopology == null) this.init();
        nodes.clear();
        ListenableDirectedWeightedGraph<ESnetNode,ESnetLink> topo =
                new ESnetTopologyWeightedGraph(ESnetLink.class);

        List<ESnetDomain> domains = this.jsonTopology.getDomains();
        ESnetDomain esnet = domains.get(0);
        List<ESnetNode> nodes = esnet.getNodes();
        for (ESnetNode node : nodes) {
            this.nodes.put(node.getId(),node);
            topo.addVertex(node);
        }
        for (ESnetNode node : nodes) {
            List<ESnetPort> ports = node.getPorts();
            for (ESnetPort port : ports) {
                List<ESnetLink> links = port.getLinks();
                for (ESnetLink link : links) {
                    // Add this link to the nodesByLink map
                    synchronized (this.nodesByLink) {
                        List<Node> list = this.nodesByLink.get(link);
                        if (list == null) {
                            // This is a new name in tha map. Need to create an new entry in the map
                            list = new ArrayList<Node>();
                            this.nodesByLink.put(link, list);
                        }
                        // Add the link to the list
                        list.add(node);
                    };
                    // Add this link to the portsByLink map
                    synchronized (this.portsByLink) {
                        List<Port> list = this.portsByLink.get(link);
                        if (list == null) {
                            // This is a new name in tha map. Need to create an new entry in the map
                            list = new ArrayList<Port>();
                            this.portsByLink.put(link, list);
                        }
                        // Add the link to the list
                        list.add(port);
                    };
                    this.analyzeLink(topo, node, link, link.getTrafficEngineeringMetric());
                }

            }
        }
        return topo;
    }

	public ListenableDirectedGraph retrieveBandwidthTopology () {
		if (this.jsonTopology == null) this.init();
		nodes.clear();
		ListenableDirectedWeightedGraph<ESnetNode,ESnetLink> topo =
				new ESnetTopologyWeightedGraph(ESnetLink.class);

		List<ESnetDomain> domains = this.jsonTopology.getDomains();
		ESnetDomain esnet = domains.get(0);
		List<ESnetNode> nodes = esnet.getNodes();
		for (ESnetNode node : nodes) {
			this.nodes.put(node.getId(),node);
			topo.addVertex(node);
		}
		for (ESnetNode node : nodes) {
			List<ESnetPort> ports = node.getPorts();
			for (ESnetPort port : ports) {
				double bandwidth = Double.parseDouble(port.getMaximumReservableCapacity());
				List<ESnetLink> links = port.getLinks();
				for (ESnetLink link : links) {
					// Add this link to the nodesByLink map
					synchronized (this.nodesByLink) {
						List<Node> list = this.nodesByLink.get(link);
						if (list == null) {
							// This is a new name in tha map. Need to create an new entry in the map
							list = new ArrayList<Node>();
							this.nodesByLink.put(link, list);
						}
						// Add the link to the list
						list.add(node);
					};
					// Add this link to the portsByLink map
					synchronized (this.portsByLink) {
						List<Port> list = this.portsByLink.get(link);
						if (list == null) {
							// This is a new name in the map. Need to create an new entry in the map
							list = new ArrayList<Port>();
							this.portsByLink.put(link, list);
						}
						// Add the link to the list
						list.add(port);
					};
					this.analyzeLink(topo, node, link, bandwidth);
				}

			}
		}
		return topo;
	}

	private void analyzeLink(ListenableDirectedWeightedGraph<ESnetNode,
                             ESnetLink> topo,
                             ESnetNode srcNode,
                             ESnetLink link,
                             double metric) {

        String[] localId = link.getId().split(":");
        String localDomain = localId[3];
        String localNode = localId[4];
        String localNodeId = idToUrn(link.getId(),4);
        String[] remoteId = link.getRemoteLinkId().split(":");
        String remoteDomain = remoteId[3];
        String remoteNode = remoteId[4];
        String remoteNodeId = idToUrn(link.getRemoteLinkId(),4);

        // Add the link to the links HashMap, index it with the port urn.
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
                // Create the edge in the graph
                topo.addEdge(srcNode,dstNode,link);
                // Make sure the opposite direction exists since ESnet links are to be assumed bidirectional
                topo.addEdge(dstNode,srcNode,link);
                if (this.isWeighted) {
                    // Add traffic engineering as weight
                    topo.setEdgeWeight(link,metric);
                }
            } else {
                // Site - This is not link, so, do not create an edge
                // Try to decode the site name. If the port section of the id starts with to- then
                // the destination is encoded.
                if (remoteId[5].startsWith("to_")) {
                    String dest = remoteId[5].substring(3);
                    this.addLinkToList(this.siteLinks,dest,link);
                }
            }
        } else {
            // Peering - This is an intra-domain topology. Other domains are not represented so this link is not
            // added.
            this.addLinkToList(this.peeringLinks,remoteId[3],link);
        }
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
    /***
    public GraphPath<Node,Link> linksToGraph(List<ESnetLink> links) {
        ListenableDirectedGraph<ESnetNode,ESnetLink> graph =
                new ListenableDirectedGraph<ESnetNode, ESnetLink>(ESnetLink.class);
        Node srcNode = null;
        Node dstNode = null;
        Node currentNode = null;
        Node previousNode = null;

        for (ESnetLink link : links) {
            // Get source Node
            List<Node> srcNodes = this.nodesByLink.get(link);
            if ((srcNodes == null) || (srcNodes.size() == 0)) {
                // This should not happen
                logger.error("No source nodes for link " + link.getId());
                return null;
            }
            previousNode = currentNode;
            currentNode = (Node) srcNodes.toArray()[0];
            // Add the node to the graph
            graph.addVertex((ESnetNode) currentNode);
            // Check if this is the first node of the path
            if (srcNode == null) {
                // First Node
                srcNode = currentNode;
            } else {
                graph.addEdge((ESnetNode) previousNode, (ESnetNode) currentNode, link);
                // Add reverse link
                graph.addEdge((ESnetNode) currentNode, (ESnetNode) previousNode, link);
            }
        }
        // Last currentNot is the destination Node
        dstNode = currentNode;
        // Build a GrapPath
        // GraphPathImpl<Node,Link> grapPath = new GraphPathImpl<Node, Link>(graph,srcNode,dstNode );
        return grapPath;
    }
    ****/

    static private String idToUrn (String id, int pos) {
        int endPos=0;
        for (int i=0; i <= pos; ++i) {
            endPos = id.indexOf(":", endPos + 1);
        }
        return id.substring(0,endPos);

    }

    /**
     * Strip trailing link portion of the urn
     * @param linkId
     * @return a normalized link id.
     */
    static public String normalizeLinkId(String linkId) {

        return null;
    }

    public String getUrl() {
        return url;
    }

    public void setUrl(String url) {
        this.url = url;
    }

    public void registerToFactory() throws IOException {
        TopologyFactory.instance().registerTopologyProvider(this.getClass().getCanonicalName(),TopologyFactory.LOCAL_LAYER2);
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
}
