package net.es.enos.esnet;

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
public class ESnetTopologyWeightedGraph extends DefaultListenableGraph <ESnetNode, ESnetLink> implements Graph<ESnetNode, ESnetLink> {
    public ESnetTopologyWeightedGraph(Class<? extends ESnetLink> edgeClass) {
        super(new DirectedMultigraph<ESnetNode, ESnetLink>(edgeClass));
    }

    public ESnetTopologyWeightedGraph() {
        super(new DirectedMultigraph<ESnetNode, ESnetLink>(ESnetLink.class));
    }

    @Override
    public double getEdgeWeight(ESnetLink link) {
        return link.getWeight();
    }

    @Override
    public void setEdgeWeight(ESnetLink link, double weight) {
        link.setWeight(weight);
    }
}
