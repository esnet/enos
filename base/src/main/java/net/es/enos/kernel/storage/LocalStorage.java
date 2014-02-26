package net.es.enos.kernel.storage;

import java.nio.file.Path;


import java.nio.file.Path;

/**
 * Created by lomax on 2/25/14.
 */
public final class LocalStorage implements Storage {

    private Path location = null;

    public LocalStorage(Path location) {
        this.location = location;
    }

    public void checkWrite(Path path) throws SecurityException {

    }

    public void checkRead(Path path) throws SecurityException {

    }

}