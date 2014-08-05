/*
 * Copyright (c) 2014, Regents of the University of California  All rights reserved.
 * Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
 * 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

package net.es.enos.api;

import org.codehaus.jackson.annotate.JsonIgnore;
import org.jgrapht.Graph;
import org.jgrapht.WeightedGraph;
import org.jgrapht.graph.DefaultListenableGraph;
import org.jgrapht.graph.DirectedMultigraph;

import java.lang.reflect.InvocationTargetException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Set;


/**
 * This class is a Resource representation of a graph.
 */
public class TopologyGraph extends Resource {
    private String className;
    private List<NodeDesc> nodeDescs;
    private List<LinkDesc> linkDescs;

    static public class NodeDesc {
        private String id;
        private Node node;

        @JsonIgnore
        public NodeDesc(String id, Node node) {
            this.id = id;
            this.node = node;
        }

        public NodeDesc() { }

        public String getId() {
            return id;
        }

        public void setId(String id) {
            this.id = id;
        }

        public Node getNode() {
            return node;
        }

        public void setNode(Node node) {
            this.node = node;
        }
    }

    static public class LinkDesc {
        private String srcNodeId;
        private String dstNodeId;
        private Link link;


        public LinkDesc() { }

        @JsonIgnore
        public LinkDesc(Link link, String srcId, String dstId) {
            this.link = link;
            this.srcNodeId = srcId;
            this.dstNodeId = dstId;
        }

        public String getSrcNodeId() {
            return srcNodeId;
        }

        public void setSrcNodeId(String srcNodeId) {
            this.srcNodeId = srcNodeId;
        }

        public String getDstNodeId() {
            return dstNodeId;
        }

        public void setDstNodeId(String dstNodeId) {
            this.dstNodeId = dstNodeId;
        }

        public Link getLink() {
            return link;
        }

        public void setLink(Link link) {
            this.link = link;
        }

    }

    static public class GenericGraph extends DefaultListenableGraph<Node, Link> implements Graph<Node, Link> {
        public GenericGraph(Class<? extends Link> edgeClass) {
            super(new DirectedMultigraph<Node, Link>(edgeClass));
        }

        public GenericGraph() {
            super(new DirectedMultigraph<Node, Link>(Link.class));
        }

        @JsonIgnore
        @Override
        public double getEdgeWeight(Link link) {
            return link.getWeight();
        }

        @JsonIgnore
        @Override
        public void setEdgeWeight(Link link, double weight) {
            link.setWeight(weight);
        }
    }

    public List<NodeDesc> getNodeDescs() {
        return nodeDescs;
    }

    public void setNodeDescs(List<NodeDesc> nodeDescs) {
        this.nodeDescs = nodeDescs;
    }

    public List<LinkDesc> getLinkDescs() {
        return linkDescs;
    }

    public void setLinkDescs(List<LinkDesc> linkDescs) {
        this.linkDescs = linkDescs;
    }

    public String getClassName() {
        return className;
    }

    public void setClassName(String className) {
        this.className = className;
    }

    public TopologyGraph() {

    }

    public TopologyGraph (Graph graph) {

        Set<Node> vertices = graph.vertexSet();
        this.nodeDescs = new ArrayList<NodeDesc>();
        this.linkDescs = new ArrayList<LinkDesc>();
        this.className = graph.getClass().getCanonicalName();
        // Index the nodes
        HashMap<String,NodeDesc> map = new HashMap<String,NodeDesc>();
        int id = 0;
        for (Node node : vertices) {
            Node n = new Node(node);
            NodeDesc desc = new NodeDesc(Integer.toString(++id),n);
            map.put(n.getResourceName(),desc);
            this.nodeDescs.add(desc);
        }
        Set<Link> links = graph.edgeSet();
        for (Link link : links) {
            String srcId = map.get(((Node) graph.getEdgeSource(link)).getResourceName()).getId();
            String dstId = map.get(((Node) graph.getEdgeTarget(link)).getResourceName()).getId();
            double weight = graph.getEdgeWeight(link);
            LinkDesc desc = new LinkDesc(new Link(link),srcId,dstId);
            linkDescs.add(desc);
        }
    }

    public Graph toGraph() throws InstantiationException, ClassNotFoundException, InvocationTargetException, IllegalAccessException {
        GenericGraph graph = new GenericGraph();

        // create a map of the Nodes and add them to the graph
        HashMap<String, Node> map = new HashMap<String,Node>();
        for (NodeDesc nodeDesc : this.nodeDescs) {
            map.put(nodeDesc.getId(),nodeDesc.getNode());
            graph.addVertex(nodeDesc.getNode());
        }
        // Add links
        for (LinkDesc linkDesc : this.linkDescs) {
            Link link = linkDesc.getLink();
            Node srcNode = map.get(linkDesc.getSrcNodeId());
            Node dstNode = map.get(linkDesc.getDstNodeId());
            graph.addEdge(srcNode,dstNode,link);
            if (graph instanceof WeightedGraph) {
                ((WeightedGraph) graph).setEdgeWeight(link,link.getWeight());
            }
        }
        return graph;
    }

    static public TopologyGraph getFullMesh(List<Node> nodes) {

        TopologyGraph topoGraph = new TopologyGraph();
        topoGraph.nodeDescs = new ArrayList<NodeDesc>();
        topoGraph.linkDescs = new ArrayList<LinkDesc>();

        for (Node node : nodes) {
            NodeDesc nodeDesc = new NodeDesc();
            nodeDesc.setNode(node);
            nodeDesc.setId(node.getResourceName());
            topoGraph.nodeDescs.add(nodeDesc);
        }
        // Create full mesh (Directed)
        for (Node srcNode : nodes) {
            for(Node dstNode : nodes) {
                if (srcNode.equals(dstNode)) {
                    continue;
                }
                LinkDesc linkDesc = new LinkDesc();
                Link link = new Link();
                link.setWeight(1);
                linkDesc.setLink(link);
                linkDesc.setSrcNodeId(srcNode.getResourceName());
                linkDesc.setDstNodeId(dstNode.getResourceName());
                topoGraph.linkDescs.add(linkDesc);
            }
        }
        return topoGraph;
    }
}
