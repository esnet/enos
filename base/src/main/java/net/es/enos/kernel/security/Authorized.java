package net.es.enos.kernel.security;

import java.nio.file.Paths;
import java.io.FilePermission;
import java.util.LinkedList;

/**
 * Created by lomax on 2/23/14.
 */
public final class Authorized {
    private static LinkedList<FilePermission> filePermissions;
    // private static LinkedList<>

    private static void init() {
        if (filePermissions != null) {
            return;
        }
        filePermissions = new LinkedList<FilePermission>();

        /********************************************************************************
         * Jyphon
         ********************************************************************************/
        // jyphon creates and uses a directory "cachedir".
        String cachedir = System.getProperty("python.cachedir");
        if (cachedir == null) {
            // This happens when running within an IDE (not running script/start-enos.sh
            // Assume "/tmp/cachedir
            cachedir="/tmp/cachedir";
            filePermissions.add(new FilePermission(Paths.get("/tmp/cachedir").normalize().toString() + "/-",
                    "read,write"));

        } else {
            filePermissions.add(new FilePermission(Paths.get(System.getProperty("python.cachedir")).normalize().toString() + "/-",
                    "read,write"));
        }
    }

    public static boolean isAuthorized (FilePermission filePermission) {
        // System.out.println ("isAuthorized ");
        init();
        for (FilePermission perm : filePermissions) {
            if (perm.implies(filePermission)) {
                // System.out.println("Authorized ");
                // TODO: log
                return true;
            }
        }
        // System.out.println("Not filePermissions");
        return false;
    }
}
