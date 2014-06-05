/*
 * Copyright (c) 2014, Regents of the University of California  All rights reserved.
 * Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
 * 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

package net.es.enos.esnet;

import net.es.enos.api.Circuit;
import net.es.enos.api.ISODateTime;
import org.joda.time.DateTime;

import java.util.List;

/**
 * Created by lomax on 5/19/14.
 */
public class ESnetCircuit extends Circuit {
    private String start; // UTC time in seconds
    private String end; // UTC time in seconds
    private String description;
    private List<ESnetSegment> segments;
    private String capacity;
    private List<String> segment_ids;
    private List<ESnetDataPlaneId> dataplane_ids;
    private String id;
    private String name;

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public List<String> getSegment_ids() {
        return segment_ids;
    }

    public void setSegment_ids(List<String> segment_ids) {
        this.segment_ids = segment_ids;
    }

    public List<ESnetDataPlaneId> getDataplane_ids() {
        return dataplane_ids;
    }

    public void setDataplane_ids(List<ESnetDataPlaneId> dataplane_ids) {
        this.dataplane_ids = dataplane_ids;
    }

    public String getCapacity() {
        return capacity;
    }

    public void setCapacity(String capacity) {
        this.capacity = capacity;
    }

    public String getStart() {
        return start;
    }

    public void setStart(String start) {
        this.start = start;
        this.setStartDateTime(new ISODateTime(start));
    }

    public String getEnd() {
        return end;
    }

    public void setEnd(String end) {
        this.end = end;
        this.setEndDateTime(new ISODateTime(end));
    }

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }

    public List<ESnetSegment> getSegments() {
        return segments;
    }

    public void setSegments(List<ESnetSegment> segments) {
        this.segments = segments;
    }


    public boolean isActive (DateTime start, DateTime end) {
        boolean res = ! ((this.getStartDateTime().compareTo(end) >= 0) ||
                        (this.getEndDateTime().compareTo(start) <=0));

        return res;
    }
}
