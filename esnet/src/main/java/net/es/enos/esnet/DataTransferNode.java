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

import net.es.netshell.api.*;
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

    public static GraphResource getAbstractFullMesh() {
        List<Node> dtns = DataTransferNode.getAll();
        GraphResource graph = GraphResource.getFullMesh(dtns);
        return graph;
    }

    public static GraphResource getRemoteFullMesh() {
        List<Node> remoteNodes = DataTransferNode.getRemoteAll();
        GraphResource graph = GraphResource.getFullMesh(remoteNodes);
        return graph;
    }

    public static GraphResource getFullMesh() {
        TopologyProvider topo = TopologyFactory.instance().retrieveTopologyProvider(TopologyFactory.LOCAL_LAYER2);
        if (topo instanceof ESnetTopology) {
                ESnetTopology topology = (ESnetTopology) topo;
            // First build the network full mesh graph
            GraphResource graphResource = DataTransferNode.getRemoteFullMesh();
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
                AbstractNode<Link> dtn = new AbstractNode<Link>(n,((DataTransferNode) n).getRemoteLinks());
                // Add the DTN into the graph

                graph.addVertex(dtn);

                // Add links
                for (Link link : dtn.getLinks()) {
                    Node node = topology.getNodeByLink(link.getResourceName());
                    graph.addEdge(dtn,node,link);
                }
            }
            return new GraphResource(graph);
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
