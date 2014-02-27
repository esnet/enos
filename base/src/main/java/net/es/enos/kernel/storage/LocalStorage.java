package net.es.enos.kernel.storage;

import java.nio.file.Path;


import java.nio.file.Path;

/**
 * Created by lomax on 2/25/14.
 */
public final class LocalStorage implements Storage {

    private Path location = null;

    public LocalStorage(Path location) {
        this.location = location.normalize();
    }

    public void checkWrite(Path path) throws SecurityException {
        if (path.normalize().startsWith(this.location)) {
            // Within the local storage, authorized
            return;
        }
        throw new SecurityException("Illegal access to " + path.getFileName());
    }

    public void checkRead(Path path) throws SecurityException {
        if (path.normalize().startsWith(this.location)) {
            // Within the local storage, authorized
            return;
        }
        throw new SecurityException("Illegal access to " + path.getFileName());
    }

}