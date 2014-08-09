/*
 * Copyright (c) 2014, Regents of the University of California  All rights reserved.
 * Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
 * 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

package net.es.enos.api;

import net.es.enos.kernel.users.User;
import org.codehaus.jackson.annotate.JsonIgnore;

import java.util.ArrayList;
import java.util.List;

/**
 * Created by lomax on 5/21/14.
 */
public class Resource extends PersistentObject {
    protected String resourceName;
    protected String description;
    private List<User> hasWriteAccess;
    private List<User> hasReadAccess;
    private List<String> capabilities;
    private List<String> parentResources;
    private List<String> childrenResources;
    private String creationStackTrace;

    public Resource() {
        this.setCreationStackTrace();
        // Create, if necessary, the capabilities List.
        if (this.capabilities == null) {
            this.capabilities = new ArrayList<String>();
        }
    }

    public Resource(String resourceName) {
        this.setCreationStackTrace();
        this.resourceName = resourceName;
    }

    public String getResourceName() {
        return resourceName;
    }

    public void setResourceName(String resourceName) {
        this.resourceName = resourceName;
    }

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }

    public List<User> getHasWriteAccess() {
        return hasWriteAccess;
    }

    public void setHasWriteAccess(List<User> hasWriteAccess) {
        this.hasWriteAccess = hasWriteAccess;
    }

    public List<User> getHasReadAccess() {
        return hasReadAccess;
    }

    public void setHasReadAccess(List<User> hasReadAccess) {
        this.hasReadAccess = hasReadAccess;
    }

    public List<String> getCapabilities() {
        return capabilities;
    }

    public void setCapabilities(List<String> capabilities) {
        this.capabilities = capabilities;
    }

    public List<String> getChildrenResources() {
        return childrenResources;
    }
    public List<String> getParentResources() {
        return parentResources;
    }

    public void setChildrenResources(List<String> childrenResources) {
        this.childrenResources = childrenResources;

    }

    public void setParentResources(List<String> parentResources) {
        this.parentResources = parentResources;
    }

    public synchronized void addProperties(String property) {
        this.capabilities.add(property);
    }
    public void addProperties(String[] properties) {
        for (String property : properties) {
            this.capabilities.add(property);
        }
    }

    public Resource (Resource object) {
        this.setCreationStackTrace();

        this.resourceName = object.getResourceName();
        if (object.getCapabilities() !=null) {
            this.capabilities = new ArrayList<String>();
            this.capabilities.addAll(object.getCapabilities());
        }
        this.description = object.getDescription();
        this.setResourceClassName(this.getClass().getCanonicalName());
        if (object.getHasReadAccess() != null) {
            this.setHasReadAccess(new ArrayList<User>());
            this.getHasReadAccess().addAll(object.getHasReadAccess());
        }
        if (object.getHasWriteAccess() != null) {
            this.setHasWriteAccess(new ArrayList<User>());
            this.getHasWriteAccess().addAll(object.getHasWriteAccess());
        }
        if (object.getParentResources() != null) {
            this.setParentResources(new ArrayList<String>());
            this.getParentResources().addAll(object.getParentResources());
        }
    }


    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || ! (o instanceof Resource)) return false;

        Resource resource = (Resource) o;
        return resourceName.equals(resource.resourceName);
    }

    @Override
    public int hashCode() {
        if (this.getResourceName() == null) {
            return super.hashCode();
        }
        return resourceName.hashCode();
    }

    @JsonIgnore
    public String getCreationStackTrace() {
        return this.creationStackTrace;
    }

    @JsonIgnore
    private final void setCreationStackTrace() {
        // this.creationStackTrace = Arrays.toString(Thread.currentThread().getStackTrace());
    }

    @Override
    public String toString() {
        return this.resourceName;
    }
}
