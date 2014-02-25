package net.es.enos.kernel.security;

import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.HashMap;
import java.io.FilePermission;
import java.util.Iterator;
import java.util.LinkedList;

/**
 * Created by lomax on 2/23/14.
 */
public final class Authorized {
    private static LinkedList<FilePermission> authorized;

    private static void init() {
        if (authorized != null) {
            return;
        }
        authorized = new LinkedList<FilePermission>();

        /********************************************************************************
         * Jyphon authorized authorized FilePermission
         ********************************************************************************/
        // jyphon creates and uses a directory "cachedir".
        String cachedir = System.getProperty("python.cachedir");
        if (cachedir == null) {
            // This happens when running within an IDE (not running script/start-enos.sh
            // Assume "/tmp/cachedir
            cachedir="/tmp/cachedir";
            authorized.add(new FilePermission(Paths.get("/tmp/cachedir").normalize().toString()+"/-",
                    "read,write"));

        } else {
            authorized.add(new FilePermission(Paths.get(System.getProperty("python.cachedir")).normalize().toString()+"/-",
                    "read,write"));
        }
    }

    public static boolean isAuthorized (FilePermission filePermission) {
        // System.out.println ("isAuthorized ");
        init();
        for (FilePermission perm : authorized) {
            if (perm.implies(filePermission)) {
                // System.out.println("Authorized ");
                // TODO: log
                return true;
            }
        }
        // System.out.println("Not authorized");
        return false;
    }
}
