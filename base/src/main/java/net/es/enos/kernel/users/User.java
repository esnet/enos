/*
 * Copyright (c) 2014, Regents of the University of California  All rights reserved.
 * Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
 * 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

package net.es.enos.kernel.users;

import net.es.enos.boot.BootStrap;

import java.lang.ref.WeakReference;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.HashMap;

/**
 * Created by lomax on 2/25/14.
 */


public class User {

    private static HashMap<String,WeakReference<User>> users = new HashMap<String, WeakReference<User>>();
    private static HashMap<String,WeakReference<User>> usersByGroup = new HashMap<String, WeakReference<User>>();

    private String name;
    private ThreadGroup threadGroup;
    private Path homePath;
    private Path currentPath;
    private boolean privileged = false;

    public ThreadGroup getThreadGroup() {
        return threadGroup;
    }

    public User (String name) {
        this.name = name;

        // Set home directory.
        this.homePath = this.currentPath =
                Paths.get(Users.getUsers().getHomePath().toString(),this.name).normalize();
        // TODO: lomax@es.net this creates a very little memory leak. Will need to have a background
        // thread to clean that up.
        User.users.put(this.name, new WeakReference<User>(this));
        this.privileged = Users.getUsers().isPrivileged(name);
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

    public boolean isPrivileged() {
        return this.privileged;
    }

    public Path getHomePath() {
        return this.homePath;
    }

	// Set the homepath to simulate changing the working directory.
	public void setHomePath(Path newPath) { this.homePath = newPath; }

    public Path getCurrentPath() {
        return currentPath;
    }

    public void setCurrentPath(Path currentPath) {
        this.currentPath = currentPath;
    }

}