/*
 * Copyright (c) 2014, Regents of the University of California  All rights reserved.
 * Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
 * 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

package net.es.enos.kernel.users;

import net.es.enos.shell.annotations.ShellCommand;
import net.es.enos.kernel.users.Users;

import java.io.InputStream;
import java.io.OutputStream;
import java.io.PrintStream;

public class UserShellCommands {
    @ShellCommand(name = "adduser",
    shortHelp = "Add a user to the system",
    longHelp = "Required arguments are a username, an initial password, and a user class.\n" +
            "The user class should be either \"root\" or \"user\".")
    public static void addUser(String[] args, InputStream in, OutputStream out, OutputStream err) {
        System.out.println("adduser with " + args.length + " arguments");

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
            longHelp = "Required arguments are a username, an initial password, and a new password.\n")
    public static void passwd(String[] args, InputStream in, OutputStream out, OutputStream err) {
        System.out.println("passwd with " + args.length + " arguments");

        PrintStream o = new PrintStream(out);

        // TODO:  Make this command interactive.
        // It should take an optional username as an argument
        // Password prompts for old and new passwords should be interactive and not echo
        // keystrokes; new password should require confirmation.
        // Basically want this to emulate UNIX passwd(1).

        // Argument checking
        if (args.length != 4) {
            o.println("Usage:  passwd <username> <old password> <new password>");
            return;
        }

        Users.getUsers().setPassword(args[1], args[2], args[3]);

    }

}
