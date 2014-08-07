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

package net.es.enos.api;

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
