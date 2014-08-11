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
