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
 * An Authorization Resource is a special SecuredResource that can not have parent resources. Their role is
 * represent an authorization token to their children Resource. If such resource is in a given container, all
 * its children Resources can be traced back to the container that shared them. This is typical of applications
 * that provides services to other applications, such as the provisioning service for instance. The delivery
 * of the service is a Resource that has an AuthorizationResource as a parent, in the container that provided
 * it, and the AuthorizationResource itself has the provided Resource as a child. Checking that double link
 * is preserved verifies that the service is authorized. Break the link in either direction means that the
 * provided service is no longer authorized.
 */
public class AuthorizationResource extends Resource implements SecuredResource {
    private String authorization;
    private String sourceContainer;
    private String destinationContainer;
    private String name;
    private List<String> resources;

    /**
     * Default constructor. The authorization string can be anything. It is meant as a token. However,
     * that name will be the name of the file into where the AuthorizationResource is stored into.
     * @param authorization
     */
    public AuthorizationResource(String name,
                                 String authorization,
                                 Container sourceContainer,
                                 Container destinationContainer) {
        super();
        this.name = name;
        this.setResourceName(authorization);
        this.authorization = authorization;
        this.sourceContainer = sourceContainer.getName();
        this.destinationContainer = destinationContainer.getName();
    }

    public String getAuthorization() {
        return authorization;
    }

    /**
     * The name of the authorization cannot be changed after being set
     * @param authorization
     */
    public final synchronized void setAuthorization(String authorization) {
        if (this.authorization == null) {
            this.authorization = authorization;
        } else {
            throw new SecurityException("not permitted");
        }
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

    public String getSourceContainer() {
        return this.sourceContainer;
    }

    public String getName() {
        return name;
    }

    public final void setName(String name) {
        if ((this.name != null) &&
                !(KernelThread.currentKernelThread().isPrivileged())) {
            throw new SecurityException("not permitted");
        }
        this.name = name;
    }


    public final void setSourceContainer(String sourceContainer) {
        if ((this.sourceContainer != null) &&
                !(KernelThread.currentKernelThread().isPrivileged())) {
            throw new SecurityException("not permitted");
        }
        this.sourceContainer = sourceContainer;
    }

    public final synchronized List<String> getResources() {
        if (this.resources == null) {
            this.resources = new ArrayList<String> ();
        }
        return new ArrayList<String>(this.resources);
    }

    public final void setResources(List<String> resources) {
        if ((this.resources != null) &&
                !(KernelThread.currentKernelThread().isPrivileged())) {
            throw new SecurityException("not permitted");
        }
        this.resources = resources;
    }

    /**
     * Returns true if the provided resource is authorized by this AuthorizationResource
     * @param resource to be authorized
     * @return true if the Resource is authorized by this AuthorizationResource. False otherwise
     */
    @JsonIgnore
    public final boolean isAuthorized(Resource resource) {
        if (resource == null) {
            return false;
        }
        // Checks that the parent / children link between the resource and this AuthorizationResource
        // is not broken.
        List<String> parents = resource.getParentResources();
        for (String parent : parents) {
            try {
                PersistentObject obj = PersistentObject.newObject(parent);
                if ( ! (obj instanceof Resource)) {
                    return false;
                }
                Resource parentResource = (Resource) obj;
                // Checks that the parent's children contains the resource
                List<String> children = parentResource.getChildrenResources();
                if ((children == null) || (children.size() == 0)) {
                    // The parent does not have children. Link is broken
                    return false;
                }
                if (!children.contains(resource)) {
                    // The parent children does not contain this resource, the link is broken
                    return false;
                }
                // Check if the ParentResource is this AuthorizationResource
                if (parentResource instanceof AuthorizationResource) {
                    if (this.getAuthorization().equals(
                            ((AuthorizationResource) parentResource).getAuthorization())) {
                        return true;
                    } else {
                        return false;
                    }
                }
                boolean isAuthorized = this.isAuthorized(parentResource);
                if (isAuthorized) {
                    return true;
                }
            } catch (InstantiationException e) {
                return false;
            }
        }
        return false;
    }

    @JsonIgnore
    public Graph<Node,Link> getAuthorizationGraph() {
        GenericGraph graph = new GenericGraph();
        this.buildAuthorizationGraph(graph, null);
        return graph;
    }

    private void buildAuthorizationGraph(GenericGraph graph, Node parent) {
        Node me = new Node();
        me.setResourceName(this.getResourceName());
        me.setDescription(this.getAuthorization());
        graph.addVertex(me);
        if (parent != null) {
            // Link to parent
            Link link = new Link();
            link.setResourceName(this.getDestinationContainer());
            graph.addEdge(parent,me,link);
        }
        if (this.resources != null) {
            for (String r : this.resources) {
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
    public List<AuthorizationResource> fromContainer() {
        return this.fromContainer(null,null);
    }

    @JsonIgnore
    public List<AuthorizationResource> fromContainer(Container container) {
        return this.fromContainer(container,null);
    }

    @JsonIgnore
    public List<AuthorizationResource> fromContainer(Container container, Class type) {
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
