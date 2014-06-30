/*
 * Copyright (c) 2014, Regents of the University of California  All rights reserved.
 * Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
 * 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

package net.es.enos.esnet;

import net.es.enos.api.*;
import org.jgrapht.Graph;
import org.jgrapht.GraphPath;
import org.jgrapht.alg.DijkstraShortestPath;
import org.joda.time.DateTime;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;


/**
 * This class implements ESnet layer 2 network. It is a singleton.
 */
public final class ESnet extends NetworkProvider {

    private static ESnet instance;
    private ESnetTopology topology;
    private static Object instanceMutex = new Object();
    private static final Logger logger = LoggerFactory.getLogger(ESnet.class);
    private OSCARS oscars;

    public static ESnet instance() {
        synchronized (ESnet.instanceMutex) {
            if (ESnet.instance == null) {
                // Create the singleton
                ESnet.instance = new ESnet();
            }
        }
        return ESnet.instance;
    }

    /**
     * Default constructor
     */
    public ESnet() {
        TopologyProvider topo = TopologyFactory.instance().retrieveTopologyProvider("localLayer2");
        if ( ! (topo instanceof ESnetTopology)) {
            // ENOS configuration must be wrong since the layer 2 topology is not ESnet topology.
            logger.error("Layer2 local topology is not a ESnetTopology. It is a " + topo.getClass().getCanonicalName());
        }
        this.topology = (ESnetTopology) topo;
        this.oscars = new OSCARS();
    }

    @Override
    public String getDnsName() {
        return "es.net";
    }

    @Override
    public Path computePath(String srcNodeName, String dstNodeName, DateTime start, DateTime end) throws IOException {
        // First retrieve the layer 2 topology graph
        Graph topoGraph = this.topology.getGraph(start, end, TopologyProvider.WeightType.TrafficEngineering);
        // Use JGrapht shortest path algorithm to compute the path
        Node srcNode = this.topology.getNode(srcNodeName);
        Node dstNode = this.topology.getNode(dstNodeName);

        if ((srcNode == null) || (dstNode == null)) {
            // Source or destination node does not exist. Cannot compute a path
            return null;
        }
        DijkstraShortestPath shortestPath = new DijkstraShortestPath (topoGraph, srcNode, dstNode);
        GraphPath<Node,Link> graphPath = shortestPath.getPath();

        // Compute the maximum reservable bandwidth on this path
        long maxBandwidth = -1; // -1 means the value was not computed.
        OSCARSReservations oscarsReservations;
        Path path = new Path();
        //
        try {
            oscarsReservations = new OSCARSReservations(this.topology);
            maxBandwidth = oscarsReservations.getMaxReservableBandwidth(graphPath,start,end);
        } catch (IOException e) {
            // Return null in case of I/O exception. This should not happen.
            logger.error("Cannot retrieve OSCARS reservation " + e.getMessage());
        }
        // Build the Path object
        path.setStart(start);
        path.setEnd(end);
        path.setGraphPath(graphPath);
        path.setMaxReservable(maxBandwidth);
        return path;
    }

    public static void registerToFactory() throws IOException {
        NetworkFactory.instance().registerNetworkProvider(ESnet.class.getCanonicalName(), NetworkFactory.LOCAL_LAYER2);
    }

    @Override
    public TopologyProvider getTopologyProvider() {
        return this.topology;
    }

    @Override
    public boolean canProvisionLayer2() {
        /* OSCARS supports only scheduled virtual circuits. Immediate and not time bounded virtucal may be
         * supported with NSI, or by using SDN capable links.
         */
        return false;
    }

    @Override
    public boolean canProvisionScheduledLayer2() {
        return true;
    }

    @Override
    public boolean supportProfile(Layer2ProvisioningProfiles profile) {
        /* While ESnet's OSCARS can support all profiles, this implementation is restricted to best effort */
        return profile.equals(Layer2ProvisioningProfiles.BestEffort);
    }

    @Override
    public ProvisionedPath provisionLayer2(Path path, Layer2ProvisioningProfiles profile) throws IOException {

        if (path.getStart().equals(path.getEnd()) ||
            path.getStart().isAfter(path.getEnd())) {
            throw new IOException("does not support provisioning with time constraints");
        }
        if ( ! this.supportProfile(profile)) {
            throw new IOException("does not support this profile");
        }
        if ( ! oscars.canProvision(path))  {
            throw new SecurityException("not authorized to provision this path");
        }
        return null;
    }

    @Override
    public void deprovisionLayer2(ProvisionedPath path) throws IOException {
        super.deprovisionLayer2(path);
    }
}
