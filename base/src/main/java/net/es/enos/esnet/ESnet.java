/*
 * Copyright (c) 2014, Regents of the University of California  All rights reserved.
 * Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
 * 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

package net.es.enos.esnet;

import net.es.enos.api.NetworkProvider;
import net.es.enos.api.Node;
import net.es.enos.api.TopologyFactory;
import net.es.enos.api.TopologyProvider;
import org.jgrapht.Graph;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * This class implements ESnet layer 2 network. It is a singleton.
 */
public class ESnet extends NetworkProvider {

    private static ESnet instance;
    private ESnetTopology topology;
    private static Object instanceMutex = new Object();
    private static final Logger logger = LoggerFactory.getLogger(ESnet.class);

    public static ESnet instance() {
        synchronized (ESnet.instanceMutex) {
            if (ESnet.instance == null) {
                // Create the singleton
                ESnet.instance = new ESnet();
            }
        }
        return ESnet.instance;
    }

    private ESnet() {
        TopologyProvider topo = TopologyFactory.instance().retrieveTopologyProvider("localLayer2");
        if ( ! (topo instanceof ESnetTopology)) {
            // ENOS configuration must be wrong since the layer 2 topology is not ESnet topology.
            logger.error("Layer2 local topology is not a ESnetTopology. It is a " + topo.getClass().getCanonicalName());
        }
        this.topology = (ESnetTopology) topo;
    }

    @Override
    public Graph computePath(Node srcNode, Node dstNode) {
        return super.computePath(srcNode, dstNode);
    }
}
