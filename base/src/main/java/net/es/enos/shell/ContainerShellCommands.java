/*
 * Copyright (c) 2014, Regents of the University of California  All rights reserved.
 * Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
 * 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

package net.es.enos.shell;

import net.es.enos.kernel.container.Container;
import net.es.enos.kernel.container.ContainerACL;
import net.es.enos.kernel.container.Containers;
import net.es.enos.kernel.exec.KernelThread;
import net.es.enos.shell.annotations.ShellCommand;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.InputStream;
import java.io.OutputStream;
import java.io.PrintStream;
import java.lang.reflect.InvocationTargetException;

/**
 * Created by lomax on 7/28/14.
 */
public class ContainerShellCommands {

    public static void mkContainer (String[] args, InputStream in, OutputStream out, OutputStream err) {
        Logger logger = LoggerFactory.getLogger(ContainerShellCommands.class);
        logger.info("mkcontainer with {} arguments", args.length);

        PrintStream o = new PrintStream(out);

        // Argument checking
        if (args.length < 2) {
            o.println("Usage mkcontainer <name>");
            return;
        }
        String name = args[2];
        try {
            Containers.createContainer(name);
        } catch (SecurityException e) {
            o.println("Not authorized to create " + e.getMessage());
            return;
        } catch (InvocationTargetException e) {
            o.println("failed with " + e.getTargetException().getMessage());
            return;
        } catch (Exception e) {
            o.println("Failed with " + e.toString());
        }
        o.println("container " + name + " is created");
    }

    @ShellCommand(name = "join",
            shortHelp = "Joins a container",
            longHelp = "join <name>")
    public static void mkJoin (String[] args, InputStream in, OutputStream out, OutputStream err) {
        Logger logger = LoggerFactory.getLogger(ContainerShellCommands.class);
        logger.info("join with {} arguments", args.length);

        PrintStream o = new PrintStream(out);

        // Argument checking
        if (args.length < 2) {
            o.println("Usage join <name>");
            return;
        }
        String name = args[1];
        try {
            KernelThread.currentKernelThread().joinContainer(name);
        } catch (SecurityException e) {
            o.println("Failed: " + e.getMessage());
            return;
        }
        o.println("container " + name + " is now the current container");
    }

    @ShellCommand(name = "leave",
            shortHelp = "Leaves the current container and re-join, if any, the previously joined container.",
            longHelp = "leave")
    public static void leave (String[] args, InputStream in, OutputStream out, OutputStream err) {
        Logger logger = LoggerFactory.getLogger(ContainerShellCommands.class);
        logger.info("leave with {} arguments", args.length);

        PrintStream o = new PrintStream(out);
        KernelThread.currentKernelThread().leaveContainer();

    }

    @ShellCommand(name = "container",
            shortHelp = "administrate a container.",
            longHelp = "container create <container name> : creates a container in the current container\n" +
                       "container list : list the sub containers of the current container\n" +
                       "container acl <container name>  : show access control list\n" +
                       "container <allow|deny> <user> <access|exec|admin> <container name> \n")
    public static void container (String[] args, InputStream in, OutputStream out, OutputStream err) {
        Logger logger = LoggerFactory.getLogger(ContainerShellCommands.class);
        logger.info("container with {} arguments", args.length);


        PrintStream o = new PrintStream(out);
        if (args.length == 1) {
            // Needs at list one option
            o.println("needs at least one option. try help container");
            return;
        }

        if (args[1].equals("create")) {
            ContainerShellCommands.mkContainer(args,in,out,err);
            return;
        } else if (args[1].equals("acl")) {
            ContainerShellCommands.showACL(args,in,out,err);
            return;
        } else if (args[1].equals("allow") || (args[1].equals("deny"))) {
            ContainerShellCommands.changeACL(args,in,out,err);
        }

    }

    public static void showACL(String[] args, InputStream in, OutputStream out, OutputStream err) {
        PrintStream o = new PrintStream(out);
        if (args.length != 3) {
            o.println("container name is missing");
            return;
        }
        Container container = new Container(args[2]);
        ContainerACL acl = container.getACL();
        String[] users;
        users = acl.getCanRead();
        o.println("Read Access:");
        if ((users == null) || (users.length == 0)) {
            o.println("    None");
        } else {
            o.print("    ");
            for (String user : users) {
                o.print(user + ",");
            }
            o.println("\n");
        }
        users = acl.getCanWrite();
        o.println("Write Access:");
        if ((users == null) || (users.length == 0)) {
            o.println("    None");
        } else {
            o.print("    ");
            for (String user : users) {
                o.print(user + ",");
            }
            o.println("\n");

        }
        users = acl.getCanAdmin();
        o.println("Administrative Access:");
        if ((users == null) || (users.length == 0)) {
            o.println("    None");
        } else {
            o.print("    ");
            for (String user : users) {
                o.print(user + ",");
            }
            o.println("\n");
        }
        users = acl.getCanExecute();
        o.println("Execution Access:");
        if ((users == null) || (users.length == 0)) {
            o.println("    None");
        } else {
            o.print("    ");
            for (String user : users) {
                o.print(user + ",");
            }
            o.println("\n");
        }


    }

    public static void changeACL(String[] args, InputStream in, OutputStream out, OutputStream err) {
        PrintStream o = new PrintStream(out);
        if (args.length != 5) {
            o.println("syntax help, please try help container");
            return;
        }
        String cmd = args[1];
        String user = args[2];
        String aclType = args[3];
        String containerName = args[4];

        try {
            Container container = new Container(containerName);
            ContainerACL acl = container.getACL();
            acl.changeACL(user,cmd,aclType);
        } catch (Exception e) {
            o.print("failed: can not change ACL: " + e.getMessage());
            return;
        }
        String[] newArgs  = {"container","acl",containerName};
        showACL(newArgs,in,out,err);
    }

}
