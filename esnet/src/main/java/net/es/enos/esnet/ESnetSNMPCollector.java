/*
 * ESnet Network Operating System (ENOS) Copyright (c) 2015, The Regents
 * of the University of California, through Lawrence Berkeley National
 * Laboratory (subject to receipt of any required approvals from the
 * U.S. Dept. of Energy).  All rights reserved.
 *
 * If you have questions about your rights to use or distribute this
 * software, please contact Berkeley Lab's Innovation & Partnerships
 * Office at IPO@lbl.gov.
 *
 * NOTICE.  This Software was developed under funding from the
 * U.S. Department of Energy and the U.S. Government consequently retains
 * certain rights. As such, the U.S. Government has been granted for
 * itself and others acting on its behalf a paid-up, nonexclusive,
 * irrevocable, worldwide license in the Software to reproduce,
 * distribute copies to the public, prepare derivative works, and perform
 * publicly and display publicly, and to permit other to do so.
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
