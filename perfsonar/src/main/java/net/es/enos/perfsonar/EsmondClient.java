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
package net.es.enos.perfsonar;

import org.slf4j.Logger;
import org.codehaus.jackson.map.ObjectMapper;
import org.codehaus.jackson.type.TypeReference;
import org.slf4j.LoggerFactory;

import java.net.URI;
import java.net.URISyntaxException;
import java.net.URL;

/**
 * Class that encapsulates the Esmond REST API.
 * Handles the retrieval of both metadata and actual timeseries data.
 * Publishing data is for the future
 * Created by bmah on 8/5/14.
 */
public class EsmondClient {

    ObjectMapper mapper;

    static final Logger logger = LoggerFactory.getLogger(EsmondClient.class);

    public EsmondClient() {
        mapper = new ObjectMapper();
    }

    /**
     * Map the name of a tool to a measurement data structure.
     * This allows us to understand the JSON returned in metadata in a tool-specific way.
     * @param tool
     * @return
     */
    protected TypeReference measurementType(String tool) {
        try {
            if (tool.equalsIgnoreCase("bwctl/iperf") ||
                tool.equalsIgnoreCase("bwctl/iperf3") ||
                tool.equalsIgnoreCase("bwctl/nuttcp")) {
                return new TypeReference<EsmondThroughputMeasurement[]>() { };
            }
            else if (tool.equalsIgnoreCase("powstream") ||
                     tool.equalsIgnoreCase("bwctl/ping")) {
                return new TypeReference<EsmondPacketSampleMeasurement[]>() { };
            }
            else if (tool.equalsIgnoreCase("bwctl/tracepath")) {
                return new TypeReference<EsmondPacketTraceMeasurement[]>() { };
            }
            else {
                return new TypeReference<EsmondMeasurement []>() { };
            }
        }
        catch (NullPointerException e) {
            return new TypeReference<EsmondMeasurement []>() { };
        }
    }

    /**
     * Retrieve esmond measurement (metadata) records
     * If specifying the type of measurement in the filter, we can try to figure out the
     * EsmondMeasurement class that best suits the data.
     * @param base URI of esmond base
     * @param filter filter object
     * @return
     */
    public EsmondMeasurement [] retrieveEsmondMeasurements(String base, EsmondMeasurementFilter filter) {
        EsmondMeasurement [] em = null;

        String url = base;
        String query = filter.toUrlQueryString();
        if (!query.isEmpty()) {
            url += "?" + query;
        }

        logger.info("send GET for {}", url);

        try {
            URL u = new URL(url);
            em = mapper.readValue(u, measurementType(filter.getToolName()));

            // Set the base URL for retrieving this Measurement object.  We'll need this
            // when retrieving data because we need to remember where the Measurement object came from.
            for (EsmondMeasurement e : em) {
                e.setBaseUrl(url.toString());
                e.setClient(this);
            }
        }
        catch (Exception e) {
            e.printStackTrace();
        }

        return em;
    }

    /**
     * Return esmond measurement (metadata) record pointed to by a single sLS psmetadata record
     * @param psm PSMetadata object retrieved from sLS
     * @return
     */
    public EsmondMeasurement [] retrieveEsmondMeasurements(PSMetadata psm) {
        EsmondMeasurement [] em = null;

        // The MA locator field in the PSMetadata record can contain multiple
        // URIs.  For now, just try the first one.
        // TODO:  Try something more intelligent, such as looping over the list
        String base = psm.getMaLocator().get(0);

        // Resolve the URI
        URI baseURI, metadataURI = null;
        try {
            baseURI = new URI(base);
            metadataURI = baseURI.resolve(psm.getPsmUri());
        }
        catch (URISyntaxException e) {
            e.printStackTrace();
        }

        logger.info("send GET for {}", metadataURI.toString());

        try {
            em = mapper.readValue(metadataURI.toURL(), measurementType(psm.getToolName()));


            // Set the base URL for retrieving this Measurement object.  We'll need this
            // when retrieving data because we need to remember where the Measurement object came from.
            for (EsmondMeasurement e : em) {
                e.setBaseUrl(metadataURI.toString());
                e.setClient(this);
            }
        }
        catch (Exception e) {
            e.printStackTrace();
        }

        return em;
    }
}
