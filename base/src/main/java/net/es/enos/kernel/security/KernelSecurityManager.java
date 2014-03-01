package net.es.enos.kernel.security;
import net.es.enos.kernel.exec.KernelThread;
import net.es.enos.kernel.net.es.enos.kernel.user.User;

import java.io.FileDescriptor;
import java.io.FilePermission;
import java.lang.SecurityManager;
import java.lang.reflect.InvocationTargetException;
import java.nio.file.Paths;
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
        // Threads that are not part of ENOS ThreadGroup are authorized
        Thread currentThread = Thread.currentThread();
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
        throw new SecurityException("Illegal Thread access from " + Thread.currentThread().getName() + " onto " +
                                     t.getName());
    }

    @Override
    public void checkPackageAccess(String p) throws SecurityException {
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
    }

    public void checkPermission(Permission perm) throws SecurityException {
        // System.out.println ("checkPermission " + perm.getName() + ":" + perm.getActions() + perm.getClass().getName());
    }

    public void checkWrite(String file) throws SecurityException {
        // System.out.println("checkWrite " + file);

        if (KernelThread.getCurrentKernelThread().isPrivileged()) {
            // System.out.println("Privileged thread: Accept");
            return;
        }

        if (Authorized.isAuthorized(new FilePermission(file,"write"))) {
            // Authorized.
            // System.out.println("Accept");
            return;
        }
        User user = User.getUser(Thread.currentThread().getThreadGroup());
        if (user != null) {
            user.getStorage().checkWrite(Paths.get(file));
        }
        // Not authorized
        // System.out.println("Reject");
        throw new SecurityException();
    }
    public void checkWrite(FileDescriptor file) throws SecurityException {
        // System.out.println("checkWrite fd ");
        // throw new SecurityException();
    }

    @Override
    public void checkRead(String file) {
        if (true) return;

        System.out.println("checkRead " + file);
        if (Thread.currentThread().getStackTrace().length > 2000) {
            System.out.println(file);
        }

        java.lang.reflect.Method method = this.getClass().getEnclosingMethod();
        try {
            KernelThread.doSysCall(this.getClass().getEnclosingMethod(),file);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    private void doCheckRead(String file) {


        if (Authorized.isAuthorized(new FilePermission(file,"read"))) {
            // Authorized.
            System.out.println("Accept");
            return;
        }
        User user = User.getUser(Thread.currentThread().getThreadGroup());
        if (user != null) {
            user.getStorage().checkRead(Paths.get(file));
        }
        // Not authorized
        // System.out.println("Reject");
        throw new SecurityException();
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
