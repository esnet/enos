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
import net.es.netshell.api.Node;
import net.es.netshell.api.TopologyProvider;
import org.jgrapht.graph.DefaultListenableGraph;

import java.io.IOException;

/**
 * Created by rueiminl on 2015/5/29.
 * refer python/topology/viewTopo.py
 */
public class viewTopo {
    @SuppressWarnings("unchecked")
    public static void main(String[] args) throws IOException {
        ESnetTopology topo = new ESnetTopology();
        DefaultListenableGraph<Node, Link> graph = topo.getGraph(TopologyProvider.WeightType.TrafficEngineering);
        GraphViewer viewer;
        viewer = new GraphViewer( (DefaultListenableGraph<ESnetNode, ESnetLink>)(Object)graph);
        viewer.init();
    }
}
