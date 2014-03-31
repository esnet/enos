/*
 * Copyright (c) 2014, Regents of the University of California  All rights reserved.
 * Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
 * 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

package net.es.enos.kernel.users;

import net.es.enos.common.DefaultValues;
import net.es.enos.common.NonExistantUserException;
import net.es.enos.common.PropertyKeys;
import net.es.enos.common.UserAlreadyExistException;
import net.es.enos.kernel.exec.KernelThread;
import net.es.enos.kernel.exec.annotations.SysCall;
import net.es.enos.kernel.security.FileACL;

import java.io.*;
import java.lang.reflect.Method;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.HashMap;

import static org.apache.commons.codec.digest.Crypt.crypt;

/**
 * Manages Users.
 * This class implements the user management. It is responsible for providing the hooks to AA(A),
 * persistent user information/state/permission. While implementation of those services may vary
 * upon deployments, the Users class is not intended to be extended. It is a singleton.
 *
 * TODO: this class is currently implemented very poorly. It is just intended so other part of ENOS can be worked on.
 * IMPORTANT: this class is not intended for production.
 */
public final class Users {

    private final static Users users = new Users();

    /* Users directory */
    public final static String USERS_DIR="users";

    public final class Profile {
        private String name;
        private String password;
        private String privilege;

        public String getName() {
            return name;
        }

        public void setName(String name) {
            this.name = name;
        }

        public String getPassword() {
            return password;
        }

        public void setPassword(String password) {
            this.password = password;
        }

        public String getPrivilege() {
            return privilege;
        }

        public void setPrivilege(String privilege) {
            this.privilege = privilege;
        }

        public Profile(String line) {
            String[] elements = line.split(":");
            if (elements.length < 2) {
                // Incorrect format. Ignore
                return;
            }
            name = elements[0];
            password = elements[1];
            privilege = elements[2];
        }

        public Profile(String name, String password, String privilege) {
            this.name = name;
            this.password = password;
            this.privilege = privilege;
        }

        @Override
        public String toString() {
            String line = "";
            line += name + ":";
            line += password + ":";
            line += privilege;

            return line;
        }
    }

    private final static String ADMIN_USERNAME = "admin";
    private final static String ADMIN_PASSWORD = "enos";
    private final static String ROOT = "root";
    private final static String USER = "user";
    private Path passwordFilePath;
    private Path enosRootPath;
    private HashMap<String,Profile> passwords = new HashMap<String, Profile>();

    public Users() {
        String enosRootDir = System.getProperty(PropertyKeys.ENOS_ROOTDIR);
        if (enosRootDir == null) {
            // Assume default.
            enosRootDir = DefaultValues.ENOS_DEFAULT_ROOTDIR;
        }
        this.enosRootPath = Paths.get(enosRootDir).normalize();
        this.passwordFilePath = Paths.get(this.enosRootPath.toString() +"/etc/enos.users");

        // Read user file or create it if necessary
        try {
            this.readUserFile();
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    public static Users getUsers() {
        return users;
    }


    public boolean authUser (String user, String password) throws IOException {
        // Read file.
        this.readUserFile();

        if (this.passwords.isEmpty()) {
            // No user has been created. Will accept "admin","enos".
            // TODO: default admin user should be configured in a safer way.
            if (Users.ADMIN_USERNAME.equals(user) && Users.ADMIN_PASSWORD.equals(password)) {
                // Create the initial configuration file
                try {
                    this.do_createUser(Users.ADMIN_USERNAME, Users.ADMIN_PASSWORD, Users.ROOT);
                } catch (UserAlreadyExistException e) {
                    // Since this code is executed only when the configuration file is empty, this should never happen.
                    e.printStackTrace();
                }
                // Accept
                return true;
            }
        }


        if (!Users.getUsers().passwords.containsKey(user)) {
            System.out.println(user + " is unknown");
            return false;
        }
        Profile userProfile = Users.getUsers().passwords.get(user);

        // Local password verification here.  Check an encrypted version of the user's password
        // against what was stored in password file, a la UNIX password authentication.
        if (userProfile.getPassword().equals(crypt(password, userProfile.getPassword()))) {
            System.out.println(user + " has entered correct password");
            return true;
        } else {
            System.out.println(user + " has entered incorrect password ");
            return false;
        }
    }



    public boolean setPassword (String userName, String oldPassword, String newPassword) {
        Method method = null;
        try {
            method = KernelThread.getSysCallMethod(this.getClass(), "do_setPassword");

            KernelThread.doSysCall(this,
                    method,
                    userName,
                    oldPassword,
                    newPassword);
        } catch (UserAlreadyExistException e) {
            return false;
        } catch (NoSuchMethodException e) {
            e.printStackTrace();
            return false;
        } catch (Exception e) {
            e.printStackTrace();
            return false;
        }
        return true;

    }


    @SysCall(
            name="do_setPassword"
    )
    public void do_setPassword(String userName, String oldPassword, String newPassword) throws NonExistantUserException {
        System.out.println("do_setPassword");

        // Make sure the user already exists.
        if (! this.passwords.containsKey(userName)) {
            throw new NonExistantUserException(userName);
        }
        KernelThread kt = KernelThread.getCurrentKernelThread();
        String currentUserName = kt.getUser().getName();

        System.out.println("current user " + currentUserName);

        // Username check.  Any user can change his or her own password.
        // A privileged user can change anybody's password.
        if ((currentUserName.equals(userName)) ||
                isPrivileged(currentUserName)) {
            System.out.println("OK to change");

            Profile userProfile = Users.getUsers().passwords.get(userName);

            // Password check the old password.
            // Alternatively if this thread is privileged, don't need to check this.
            if (isPrivileged(currentUserName) ||
                    userProfile.getPassword().equals(crypt(oldPassword, userProfile.getPassword()))) {

                System.out.println("Password check succeeded");

                // TODO:  Encrypt new password and write out the users file
            }


        }


    }

    public boolean createUser  (String username, String password, String privilege) {
        Method method = null;
        try {
            method = KernelThread.getSysCallMethod(this.getClass(), "do_createUser");

            KernelThread.doSysCall(this,
                    method,
                    username,
                    password,
                    privilege);
        } catch (UserAlreadyExistException e) {
            return false;
        } catch (NoSuchMethodException e) {
            e.printStackTrace();
            return false;
        } catch (Exception e) {
            e.printStackTrace();
            return false;
        }
        return true;
    }

    @SysCall(
            name="do_createUser"
    )
    public void do_createUser (String username, String password, String privilege) throws UserAlreadyExistException, IOException {
        System.out.println("do_createUser");
        // Checks if the user already exists
        if (this.passwords.containsKey(username)) {
            throw new UserAlreadyExistException(username);
        }
        // Construct the new Profile.
        Profile userProfile = new Profile(
                username,
                crypt(password), // Let the Crypt library pick a suitable algorithm and a random salt
                privilege);
        this.passwords.put(username,userProfile);
        // Create home directory
        File homeDir = new File (Paths.get(this.getHomePath().toString(), username).toString());
        homeDir.mkdirs();
        // Create proper access right
        FileACL fileACL = new FileACL(homeDir.toPath());
        fileACL.allowUserRead(username);

        // Commit ACL's
        fileACL.store();

        // Update ENOS user file
        this.writeUserFile();

    }

    public boolean isPrivileged (String username) {
        if (this.passwords.isEmpty()  && Users.ADMIN_USERNAME.equals(username)) {
            // Initial configuration. Add admin user and create configuration file.
            return true;
        }
        Profile userProfile = this.passwords.get(username);
        if (userProfile == null) {
            // Not a user
            return false;
        }
        if (Users.ROOT.equals(userProfile.getPrivilege())) {
            return true;
        } else {
            return false;
        }
    }

    private synchronized void readUserFile() throws IOException {
        File passwordFile = new File(this.passwordFilePath.toString());
        passwordFile.getParentFile().mkdirs();
        if (!passwordFile.exists()) {
            // File does not exist yet, create it.
            if (!passwordFile.createNewFile()) {
                // File could not be created, return a RuntimeError
                throw new RuntimeException("Cannot create " + this.passwordFilePath.toString());
            }
        }
        BufferedReader reader = new BufferedReader(new FileReader(passwordFile));
        String line = null;

        // Reset the cache
        this.passwords.clear();

        while ((line = reader.readLine()) != null) {
            Profile p = new Profile(line);
            if (p.getName() != null) {
                this.passwords.put(p.getName(), p);
            }
            else {
                System.out.print("Malformed user entry:  " + line);
            }
        }
    }


    private synchronized void writeUserFile() throws IOException {
        File passwordFile = new File(this.passwordFilePath.toString());
        BufferedWriter writer = new BufferedWriter(new FileWriter(passwordFile));

        for (Profile p : this.passwords.values() ) {
            writer.write(p.toString());
            writer.newLine();
        }
        writer.flush();
        writer.close();
    }

    public Path getHomePath() {
        return Paths.get(this.enosRootPath.toString(),Users.USERS_DIR);
    }

}
