/*
 * Copyright (c) 2014, Regents of the University of California  All rights reserved.
 * Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
 * 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

package net.es.enos.shell;

import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.Arrays;
import java.util.Set;

import jline.console.ConsoleReader;
import jline.console.ENOSConsoleReader;
import jline.console.completer.StringsCompleter;
import net.es.enos.kernel.exec.KernelThread;


import net.es.enos.python.PythonShell;
import net.es.enos.shell.annotations.ShellCommand;

public class Shell {

    private InputStream in;
    private OutputStream out = null;
    private ConsoleReader consoleReader = null;
    private ENOSConsoleReader ENOSConsoleReader = null;
    private StringsCompleter stringsCompleter = null;
    private KernelThread kernelThread = null;
    private String prompt = "\nenos";

    /**
    public static String banner =
            " _       __     __                             __           _______   ______  _____\n" +
            "| |     / /__  / /________  ____ ___  ___     / /_____     / ____/ | / / __ \\/ ___/\n" +
            "| | /| / / _ \\/ / ___/ __ \\/ __ `__ \\/ _ \\   / __/ __ \\   / __/ /  |/ / / / /\\__ \\ \n" +
            "| |/ |/ /  __/ / /__/ /_/ / / / / / /  __/  / /_/ /_/ /  / /___/ /|  / /_/ /___/ / \n" +
            "|__/|__/\\___/_/\\___/\\____/_/ /_/ /_/\\___/   \\__/\\____/  /_____/_/ |_/\\____//____/  \n" +
            "  ";
     **/

    public static String banner = "Welcome to ENOS\n";

    public OutputStream getOut() {
        return out;
    }

    public void setOut(OutputStream out) {
        this.out = out;
    }

    public void setIn(InputStream in) {
        this.in = in;
    }

    public Shell(InputStream in, OutputStream out) throws IOException {
        this.out = out;
    }

    private void print(String line) {
        try {
            this.out.write(line.getBytes());
            this.out.flush();
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    public String getPrompt() {
        return prompt;
    }

    public void setPrompt(String prompt) {
        this.prompt = "\n" + prompt;
    }

    public void startShell() {
        System.out.println("Shell is starting");
        this.kernelThread = KernelThread.getCurrentKernelThread();

        this.setPrompt(kernelThread.getUser().getName() + "@enos> ");

        this.out = new ShellOutputStream(out);
        try {
            this.out.write(Shell.banner.getBytes());
            this.out.flush();
        } catch (IOException e) {
            e.printStackTrace();
        }

        try {
                this.consoleReader = new ConsoleReader(this.in, this.out, new ENOSTerminal());
                this.ENOSConsoleReader = new ENOSConsoleReader(this.in, this.out, new ENOSTerminal());
        } catch (Exception e) {
            e.printStackTrace();
        }
        this.in = new ShellInputStream(this.in, this.consoleReader,this.ENOSConsoleReader);

        // Initialize command completion with commands from modules.
        Set<String> commandNames = ShellCommandsFactory.getCommandNames();
        this.stringsCompleter = new StringsCompleter(commandNames);

        Method method = null;

        while (true) {
            try {
                /*
                 * Enable command completion while we try to get a line from the user,
                 * turn it off immediately afterward to avoid interference with
                 * possible interactive commands.
                 */
                consoleReader.addCompleter(this.stringsCompleter);
                String line = this.consoleReader.readLine(this.prompt);
                consoleReader.removeCompleter(this.stringsCompleter);

                if (line == null) {
                    continue;
                }

                String[] args = line.trim().split("\\s+");
                if (args.length == 0 || (args.length == 1 && args[0].isEmpty())) {
                    continue;
                }

                // The shell has a few built-in command handlers.  Generally these
                // built-in commands should be so because they require some special
                // handling (i.e. access to the Shell member variables).  Other command
                // handlers should be implemented as ShellCommands.
                if (args[0].equals("exit")) {
                    break;
                } else if (args[0].equals("help")) {

                    // "help" with no arguments gives a sorted list of commands along with
                    // short help.
                    if (args.length == 1) {
                        String[] cmds = commandNames.toArray(new String[commandNames.size()]);

                        Arrays.sort(cmds);

                        for (String n : cmds) {

                            Method m = ShellCommandsFactory.getCommandMethod(n);
                            ShellCommand command = m.getAnnotation(ShellCommand.class);
                            //Make sure user has privilege needed to view help for privileged commands
                            if (command.privNeeded() && KernelThread.getCurrentKernelThread().isPrivileged() ||
                                    ! command.privNeeded()) {
                                this.print(n + "\t" + command.shortHelp() + "\n");
                            }
                        }
                    }
                    // "help" with the name of a top-level command gives a longer help
                    // message for that one command.
                    else {
                        Method m = ShellCommandsFactory.getCommandMethod(args[1]);
                        if (m != null) {
                            ShellCommand command = m.getAnnotation(ShellCommand.class);
	                        // Don't show help for options the user can't access
                            if (command.privNeeded() && KernelThread.getCurrentKernelThread().isPrivileged() ||
                                    ! command.privNeeded()) {
                                this.print(args[1] + "\t" + command.shortHelp() + "\n");
                                // Print longer help if it's available.
                                if (!command.longHelp().isEmpty()) {
                                    this.print("\n" + command.longHelp() + "\n");
                                }
                            } else {
                                this.print("Your user account does not have the privilege needed to view help for this" + "\n" + "command");
                            }
                        }
                        else {
                            this.print(args[1] + " is an invalid command");
                        }
                    }
                    continue;
                }

                method = ShellCommandsFactory.getCommandMethod(args[0]);
                if (method == null) {
                    // Try to see if a python program exist with that name
                    String path = PythonShell.getProgramPath(args[0]);
                    if (path != null) {
                        // There is a python command of that name execute it. A new String[] with the first
                        // element set to "python" must be created in order to simulate the python command line.
                        String[] newArgs = new String[args.length + 1];
                        newArgs[0] = "python";
                        int index = 1;
                        for (String s : args) {
                            newArgs[index] = s;
                        }
                        try {
                            PythonShell.startPython(newArgs, this.in, this.out, this.out);
                        } catch (Exception e) {
                            // This is a catch all. Make sure that the thread recovers in a correct state
                            this.print( e.toString());
                        }
                    }
                    // Non existing command
                    this.print(args[0] + " is an invalid command");
                    continue;
                }
                try {
                    ShellCommand command = method.getAnnotation(ShellCommand.class);

                    if (command.forwardLines()) {
                        method.invoke(null, args, this.in, this.out, this.out);
                    } else {
                        // Assume static method    TODO: lomax@es.net to be revisited
                        method.invoke(null, args, this.in, this.out, this.out);
                    }
                } catch (IllegalAccessException e) {
                    this.print(e.toString());
                    continue;
                } catch (InvocationTargetException e) {
                   this.print( e.toString());
                   continue;
                } catch (Exception e) {
                    // This is a catch all. Make sure that the thread recovers in a correct state
                    this.print( e.toString());
                }
            } catch (IOException e) {
                break;
            }
        }
        this.destroy();
    }

    // Whatever cleanup is needed after the shell is done.  Subclasses should override if needed.
    public void destroy() {
    }
}