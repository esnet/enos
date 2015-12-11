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
 * This includes the data members from the BaseMetadata, BaseP2PMetadata,
 * BaseIPPacketMetaData, and BaseTimeMetadata JSON object definitions from the MA REST API.
 * Created by bmah on 8/5/14.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
public class EsmondMeasurement {

    @JsonIgnore
    static final Logger logger = LoggerFactory.getLogger(EsmondMeasurement.class);

    /* From BaseMetadata JSON object definition */
    protected String uri;
    @JsonProperty("metadata-key")
    protected String metadataKey;
    @JsonProperty("subject-type")
    protected String subjectType;
    @JsonProperty("event-types")
    protected EventType eventTypes[];

    /* From BaseP2PMetadata JSON object definition */
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

    /* From BaseIPPacketMetaData JSON object definition */
    @JsonProperty("ip-tos")
    protected int ipTos;
    @JsonProperty("ip-ttl")
    protected int ipTtl;
    @JsonProperty("ip-transport-protocol")
    protected String ipTransportProtocol;
    @JsonProperty("ip-packet-size")
    protected int ipPacketSize;

    /* From BaseTimeMetadata JSON object definition */
    @JsonProperty("time-duration")
    protected int timeDuration;
    @JsonProperty("time-interval")
    protected int timeInterval;
    @JsonProperty("time-interval-randomization")
    protected int timeIntervalRandomization;
    @JsonProperty("time-probe-interval")
    protected int timeProbeInterval;

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

    public String getUri() {
        return uri;
    }

    public void setUri(String uri) {
        this.uri = uri;
    }

    public String getMetadataKey() {
        return metadataKey;
    }

    public void setMetadataKey(String metadataKey) {
        this.metadataKey = metadataKey;
    }

    public String getSubjectType() {
        return subjectType;
    }

    public void setSubjectType(String subjectType) {
        this.subjectType = subjectType;
    }

    public EventType[] getEventTypes() {
        return eventTypes;
    }

    public void setEventTypes(EventType[] eventTypes) {
        this.eventTypes = eventTypes;
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

    public int getIpTos() {
        return ipTos;
    }

    public void setIpTos(int ipTos) {
        this.ipTos = ipTos;
    }

    public int getIpTtl() {
        return ipTtl;
    }

    public void setIpTtl(int ipTtl) {
        this.ipTtl = ipTtl;
    }

    public String getIpTransportProtocol() {
        return ipTransportProtocol;
    }

    public void setIpTransportProtocol(String ipTransportProtocol) {
        this.ipTransportProtocol = ipTransportProtocol;
    }

    public int getIpPacketSize() {
        return ipPacketSize;
    }

    public void setIpPacketSize(int ipPacketSize) {
        this.ipPacketSize = ipPacketSize;
    }

    public int getTimeDuration() {
        return timeDuration;
    }

    public void setTimeDuration(int timeDuration) {
        this.timeDuration = timeDuration;
    }

    public int getTimeInterval() {
        return timeInterval;
    }

    public void setTimeInterval(int timeInterval) {
        this.timeInterval = timeInterval;
    }

    public int getTimeIntervalRandomization() {
        return timeIntervalRandomization;
    }

    public void setTimeIntervalRandomization(int timeIntervalRandomization) {
        this.timeIntervalRandomization = timeIntervalRandomization;
    }

    public int getTimeProbeInterval() {
        return timeProbeInterval;
    }

    public void setTimeProbeInterval(int timeProbeInterval) {
        this.timeProbeInterval = timeProbeInterval;
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
