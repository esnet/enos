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

    /**
     * Default constructor. The authorization string can be anything. It is meant as a token. However,
     * that name will be the name of the file into where the AuthorizationResource is stored into.
     * @param authorization
     */
    public AuthorizationResource(String authorization) {
        super();
        this.setResourceName(authorization);
        this.authorization = authorization;
    }

    public String getAuthorization() {
        return authorization;
    }

    public void setAuthorization(String authorization) {
        this.authorization = authorization;
    }

    @JsonIgnore
    /**
     * Returns true if the provided resource is authorized by this AuthorizationResource
     * @param resource to be authorized
     * @return true if the Resource is authorized by this AuthorizationResource. False otherwise
     */
    public boolean isAuthorized(Resource resource) {
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
}
