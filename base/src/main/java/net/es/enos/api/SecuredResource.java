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
import org.codehaus.jackson.annotate.JsonIgnore;

import java.util.ArrayList;
import java.util.List;

/**
 * A SecureResource is a Resource that belongs to a container. Its name is its path name within
 * the Container directory i.e, a Secured Resource "myresource" in a Container /applications/myapp
 * is named /applications/myapp/myresource.
 *
 * A SecuredResource also requires to be privileged in order to change or modify the list of children and
 * parents.
 */
public class SecuredResource extends Resource {
    private String containerName;


    @Override
    public final synchronized void setChildrenResources(List<String> childrenResources) {
        if ((this.getChildrenResources() == null) || (KernelThread.currentKernelThread().isPrivileged())) {
            this.setChildrenResources(childrenResources);
        } else {
            throw new SecurityException("Operation not permitted");
        }
    }

    @Override
    public final synchronized void setParentResources(List<String> parentResources) {
        if ((this.getParentResources() == null) || (KernelThread.currentKernelThread().isPrivileged())) {
            this.setParentResources(parentResources);
        } else {
            throw new SecurityException("Operation not permitted");
        }
    }

    public final synchronized void setContainerName(String containerName) {
        if ((this.containerName == null) || (KernelThread.currentKernelThread().isPrivileged())) {
            this.containerName = containerName;
        } else {
            throw new SecurityException("Operation not permitted");
        }
    }

    public final synchronized void setResourceName(String resourceName) {
        if ((this.getResourceName() == null) || (KernelThread.currentKernelThread().isPrivileged())) {
            this.setResourceName(resourceName);
        } else {
            throw new SecurityException("Operation not permitted");
        }
    }

    @Override
    public List<String> getChildrenResources() {
        return new ArrayList(this.getChildrenResources());
    }

    @Override
    public List<String> getParentResources() {
        return new ArrayList(this.getParentResources());
    }

    public String getContainerName() {
        return this.containerName;
    }

    @JsonIgnore
    public String getShortName() {
        String[] items = this.getResourceName().split("/");
        return items[items.length - 1];
    }

    public static String toContainerName (String name) {
        String[] elems = name.split("/");
        return name.substring(0, name.length() - (elems[elems.length - 1].length() +1));
    }

}
