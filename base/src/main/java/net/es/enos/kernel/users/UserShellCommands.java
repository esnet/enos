/*
 * Copyright (c) 2014, Regents of the University of California  All rights reserved.
 * Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
 * 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

package net.es.enos.kernel.users;

import jline.console.ENOSConsoleReader;
import net.es.enos.kernel.exec.KernelThread;
import net.es.enos.shell.annotations.ShellCommand;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.io.PrintStream;


import jline.UnixTerminal;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class UserShellCommands {
    @ShellCommand(name = "adduser",
    shortHelp = "Add a user to the system",
    longHelp = "Required arguments are a username, an initial password, a user class, a name, an organization name, and an email.\n" +
            "The user class should be either \"root\" or \"user\".",
    privNeeded = true)
    public static void addUser(String[] args, InputStream in, OutputStream out, OutputStream err) {
        Logger logger = LoggerFactory.getLogger(UserShellCommands.class);
        logger.info("adduser with {} arguments", args.length);

        boolean newUser = false;
        PrintStream o = new PrintStream(out);

        // Argument checking
        if (args.length != 7) {
            o.println("Usage:  adduser <username> <password> <userclass> <name> <organization> <email>");
            return;
        }

        UserProfile newProfile = new UserProfile(args[1], args[2], args[3], args[4], args[5], args[6]);

        newUser = Users.getUsers().createUser(newProfile);

        if (newUser) {
            o.print("New User created!");
        } else {
            o.print("Unable to create new user");
        }

    }

    @ShellCommand(name = "passwd",
            shortHelp = "Change user password",
            longHelp = "No arguments are required; this command will prompt for them interactively.\n")
    public static void passwd(String[] args, InputStream in, OutputStream out, OutputStream err) {
        Logger logger = LoggerFactory.getLogger(UserShellCommands.class);
        logger.info("passwd with {} arguments", args.length);

        PrintStream o = new PrintStream(out);

        ENOSConsoleReader consoleReader = null;
        try {
            consoleReader = new ENOSConsoleReader(in, out, new UnixTerminal());
        } catch (Exception e) {
            e.printStackTrace();
            return;
        }
        // in = new ShellInputStream(in, consoleReader);

        try {
            // Get our current username.
            String thisUserName = KernelThread.getCurrentKernelThread().getUser().getName();

            // If this thread is privileged, then ask for a username (because we can set anybody's passwd).
            // If not privileged, require password verification to change our own passwd.
            String userName, oldPassword;
            if (KernelThread.getCurrentKernelThread().isPrivileged()) {
                userName = consoleReader.readLine("Username (default = " + thisUserName + "): ");
                if (userName.isEmpty()) {
                    userName = thisUserName;
                }
            }
            else {
                userName = KernelThread.getCurrentKernelThread().getUser().getName();
                oldPassword = consoleReader.readLine("Old password: ", '*');

                // Password check to fail early here
                // TODO:  Figure out why this fails.
                // ^User is not privileged, authUser requires access to passwd file.
                if (! Users.getUsers().authUser(thisUserName, oldPassword)) {
                    o.println("Old password is incorrect");
                    return;
                }
            }

            o.println("Changing password for " + userName);
            String newPassword = consoleReader.readLine("New password: ", '*');
            String new2Password = consoleReader.readLine("New password (confirm): ", '*');
            if (! newPassword.equals(new2Password)) {
                o.println("Error: Passwords do not match");
                return;
            }

            boolean p = Users.getUsers().setPassword(userName, newPassword);
            if (p) {
                o.println("Password change successful!");
            }
            else {
                o.println("Password change failed...");
            }

        } catch (IOException e) {
            return;
        }
    }


    @ShellCommand(name = "removeuser",
            shortHelp = "Remove a user from the system",
            longHelp = "No arguments are required. \n")
    public static void removeUser(String[] args, InputStream in, OutputStream out, OutputStream err) {
        Logger logger = LoggerFactory.getLogger(UserShellCommands.class);
        logger.info("removeuser with {} arguments", args.length);

        PrintStream o = new PrintStream(out);

        if (args.length != 1) {
            o.print("removeuser does not take any parameters");
	        return;
        }

        ENOSConsoleReader consoleReader = null;
        try {
            consoleReader = new ENOSConsoleReader(in, out, new UnixTerminal());
        } catch (Exception e) {
            e.printStackTrace();
            return;
        }

        try {
            // Get current username.
            String thisUserName = KernelThread.getCurrentKernelThread().getUser().getName();

            // If this thread is privileged, then ask for a username (because we can remove any user).
            // If not privileged, require password verification to remove user.
            String userName, password;
            if (KernelThread.getCurrentKernelThread().isPrivileged()) {
                userName = consoleReader.readLine("Username (default = " + thisUserName + "): ");
                if (userName.isEmpty()) {
                    userName = thisUserName;
                }
            }
            else {
                userName = KernelThread.getCurrentKernelThread().getUser().getName();
                password = consoleReader.readLine("Password: ", '*');

                if (! Users.getUsers().authUser(thisUserName, password)) {
                    o.println("Password is incorrect");
                    return;
                }
            }

            o.println("Are you sure you wish to remove this user account?");
            String confirmRemove = consoleReader.readLine("Y/N: ");
            if (confirmRemove.equals("Y")) {
                boolean r = Users.getUsers().removeuser(userName);
                if (r) {
                    o.print("Removed User!");
                } else {
                    o.print("Unable to remove user...");
                }
            } else {
	            o.print("Not removing user.");
            }

        } catch (IOException e) {
            return;
        }
    }
}