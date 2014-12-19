/*
 * Copyright (c) 2014, Regents of the University of California  All rights reserved.
 * Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
 * 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

package net.es.enos.esnet;

import net.es.netshell.api.Link;
import net.es.netshell.api.TopologyFactory;

import java.util.HashMap;

/**
 * Created by lomax on 6/30/14.
 */
public class PerfSONAR {
    private HashMap<String,PerfSONARTester> testers = new HashMap<String,PerfSONARTester>();

    public PerfSONAR() {
        this.getCoreTesters();
    }


    /**
     * Retrieve the links from the topology, and assume that a link to a tester host contains the
     * string "-pt"
     */
    private void getCoreTesters() {

        ESnetTopology topology =
                (ESnetTopology) TopologyFactory.instance().retrieveTopologyProvider(TopologyFactory.LOCAL_LAYER2);

        HashMap<String,Link> links = topology.getLinks();

        for (String link : links.keySet()) {
            String description = ESnetTopology.idToDescription(link);
            if (description.contains("-pt")) {
                // This is a link to a perfSONAR tester connect to one of ESnet core router
                PerfSONARTester ptNode = new PerfSONARTester();
                ptNode.setResourceName(description.substring(3));
                ptNode.addLink((ESnetLink) links.get(link));
                this.testers.put(ESnetTopology.idToName(link), ptNode);
            }
        }
    }

    public HashMap<String, PerfSONARTester> getTesters() {
        return testers;
    }
}
