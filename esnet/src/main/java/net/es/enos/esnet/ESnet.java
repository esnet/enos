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
import net.es.netshell.kernel.exec.KernelThread;
import net.es.netshell.kernel.exec.annotations.SysCall;
import org.jgrapht.Graph;
import org.jgrapht.GraphPath;
import org.jgrapht.alg.DijkstraShortestPath;
import org.joda.time.DateTime;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.lang.reflect.Method;


/**
 * This class implements ESnet layer 2 network. It is a singleton.
 */
public final class ESnet extends NetworkProvider {

    private static ESnet instance;
    private ESnetTopology topology;
    private static Object instanceMutex = new Object();
    private static final Logger logger = LoggerFactory.getLogger(ESnet.class);

    public static ESnet instance() {
        synchronized (ESnet.instanceMutex) {
            if (ESnet.instance == null) {
                // Create the singleton
                ESnet.instance = new ESnet();
            }
        }
        return ESnet.instance;
    }

    /**
     * Default constructor
     */
    public ESnet() {
        TopologyProvider topo = TopologyFactory.instance().retrieveTopologyProvider("localLayer2");
        if ( ! (topo instanceof ESnetTopology)) {
            // ENOS configuration must be wrong since the layer 2 topology is not ESnet topology.
            logger.error("Layer2 local topology is not a ESnetTopology. It is a " + topo.getClass().getCanonicalName());
        }
        this.topology = (ESnetTopology) topo;
    }

    @Override
    public String getDnsName() {
        return "es.net";
    }

    @Override
    public Path computePath(String srcNodeName, String dstNodeName, DateTime start, DateTime end) throws IOException {
        // First retrieve the layer 2 topology graph
        Graph topoGraph = this.topology.getGraph(start, end, TopologyProvider.WeightType.TrafficEngineering);
        // Use JGrapht shortest path algorithm to compute the path
        Node srcNode = this.topology.getNode(srcNodeName);
        Node dstNode = this.topology.getNode(dstNodeName);

        if ((srcNode == null) || (dstNode == null)) {
            // Source or destination node does not exist. Cannot compute a path
            return null;
        }
        DijkstraShortestPath shortestPath = new DijkstraShortestPath (topoGraph, srcNode, dstNode);
        GraphPath<Node,Link> graphPath = shortestPath.getPath();

        // Compute the maximum reservable bandwidth on this path
        long maxBandwidth = -1; // -1 means the value was not computed.
        OSCARSReservations oscarsReservations;
        Path path = new Path();

        try {
            oscarsReservations = new OSCARSReservations(this.topology);
            maxBandwidth = oscarsReservations.getMaxReservableBandwidth(graphPath,start,end);
        } catch (IOException e) {
            // Return null in case of I/O exception. This should not happen.
            logger.error("Cannot retrieve OSCARS reservation " + e.getMessage());
        }
        // Build the Path object
        path.setStart(start);
        path.setEnd(end);
        path.setGraphPath(graphPath);
        path.setMaxReservable(maxBandwidth);
        return path;
    }

    public static void registerToFactory() throws IOException {
        NetworkFactory.instance().registerNetworkProvider(ESnet.class.getCanonicalName(), NetworkFactory.LOCAL_LAYER2);
    }

    @Override
    public TopologyProvider getTopologyProvider() {
        return this.topology;
    }

    @Override
    public boolean canProvisionLayer2() {
        /* OSCARS supports only scheduled virtual circuits. Immediate and not time bounded virtucal may be
         * supported with NSI, or by using SDN capable links.
         */
        return false;
    }

    @Override
    public boolean canProvisionScheduledLayer2() {
        return true;
    }

    @Override
    public boolean supportProfile(Layer2ProvisioningProfiles profile) {
        /* While ESnet's OSCARS can support all profiles, this implementation is restricted to best effort */
        return profile.equals(Layer2ProvisioningProfiles.BestEffort);
    }

    @Override
    public ProvisionedPath provisionLayer2(Path path, Layer2ProvisioningProfiles profile) throws IOException {

        if (path.getStart().equals(path.getEnd()) ||
            path.getStart().isAfter(path.getEnd())) {
            throw new IOException("incorrect time constraints");
        }
        if ( ! this.supportProfile(profile)) {
            throw new IOException("does not support this profile");
        }
        Method method = null;
        try {
            method = KernelThread.getSysCallMethod(this.getClass(), "do_authUser");

            KernelThread.doSysCall(this,
                    method,
                    path,
                    profile);
        } catch (NonExistentUserException e) {
            return null;
        } catch (NoSuchMethodException e) {
            e.printStackTrace();
            return null;
        } catch (Exception e) {
            e.printStackTrace();
            return null;
        }
        // Verify ACL
        return null;
    }

    @SysCall(
            name="do_provisionLayer2"
    )
    private ProvisionedPath do_ProvisionedPath(Path path, Layer2ProvisioningProfiles profile) throws IOException {
        return null;
    }

    @Override
    public void deprovisionLayer2(ProvisionedPath path) throws IOException {
        super.deprovisionLayer2(path);
    }


}
