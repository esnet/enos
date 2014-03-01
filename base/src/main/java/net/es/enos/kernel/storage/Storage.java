package net.es.enos.kernel.storage;

import java.nio.file.Path;

/**
 * Created by lomax on 2/25/14.
 */
public interface Storage {

    public void checkWrite(Path path) throws SecurityException;
    public void checkRead(Path path) throws SecurityException ;
    public Path getRootPath();

}
