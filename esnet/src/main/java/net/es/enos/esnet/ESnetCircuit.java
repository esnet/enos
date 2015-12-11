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

import net.es.netshell.api.ISODateTime;
import net.es.netshell.api.Resource;
import org.joda.time.DateTime;

import java.util.List;

/**
 * Created by lomax on 5/19/14.
 */
public class ESnetCircuit extends Resource {
    private String start; // UTC time in seconds
    private String end; // UTC time in seconds
    private String description;
    private List<ESnetSegment> segments;
    private String capacity;
    private List<String> segment_ids;
    private List<ESnetDataPlaneId> dataplane_ids;
    private String id;
    private String name;
    private ISODateTime startDateTime;
    private ISODateTime endDateTime;

    public ISODateTime getStartDateTime() {
        return startDateTime;
    }

    public void setStartDateTime(ISODateTime startDateTime) {
        this.startDateTime = startDateTime;
    }

    public ISODateTime getEndDateTime() {
        return endDateTime;
    }

    public void setEndDateTime(ISODateTime endDateTime) {
        this.endDateTime = endDateTime;
    }

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
        this.setResourceName(id);
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
    @Override
    public String toString() {
        return super.toString();
    }

    @Override
    protected Object clone() throws CloneNotSupportedException {
        return super.clone();
    }

    @Override
    public boolean equals(Object obj) {
        if ( ! (obj instanceof ESnetCircuit) ) {
            return false;
        }
        return ((ESnetCircuit) obj).getId().equals(this.getId());
    }
}
