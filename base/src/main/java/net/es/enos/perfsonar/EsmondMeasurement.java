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

import org.codehaus.jackson.annotate.JsonIgnore;
import org.codehaus.jackson.annotate.JsonIgnoreProperties;
import org.codehaus.jackson.annotate.JsonProperty;
import org.codehaus.jackson.type.TypeReference;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.net.URI;
import java.net.URISyntaxException;

/**
 * Base class for Esmond metadata items
 * Subclasses may extend this class for specific measurements by adding more fields.
 * Created by bmah on 8/5/14.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
public class EsmondMeasurement {

    @JsonIgnore
    static final Logger logger = LoggerFactory.getLogger(EsmondMeasurement.class);

    /* Fields present in all metadata objects */
    protected String source;
    protected String destination;
    @JsonProperty("measurement-agent")
    protected String measurementAgent;
    @JsonProperty("input-source")
    protected String inputSource;
    @JsonProperty("input-destination")
    protected String inputDestination;
    @JsonProperty("tool-name")
    protected String toolName;
    @JsonProperty("event-types")
    protected EventType eventTypes[];

    static public class EventType {
        @JsonProperty("base-uri")
        protected String baseUri;
        @JsonProperty("event-type")
        protected String eventType;
        protected SummaryType summaries[];
        @JsonProperty("time-updated")
        protected int timeUpdated;

        public String getBaseUri() {
            return baseUri;
        }

        public void setBaseUri(String baseUri) {
            this.baseUri = baseUri;
        }

        public String getEventType() {
            return eventType;
        }

        public void setEventType(String eventType) {
            this.eventType = eventType;
        }

        public SummaryType[] getSummaries() {
            return summaries;
        }

        public void setSummaries(SummaryType[] summaries) {
            this.summaries = summaries;
        }

        public int getTimeUpdated() {
            return timeUpdated;
        }

        public void setTimeUpdated(int timeUpdated) {
            this.timeUpdated = timeUpdated;
        }
    }

    static public class SummaryType{
        @JsonProperty("summary-type")
        protected String summaryType;
        @JsonProperty("summary-window")
        protected String summaryWindow;
        @JsonProperty("time-updated")
        protected int timeUpdated;
        protected String uri;

        public String getSummaryType() {
            return summaryType;
        }

        public void setSummaryType(String summaryType) {
            this.summaryType = summaryType;
        }

        public String getSummaryWindow() {
            return summaryWindow;
        }

        public void setSummaryWindow(String summaryWindow) {
            this.summaryWindow = summaryWindow;
        }

        public int getTimeUpdated() {
            return timeUpdated;
        }

        public void setTimeUpdated(int timeUpdated) {
            this.timeUpdated = timeUpdated;
        }

        public String getUri() {
            return uri;
        }

        public void setUri(String uri) {
            this.uri = uri;
        }
    }

    public String getSource() {
        return source;
    }

    public void setSource(String source) {
        this.source = source;
    }

    public String getDestination() {
        return destination;
    }

    public void setDestination(String destination) {
        this.destination = destination;
    }

    public String getMeasurementAgent() {
        return measurementAgent;
    }

    public void setMeasurementAgent(String measurementAgent) {
        this.measurementAgent = measurementAgent;
    }

    public String getInputSource() {
        return inputSource;
    }

    public void setInputSource(String inputSource) {
        this.inputSource = inputSource;
    }

    public String getInputDestination() {
        return inputDestination;
    }

    public void setInputDestination(String inputDestination) {
        this.inputDestination = inputDestination;
    }

    public String getToolName() {
        return toolName;
    }

    public void setToolName(String toolName) {
        this.toolName = toolName;
    }

    public EventType[] getEventTypes() {
        return eventTypes;
    }

    public void setEventTypes(EventType[] eventTypes) {
        this.eventTypes = eventTypes;
    }

    // Other stuff
    @JsonIgnore
    private String baseUrl;
    @JsonIgnore
    private EsmondClient client;

    public String getBaseUrl() {
        return baseUrl;
    }

    public void setBaseUrl(String baseUrl) {
        this.baseUrl = baseUrl;
    }

    public EsmondClient getClient() {
        return client;
    }

    public void setClient(EsmondClient client) {
        this.client = client;
    }

    /**
     * Grab a dataset given a type of events from this measurement, plus a filter
     * Uses the eventType to figure out the JSON structure we're supposed to be
     * parsing from esmond, and create the appropriate Java objects.
     * @param et event type
     * @param f filter
     * @return array of time series objects
     */
    public EsmondTimeSeriesObject[] retrieveData(EventType et, EsmondDataFilter f) {

        // Starting from the URL where we grabbed the EsmondMeasurement, figure out where to
        // retrieve the data.
        URI baseURI, dataURI = null;
        try {
            baseURI = new URI(baseUrl);
            dataURI = baseURI.resolve(et.getBaseUri() + "?" + f.toUrlQueryString());
        }
        catch (URISyntaxException e) {
            e.printStackTrace();
        }

        // Switch on et.eventType to figure out the type of data we should retrieve.
        // Practically speaking we need to have some recognized event-type otherwise
        // we don't know what kind of time series objects are coming back to us.
        TypeReference t = null;
        // References:
        // throughput:  perfsonar-ps wiki (MeasurementArchiveClientGuide)
        // packet-loss-rate:  perfsonar-ps wiki (MeasurementArchiveClientGuide)
        // packet-retransmits:  observed bwctl/iperf3 dataset
        // time-error-estimates:  observed powstream dataset
        // packet-duplicates:  observed powstream dataset
        // packet-count-sent:  observed powstream dataset
        // packet-count-lost:  observed powstream dataset
        if (et.eventType.equalsIgnoreCase("throughput") ||
            et.eventType.equalsIgnoreCase("packet-loss-rate") ||
            et.eventType.equalsIgnoreCase("packet-retransmits") ||
            et.eventType.equalsIgnoreCase("time-error-estimates") ||
            et.eventType.equalsIgnoreCase("packet-duplicates") ||
            et.eventType.equalsIgnoreCase("packet-count-sent") ||
            et.eventType.equalsIgnoreCase("packet-count-lost")) {
            t = new TypeReference<EsmondDoubleTimeSeriesObject[]>() { };
        }
        // References:
        // histogram-rtt:  perfsonar-ps wiki (MeasurementArchiveClientGuide)
        // histogram-owdelay:  perfsonar-ps wiki (MeasurementArchiveClientGuide)
        // histogram-ttl:  observed powstream dataset
        else if (et.eventType.equalsIgnoreCase("histogram-rtt") ||
                 et.eventType.equalsIgnoreCase("histogram-owdelay") ||
                 et.eventType.equalsIgnoreCase("histogram-ttl")) {
            t = new TypeReference<EsmondHistogramTimeSeriesObject []>() { };
        }
        // References:
        // packet-trace:  perfsonar-ps wiki (MeasurementArchiveClientGuide)
        else if (et.eventType.equalsIgnoreCase("packet-trace")) {
            t = new TypeReference<EsmondPacketTraceTimeSeriesObject []>() { };
        }
        // Fallback case.  Note this case, which only happens when we don't
        // recognize the eventType, is pretty useless since we don't know the
        // type of the value field in the tuple.
        else {
            t = new TypeReference<EsmondTimeSeriesObject []>() { };
        }

        // Get the data
        EsmondTimeSeriesObject[] data = null;
        try {
            logger.info("GET {}", dataURI.toString());
            data = getClient().mapper.readValue(dataURI.toURL(), t);
        }
        catch (Exception e) {
            e.printStackTrace();
        }

        return data;
    }
}
