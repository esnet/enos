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

import net.es.lookup.common.exception.RecordException;
import net.es.lookup.records.Network.PSMetadataRecord;
import org.codehaus.jackson.annotate.JsonIgnore;

import java.net.InetAddress;
import java.util.LinkedList;
import java.util.List;

/**
 * Created by bmah on 7/31/14.
 *
 * This class roughly encapsulates a PSMetadataRecord from sLS.
 */
public class PSMetadata {

    // Information slurped in from sLS
    private List<String> communities;
    private InetAddress dstAddress;
    private List<String> eventTypes;
    private List<String> maLocator;
    private InetAddress measurementAgent;
    private InetAddress srcAddress;
    private String toolName;
    private String psmUri;   // Need to name this differently to avoid naming conflict

    // Other metadata
    @JsonIgnore
    private String queryServer; // which sLS server did this record come from?
    private String uri;

    public List<String> getCommunities() {
        return communities;
    }

    public void setCommunities(List<String> communities) {
        this.communities = communities;
    }

    public InetAddress getDstAddress() {
        return dstAddress;
    }

    public void setDstAddress(InetAddress dstAddress) {
        this.dstAddress = dstAddress;
    }

    public List<String> getEventTypes() {
        return eventTypes;
    }

    public void setEventTypes(List<String> eventTypes) {
        this.eventTypes = eventTypes;
    }

    public List<String> getMaLocator() {
        return maLocator;
    }

    public void setMaLocator(List<String> maLocator) {
        this.maLocator = maLocator;
    }

    public InetAddress getMeasurementAgent() {
        return measurementAgent;
    }

    public void setMeasurementAgent(InetAddress measurementAgent) {
        this.measurementAgent = measurementAgent;
    }

    public InetAddress getSrcAddress() {
        return srcAddress;
    }

    public void setSrcAddress(InetAddress srcAddress) {
        this.srcAddress = srcAddress;
    }

    public String getToolName() {
        return toolName;
    }

    public void setToolName(String toolName) {
        this.toolName = toolName;
    }

    public String getPsmUri() {
        return psmUri;
    }

    public void setPsmUri(String psmUri) {
        this.psmUri = psmUri;
    }

    public String getQueryServer() {
        return queryServer;
    }

    public void setQueryServer(String queryServer) {
        this.queryServer = queryServer;
    }

    public String getUri() {
        return uri;
    }

    public void setUri(String uri) {
        this.uri = uri;
    }

    public PSMetadata() {
        communities = new LinkedList<String>();
        eventTypes = new LinkedList<String>();
        maLocator = new LinkedList<String>();
    }

    public static final PSMetadata parsePSMetadataRecord(PSMetadataRecord metadataRecord) {

        PSMetadata p = new PSMetadata();

//            communities = metadataRecord.getCommunities();
        try {
            p.setDstAddress(metadataRecord.getDstAddress());
        }
        catch (RecordException e) { }
        p.setEventTypes(metadataRecord.getEventTypes());
        p.maLocator = metadataRecord.getMALocator();
        try {
            p.measurementAgent = metadataRecord.getMeasurementAgent();
        }
        catch (RecordException e) { }
        try {
            p.srcAddress = metadataRecord.getSrcAddress();
        }
        catch (RecordException e) { }
        p.setToolName(metadataRecord.getToolName());
        p.setPsmUri(metadataRecord.getUri());

        return p;
    }
}
