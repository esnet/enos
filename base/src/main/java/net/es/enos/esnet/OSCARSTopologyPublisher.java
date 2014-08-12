/*
 * Copyright (c) 2014, Regents of the University of California  All rights reserved.
 * Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
 * 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

package net.es.enos.esnet;

import com.sun.jersey.api.client.Client;
import com.sun.jersey.api.client.ClientResponse;
import com.sun.jersey.api.client.WebResource;
import com.sun.jersey.api.client.config.ClientConfig;
import com.sun.jersey.api.client.config.DefaultClientConfig;
import com.sun.jersey.api.json.JSONConfiguration;
import com.sun.jersey.client.urlconnection.HTTPSProperties;
import net.es.enos.api.PersistentObject;
import net.es.enos.api.TopologyFactory;
import org.codehaus.jackson.JsonGenerationException;
import org.codehaus.jackson.map.JsonMappingException;
import org.codehaus.jackson.map.ObjectMapper;
import org.codehaus.jackson.type.TypeReference;
import org.codehaus.jettison.json.JSONException;
import org.codehaus.jettison.json.JSONObject;
import org.joda.time.DateTime;
import org.joda.time.format.DateTimeFormat;
import org.joda.time.format.DateTimeFormatter;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import javax.net.ssl.*;
import java.io.*;
import java.nio.file.Paths;
import java.security.cert.CertificateException;

/**
 * Implements the retrival, parsing and archiving of the topology published by OSCARS. It contains the topology that
 * reservable by OSCARS as well as the layer 3 topology.
 */
public class OSCARSTopologyPublisher {
    public static final String ESNET_DEFAULT_URL = "https://oscars.es.net/topology-publisher";
    public static final String CACHE_DIR = "cache";
    public static final String CACHE_FILE_PREFIX = "oscars";
    private final Logger logger = LoggerFactory.getLogger(OSCARSTopologyPublisher.class);
    private DateTime date;

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

    public OSCARSTopologyPublisher() {
        this.date = DateTime.now();
    }

    public OSCARSTopologyPublisher(String date) {
        DateTimeFormatter formatter = DateTimeFormat.forPattern("dd/MM/yyyy");
        this.date = formatter.parseDateTime(date);
    }

    public String toString() {
        // Check if we have today's topology already cached
        if (this.isCached()) {
            try {
                logger.info("Loading topology from cache");
                return this.loadTopology();
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
        // If date is not today and there was no archive, return null
        if ( ! this.isToday()) {
            return null;
        }

        // Today's topology has not yet been downloaded or there was a problem reading it from file. Download
        // from URL.
        String topology = this.loadFromUrl();
        if (topology == null) {
            return null;
        }
        // Save it into the cache / archive
        try {
            this.saveTopology(topology);
        } catch (IOException e) {
            e.printStackTrace();
        }
        return topology;
    }

    public boolean isToday() {
        DateTime now = DateTime.now();
        return this.date.withTimeAtStartOfDay().isEqual(now.withTimeAtStartOfDay());
    }
    /**
     * This method reads the provided file to load the topology in the wire format, instead of
     * downloading it from the topology service. This is useful when network is not available and only
     * a cached version of the topology can be used.
     * @param file
     * @throws java.io.IOException
     */
    private String loadFromFile (File file) throws IOException {
        InputStream in = new FileInputStream(file);
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
        return stringbuffer.toString();
    }

    private String loadTopology() throws IOException {
        File file = this.buildCachedFile();
        return this.loadFromFile(file);
    }

    private void saveTopology(String topology) throws IOException {
        File file = this.buildCachedFile();
        this.saveToFile(file, topology);
    }

    private void saveToFile (File file, String wireFormat) throws IOException {
        if ((wireFormat == null) || (wireFormat.length() == 0)) {
            // Nothing to save, just return
            logger.warn("Topology wire format is empty or null");
            return;
        }
        /* Make sure all directories exist */
        file.getParentFile().mkdirs();
        OutputStream out = new FileOutputStream(file);
        out.write(wireFormat.getBytes());
        out.flush();
    }
    /**
     * Check if there is topology in the cache that was retrieved from the URL today.
     * @return
     */
    private boolean isCached() {
        File file = this.buildCachedFile();
        return file.exists();
    }

    public File buildCachedFile() {

        String fileName = CACHE_FILE_PREFIX + "." +
                this.date.getYear() + "-" +
                this.date.getMonthOfYear() + "-" +
                this.date.getDayOfMonth();

        String filePath = Paths.get(
                TopologyFactory.FACTORY_DIR,
                CACHE_DIR,
                fileName).toString();
        // Get the Operating System absulute path
        File file = PersistentObject.buildFile(filePath);
        return file;
    }


    /**
     * Loads the topology from the ESnet URL. The result is in JSON format.
     * @return a single string that contains the whole topology in its wire format.
     */
    private String loadFromUrl () {

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

            WebResource webResource = client.resource(OSCARSTopologyPublisher.ESNET_DEFAULT_URL);

            ClientResponse response = webResource.accept("application/json").get(ClientResponse.class);
            if (response.getStatus() != 200) {
                throw new RuntimeException("Failed : HTTP error code : "
                        + response.getStatus());
            }

            String output = response.getEntity(String.class);
            output = this.normalize(output);
            return output;

        } catch (Exception e) {
           logger.warn("Cannot retrieve the topology");
            return null;
        }
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

    public ESnetJSONTopology toJSON () {
        ObjectMapper mapper = new ObjectMapper();

        try {
            String json = this.toString();
            if ((json == null) || (json.length() == 0)) {
                return null;
            }
            JSONObject jsonObj = new JSONObject(this.toString());
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

}
