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
import org.jgrapht.Graph;
import org.jgrapht.graph.DirectedMultigraph;
import org.jgrapht.graph.DefaultListenableGraph;

/**
 * JGrapht Weighted graphs implies that either the edges extends DefaultWeightedEdge, or the WeightedGraph to
 * overwrite the setEdgeWeight(). Since ESnetLink already extends Link, it is not possible to extend
 * DefaultWeightEdge, therefore, the only solution is to extends WeightedGraph. This is the purpose of this
 * class.
 */
public class ESnetTopologyWeightedGraph extends DefaultListenableGraph <Node, Link> implements Graph<Node, Link> {
    public ESnetTopologyWeightedGraph(Class<? extends ESnetLink> edgeClass) {
        super(new DirectedMultigraph<Node, Link>(edgeClass));
    }

    public ESnetTopologyWeightedGraph() {
        super(new DirectedMultigraph<Node, Link>(Link.class));
    }

    @Override
    public double getEdgeWeight(Link link) {
        return link.getWeight();
    }

    @Override
    public void setEdgeWeight(Link link, double weight) {
        link.setWeight(weight);
    }
}
