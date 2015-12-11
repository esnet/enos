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
