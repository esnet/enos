package net.es.enos.kernel.security;
import java.io.FileDescriptor;
import java.io.FilePermission;
import java.lang.SecurityManager;
import java.security.Permission;

/**
 * Created by lomax on 2/7/14.
 */
public class KernelSecurityManager extends SecurityManager {
    SecurityManager rootSecurityManager = null;
    public KernelSecurityManager(SecurityManager rootSecurityManager) {
        this.rootSecurityManager = rootSecurityManager;
    }

    public void checkAccess(Thread t) throws SecurityException {
        // System.out.println("checkAccess(Thread t = " + t.getName());
        //
        // throw new SecurityException();
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
}
