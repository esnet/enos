/*
 * Copyright (c) 2014, Regents of the University of California  All rights reserved.
 * Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
 * 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

package net.es.enos.esnet;

import net.es.enos.api.AuthorizationResource;
import net.es.enos.api.GraphResource;
import net.es.enos.api.Resource;
import net.es.enos.kernel.container.Container;
import net.es.enos.kernel.exec.KernelThread;

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
