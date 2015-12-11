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
 * Class of packet trace metadata.
 * Analogous to BasePacketTraceMetadata
 * Created by bmah on 8/11/14.
 */
public class EsmondPacketTraceMeasurement {
    @JsonProperty("trace-first-ttl")
    protected int traceFirstTtl;
    @JsonProperty("trace-max-ttl")
    protected int traceMaxTtl;
    @JsonProperty("trace-num-queries")
    protected int traceNumQueries;

    public int getTraceFirstTtl() {
        return traceFirstTtl;
    }

    public void setTraceFirstTtl(int traceFirstTtl) {
        this.traceFirstTtl = traceFirstTtl;
    }

    public int getTraceMaxTtl() {
        return traceMaxTtl;
    }

    public void setTraceMaxTtl(int traceMaxTtl) {
        this.traceMaxTtl = traceMaxTtl;
    }

    public int getTraceNumQueries() {
        return traceNumQueries;
    }

    public void setTraceNumQueries(int traceNumQueries) {
        this.traceNumQueries = traceNumQueries;
    }
}
