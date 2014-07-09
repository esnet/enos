package net.es.enos.esnet;

import org.jgrapht.graph.DirectedMultigraph;
import org.jgrapht.graph.DefaultListenableGraph;
import org.jgrapht.DirectedGraph;

/**
 * JGrapht Weighted graphs implies that either the edges extends DefaultWeightedEdge, or the WeigtedGrap to
 * overwrite the setEdgeWeight(). Since ESnetLink already extends Link, it is not possible to extend
 * DefaultWeightEdge, therefore, the only solution is to extends WeightedGraph. This is the purpose of this
 * class.
 */
public class ESnetTopologyWeightedGraph extends DefaultListenableGraph <ESnetNode, ESnetLink> implements DirectedGraph<ESnetNode, ESnetLink>{
    public ESnetTopologyWeightedGraph(Class<? extends ESnetLink> edgeClass) {
        super(new DirectedMultigraph<ESnetNode, ESnetLink>(edgeClass));
    }

    //public ESnetTopologyWeightedGraph(WeightedGraph<ESnetNode, ESnetLink> base) {
        //super(base);
    //}

    @Override
    public double getEdgeWeight(ESnetLink link) {
        return link.weight;
    }

    @Override
    public void setEdgeWeight(ESnetLink link, double weight) {
        link.weight = weight;
    }
}
