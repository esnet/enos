package net.es.enos.kernel.net.es.enos.kernel.user;

import net.es.enos.boot.BootStrap;

import java.lang.ref.WeakReference;
import java.util.HashMap;
import java.util.UUID;

/**
 * Created by lomax on 2/25/14.
 */


public final class User {

    private static HashMap<String,WeakReference<User>> users = new HashMap<String, WeakReference<User>>();
    private static HashMap<String,WeakReference<User>> usersByGroup = new HashMap<String, WeakReference<User>>();

    private String name;
    private UUID id;
    private ThreadGroup threadGroup;


    public ThreadGroup getThreadGroup() {
        return threadGroup;
    }

    public User (String name) {
        this.name = name;
        this.id = UUID.randomUUID();
        User.users.put(this.name, new WeakReference<User>(this));
        // Create the user ThreadGroup
        this.threadGroup = new ThreadGroup(BootStrap.getBootStrap().getSecurityManager().getEnosRootThreadGroup(),
                                           "ENOS User " + name + " ThreadGroup");
        User.usersByGroup.put(this.threadGroup.getName(), new WeakReference<User>(this));
    }

    public String getName() {
        return name;
    }

    public static User getUser(String username) {
        synchronized (User.users) {
            WeakReference weakRef = User.users.get(username);
            if (weakRef != null) {
                return (User) weakRef.get();
            }
            return null;
        }
    }

    public static User getUser(ThreadGroup group) {
        synchronized (User.users) {
            WeakReference weakRef = User.usersByGroup.get(group.getName());
            if (weakRef != null) {
                return (User) weakRef.get();
            }
            return null;
        }
    }

}
