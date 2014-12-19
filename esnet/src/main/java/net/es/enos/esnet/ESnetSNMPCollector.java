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
import org.codehaus.jackson.JsonGenerationException;
import org.codehaus.jackson.annotate.JsonIgnore;
import org.codehaus.jackson.map.JsonMappingException;
import org.codehaus.jackson.map.ObjectMapper;
import org.codehaus.jackson.type.TypeReference;
import org.codehaus.jettison.json.JSONException;
import org.codehaus.jettison.json.JSONObject;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

/**
 * Created by lomax on 7/2/14.
 */
public class ESnetSNMPCollector {
    public static String SNMP_COLLECTOR_URL = "http://snmp-east.es.net:8001/snmp/";

    public static String loadFromUrl(String request) {

        try {
            ClientConfig clientConfig = new DefaultClientConfig();

            Client client = Client.create(clientConfig);
            clientConfig.getFeatures().put(JSONConfiguration.FEATURE_POJO_MAPPING, Boolean.TRUE);

            WebResource webResource = client.resource(SNMP_COLLECTOR_URL + request);

            ClientResponse response = webResource.accept("application/json").get(ClientResponse.class);
            if (response.getStatus() != 200) {
                throw new RuntimeException("Failed : HTTP error code : "
                        + response.getStatus());
            }

            String output = response.getEntity(String.class);
            return output;

        } catch (Exception e) {

            e.printStackTrace();
            return null;
        }
    }

    public static List<ESnetSNMPNode> getNodes() {
        ArrayList<String> nodes = new ArrayList<String>();
        // Retrieve the nodes from the base SNMP API
        String wireformat = ESnetSNMPCollector.loadFromUrl("");
        // Create JSON objects - the following code should be made generic but I (lomax@es.net) has not been
        // able to make TypeReference work with the class as a parameter. TODO: fix it.
        ObjectMapper mapper = new ObjectMapper();
        ESnetSNMPNodes nodesRoot = null;
        try {
            JSONObject jsonObj = new JSONObject(wireformat);
            nodesRoot = mapper.readValue(jsonObj.toString(),
                    new TypeReference<ESnetSNMPNodes>()
                    {
                    });
            return nodesRoot.getChildren();
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

    public static List<ESnetSNMPInterface> getInterface(String nodeName) {
        ArrayList<ESnetSNMPInterface> nodes = new ArrayList<ESnetSNMPInterface>();
        String wireformat = ESnetSNMPCollector.loadFromUrl(nodeName + "/interface/");

        // Create JSON objects - the following code should be made generic but I (lomax@es.net) has not been
        // able to make TypeReference work with the class as a parameter. TODO: fix it.
        ObjectMapper mapper = new ObjectMapper();
        ESnetSNMPInterfaceWrapper root = null;
        try {
            JSONObject jsonObj = new JSONObject(wireformat);
            root = mapper.readValue(jsonObj.toString(),
                    new TypeReference<ESnetSNMPInterfaceWrapper>()
                    {
                    });
            return root.getChildren();
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

    @JsonIgnore
    public static ESnetSNMPCounter getData (String nodeName, String ifName,String type) {
        // Build the URI
        String uri = nodeName + "/interface/" + interfaceToURI(ifName) + "/" + type;
        String wireformat = ESnetSNMPCollector.loadFromUrl(uri);

        // Create JSON objects - the following code should be made generic but I (lomax@es.net) has not been
        // able to make TypeReference work with the class as a parameter. TODO: fix it.
        ObjectMapper mapper = new ObjectMapper();
        ESnetSNMPCounter root = null;
        try {
            JSONObject jsonObj = new JSONObject(wireformat);
            root = mapper.readValue(jsonObj.toString(),
                    new TypeReference<ESnetSNMPCounter>()
                    {
                    });

            return root;

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
     * Make the interface name be URI friendly: since "/" is significant in a uri, ports names such as
     * xe-1/2/0 need to be changed into xe-1_2_0
     * @param ifName
     * @return
     */
    public static String interfaceToURI(String ifName) {
        return ifName.replace('/','_');
    }


}
