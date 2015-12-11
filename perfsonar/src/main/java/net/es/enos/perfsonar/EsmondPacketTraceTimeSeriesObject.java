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

import org.codehaus.jackson.annotate.JsonProperty;

/**
 * Packet trace data point
 * Created by bmah on 8/6/14.
 */
public class EsmondPacketTraceTimeSeriesObject extends EsmondTimeSeriesObject{

    /**
     * One (e.g.) traceroute measurement
     * A bunch of these make up the packet trace.
     */
    public static class TracePoint {
        @JsonProperty("error_message")
        private String errorMessage;
        private String ip;
        private String mtu;
        private String query;
        private String rtt;
        private int success;
        private int ttl;

        public String getErrorMessage() {
            return errorMessage;
        }

        public void setErrorMessage(String errorMessage) {
            this.errorMessage = errorMessage;
        }

        public String getIp() {
            return ip;
        }

        public void setIp(String ip) {
            this.ip = ip;
        }

        public String getMtu() {
            return mtu;
        }

        public void setMtu(String mtu) {
            this.mtu = mtu;
        }

        public String getQuery() {
            return query;
        }

        public void setQuery(String query) {
            this.query = query;
        }

        public String getRtt() {
            return rtt;
        }

        public void setRtt(String rtt) {
            this.rtt = rtt;
        }

        public int getSuccess() {
            return success;
        }

        public void setSuccess(int success) {
            this.success = success;
        }

        public int getTtl() {
            return ttl;
        }

        public void setTtl(int ttl) {
            this.ttl = ttl;
        }
    }

    TracePoint[] val;

    public TracePoint[] getVal() {
        return val;
    }

    public void setVal(TracePoint[] val) {
        this.val = val;
    }

}
