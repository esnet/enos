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
 * Class of throughput measurements' metadata.
 * Roughly corresponds to the BaseThroughputMetaData JSON object definition
 * from the MA REST API.
 * Created by bmah on 8/7/14.
 */
public class EsmondThroughputMeasurement extends EsmondMeasurement {

    // Metadata fields specific to throughput measurements
    @JsonProperty("bw-buffer-size")
    protected int bwBufferSize;
    @JsonProperty("bw-parallel-streams")
    protected int bwParallelStreams;
    @JsonProperty("bw-target-bandwidth")
    protected int bwTargetBandwidth;
    @JsonProperty("bw-zero-copy")
    protected boolean bwZeroCopy;
    @JsonProperty("bw-ignore-first-seconds")
    protected int bwIgnoreFirstSeconds;

    public int getBwBufferSize() {
        return bwBufferSize;
    }

    public void setBwBufferSize(int bwBufferSize) {
        this.bwBufferSize = bwBufferSize;
    }

    public int getBwParallelStreams() {
        return bwParallelStreams;
    }

    public void setBwParallelStreams(int bwParallelStreams) {
        this.bwParallelStreams = bwParallelStreams;
    }

    public int getBwTargetBandwidth() {
        return bwTargetBandwidth;
    }

    public void setBwTargetBandwidth(int bwTargetBandwidth) {
        this.bwTargetBandwidth = bwTargetBandwidth;
    }

    public boolean isBwZeroCopy() {
        return bwZeroCopy;
    }

    public void setBwZeroCopy(boolean bwZeroCopy) {
        this.bwZeroCopy = bwZeroCopy;
    }

    public int getBwIgnoreFirstSeconds() {
        return bwIgnoreFirstSeconds;
    }

    public void setBwIgnoreFirstSeconds(int bwIgnoreFirstSeconds) {
        this.bwIgnoreFirstSeconds = bwIgnoreFirstSeconds;
    }
}
