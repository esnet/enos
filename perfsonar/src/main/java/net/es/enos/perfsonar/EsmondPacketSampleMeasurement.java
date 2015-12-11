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
 * Class of packet sample measurement metadata.
 * Roughly based on BasePacketSampleMetadata from the MA REST API.
 * Created by bmah on 8/11/14.
 */
public class EsmondPacketSampleMeasurement extends EsmondMeasurement {
    @JsonProperty("sample-bucket-width")
    protected double sampleBucketWidth;
    @JsonProperty("sample-size")
    protected int sampleSize;

    public double getSampleBucketWidth() {
        return sampleBucketWidth;
    }

    public void setSampleBucketWidth(double sampleBucketWidth) {
        this.sampleBucketWidth = sampleBucketWidth;
    }

    public int getSampleSize() {
        return sampleSize;
    }

    public void setSampleSize(int sampleSize) {
        this.sampleSize = sampleSize;
    }
}
