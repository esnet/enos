/*
 * Copyright (c) 2014, Regents of the University of California  All rights reserved.
 * Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
 * 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

package net.es.enos.api;

import net.es.enos.kernel.container.Container;
import net.es.enos.kernel.exec.KernelThread;
import org.codehaus.jackson.annotate.JsonIgnore;
import org.jgrapht.Graph;

import java.util.ArrayList;
import java.util.List;

/**
 * An AuthorizationResource is an abstract class that implements authorization for a given container to use
 * resources that are shared or controlled by another container. Typically, an ENOS application that brokers
 * resources for other application, such as network provisioning for instance, extends AuthorizationResource
 * to describe what a container has the right to do, by overwriting  the isAuthorized(Resource) method.
 *
 * AuthorizationResource can also be used to implement delegation: like any Resource, an AuthorizationResource
 * can have parents and children, forming an authorization graph. The authorization graph is secured by
 * forbidding un-privileged thread to change the parents or children. In other words, management of the
 * authorization must be made within a SysCall implemented by the resource broker (ENOS application).
 */
public abstract class AuthorizationResource extends Resource implements SecuredResource {

    private String destinationContainer;

    /**
     * Default constructor. The authorization string can b
     */
    public AuthorizationResource(String name, Container destinationContainer) {
        super();
        this.setResourceName(name);
        this.destinationContainer = destinationContainer.getName();
    }

    public String getDestinationContainer() {
        return destinationContainer;
    }

    public final void setDestinationContainer(String destinationContainer) {
        if ((this.destinationContainer != null) &&
            !(KernelThread.currentKernelThread().isPrivileged())) {
            throw new SecurityException("not permitted");
        }
        this.destinationContainer = destinationContainer;
    }

    /**
     * This method is intended to be overwritten by the implementing class. isAuthorized is
     * @param resource that is requested
     * @return true if the AuthorizationResource allows the container that is requesting to
     * use all or part of the resource. Returns false otherwise.
     */
    @JsonIgnore
    protected boolean isAuthorized(Resource resource) {
        throw new SecurityException("not permitted");
    }

    /**
     * Check if the resource is allowed to be used. This method will walk the graph
     * of AuthorizationResource, invoking isAuthorized() on each parent AuthorizationResource
     * graph. A SecurityException is thrown if at least one of them denies the access to the resource.
     * @param resource
     */
    public final void checkPermission(Resource resource) {
        Graph<Node, Link> authGraph = this.getAuthorizationGraph();
        if (authGraph == null) {
            throw new SecurityException("no authorization graph");
        }
        this.checkPermission(resource, authGraph);
    }

    private void checkPermission(Resource resource, Graph<Node,Link> authGraph) {
        if (! this.isAuthorized(resource)) {
            throw new SecurityException("not authorized");
        }
        // Find the Node of this AuthorizationResource. Relies on file name to check
        // if a node in the graph is the same as the current.
        Node currentNode = null;
        for (Node n : authGraph.vertexSet()) {
            if (n.getResourceName().equals(this.getFileName())) {
                currentNode = n;
                break;
            }
        }
        if (currentNode == null) {
            throw new SecurityException("invalid authorization graph");
        }
        for (Link link : authGraph.edgesOf(currentNode)) {
            Node srcNode = authGraph.getEdgeSource(link);
            if (srcNode.equals(currentNode)) {
                // This a link to a children. No need to check permission
                continue;
            }
            // Retrieve the AuthorizationResource
            try {
                AuthorizationResource parent =
                        (AuthorizationResource) PersistentObject.newObject(srcNode.getResourceName());
                parent.checkPermission(resource,authGraph);
            } catch (InstantiationException e) {
                throw new SecurityException("cannot access AuthorizationResource " + srcNode.getResourceName());
            }
        }
    }

    @JsonIgnore
    public final Graph<Node,Link> getAuthorizationGraph() {
        GenericGraph graph = new GenericGraph();
        this.buildAuthorizationGraph(graph, null);
        return graph;
    }

    private void buildAuthorizationGraph(GenericGraph graph, Node current) {
        Node me = new Node();
        // Set the resourceName to the file name of the authorization resource
        me.setResourceName(this.getFileName());
        graph.addVertex(me);
        if (current != null) {
            Link link = new Link();
            link.setResourceName(current.getResourceName());
            graph.addEdge(current,me,link);
        }
        if (this.getParentResources() != null) {
            for (String r : this.getParentResources()) {
                try {
                    AuthorizationResource authResource = (AuthorizationResource) PersistentObject.newObject(r);
                    this.buildAuthorizationGraph(graph, me);
                } catch (InstantiationException e) {
                    // Ignore. The authorization may have been removed
                    continue;
                }
            }
        }
        return;
    }

    @JsonIgnore
    public final List<AuthorizationResource> fromContainer() {
        return this.fromContainer(null,null);
    }

    @JsonIgnore
    public final List<AuthorizationResource> fromContainer(Container container) {
        return this.fromContainer(container,null);
    }

    @JsonIgnore
    public final List<AuthorizationResource> fromContainer(Container container, Class type) {
        ArrayList<AuthorizationResource> res = new ArrayList<AuthorizationResource>();
        Graph<Node,Link> graph = this.getAuthorizationGraph();
        for (Link link : graph.edgeSet()) {
            if ((container == null) || link.getResourceName().equals(container.getName())) {
                Node source = graph.getEdgeSource(link);
                try {
                    AuthorizationResource authResource =
                            (AuthorizationResource) PersistentObject.newObject(source.getResourceClassName());
                    if ((type == null) ||
                        authResource.getResourceClassName().equals(type.getCanonicalName())) {
                        res.add(authResource);
                    }
                } catch (InstantiationException e) {
                    // Ignore. Invalid or removed
                    continue;
                }
            }
        }
        return res;
    }
}
