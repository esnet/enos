package net.es.enos.kernel.container;

import net.es.enos.api.PersistentObject;
import net.es.enos.api.Resource;
import net.es.enos.boot.BootStrap;
import net.es.enos.kernel.exec.KernelThread;
import net.es.enos.kernel.security.FileACL;
import net.es.enos.kernel.users.User;
import org.codehaus.jackson.annotate.JsonIgnore;

import java.io.File;
import java.io.IOException;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.HashMap;

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
        this.name = Containers.absoluteName(name);
        this.path = Paths.get(BootStrap.rootPath.toString(),this.name).toAbsolutePath();
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
    public void create() throws IOException {
        // Create the directory container
        this.path.toFile().mkdirs();
        // Set the read right to the creator
        User user = KernelThread.getCurrentKernelThread().getUser();
        ContainerACL acl = new ContainerACL(this.path);
        acl.allowSubContainer(user.getName());
        acl.allowUserRead(user.getName());
        acl.allowUserExecute(user.getName());
        acl.store();
    }

    public String getName() {
        return name;
    }

    public String getParentContainer() {
        return parentContainer.getName();
    }

    public void join() {
        KernelThread.getCurrentKernelThread().joinContainer(this.getName());
    }

    public void leave() {
        KernelThread.getCurrentKernelThread().leaveContainer();
    }

}

