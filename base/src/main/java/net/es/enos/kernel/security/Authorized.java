package net.es.enos.kernel.security;

import java.util.HashMap;

/**
 * Created by lomax on 2/23/14.
 */
public final class Authorized {
    private static HashMap<String,Boolean> authorized = new HashMap<String,Boolean>();
    private static final String homeDir = System.getProperty("user.dir");

    static {
        // All path are relative to current directory.  A true value means Write and Create auth.
        // jyphon creates and uses a directory "cachedir".

        authorized.put("cachedir",new Boolean(true));
        // authorized.put("",new Boolean(true));
    }

    public static boolean isAuthorized (String file, boolean writeRequest) {

        for (String authorizedPath : authorized.keySet()) {
            System.
        }
    }
}
