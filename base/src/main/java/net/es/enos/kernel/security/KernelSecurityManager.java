package net.es.enos.kernel.security;
import net.es.enos.kernel.exec.KernelThread;

import java.io.FileDescriptor;
import java.io.FilePermission;
import java.lang.SecurityManager;
import java.security.Permission;

/**
 * Created by lomax on 2/7/14.
 */
public class KernelSecurityManager extends SecurityManager {
    private ThreadGroup enosRootThreadGroup = new ThreadGroup("ENOS Root ThreadGroup");

    public KernelSecurityManager() {
        System.setSecurityManager(this);
    }

    @Override
    public boolean getInCheck() {
        return super.getInCheck();
    }

    public void checkAccess(Thread t) throws SecurityException {
        // System.out.println("checkAccess(Thread current= " + Thread.currentThread().getName() + " t = " + t.getName());
        // Authorized all non ENOS user threads. Perhaps too much but needed for nio
    }

    @Override
    public void checkPackageAccess(String p) throws SecurityException {
        // System.out.println("checkPackageAccess " + p);
    }

    public void checkPermission(Permission perm) throws SecurityException {
        // System.out.println ("checkPermission " + perm.getName() + ":" + perm.getActions() + perm.getClass().getName());
    }

    public void checkWrite(String file) throws SecurityException {
        System.out.println("checkWrite " + file);

        if (KernelThread.getCurrentKernelThread().isPrivileged()) {
            System.out.println("Privileged thread: Accept");
            return;
        }

        if (Authorized.isAuthorized(new FilePermission(file,"write"))) {
            // Authorized.
            System.out.println("Accept");
            return;
        }
        // Not authorized
        System.out.println("Reject");
        throw new SecurityException();
    }
    public void checkWrite(FileDescriptor file) throws SecurityException {
        // System.out.println("checkWrite fd ");
        // throw new SecurityException();
    }

    @Override
    public ThreadGroup getThreadGroup() {
        return this.enosRootThreadGroup;
    }

    public ThreadGroup getEnosRootThreadGroup() {
        return this.enosRootThreadGroup;
    }

}
