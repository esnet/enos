package net.es.enos.kernel.security;
import net.es.enos.kernel.exec.KernelThread;
import net.es.enos.kernel.net.es.enos.kernel.user.User;

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
        System.out.println("checkAccess(Thread current= " + Thread.currentThread().getName() + " t = " + t.getName());
        // Threads that are not part of ENOS ThreadGroup are authorized
        Thread currentThread = Thread.currentThread();
        if ((currentThread.getThreadGroup() == null) ||
            (this.enosRootThreadGroup.parentOf(currentThread.getThreadGroup()))) {
            return;
        }
        if (Thread.currentThread().getThreadGroup().parentOf(t.getThreadGroup())) {
            // A thread can do whatever it wants on thread of the same user
            return;
        }
        throw new SecurityException("Illegal Thread access from " + Thread.currentThread().getName() + " onto " +
                                     t.getName());
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
        // return this.enosRootThreadGroup;
        return null;
    }

    public ThreadGroup getEnosRootThreadGroup() {
        return this.enosRootThreadGroup;
    }

}
