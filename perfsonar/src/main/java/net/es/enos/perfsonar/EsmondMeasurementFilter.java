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

/**
 * Filter / query object for esmond measurements / metadata
 * Created by bmah on 8/5/14.
 */
public class EsmondMeasurementFilter extends EsmondFilter {

    String source;
    String destination;
    String measurementAgent;
    String inputSource; // don't search on this per API docs
    String inputDestination; // don't search on this per API docs
    String toolName;

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

    @Override
    public String toUrlQueryString() {
        QueryString q = new QueryString();

        // esmond really wants format=json
        q.add("format", "json");

        if (source != null && !source.isEmpty()) {
            q.add("source", source);
        }

        if (destination != null && !destination.isEmpty()) {
            q.add("destination", destination);
        }

        if (measurementAgent != null && !measurementAgent.isEmpty()) {
            q.add("measurement-agent", measurementAgent);
        }

        if (inputSource != null && !inputSource.isEmpty()) {
            q.add("input-source", inputSource);
        }

        if (inputDestination != null && !inputDestination.isEmpty()) {
            q.add("input-destination", inputDestination);
        }

        if (toolName != null && !toolName.isEmpty()) {
            q.add("tool-name", toolName);
        }

        return q.getQuery();
    }

}
