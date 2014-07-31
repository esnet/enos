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
        this.name = name;
        this.path = Containers.getPath(name);
        // Verify that the directory can be accessed
        if (this.path.toFile().exists()) {
            if (!this.path.toFile().canRead()) {
                throw new SecurityException("Cannot access this container");
            }
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
}

