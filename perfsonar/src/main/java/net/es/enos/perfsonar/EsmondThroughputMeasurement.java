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
