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
 * Encapsulation of esmond filter on data sets by time
 * Created by bmah on 8/5/14.
 */
public class EsmondDataFilter extends EsmondFilter {

    // These are all expressed as seconds since the epoch, in other words time_t.
    // We want 64-bit time_t values, so use long data types, which are 64-bit
    // signed in Java.
    long time;
    long timeStart;
    long timeEnd;
    long timeRange;

    public long getTime() {
        return time;
    }

    public void setTime(long time) {
        this.time = time;
    }

    public long getTimeStart() {
        return timeStart;
    }

    public void setTimeStart(long timeStart) {
        this.timeStart = timeStart;
    }

    public long getTimeEnd() {
        return timeEnd;
    }

    public void setTimeEnd(long timeEnd) {
        this.timeEnd = timeEnd;
    }

    public long getTimeRange() {
        return timeRange;
    }

    public void setTimeRange(long timeRange) {
        this.timeRange = timeRange;
    }

    public EsmondDataFilter() {
        super();
        time = -1;
        timeStart = -1;
        timeEnd = -1;
        timeRange = -1;
    }

    @Override
    public String toUrlQueryString() {
        QueryString q = new QueryString();

        // esmond really wants format=json
        q.add("format", "json");

        if (time != -1) {
            q.add("time", new Long(time).toString());
        }

        if (timeStart != -1) {
            q.add("time-start", new Long(timeStart).toString());
        }

        if (timeEnd != -1) {
            q.add("time-end", new Long(timeEnd).toString());
        }

        if (timeRange != -1) {
            q.add("time-range", new Long(timeRange).toString());
        }

        return q.getQuery();
    }
}
