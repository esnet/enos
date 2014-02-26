package net.es.enos.kernel.net.es.enos.kernel.user;

import java.security.Permission;

/**
 * Created by lomax on 2/25/14.
 */
public class UserPermission extends Permission {
    /**
     * Constructs a permission with the specified name.
     *
     * @param name name of the Permission object being created.
     */
    public UserPermission(String name) {
        super(name);
    }

    @Override
    public boolean implies(Permission permission) {
        if (! (permission instanceof UserPermission)) {
            // Probably due to a bug in the caller. Returns false
            return false;
        }
        return false;
    }

    @Override
    public boolean equals(Object obj) {
        return false;
    }

    @Override
    public int hashCode() {
        return 0;
    }

    @Override
    public String getActions() {
        return null;
    }
}
