package net.es.enos.esnet;

import org.jgrapht.WeightedGraph;
import org.jgrapht.graph.ListenableDirectedWeightedGraph;

/**
 * JGrapht Weighted graphs implies that either the edges extends DefaultWeightedEdge, or the WeigtedGrap to
 * overwrite the setEdgeWeight(). Since ESnetLink already extends Link, it is not possible to extend
 * DefaultWeightEdge, therefore, the only solution is to extends WeightedGraph. This is the purpose of this
 * class.
 */
public class ESnetTopologyWeightedGraph extends ListenableDirectedWeightedGraph <ESnetNode, ESnetLink> {
    public ESnetTopologyWeightedGraph(Class<? extends ESnetLink> edgeClass) {
        super(edgeClass);
    }

    public ESnetTopologyWeightedGraph(WeightedGraph<ESnetNode, ESnetLink> base) {
        super(base);
    }

    @Override
    public double getEdgeWeight(ESnetLink link) {
        return link.weight;
    }

    @Override
    public void setEdgeWeight(ESnetLink link, double weight) {
        link.weight = weight;
    }
}
