/*
 * Copyright (c) 2014, Regents of the University of California  All rights reserved.
 * Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
 * 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

package net.es.enos.api;

import net.es.enos.kernel.exec.KernelThread;
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
    private List<String> parentResources;
    private List<String> childrenResources;
    private String creationStackTrace;

    public Resource() {
        this.setCreationStackTrace();
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

    public Resource (Resource object) {
        this.setCreationStackTrace();

        if (object instanceof SecuredResource) {
            // Cannot clone SecuredResource
            throw new SecurityException("operation is not permitted");
        }
        this.resourceName = object.getResourceName();

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

    public final synchronized void setResourceName (List<String> parentResources) {
        if (! (this instanceof SecuredResource) ||
                (this.getResourceName() == null) ||
                (KernelThread.currentKernelThread().isPrivileged())) {
            this.setResourceName(parentResources);
        } else {
            throw new SecurityException("Operation not permitted");
        }
    }

    public final synchronized void setChildrenResources(List<String> childrenResources) {
        if (!(this instanceof SecuredResource) ||
              (this.getChildrenResources() == null) ||
              (KernelThread.currentKernelThread().isPrivileged())) {
            this.setChildrenResources(childrenResources);
        } else {
            throw new SecurityException("Operation not permitted");
        }
    }

    public final synchronized void setParentResources(List<String> parentResources) {
        if (! (this instanceof SecuredResource) ||
              (this.getParentResources() == null) ||
              (KernelThread.currentKernelThread().isPrivileged())) {
            this.setParentResources(parentResources);
        } else {
            throw new SecurityException("Operation not permitted");
        }
    }

    public final synchronized List<String> getParentResources() {
        if (!(this instanceof SecuredResource)) {
            return this.parentResources;
        }
        // This is a secured Resource. Clone the list first.
        return new ArrayList<String>(this.parentResources);
    }

    public final synchronized List<String> getChildrenResources() {
        if (!(this instanceof SecuredResource)) {
            return this.childrenResources;
        }
        // This is a secured Resource. Clone the list first.
        return new ArrayList<String>(this.childrenResources);
    }
}
