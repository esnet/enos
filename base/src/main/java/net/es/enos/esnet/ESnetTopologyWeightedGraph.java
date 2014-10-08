package net.es.enos.esnet;

import net.es.enos.api.Link;
import net.es.enos.api.Node;
import org.jgrapht.Graph;
import org.jgrapht.graph.DirectedMultigraph;
import org.jgrapht.graph.DefaultListenableGraph;
import org.jgrapht.DirectedGraph;

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
