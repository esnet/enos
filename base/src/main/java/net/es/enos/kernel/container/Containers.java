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

import java.io.File;
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


    public static class ContainerException extends Exception {
        public ContainerException(String message) {
            super(message);
        }
    }

    public static String canonicalName (String name) {
        if (name == null) {
            return null;
        }

        if (name.startsWith("/")) {
            // Already canonical
            return name;
        }
        // Relative path to the current container
        String currentContainer = KernelThread.currentContainer();
        if (currentContainer == null) {
            // Current is root
            return "/" + name;
        }
        return currentContainer + "/" + name;
    }

    public static Path getPath(String name) {
        return Paths.get(BootStrap.rootPath.toString(),
                         Containers.ROOT,
                         Containers.canonicalName(name));
    }

    public static boolean exists(String name) {
        return Containers.getPath(name).toFile().exists();
    }


    public static void createContainer (String name) throws Exception {
        Method method;

        method = KernelThread.getSysCallMethod(Containers.class, "do_createContainer");
        KernelThread.doSysCall(Container.class, method, name);

    }

    @SysCall(
            name="do_createContainer"
    )
    public final static void do_createContainer (String name) throws Exception {

        boolean isPrivileged = KernelThread.currentKernelThread().getUser().isPrivileged();
        logger.info(KernelThread.currentKernelThread().getUser().getName()
                + (isPrivileged ? "(privileged)" : "(not privileged)")
                + " is trying to create a container named "
                + name);
        // Checks if the container already exists
        if (exists(name)) {
            logger.debug("Already exists");
            throw new ContainerException("already exists");
        }
        if (! isPrivileged) {
            // Only privileged users can create containers
            logger.info(KernelThread.currentKernelThread().getUser() + " is not privileged");
            throw new SecurityException("Must be privileged");
        }
        // Makes sure that the container root directory does exist.
        checkContainerDir();
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

    public static void checkContainerDir () {
        if ( ! homePath.toFile().exists()) {
            // Create root container
            Containers.homePath.toFile().mkdirs();
        }
    }

}
