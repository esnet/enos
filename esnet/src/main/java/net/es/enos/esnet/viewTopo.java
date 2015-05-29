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
