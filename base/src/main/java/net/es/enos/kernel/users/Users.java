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
import net.es.enos.common.PropertyKeys;
import net.es.enos.common.UserAlreadyExistException;
import net.es.enos.kernel.exec.KernelThread;
import net.es.enos.kernel.exec.annotations.SysCall;

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

    class Profile {

        private String username;
        private String password;
        private String privilege;
        private String fullname;
        private String email;

        public String getUsername() {
            return username;
        }

        public void setUsername(String username) {
            this.username = username;
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

        public String getFullname() {
            return fullname;
        }

        public void setFullname(String fullname) {
            this.fullname = fullname;
        }

        public String getEmail() {
            return email;
        }

        public void setEmail(String email) {
            this.email = email;
        }

        private final static int PROFILE_SIZE = 5;
        private final static int USER_NAME = 0;
        private final static int PASSWORD = 1;
        private final static int PRIVILEGE = 2;
        private final static int FULLNAME = 3;
        private final static int EMAIL = 4;

        /**
         * Default constructor
         */
        Profile() {
        }

        /**
         * Construct a new Profile object from a textual representation
         * @param line line from password file
         * @return Profile object, empty if an error occurred.
         */
        Profile (String line) {
            String [] elements = line.split(":", -1); // allow trailing empty strings
            if (elements.length < PROFILE_SIZE) {
                // Incorrect format.
                System.out.println("Ignoring malformed password line.");
                return;
            }
            username = elements[USER_NAME];
            password = elements[PASSWORD];
            privilege = elements[PRIVILEGE];
            fullname = elements[FULLNAME];
            email = elements[EMAIL];
        }

        String toLine() {
            String line = "";
            line += username + ":";
            line += password + ":";
            line += privilege + ":";
            line += fullname + ":";
            line += email + ":";
            return line;
        }

    }

    // Default admin username and password
    private final static String ADMIN_USERNAME = "admin";
    private final static String ADMIN_PASSWORD = "enos";

    // Privilege types
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
        // Create user home directory if necessary.

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
                    System.out.println("Creating default admin user");
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


    /**
     * Userland part of password changing
     * @param username the name of the user whose password will be changed
     * @param oldPassword the old password, used for verification
     * @param newPassword the new password
     * @return true if successful
     */
    public boolean setPassword (String username, String oldPassword, String newPassword) {
        System.out.println("setPassword " + username);
        Method method = null;
        try {
            method = KernelThread.getSysCallMethod(this.getClass(), "do_setPassword");
            KernelThread.doSysCall(this, method, username, oldPassword, newPassword);
        } catch (UserAlreadyExistException e) {
            return false;
        }
        catch (NoSuchMethodException e) {
            e.printStackTrace();
            return false;
        }
        catch (Exception e) {
            e.printStackTrace();
            return false;
        }
        return true;
    }

    /**
     * Kernel part of password changing.
     * Any user is allowed to change her own password, but needs to specify their old
     * password.  Privileged ("root") users can change any user's password without
     * specifying an old password.
     * @param username the name of the user whose password will be changed
     * @param oldPassword the old password, used for verification
     * @param newPassword the new password
     * @throws UserAlreadyExistException
     * @throws IOException
     */
    @SysCall(
            name="do_setPassword"
    )
    public void do_setPassword(String username, String oldPassword, String newPassword) throws
    UserAlreadyExistException, IOException {
        System.out.println("doSetPassword");

        // Get the profile for the user in question
        Profile userProfile = this.passwords.get(username);
        if (userProfile == null) {
            throw new UserAlreadyExistException(username); // XXX user not found
        }

        // Users can always change their own passwords.  root-privileged users can change
        // anyone's passwords.  Other combinations fail.
        if (!KernelThread.getCurrentKernelThread().getUser().getName().equals(username) &&
                !KernelThread.getCurrentKernelThread().getUser().isPrivileged()) {
            throw new UserAlreadyExistException(username); // XXX permission fail
        }

        // Local password verification.  If the user has root privileges we can skip this.
        if (! userProfile.getPassword().equals(crypt(oldPassword, userProfile.getPassword())) &&
                !KernelThread.getCurrentKernelThread().getUser().isPrivileged()) {
            throw new UserAlreadyExistException(username); // XXX password mismatch
        }

        // XXX password policy hook here?

        // Write new hashed password
        userProfile.setPassword(crypt(newPassword));
        this.passwords.put(username, userProfile);
        this.writeUserFile();
    }

    public boolean createUser  (String username, String password, String privilege) {
        System.out.println("createUser " + username);
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
        System.out.println("createUser returns true");
        return true;
    }

    @SysCall(
            name="do_createUser"
    )
    public void do_createUser (String username, String password, String privilege) throws UserAlreadyExistException, IOException {
        System.out.println("do_createUser");

        // TODO:  Syntax checks on username

        // Checks if the user already exists
        if (this.passwords.containsKey(username)) {
            throw new UserAlreadyExistException(username);
        }
        // Construct the userProfile.
        Profile userProfile;
        userProfile = new Profile();
        userProfile.setUsername(username);
        userProfile.setPassword(crypt(password)); // Let the Crypt library pick a suitable algorithm and a random salt
        userProfile.setPrivilege(privilege);
        userProfile.setFullname(""); // TODO:  Figure out a good way to populate these non-essential fields
        userProfile.setEmail("");
        this.passwords.put(username,userProfile);
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
        BufferedReader reader = reader = new BufferedReader(new FileReader(passwordFile));
        String line = null;

        // Reset the cache
        this.passwords.clear();

        while ((line = reader.readLine()) != null) {
            Profile p;
            p = new Profile(line);
            if (p.getUsername() == null) {
                // Incorrect format. Ignore
                continue;
            }
            this.passwords.put(p.getUsername(), p);
        }
    }


    private synchronized void writeUserFile() throws IOException {
        File passwordFile = new File(this.passwordFilePath.toString());
        BufferedWriter writer = new BufferedWriter(new FileWriter(passwordFile));

        // Format the line

        for (Profile p : this.passwords.values() ) {
            String line = p.toLine();
            writer.write(line);
            writer.newLine();
        }
        writer.flush();
        writer.close();
    }

}
