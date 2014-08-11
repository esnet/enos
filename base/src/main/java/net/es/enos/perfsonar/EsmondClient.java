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
            if (tool.equalsIgnoreCase("bwctl/iperf3")) {
                return new TypeReference<EsmondBwctlIperf3Measurement []>() {
                };
            } else {
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
