/*
 * Copyright (c) 2014, Regents of the University of California.
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 * 1. Redistributions of source code must retain the above copyright notice,
 * this list of conditions and the following disclaimer.
 *
 * 2. Redistributions in binary form must reproduce the above copyright notice,
 * this list of conditions and the following disclaimer in the documentation
 * and/or other materials provided with the distribution.
 *
 * 3. Neither the name of the copyright holder nor the names of its contributors
 * may be used to endorse or promote products derived from this software without
 * specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 * DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
 * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
 * CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
 * OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

package net.es.enos.kernel.users;

import net.es.enos.api.DefaultValues;
import net.es.enos.api.NonExistantUserException;
import net.es.enos.api.UserAlreadyExistException;
import net.es.enos.api.UserException;
import net.es.enos.boot.BootStrap;
import net.es.enos.kernel.exec.KernelThread;
import net.es.enos.kernel.exec.annotations.SysCall;
import net.es.enos.kernel.security.FileACL;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.*;
import java.lang.reflect.Method;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.HashMap;
import java.util.Arrays;
import java.util.List;


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

    private final static String ADMIN_USERNAME = "admin";
    private final static String ADMIN_PASSWORD = "enos";

    private final static String ROOT = "root";
    private final static String USER = "user";
    List<String> privArray = Arrays.asList(ROOT, USER); //List of privs to check when creating user

    private Path passwordFilePath;
    private Path enosRootPath;
    private HashMap<String,UserProfile> passwords = new HashMap<String, UserProfile>();
    private final Logger logger = LoggerFactory.getLogger(Users.class);

    public Users() {
        // Figure out the ENOS root directory.
        String enosRootDir = BootStrap.getMasterConfiguration().getGlobal().getRootDirectory();
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

    /**
     * Return true if a user exists, false otherwise
     * @param user user to check
     * @return true if user exists
     */
    public boolean userExists(String user) {
        return Users.getUsers().passwords.containsKey(user);
    }

    public boolean authUser (String userName, String password) {
        Method method = null;
        try {
            method = KernelThread.getSysCallMethod(this.getClass(), "do_authUser");

            KernelThread.doSysCall(this,
                    method,
                    userName,
                    password);
        } catch (NonExistantUserException e) {
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
            name="do_authUser"
    )
    public void  do_authUser (String user, String password) throws NonExistantUserException, UserException {
        logger.info("do_authUser entry");

        // Read file.
        try {
            this.readUserFile();
        } catch (IOException e) {
            logger.error("Cannot read password file");
        }

        if (this.passwords.isEmpty()) {
            // No user has been created. Will accept "admin","enos".
            // TODO: default admin user should be configured in a safer way.
            if (Users.ADMIN_USERNAME.equals(user) && Users.ADMIN_PASSWORD.equals(password)) {
                // Create the initial configuration file
                try {
                    UserProfile adminProfile = new UserProfile(Users.ADMIN_USERNAME, Users.ADMIN_PASSWORD, Users.ROOT, "Admin", "ESNet", "admin@es.net");
                    this.do_createUser(adminProfile);
                } catch (UserAlreadyExistException e) {
                    // Since this code is executed only when the configuration file is empty, this should never happen.
                    logger.error("User {} already exists in empty configuration file", Users.ADMIN_USERNAME);
                } catch (IOException e) {
                    // This shouldn't happen either...it means we couldn't create the initial password file.
                    logger.error("Cannot create initial password file");
                }
            }
        }

        logger.warn("looking for key for {}", user);
        if (!Users.getUsers().passwords.containsKey(user)) {
            logger.warn("{} is unknown", user);
        }
        UserProfile userProfile = Users.getUsers().passwords.get(user);

        // Local password verification here.  Check an encrypted version of the user's password
        // against what was stored in password file, a la UNIX password authentication.
        if (userProfile.getPassword().equals(crypt(password, userProfile.getPassword()))) {
            logger.warn("{} has entered correct password", user);

        } else {
            logger.warn("{} has entered incorrect password", user);
            throw new UserException (user);
        }
    }


    public boolean setPassword (String userName, String newPassword) {
        Method method = null;
        try {
            method = KernelThread.getSysCallMethod(this.getClass(), "do_setPassword");

            KernelThread kt = KernelThread.getCurrentKernelThread();
            String currentUserName = kt.getUser().getName();

            logger.info("current user {}", currentUserName);

            if ((currentUserName.equals(userName)) ||
                    isPrivileged(currentUserName)) {
                logger.info("OK to change");

                KernelThread.doSysCall(this,
                        method,
                        userName,
                        newPassword);
            }
        } catch (NonExistantUserException e) {
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
    public void do_setPassword(String userName, String newPassword) throws NonExistantUserException, IOException {
        logger.info("do_setPassword entry");

	    try {
		    this.readUserFile();
	    } catch (IOException e) {
		    logger.error("Cannot read password file");
	    }

	    // Make sure the user exists.
        if (!this.passwords.containsKey(userName)) {
            throw new NonExistantUserException(userName);
        }

        UserProfile userProfile = Users.getUsers().passwords.get(userName);

//      Encrypt new password and write out the users file
        userProfile.setPassword(crypt(newPassword));
        this.writeUserFile();
    }


    public boolean createUser (UserProfile newUser) {
        Method method = null;
        try {
            method = KernelThread.getSysCallMethod(this.getClass(), "do_createUser");

            // Check if user is authorized to change password
            if (KernelThread.getCurrentKernelThread().isPrivileged()) {
                KernelThread.doSysCall(this,
                        method,
                        newUser);
            } else {
                return false;
            }

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
    public void do_createUser (UserProfile newUser) throws UserAlreadyExistException, UserException, IOException {
        logger.info("do_createUser entry");

        String username = newUser.getName();
        String password = newUser.getPassword();
        String privilege = newUser.getPrivilege();
        String name = newUser.getRealName();
        String organization = newUser.getorganization();
        String email = newUser.getemail();

        // Check if fields entered contain valid characters (and don't contain colons)
        if (! username.matches("[a-zA-Z0-9_]+") || name.contains(":")
                || organization.contains(":") || email.contains(":")
                || ! email.contains("@") || ! email.contains(".")) {
            throw new UserException(username);
        }

        // Make sure privilege value entered is valid
        if (!privArray.contains(privilege)) {
            throw new UserException(username);
        }

        // Checks if the user already exists
	    try {
		    this.readUserFile();
	    } catch (IOException e) {
		    logger.error("Cannot read password file");
	    }
        if (this.passwords.containsKey(username)) {
            throw new UserAlreadyExistException(username);
        }

        // Construct the new Profile.
        UserProfile userProfile = new UserProfile(username,
                crypt(password), // Let the Crypt library pick a suitable algorithm and a random salt
                privilege,
                name,
                organization,
                email);
        this.passwords.put(username,userProfile);

        // Create home directory
        File homeDir = new File (Paths.get(this.getHomePath().toString(), username).toString());

        homeDir.mkdirs();
        // Create proper access right
        FileACL fileACL = new FileACL(homeDir.toPath());
        fileACL.allowUserRead(username);
        fileACL.allowUserWrite(username);

        // Commit ACL's
        fileACL.store();

        // Update ENOS user file
        this.writeUserFile();

    }

    public boolean removeuser (String userName) {
        Method method = null;
        KernelThread kt = KernelThread.getCurrentKernelThread();
        String currentUserName = kt.getUser().getName();

        try {
            method = KernelThread.getSysCallMethod(this.getClass(), "do_removeUser");

            if ((currentUserName.equals(userName)) ||
                    isPrivileged(currentUserName)) {
                logger.info("OK to remove");
                KernelThread.doSysCall(this,
                        method,
                        userName);
            }
        } catch (NonExistantUserException e) {
            return false;
        } catch (NoSuchMethodException e) {
            e.printStackTrace();
            return false;
        } catch (Exception e) {
            e.printStackTrace();
            return false;
        }

        if (! isPrivileged(currentUserName) || currentUserName.equals(userName)) {
            // End user session if not privileged account (unless root removed own account)
            kt.getThread().interrupt();
        }
        return true;
    }


    @SysCall(
            name="do_removeUser"
    )
    public void do_removeUser(String userName) throws NonExistantUserException, IOException {
        logger.info("do_removeUser entry");

        // Make sure the user exists.
	    try {
		    this.readUserFile();
	    } catch (IOException e) {
		    logger.error("Cannot read password file");
	    }

        if (!this.passwords.containsKey(userName)) {
            throw new NonExistantUserException(userName);
        }

        UserProfile userProfile = Users.getUsers().passwords.get(userName);
        // Set name to null so writeUserFile will skip this UserProfile
        userProfile.setName(null);

        File userDir = new File (Paths.get(this.getHomePath().toString(), userName).toString());

        //Delete user directory
        this.deleteUserDir(userDir);

	    // Delete .acl file associated with this user account
	    File aclDelete = new File (Paths.get(Users.getUsers().getHomePath().toString(), ".acl", userName).toString());
	    aclDelete.delete();

        // Save User File with removed user
        this.writeUserFile();
    }


	public boolean mkdir (File homeDir) {
		try {
			KernelThread kt = KernelThread.getCurrentKernelThread();
			String username = kt.getUser().getName();

			// Check if directory entered contain valid characters only
			if (! homeDir.getName().matches("[a-zA-Z0-9_]+")) {
				throw new UserException(username);
			}

			// Make sure directory doesn't already exist.
			if (! homeDir.exists()) {
				// Will throw exception if user does not have proper permissions to write in directory.
				homeDir.mkdir();
			} else {
				throw new IOException();
			}

			// Create proper access rights in new directory
			FileACL fileACL = new FileACL(homeDir.toPath());
			fileACL.allowUserRead(username);
			fileACL.allowUserWrite(username);

			// Commit ACL's
			fileACL.store();

		} catch (Exception e) {
			e.printStackTrace();
			return false;
		}
		return true;
	}


    public boolean isPrivileged (String username) {

        if (this.passwords.isEmpty()  && Users.ADMIN_USERNAME.equals(username)) {
            // Initial configuration. Add admin user and create configuration file.
            return true;
        }
        UserProfile userProfile = this.passwords.get(username);

        if (userProfile == null) {
            // Not a user
            return false;
        }
        logger.debug(userProfile.getPrivilege());

        return Users.ROOT.equals(userProfile.getPrivilege());

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
            UserProfile p = new UserProfile(line);
            if (p.getName() != null) {
                this.passwords.put(p.getName(), p);
            }
            else {
                logger.error("Malformed user entry:  {}", line);
            }
        }
    }


    private synchronized void writeUserFile() throws IOException {
        File passwordFile = new File(this.passwordFilePath.toString());
        BufferedWriter writer = new BufferedWriter(new FileWriter(passwordFile));
        for (UserProfile p : this.passwords.values() ) {
            if (p.getName() != null) {
                writer.write(p.toString());
                writer.newLine();
            }
        }
        writer.flush();
        writer.close();
    }


    private synchronized void deleteUserDir(File userDir) throws IOException {

        // Remove all files from directory before deleting directory.
        if (userDir.list().length == 0) {
            userDir.delete();
	        logger.debug("Directory deleted");
        } else {
            for (File userFile : userDir.listFiles()) {
                userFile.delete();
            }
	        // Make sure all files have been deleted from the directory.
            if (userDir.list().length == 0) {
                userDir.delete();
	            logger.debug("Directory deleted");
            }
        }
    }


    public Path getHomePath() {
        return enosRootPath.resolve(USERS_DIR);
    }

    public Path getHomePath(String username) {
        return getHomePath().resolve(username);
    }

}