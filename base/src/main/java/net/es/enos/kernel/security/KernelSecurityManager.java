/*
 * Copyright (c) 2014, Regents of the University of California.
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 * 1. Redistributions of source code must retain the above copyright notice,
 * this list of conditions and the following disclaimer.
 *
 * 2. Redistributions in binary form must reproduce the above copyright notice,
 * this list of conditions and the following disclaimer in the documentation
 * and/or other materials provided with the distribution.
 *
 * 3. Neither the name of the copyright holder nor the names of its contributors
 * may be used to endorse or promote products derived from this software without
 * specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 * DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
 * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
 * CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
 * OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

package net.es.enos.kernel.security;
import net.es.enos.boot.BootStrap;
import net.es.enos.api.DefaultValues;
import net.es.enos.api.ENOSException;
import net.es.enos.api.PropertyKeys;
import net.es.enos.kernel.exec.KernelThread;
import net.es.enos.kernel.exec.annotations.SysCall;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.FileDescriptor;
import java.io.IOException;
import java.lang.SecurityManager;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.security.Permission;
import java.util.HashMap;
import java.util.Map;

/**
 * This class implements the core ENOS Security Manager. It implements SecurityManager and is set as the System
 * SecurityManager. It is, therefore, critical to the overall security if the system.
 */
public class KernelSecurityManager extends SecurityManager {
    private ThreadGroup enosRootThreadGroup = new ThreadGroup("ENOS Root ThreadGroup");
    private Path rootPath;
    private final Logger logger = LoggerFactory.getLogger(KernelSecurityManager.class);
    private static HashMap<String,Boolean> writeAccess = new HashMap<String,Boolean>();

    public KernelSecurityManager() {
        String sec = System.getProperty(PropertyKeys.ENOS_SECURITYMANAGER);
        if ((sec != null) && (sec.equals("no")))  {
            // No do start SecurityManager. If undefined, start SecurityManager
            logger.warn("enos.securitymanager is set to no. This disables ENOS SecurityManager, which disables security all together. MUST NOT RUN IN PRODUCTION.");
            return;
        }
        this.preloadClasses();
        this.initializePreAuthorized();
        System.setSecurityManager(this);

        // Figure out the ENOS root directory.
        String rootdir;
        try {
            rootdir = BootStrap.getMasterConfiguration().getGlobal().getRootDirectory();
        }
        catch (NullPointerException e) {
            rootdir = DefaultValues.ENOS_DEFAULT_ROOTDIR;
        }
        this.rootPath = Paths.get(rootdir).normalize();
    }

    @Override
    public boolean getInCheck() {
        return super.getInCheck();
    }

    @Override
    public void checkAccess(Thread t) throws SecurityException {
        // System.out.println("checkAccess(Thread current= " + Thread.currentThread().getName() + " t = " + t.getName());
        // Threads that are not part of ENOS ThreadGroup are authorized
        Thread currentThread = Thread.currentThread();
        // System.out.println("checkAccess " + currentThread.getThreadGroup().getName());
        if (this.isPrivileged()) {
            return;
        }

        if ((currentThread.getThreadGroup() == null) ||
            (KernelThread.getCurrentKernelThread().isPrivileged()) ||
            ( !this.enosRootThreadGroup.parentOf(currentThread.getThreadGroup()))) {
            return;
        }
        if (Thread.currentThread().getThreadGroup().parentOf(t.getThreadGroup())) {
            // A thread can do whatever it wants on thread of the same user
            return;
        }
        if ( ! this.enosRootThreadGroup.parentOf(t.getThreadGroup())) {
            // This is a non ENOS Thread. Allow since the only non ENOS thread that can be referenced to are
            // from java library classes. This is safe.
            return;
        }
        Thread.dumpStack();

        throw new SecurityException("Illegal Thread access from " + Thread.currentThread().getName() + " onto " +
                                     t.getName());
    }

    @Override
    public void checkPackageAccess(String p) throws SecurityException {

        // TODO: lomax@es.net the restriction on es.net classes sounds like a neat idea, but might not be
        // neither realistic nor usefull. To revisit.

        /*****
        // System.out.println("package= " + p);
        if (! p.startsWith("net.es")) {
            // Authorize all non ENOS classes
            // System.out.println("non ENOS: Accept");
            return;
        }

        // net.es.enos.kernel.security is always allowed
        if ("net.es.enos.kernel.security".equals(p) || ("net.es.enos.kernel.exec".equals(p))) {
            return;
        }

        if (KernelThread.getCurrentKernelThread().isPrivileged()) {
            return;
        }


        // System.out.println("Reject");
        throw new SecurityException("Thread " + Thread.currentThread().getName() + " attempted to access a non authorized ENOS class: " + p);
        **/
    }

    @Override
    public void checkPermission(Permission perm) throws SecurityException {
        // System.out.println ("checkPermission " + perm.getName() + ":" + perm.getActions() + perm.getClass().getName());
    }


    @Override
    public void checkWrite(String file) throws SecurityException {
        logger.debug("checkWrite " + file );
        for (Map.Entry<String, Boolean> s : KernelSecurityManager.writeAccess.entrySet()) {
            if (s.getValue() && file.startsWith(s.getKey())) {
                // Allowed by predefined access
                logger.info("Allowing write access by predefined access to " + file);
                return;
            } else if (!s.getValue() && file.equals(s.getKey())) {
                // Request strict pathname
                logger.info("Allowing write access by predefined access to " + file);
                return;
            }
        }
        if (this.isPrivileged()) {
            logger.info("checkWrite allows " + file + " because thread is privileged");
            return;
        }
        try {
            if (this.rootPath == null ||
                    (!file.startsWith(this.rootPath.toFile().toString()) &&
                            !file.startsWith(this.rootPath.toFile().getCanonicalPath()))) {
                // If the file is not within ENOS root dir, reject.
                // TODO: this should be sufficient but perhaps needs to be revisited
                logger.info("reject write file " + file + " because the file is not an ENOS file");
                throw new SecurityException("Cannot write file " + file);
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
        try {
            FileACL acl = new FileACL(Paths.get(file));
            if (acl.canWrite(KernelThread.getCurrentKernelThread().getUser().getName())) {
                logger.info("checkWrite allows " + file + " because ENOS User ACL for the user allows it.");
                return;
            }
        } catch (IOException e) {
            logger.info("checkWrite rejects " + file + " due to IOException " + e.getMessage());
            throw new SecurityException("IOException when retrieving ACL of " + file + ": " + e);
        }
        logger.info("checkWrite rejects " + file);

        throw new SecurityException("Not authorized to write file " + file);
    }

    public void checkWrite(FileDescriptor file) throws SecurityException {
        // System.out.println("checkWrite fd ");
        // throw new SecurityException();
    }

    @Override
    public void checkRead(String file) {
        logger.debug("checkRead starts " + file );

        if (this.rootPath == null || !file.startsWith(this.rootPath.toFile().getAbsolutePath())) {
            // If the file is not within ENOS root dir, allow and rely on system permissions for read.
            // TODO: this should be sufficient but perhaps needs to be revisited
            logger.debug("checkRead ok " + file + " not an ENOS file. Rely on system access");
            return;
        }
        if (this.isPrivileged()) {
            logger.debug("checkRead ok " + file + " because thread is privileged");
            return;
        }
        try {
            FileACL acl = new FileACL(Paths.get(file));
            if (acl.canRead()) {
                logger.debug("checkRead ok " + file + " because user ENOS ACL allows it.");
                return;
            }
        } catch (IOException e) {
            logger.info("checkRead reject " + file + " got exception " + e.toString());
            throw new SecurityException("IOException when retrieving ACL of " + file + ": " + e);
        }
        logger.info("checkRead reject  " + file + " because thread is user, file is in ENOS rootdir and user ACL does not allows");
        throw new SecurityException("Not authorized to read file " + file);
    }


    @Override
    public ThreadGroup getThreadGroup() {
        // return this.enosRootThreadGroup;
        return null;
    }

    /**
     * All ENOS threads are part of a ThreadGroup that share a same, root, ThreadGroup.
     * getEnosRootThreadGroup returns that ThreadGroup.
     * @return ENOS root ThreadGroup
     */
    public ThreadGroup getEnosRootThreadGroup() {
        return this.enosRootThreadGroup;
    }

    private boolean isPrivileged() {

        Thread t = Thread.currentThread();
        ThreadGroup enosRootThreadGroup = null;
        // BootStrap may be null when running within an IDE: the SecurityManager is changed by ENOS.
        if ((BootStrap.getBootStrap() == null) || (BootStrap.getBootStrap().getSecurityManager() == null)) {
            // Still bootstrapping
            return true;
        }

        enosRootThreadGroup = BootStrap.getBootStrap().getSecurityManager().getEnosRootThreadGroup();

        if (t.getThreadGroup() == null) {
            // Not created yet, this is still bootstraping
            return true;
        } else if (!enosRootThreadGroup.parentOf(t.getThreadGroup())) {
            // This thread has no group: not an ENOS thread
            return true;

        } else {
            // This is an ENOS thread.
            return KernelThread.getCurrentKernelThread().isPrivileged();
        }
    }

    /**
     * Classes that the KernelSecurityManager need to be preloaded so there is not a cyclic dependency
     */
    private void preloadClasses () {
        Class c = KernelThread.class;
        c = SysCall.class;
        c = ENOSException.class;
        c = net.es.enos.api.DefaultValues.class;
    }

    private void initializePreAuthorized() {
        String classPath =  System.getProperty("java.class.path");
        if ((classPath != null) && (classPath.split(" ").length > 0)) {
            // More than one element in the class path means that ENOS is running within its ONEJAR. Therefore
            // we need to allow write access to the jyphon cache. TODO: this sounds dangerous
            KernelSecurityManager.writeAccess.put(System.getProperty("java.class.path") + "!", new Boolean(true));

        }
    }
}
