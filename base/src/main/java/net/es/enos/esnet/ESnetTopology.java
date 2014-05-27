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
import net.es.enos.api.TopologyFactory;
import net.es.enos.api.TopologyProvider;
import org.codehaus.jackson.JsonGenerationException;
import org.codehaus.jackson.map.JsonMappingException;
import org.codehaus.jackson.map.ObjectMapper;
import org.codehaus.jackson.type.TypeReference;
import org.codehaus.jettison.json.JSONException;
import org.codehaus.jettison.json.JSONObject;
import org.jgrapht.graph.ListenableDirectedGraph;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import javax.net.ssl.*;
import java.io.IOException;
import java.security.cert.CertificateException;
import java.util.HashMap;
import java.util.List;


/**
 * Created by lomax on 5/16/14.
 */
public class ESnetTopology extends TopologyProvider {
    public static final String ESNET_DEFAULT_URL = "https://oscars.es.net/topology-publisher";
    private final Logger logger = LoggerFactory.getLogger(ESnetTopology.class);
    private String wireFormatTopology;
    private ESnetJSONTopology jsonTopology;
    private String url;

    private HashMap<String, ESnetNode> nodes = new HashMap<String, ESnetNode>();
    private HashMap<String, ESnetNode> sites = new HashMap<String, ESnetNode>();
    private HashMap<String, ESnetNode> peerings = new HashMap<String, ESnetNode>();

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

    public ESnetTopology() throws IOException {
        super();
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

    public HashMap<String, ESnetNode> getSites() {
        return sites;
    }

    public HashMap<String, ESnetNode> getPeerings() {
        return peerings;
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
        ListenableDirectedGraph<ESnetNode,ESnetLink> topo =
                new ListenableDirectedGraph<ESnetNode,ESnetLink>(ESnetLink.class);

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
                    this.analyzeLink(topo, node, link);
                }

            }
        }
        return topo;
    } 
    private void analyzeLink(ListenableDirectedGraph<ESnetNode,ESnetLink> topo, ESnetNode srcNode, ESnetLink link) {
        // System.out.println(node.getId() + " -- " + link.getId() + " -- " + link.getRemoteLinkId());
        String[] localId = link.getId().split(":");
        String localDomain = localId[3];
        String localNode = localId[4];
        String localNodeId = idToUrn(link.getId(),4);
        String[] remoteId = link.getRemoteLinkId().split(":");
        String remoteDomain = remoteId[3];
        String remoteNode = remoteId[4];
        String remoteNodeId = idToUrn(link.getRemoteLinkId(),4);
        if (localDomain.equals(remoteDomain)) {
            // Within ESnet
            if ( !localNode.equals(remoteNode)) {
                // Nodes are different, this is link
                // System.out.println("INTERNAL LINK " + localNodeId + " -- " + link.getId() + " -- " + link.getRemoteLinkId());
                ESnetNode dstNode = this.nodes.get(remoteNodeId);
                if (dstNode == null) {
                    throw new RuntimeException("No Node");
                }
                topo.addEdge(srcNode,dstNode,link);
            } else {
                // Site
                ESnetSite site = new ESnetSite(remoteNodeId);
                topo.addVertex(site);
                this.sites.put(remoteNodeId,site);
                topo.addEdge(srcNode,site,link);
                topo.addEdge(site,srcNode,link);
            }
        } else {
            // Peering
            ESnetPeering peering = new ESnetPeering(remoteNodeId);
            topo.addVertex(peering);
            this.sites.put(remoteNodeId,peering);
            topo.addEdge(srcNode,peering,link);
            topo.addEdge(peering,srcNode,link);
        }
    }

    static public String idToUrn (String id, int pos) {
        int endPos=0;
        for (int i=0; i <= pos; ++i) {
            endPos = id.indexOf(":", endPos + 1);
        }
        return id.substring(0,endPos);

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

    // urn:ogf:network:es.net:wash-sdn2:xe-8/0/0:*
}
