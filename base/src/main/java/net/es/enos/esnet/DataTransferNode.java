/*
 * Copyright (c) 2014, Regents of the University of California  All rights reserved.
 * Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
 * 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

package net.es.enos.esnet;

import net.es.enos.api.*;
import org.codehaus.jackson.annotate.JsonIgnore;
import org.jgrapht.Graph;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.lang.reflect.InvocationTargetException;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;

/**
 * This class represents a Data Transfer Node that is deployed within ESnet.
 * The type, which is a long, represent the type or class of the DTN expressed
 * in byte/sec. That means the machine is capable of this kind of bandwidth, network,
 * i/o, cpu.
 */
public class DataTransferNode extends Host {
    public final static Logger logger = LoggerFactory.getLogger(DataTransferNode.class);

    @JsonIgnore
    public static String DTN_DIR="/dtn";
    @JsonIgnore
    private String shortName;
    private String type;
    private List<DataTransferNodeInterface> interfaces;

    public static class AbstractNode<T> extends Node {
        private List<T> links;
        @JsonIgnore
        private String shortName;

        public AbstractNode (Node node, List<T> links) {
            super(node);
            this.shortName = node.toString();
            this.links = links;
        }

        public List<T> getLinks() {
            return links;
        }

        public void setLinks(List<T> links) {
            this.links = links;
        }

        @Override
        public String toString() {
            return this.shortName;
        }

    }

    public String getType() {
        return type;
    }

    public void setType(String type) {
        this.type = type;
    }

    public List<DataTransferNodeInterface> getInterfaces() {
        return interfaces;
    }

    public void setInterfaces(ArrayList<DataTransferNodeInterface> interfaces) {
        this.interfaces = interfaces;
    }


    /**
     * If a file describing the DataTransferNode exists in DTN_DIR, this method will return a
     * DataTransferNode object loaded from that file. Returns null otherwise
     * @param name of the DataTransferNode
     * @return if existing, a DataTransferNode
     */
    @JsonIgnore
    public static DataTransferNode getDataTransferNode(String name) {
        // Load from local file system
        DataTransferNode dtn = null;
        try {
            dtn = (DataTransferNode) PersistentObject.newObject(DataTransferNode.class,
                                                                Paths.get(DTN_DIR, name).toString());
            dtn.shortName = name;
        } catch (IOException e) {
            e.printStackTrace();
        } catch (InstantiationException e) {
            e.printStackTrace();
        }

        return dtn;
    }

    public void save() throws IOException {
        this.save(Paths.get(DTN_DIR, this.getResourceName()).toString());
    }

    /**
     * Returns the ESnetLink of the router/switch this DTN is connected to. The layer 2 Topology
     * is used by default.
     * @return
     */
    @JsonIgnore
    public List<Link> getRemoteLinks() {
        TopologyProvider topo = TopologyFactory.instance().retrieveTopologyProvider(TopologyFactory.LOCAL_LAYER2);
        if (topo instanceof ESnetTopology) {
            ESnetTopology topology = (ESnetTopology) topo;
            ArrayList<Link> links = new ArrayList<Link>();
            for (DataTransferNodeInterface dtnInterface : this.interfaces) {
                for (DataTransferNodeLink dtnLink : dtnInterface.getIfLinks()) {
                    ESnetLink esnetLink = topology.searchLink(dtnLink.getRemoteId());
                    if (esnetLink != null) {
                        links.add(new Link(esnetLink));
                    }
                }
            }
            return links;
        } else {
            // Only support ESnet for now
            return null;
        }
    }

    /**
     * Returns the ESnetNode of the router/switch this DTN is connected to. The layer 2 Topology
     * is used by default.
     * @return
     */
    @JsonIgnore
    public List<Node> getRemoteNodes()  {
        TopologyProvider topo = TopologyFactory.instance().retrieveTopologyProvider(TopologyFactory.LOCAL_LAYER2);
        if (topo instanceof ESnetTopology) {
            ESnetTopology topology = (ESnetTopology) topo;
            ArrayList<Node> nodes = new ArrayList<Node>();
            for (DataTransferNodeInterface dtnInterface : this.interfaces) {
                for (DataTransferNodeLink dtnLink : dtnInterface.getIfLinks()) {
                    ESnetLink esnetLink = topology.searchLink(dtnLink.getRemoteId());
                    if (esnetLink != null) {
                        Node node = topology.getNodeByLink(esnetLink.getRemoteLinkId());
                        if (node != null) {
                            nodes.add(new AbstractNode<DataTransferNodeLink>
                                                    (node,dtnInterface.getIfLinks()));
                        }
                    }
                }
            }
            return nodes;
        } else {
            // Only support ESnet for now
            return null;
        }
    }

    /**
     * Returns the Port of the router/switch this DTN is connected to. The layer 2 Topology
     * is used by default.
     * @return
     */
    @JsonIgnore
    public List<Port> getRemotePorts() {
        TopologyProvider topo = TopologyFactory.instance().retrieveTopologyProvider(TopologyFactory.LOCAL_LAYER2);
        if (topo instanceof ESnetTopology) {
            ESnetTopology topology = (ESnetTopology) topo;
            ArrayList<Port> ports = new ArrayList<Port>();
            for (DataTransferNodeInterface dtnInterface : this.interfaces) {
                for (DataTransferNodeLink dtnLink : dtnInterface.getIfLinks()) {
                    ESnetLink esnetLink = topology.searchLink(dtnLink.getRemoteId());
                    if (esnetLink != null) {
                        Port port = topology.getPortByLink(esnetLink.getRemoteLinkId());
                        if (port != null) {
                            ports.add(new Port(port));
                        }
                    }
                }
            }
            return ports;
        } else {
            // Only support ESnet for now
            return null;
        }
    }

    public static GraphSecuredResource getAbstractFullMesh() {
        List<Node> dtns = DataTransferNode.getAll();
        GraphSecuredResource graph = GraphSecuredResource.getFullMesh(dtns);
        return graph;
    }

    public static GraphSecuredResource getRemoteFullMesh() {
        List<Node> remoteNodes = DataTransferNode.getRemoteAll();
        GraphSecuredResource graph = GraphSecuredResource.getFullMesh(remoteNodes);
        return graph;
    }

    public static GraphSecuredResource getFullMesh() {
        TopologyProvider topo = TopologyFactory.instance().retrieveTopologyProvider(TopologyFactory.LOCAL_LAYER2);
        if (topo instanceof ESnetTopology) {
                ESnetTopology topology = (ESnetTopology) topo;
            // First build the network full mesh graph
            GraphSecuredResource graphResource = DataTransferNode.getRemoteFullMesh();
            // Second connect the DTN's to them
            List<Node> dtns = DataTransferNode.getAll();
            Graph graph = null;
            try {
                graph = graphResource.toGraph();

            } catch (InstantiationException e) {
                return null;
            } catch (ClassNotFoundException e) {
                return null;
            } catch (InvocationTargetException e) {
                return null;
            } catch (IllegalAccessException e) {
                return null;
            }
            for (Node n : dtns) {
                AbstractNode<Link> dtn = new AbstractNode<Link>(n,
                                                                ((DataTransferNode) n).getRemoteLinks());
                // Add the DTN into the graph

                graph.addVertex(dtn);

                // Add links
                for (Link link : dtn.getLinks()) {
                    Node node = topology.getNodeByLink(link.getResourceName());
                    graph.addEdge(dtn,node,link);
                }
            }
            return new GraphSecuredResource(graph);
        } else {
            return null;
        }
    }


    public static List<Node> getRemoteAll() {
        List<Node> dtns = DataTransferNode.getAll();
        ArrayList<Node> remoteNodes = new ArrayList<Node>();
        for (Node n : dtns) {
            if (! (n instanceof DataTransferNode)) {
                logger.warn("Invalid object in DataTransferNode directory of type " + n.getClass());
                continue;
            }
            DataTransferNode dtn = (DataTransferNode) n;
            List<Node> nodes = dtn.getRemoteNodes();
            if ((nodes != null) && (nodes.size() > 0)) {
                for (Node n2 : nodes) {
                    remoteNodes.add(n2);
                }
            }
        }
        return remoteNodes;
    }

    public static List<Node> getAll() {
        java.nio.file.Path dtnPath = FileUtils.toRealPath(DTN_DIR);
        ArrayList<Node> dtns = new ArrayList<Node>();
        for (String fileName : dtnPath.toFile().list()) {
            try {
                DataTransferNode node = DataTransferNode.getDataTransferNode(fileName);
                dtns.add(node);
            } catch (Exception e) {
                // May happen if the file, somehow, is not that of a DataTransferNode
                logger.warn("Cannot read " + fileName + "\nreason:" + e.getMessage());
                continue;
            }
        }
        return dtns;
    }

    @Override
    public String toString() {
        if (this.shortName != null) {
            return this.shortName;
        }
        return super.toString();
    }
}
