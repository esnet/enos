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
import net.es.enos.kernel.users.User;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.*;
import java.lang.reflect.Method;
import java.nio.file.Path;
import java.nio.file.Paths;


/**
 * Created by lomax on 7/25/14.
 */
public class Containers {
    public static String ROOT = "/containers";
    private static Logger logger = LoggerFactory.getLogger(Containers.class);
    private static Path homePath = Paths.get(BootStrap.rootPath.toString(),
                                             ROOT).toAbsolutePath();

    // Makes sure the containers directory exists
    static {
        if ( ! homePath.toFile().exists()) {
            // Create root container
            Containers.homePath.toFile().mkdirs();
        }
    }


    public static class ContainerException extends Exception {
        public ContainerException(String message) {
            super(message);
        }
    }


    public static String absoluteName (String name) {

        String pathName;
        if (name == null) {
            return null;
        }
        if (name.startsWith("/")) {
            // Absolute name
            pathName = Containers.ROOT + "/" + name;
        }
        // Relative to currentContainer
        Container currentContainer = KernelThread.currentKernelThread().getCurrentContainer();
        if (currentContainer != null) {
            pathName = currentContainer.getName() + "/" + name;
        } else {
            pathName = Containers.ROOT + "/" + name;
        }
        return pathName;
    }

    public static Path getPath(String name) {
        return Paths.get(BootStrap.rootPath.toString(), Containers.absoluteName(name));
    }

    public static boolean exists(String name) {
        return Containers.getPath(name).toFile().exists();
    }


    public static void createContainer (String name) throws Exception {
        Method method;
        try {
            method = KernelThread.getSysCallMethod(Container.class, "do_createContainer");

            KernelThread.doSysCall(Container.class, method, name);

        } catch (Exception e) {
            // Nothing particular to do.
            e.printStackTrace();
        }
    }

    @SysCall(
            name="do_createContainer"
    )
    private final static void do_createContainer (String name) throws Exception {

        // Check permission: load the current container and checks for ADMIN access
        String containerName = KernelThread.currentContainer();
        if (containerName == null) {
            // Must be in a container
            throw new SecurityException("Must be in a container in order to create one");
        }
        ContainerACL parentAcl = new Container(containerName).getACL();
        if (!parentAcl.canAdmin(KernelThread.currentKernelThread().getUser().getName())) {
            // Does not have the ADMIN right in the current container
            throw new SecurityException("Must be ADMIN");
        }
        // Checks if the container already exists
        if (exists(name)) {
            throw new ContainerException("already exists");
        }

        // Create the directory container
        Path containerPath = Paths.get(Containers.getPath(name).toString());
        new File(containerPath.toString()).mkdirs();
        // Set the read right to the creator
        User user = KernelThread.currentKernelThread().getUser();
        ContainerACL acl = new ContainerACL(containerPath);
        acl.allowAdmin(user.getName());
        acl.allowUserRead(user.getName());
        acl.allowUserExecute(user.getName());
        acl.store();
        // Creates a Container object
        return;
    }

    public static ContainerACL getACL(String name)  {
        Path containerPath = Paths.get(Containers.getPath(name).toString());
        ContainerACL acl = new ContainerACL(containerPath);
        return acl;
    }
}
