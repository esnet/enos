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
