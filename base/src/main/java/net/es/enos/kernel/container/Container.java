/*
 * Copyright (c) 2014, Regents of the University of California  All rights reserved.
 * Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
 * 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

package net.es.enos.kernel.container;

import net.es.enos.boot.BootStrap;
import net.es.enos.kernel.exec.KernelThread;
import net.es.enos.kernel.exec.annotations.SysCall;

import java.io.IOException;
import java.lang.reflect.Method;
import java.nio.file.Path;
import java.nio.file.Paths;

/**
 * Created by lomax on 5/27/14.
 */
public final class Container {

    private String name;
    private Path path;
    private Container parentContainer;


    public Container (String name, Container parentContainer) {
        this(name);
        this.parentContainer = parentContainer;
    }

    public Container (String name) {
        this.name = Containers.canonicalName(name);
        this.path = Containers.getPath(name);
        // Verify that the directory can be accessed
        if (this.path.toFile().exists()) {
            if (!this.path.toFile().canRead()) {
                throw new SecurityException("Cannot access this container");
            }
        } else {
            throw new SecurityException("Container does not exist");
        }
    }

    public Path getPath() {
        return Paths.get(BootStrap.rootPath.toString(),this.name);
    }

    public String getName() {
        return name;
    }

    public String getParentContainer() {
        if (this.parentContainer != null) {
            return parentContainer.getName();
        } else {
            return null;
        }
    }

    public void join() {
        KernelThread.currentKernelThread().joinContainer(this.getName());
    }

    public void leave() {
        KernelThread.currentKernelThread().leaveContainer();
    }

    public ContainerACL getACL()  {
        return Containers.getACL(this.getName());
    }

    public void setACL (ContainerACL acl) {

        Method method;
        try {
            method = KernelThread.getSysCallMethod(this.getClass(), "do_setACL");

            KernelThread.doSysCall(this, method, acl);

        } catch (Exception e) {
            // Nothing particular to do.
            e.printStackTrace();
        }
    }

    @SysCall(
            name="do_setACL"
    )
    public void do_setACL(ContainerACL acl) throws IOException {
        // Check if user has the right to administrate this container
        ContainerACL realAcl = this.getACL();
        if (realAcl.canAdmin(KernelThread.currentKernelThread().getUser().getName())) {
            // Authorized, save the acl
            acl.store();
        } else {
            throw new SecurityException("not authorized to administrate this container");
        }
    }

    public String getShortName() {
        String[] items = this.name.split("/");
        return items[items.length - 1];
    }

}

