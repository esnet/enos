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

import net.es.netshell.api.AuthorizationResource;
import net.es.netshell.api.GraphResource;
import net.es.netshell.api.Resource;
import net.es.netshell.kernel.container.Container;
import net.es.netshell.kernel.exec.KernelThread;

/**
 * Implements AuthorizationResource for OSCARS.
 *      * A resource is authorized when the following conditions are met:
 *     - the resource is a GraphResource
 *     - the resource is a subset of at least one of the GraphResource in the list of resources that are
 *     listed in the OSCARSAuthorizationResource.
 */
public class OSCARSAuthorizationResource extends AuthorizationResource {

    private GraphResource authorizedGraph;

    /**
     * Default constructor. The authorization string can b
     *
     * @param name
     * @param destinationContainer
     */
    public OSCARSAuthorizationResource(String name, GraphResource authorizedGraph, Container destinationContainer) {
        super(name, destinationContainer);
        this.authorizedGraph = authorizedGraph;
    }

    /**
     * Checks of a resource is authorized by this OSCARSAuthorizationResource.
     * A resource is authorized when the following conditions are met:
     *     - the resource is a GraphResource
     *     - the resource is a subset of at least one of the GraphResource in the list of resources that are
     *     listed in the OSCARSAuthorizationResource.
     * @param resource that is requested
     * @return true if the resource is authorized.
     */
    @Override
    protected boolean isAuthorized(Resource resource) {
        if (this.authorizedGraph == null) {
            return false;
        }
        if ( ! (resource instanceof GraphResource)) {
            // Only supports GraphResource based authorization
            return false;
        }
        GraphResource targetGraph = (GraphResource) resource;
        return targetGraph.isSubGraphOf(this.authorizedGraph);
    }

    public final void setAuthorizedGraph(GraphResource authorizedGraph) {
        if ((this.authorizedGraph!= null) &&
                !(KernelThread.currentKernelThread().isPrivileged())) {
            throw new SecurityException("not permitted");
        }
        this.authorizedGraph = authorizedGraph;
    }

    public GraphResource getAuthorizedGraph() {
        return this.authorizedGraph;
    }

}
