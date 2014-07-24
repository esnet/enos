package net.es.enos.kernel.container;

import net.es.enos.api.PersistentObject;
import net.es.enos.api.Resource;
import net.es.enos.kernel.users.User;

import java.io.IOException;
import java.nio.file.Paths;
import java.util.HashMap;

/**
 * Created by lomax on 5/27/14.
 */
public class Container extends Resource {

    public static String CONTAINERS_ROOT = "/containers";
    public static String CONTAINERS_DIRECTORY = "all";

    public Container(String name) {
        super(name);
        this.setResourceName(name);
    }

    private String buildFilePath(String name) {
        return Paths.get(CONTAINERS_ROOT, CONTAINERS_DIRECTORY, this.getResourceName()).toString();
    }

    public void save() throws IOException {
        this.save(this.buildFilePath(Paths.get(CONTAINERS_ROOT,
                                               CONTAINERS_DIRECTORY,
                                               this.getResourceName()).toString()));
    }

    public static Container newContainer(String name) throws IOException, InstantiationException {
        String filePath = Paths.get(CONTAINERS_ROOT, CONTAINERS_DIRECTORY, name).toString();
        return (Container) PersistentObject.newObject(Container.class,filePath);
    }

}
