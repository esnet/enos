/*
 * Copyright (c) 2014, Regents of the University of California  All rights reserved.
 * Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
 * 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

package net.es.enos.kernel.container;

import net.es.enos.api.FileUtils;
import net.es.enos.api.PersistentObject;
import net.es.enos.api.Resource;
import net.es.enos.api.ResourceUtils;
import net.es.enos.boot.BootStrap;
import net.es.enos.kernel.exec.KernelThread;
import net.es.enos.kernel.exec.annotations.SysCall;
import net.es.enos.kernel.users.User;
import net.es.enos.kernel.users.UserProfile;
import net.es.enos.kernel.users.Users;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.IOException;
import java.lang.reflect.Method;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;


/**
 * Created by lomax on 7/25/14.
 */
public class Containers {
    public static String ROOT = "/containers";
    public static String SYSTEM_DIR = "/sys";
    public static String USER_DIR = "/users";
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
        KernelThread.doSysCall(Container.class, method, name, true);

    }

    public static void createContainer (String name, boolean createUser) throws Exception {
        Method method;

        method = KernelThread.getSysCallMethod(Containers.class, "do_createContainer");
        KernelThread.doSysCall(Container.class, method, name, createUser);

    }

    @SysCall(
            name="do_createContainer"
    )
    public final static void do_createContainer (String name, boolean createUser) throws Exception {

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
        if ((! isPrivileged) && Containers.isSystem(name)) {
            // Only privileged users can create system containers
            logger.info(KernelThread.currentKernelThread().getUser() + " is not privileged");
            throw new SecurityException("Must be privileged to create system containers");
        }

        // Makes sure that the container root directory does exist.
        checkContainerDir();
        // Create the directory container
        Path containerPath = Paths.get(Containers.getPath(name).toString());

        if (! isPrivileged) {
            // Verifies that the thread user has the ADMIN right
            ContainerACL acl = new ContainerACL(containerPath);
            if (! acl.canAdmin(KernelThread.currentKernelThread().getUser().getName())) {
                throw new SecurityException("Needs admin access to create container " + name);
            }
        }

        new File(containerPath.toString()).mkdirs();
        // Set the read right to the creator
        User user = KernelThread.currentKernelThread().getUser();
        ContainerACL acl = new ContainerACL(containerPath);
        acl.allowAdmin(user.getName());
        acl.allowUserRead(user.getName());
        acl.allowUserExecute(user.getName());
        acl.store();
        // Creates the Container user.
        //
        //public UserProfile(String username, String password, String privilege, String name, String organization, String email) {
        UserProfile profile = new UserProfile(FileUtils.normalize(containerPath.toString()),
                                                                  "*",
                                                                  "user",
                                                                  containerPath.toString(),
                                                                  "Container",
                                                                  "none");
        if (createUser) {
            Users users = new Users();
            users.createUser(profile);
        }

        return;
    }

    public static void removeContainer (String name) throws Exception {
        Method method;

        method = KernelThread.getSysCallMethod(Containers.class, "do_removeContainer");
        KernelThread.doSysCall(Container.class, method, name, true);
    }

    public static void removeContainer (String name, boolean removeUser) throws Exception {
        Method method;

        method = KernelThread.getSysCallMethod(Containers.class, "do_removeContainer");
        KernelThread.doSysCall(Container.class, method, name, removeUser);

    }

    @SysCall(
            name="do_removeContainer"
    )
    public final static void do_removeContainer (String name, boolean removeUser) throws Exception {
        // TODO: to be implemented
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

    public static boolean isSystem (String container) {
        String containerName = FileUtils.normalize(container);
        return container.startsWith(ROOT + "/" + SYSTEM_DIR);
    }

    /**
     * This method allows a SecuredResource to be shared with other containers. Containers then can import/clone
     * the SecuredResource using the method importResource. This system call ensures that the list of children
     * and parent resource is maintained. The thread invoking shareResource must either be privileged or have
     * the ADMIN right in the container where the shared SecuredResource is.
     * @param resource  a SecureResource to be shared
     * @param container name of the container the resource is shared with
     */
    public static void shareResource(ResourceUtils resource, String container) {
        Method method;

        method = KernelThread.getSysCallMethod(Containers.class, "do_shareResource");
        try {
            KernelThread.doSysCall(Container.class, method, resource, container);
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }

    @SysCall(
            name="do_shareResource"
    )
    public static void do_shareResource(ResourceUtils resource, String container) {

        String currentContainer = KernelThread.currentKernelThread().getCurrentContainer().getName();
        String resourceContainer = resource.getContainerName();
        if (!KernelThread.currentKernelThread().getUser().isPrivileged()) {

            if ((currentContainer == null) || !currentContainer.equals(resourceContainer)) {
                // Now allowed
                throw new SecurityException("not permitted");
            }
            ContainerACL acl = KernelThread.currentKernelThread().getCurrentContainer().getACL();

            if ((acl == null) || !acl.canAdmin(KernelThread.currentKernelThread().getUser().getName())) {
                // Now allowed
                throw new SecurityException("not permitted");
            }
        }
        List<String> children = resource.getChildrenResources();
        if (children == null) {
            children = new ArrayList<String>();
        }
        // Add a children to the SecuredResource
        children.add(container + "/" + resource.getShortName());
        resource.setChildrenResources(children);
    }

    /**
     * Unshares a resource that was previously shared with a container. This system call removes
     * the container from the resource's list of children, making the cloned resource invalid.
     * @param resource
     * @param container
     */
    public static void unShareResource(ResourceUtils resource, String container)  {
        Method method;

        method = KernelThread.getSysCallMethod(Containers.class, "do_unShareResource");
        try {
            KernelThread.doSysCall(Container.class, method, resource, container);
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }
    @SysCall(
            name="do_unShareResource"
    )
    public static void do_unShareResource(ResourceUtils resource, String container) {

        String currentContainer = KernelThread.currentKernelThread().getCurrentContainer().getName();
        String resourceContainer = resource.getContainerName();
        if (!KernelThread.currentKernelThread().getUser().isPrivileged()) {

            if ((currentContainer == null) || !currentContainer.equals(resourceContainer)) {
                // Now allowed
                throw new SecurityException("not permitted");
            }
            ContainerACL acl = KernelThread.currentKernelThread().getCurrentContainer().getACL();

            if ((acl == null) || !acl.canAdmin(KernelThread.currentKernelThread().getUser().getName())) {
                // Now allowed
                throw new SecurityException("not permitted");
            }
            removeShare(resource,container);
        }

    }

    private static void removeShare(ResourceUtils resource, String container) {

        List<String> children = resource.getChildrenResources();
        if (children == null) {
            // Nothing to do
            return;
        }
        String cloneResourceName = container + "/" + resource.getShortName();
        ArrayList<String> newChildren = new ArrayList<String>();
        for (String child : children) {
            if (!child.equals(cloneResourceName)) {
                // Not from the container. Keep it
                newChildren.add(child);
            } else {
                // Delete the children
                try {
                    PersistentObject obj = PersistentObject.newObject(cloneResourceName);
                    obj.delete();
                    // unshare the clone itself
                    if (obj instanceof ResourceUtils) {
                        ResourceUtils cloneResource = (ResourceUtils) obj;
                        List<String> cloneChildren = cloneResource.getChildrenResources();
                        if (cloneChildren != null) {
                            for (String cloneChild : cloneChildren) {
                                removeShare(cloneResource,
                                        ResourceUtils.toContainerName(cloneResourceName));
                            }
                        }
                    }
                } catch (InstantiationException e) {
                    // Already removed
                    continue;
                }
            }
        }
        resource.setChildrenResources(newChildren);
    }

    /**
     * Import a SecuredResource that is shared. A clone of the shared resource is created.
     * @param resourceName
     * @throws InstantiationException
     * @throws IOException
     */
    public static void importResource (String resourceName) throws InstantiationException, IOException {
        Method method;
        try {
            method = KernelThread.getSysCallMethod(Containers.class, "do_importResource");
            KernelThread.doSysCall(Container.class, method, resourceName);
        } catch (InstantiationException e) {
            throw e;
        } catch (IOException e) {
            throw e;
        } catch (Exception e)  {
            throw new RuntimeException(e);
        }
    }

    @SysCall(
            name="do_importResource"
    )
    public static void do_importResource (String resourceName) throws InstantiationException, IOException {

        Container currentContainer = KernelThread.currentKernelThread().getCurrentContainer();
        ContainerACL acl = currentContainer != null ?
                currentContainer.getACL() :
                null;

        if (!KernelThread.currentKernelThread().getUser().isPrivileged()) {
            if ((acl == null) || !acl.canAdmin(KernelThread.currentKernelThread().getUser().getName())) {
                // Now allowed
                throw new SecurityException("not permitted");
            }
        }

        PersistentObject obj = Resource.newObject(resourceName);
        if (!(obj instanceof ResourceUtils)) {
            throw new SecurityException("Only SecuredResource can be imported");
        }

        // Clone the resource and save it in the current container.
        ResourceUtils resource = (ResourceUtils) obj;
        String newResourceName = currentContainer.getName() + "/" + resource.getShortName();

        List<String> parents = new ArrayList<String>();
        parents.add(resourceName);
        resource.setParentResources(parents);
        resource.setChildrenResources(new ArrayList<String>());

        resource.setResourceName(newResourceName);
        resource.save(newResourceName);
    }

}
