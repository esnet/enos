/*
 * Copyright (c) 2014, Regents of the University of California  All rights reserved.
 * Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
 * 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

package net.es.enos.api;

import net.es.enos.boot.BootStrap;
import org.codehaus.jackson.annotate.JsonIgnore;
import org.jgrapht.Graph;
import org.jgrapht.GraphPath;
import org.joda.time.DateTime;

import java.io.IOException;
import java.nio.file.Paths;
import java.util.List;
import java.util.UUID;
/**
 * Created by lomax on 5/21/14.
 */
public abstract class NetworkProvider extends Resource {

    /**
     * Various defined provisioning profiles that network may implement
     */
    public static enum Layer2ProvioningProfiles {
        BestEffort,           // No bandwidth guaranty.
        StrictBandwidth,      // Guaranted bandwidth but no burst allowed
        BandwidthWithBurst    // Guaranted bandwidth burst ok when possible
    }

    @JsonIgnore
    public static final String NETWORKS_DIR = "networks";

    public Path computePath (String srcNode, String dstNode, DateTime start, DateTime end) throws IOException {
        return null;
    }

    /**
     * Convenience method computing the path start now and ending one minute later.
     * @param srcNodeName
     * @param dstNodeName
     * @return
     */
    public Path computePath (String srcNodeName, String dstNodeName) throws IOException {
        DateTime start = DateTime.now();
        DateTime end = start.plusMinutes(1);
        return this.computePath(srcNodeName,dstNodeName,start,end);
    }

    /**
     * Returns the TopologyProvider of this network
     * @return
     */
    public TopologyProvider getTopologyProvider() {
        return null;
    }

    /**
     * Returns true if this network is capable of provisioning Layer 2 circuits.
     * @return  whether if this network is capable of provisioning Layer 2 circuits.
     */
    public boolean canProvisionLayer2() {
        return false;
    }

    /**
     * Returns true if this network is capable of provisioning and scheduling Layer 2 circuits a
     * @return  whether if this network is capable of provisioning Layer 2 circuits or
     * if the network is not capable of provisioning layer 2 circuits
     */
    public boolean canProvisionScheduledLayer2() {
        return false;
    }

    public boolean supportProfile (Layer2ProvioningProfiles profile) {
        return false;
    }

    /**
     * Provision and schedule the provided layer 2 path.
     * @param path
     * @return
     * @throws IOException when provisioning the provided path failed or
     * if the network is not capable of provisioning and schedule layer 2 circuits
     */
    /**
     *rovision and schedule the provided layer 2 path.
     * @param path  provided path to provision
     * @param profile desired profile. An IOException is thrown when the profile is not available
     * @param start
     * @param end
     * @return Provisioned and scheduled path
     * @throws IOException
     */
    public ProvisionedScheduledPath provisionLayer2(Path path,
                                                    Layer2ProvioningProfiles profile,
                                                    DateTime start,
                                                    DateTime end) throws IOException {
        throw new IOException("Can not provision layer 2 circuits");
    }

    /**
     * Provision the provided layer 2 path providing start and end date. Note that some
     * networks may not be able to provision with start and end dates. In this case, they
     * are expected to throw an IOException.
     * @param path rovided path to provision
     * @param profile desired profile. An IOException is thrown when the profile is not available
     * @return Provisioned path
     * @throws IOException when provisioning the provided path failed
     */
    public ProvisionedPath  provisionLayer2(Path path,
                                            Layer2ProvioningProfiles profile ) throws IOException {
        return null;
    }

    /**
     *
     * @param path
     * @throws IOException
     */
    public void deprovisionLayer2(ProvisionedPath path) throws IOException {

    }

}
