package net.es.enos.kernel.container;

import net.es.enos.api.PersistentObject;
import net.es.enos.api.Resource;
import net.es.enos.boot.BootStrap;
import net.es.enos.kernel.exec.KernelThread;
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

    public Container (String name) {
        this.name = Containers.absoluteName(name);
        this.path = Paths.get(BootStrap.rootPath.toString(),this.name).toAbsolutePath();
        // Verify that the directory can be accessed
        if (this.path.toFile().exists()) {
            if (!this.path.toFile().canRead()) {
                throw new SecurityException("Cannot access this container");
            }
        } else {
            // This Container has not been made persistent yet. Verify that the parent is writable.
            if (this.path.getParent() != null) {
                if (! this.path.getParent().toFile().canWrite()) {
                    throw new SecurityException("Cannot create this container.");
                }
            } else {
                throw new SecurityException("Invalid name");
            }

        }
    }

    public Path getPath() {
        return Paths.get(BootStrap.rootPath.toString(),this.name);
    }
    public void create() {
        this.path.toFile().mkdirs();
    }

    public String getName() {
        return name;
    }
}
