/*
 * Copyright (c) 2014, Regents of the University of California  All rights reserved.
 * Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
 * 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

package net.es.enos.topology;

import com.sun.jersey.api.client.Client;

import com.sun.jersey.api.client.ClientResponse;
import com.sun.jersey.api.client.WebResource;
import com.sun.jersey.api.client.config.ClientConfig;
import com.sun.jersey.api.client.config.DefaultClientConfig;

import com.sun.jersey.api.json.JSONConfiguration;
import com.sun.jersey.client.urlconnection.HTTPSProperties;
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
import java.io.File;
import java.io.IOException;
import java.security.cert.CertificateException;


/**
 * Created by lomax on 5/16/14.
 */
public class ESnetTopology {
    public static final String ESNET_DEFAULT_URL = "https://oscars.es.net/topology-publisher";
    private final Logger logger = LoggerFactory.getLogger(ESnetTopology.class);
    private String wireFormatTopology;
    private ESnetJSONTopology jsonTopology;

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
        this.wireFormatTopology = this.retrieveTopology();
        this.jsonTopology = this.wireFormatToJSON(this.wireFormatTopology);
    }
    public String retrieveTopology() {

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

    public ESnetJSONTopology getJSONTopology() {
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
     * ESnet topology uses two different format in ID:
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

    public ListenableDirectedGraph getGraph () {
        ListenableDirectedGraph graphToplogy = null;

        return null;
    }
}

