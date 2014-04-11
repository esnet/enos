/*
 * Copyright (c) 2014, Regents of the University of California  All rights reserved.
 * Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
 * 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

package net.es.enos.kernel.users;

import net.es.enos.kernel.exec.KernelThread;
import net.es.enos.shell.ShellInputStream;
import net.es.enos.shell.annotations.ShellCommand;
import net.es.enos.kernel.users.Users;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.io.PrintStream;

import jline.UnixTerminal;
import jline.console.ConsoleReader;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class UserShellCommands {
    @ShellCommand(name = "adduser",
    shortHelp = "Add a user to the system",
    longHelp = "Required arguments are a username, an initial password, and a user class.\n" +
            "The user class should be either \"root\" or \"user\".")
    public static void addUser(String[] args, InputStream in, OutputStream out, OutputStream err) {
        Logger logger = LoggerFactory.getLogger(UserShellCommands.class);
        logger.info("adduser with {} arguments", args.length);

        PrintStream o = new PrintStream(out);

        // Argument checking
        if (args.length != 4) {
            o.println("Usage:  adduser <username> <password> <userclass>");
            return;
        }

        Users.getUsers().createUser(args[1], args[2], args[3]);

    }

    @ShellCommand(name = "passwd",
            shortHelp = "Change user password",
            longHelp = "No arguments are required; this command will prompt for them interactively.\n")
    public static void passwd(String[] args, InputStream in, OutputStream out, OutputStream err) {
        Logger logger = LoggerFactory.getLogger(UserShellCommands.class);
        logger.info("passwd with {} arguments", args.length);

        PrintStream o = new PrintStream(out);

        ConsoleReader consoleReader = null;
        try {
            consoleReader = new ConsoleReader(in, out, new UnixTerminal());
        } catch (Exception e) {
            e.printStackTrace();
            return;
        }
        // in = new ShellInputStream(in, consoleReader);

        try {
            // If this thread is privileged, then ask for a username (because we can set anybody's passwd).
            // If not privileged, require password verification to change our own passwd.
            String userName, oldPassword;
            if (KernelThread.getCurrentKernelThread().isPrivileged()) {
                userName = consoleReader.readLine("Username: ");
                oldPassword = "";
            }
            else {
                userName = KernelThread.getCurrentKernelThread().getUser().getName();
                oldPassword = consoleReader.readLine("Old password: ", '*');

                // Password check to fail early here
                /* XXX something is broken here, but what?
                if (Users.getUsers().authUser(userName, oldPassword) == false) {
                    o.println("Old password is incorrect");
                    return;
                }
                */
            }

            String newPassword = consoleReader.readLine("New password (initial): ", '*');
            String new2Password = consoleReader.readLine("New password (confirm): ", '*');
            if (! newPassword.equals(new2Password)) {
                o.println("New and old passwords do not match");
                return;
            }

            boolean p = Users.getUsers().setPassword(userName, oldPassword, newPassword);
            if (p) {
                o.println("Password change successful");
            }
            else {
                o.println("Password change failed");
            }

        } catch (IOException e) {
            return;
        }


    }

}
