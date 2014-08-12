/*
 * Copyright (c) 2014, Regents of the University of California  All rights reserved.
 * Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
 * 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

package net.es.enos.esnet;

import net.es.enos.api.GraphSecuredResource;
import net.es.enos.api.Link;
import net.es.enos.api.Node;
import net.es.enos.api.Path;
import net.es.enos.kernel.container.Container;
import net.es.enos.kernel.container.Containers;
import org.jgrapht.GraphPath;
import org.joda.time.DateTime;

import java.util.List;

/**
 * Created by lomax on 6/27/14.
 */
public final class OSCARS {

    public static String ROOT_CONTAINER = "/sys/services/oscars";
    public static String FULL_TOPOLOGY_CONTAINER = ROOT_CONTAINER + "/" + "all";

    /**
     * Checks if the user can provision the provided path. A user is authorized to
     * provision a path only if it has the right to provision each of links of the
     * path and within the provided time range and is authorized to terminate the
     * path at the provided endpoints.
     * @param path
     * @return
     */
    public boolean canProvision (Path path) {
        OSCARSUser oscarsUser = null;
        // Check if the current user is an authorized user to use OSCARS
        // TODO
        GraphPath<Node,Link> graphPath = path.getGraphPath();
        DateTime start = path.getStart();
        DateTime end = path.getEnd();
        Node startNode = graphPath.getStartVertex();
        Node endNode = graphPath.getEndVertex();
        List<Link> links = graphPath.getEdgeList();

        return false;
    }


    static public void install() throws Exception {
        // Create OSCARS container
        Containers.createContainer(ROOT_CONTAINER);
        // Create the container that contains the full OSCARS topology
        Containers.createContainer(FULL_TOPOLOGY_CONTAINER);

    }

    /**
     * Creates an authorization GraphSecuredResource into a container. This container will then be authorized
     * to create OSCARS circuits as long as they are a subset of the authorized graph.
     * The creator of the authorized graph must join a container (source) that is already authorized
     * for the graph.
     * @param graph
     * @return
     */
    static GraphSecuredResource createAuthorizedGraph (GraphSecuredResource graph, Container dest) {
        // Verify that the container in which the calling thread

        return null;
    }


}
