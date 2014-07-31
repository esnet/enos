/*
 * Copyright (c) 2014, Regents of the University of California  All rights reserved.
 * Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
 * 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

package net.es.enos.python;

import net.es.enos.boot.BootStrap;
import net.es.enos.kernel.exec.KernelThread;
import net.es.enos.kernel.security.ExitSecurityException;
import net.es.enos.kernel.users.User;
import net.es.enos.shell.ShellInputStream;;
import net.es.enos.shell.annotations.ShellCommand;


import java.io.*;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.HashMap;

import org.python.core.PyDictionary;
import org.python.util.PythonInterpreter;
import org.python.util.InteractiveConsole;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
// import org.python.util.JLineConsole;


/**
 * Created by lomax on 2/20/14.
 */
public class PythonShell {
    private static final Logger logger = LoggerFactory.getLogger(PythonShell.class);
    private static HashMap<InputStream,PyDictionary> locals = new HashMap<InputStream, PyDictionary>();

    @ShellCommand(
            name="python",
            forwardLines=false,
            shortHelp="Invoke interactive Python shell",
            longHelp="EOF in the shell exits the shell and returns control to the top-level\n" +
                    "ENOS shell."
    )
    public static void startPython (String[] args, InputStream in, OutputStream out, OutputStream err) {

        final Logger logger = LoggerFactory.getLogger(PythonShell.class);
        if (in instanceof ShellInputStream) {
            ((ShellInputStream) in).setDoCompletion(false);
        }
        PyDictionary sessionLocals;
        boolean isFirstSession = true;
        // Find or create locals
        synchronized (PythonShell.locals) {
            if (PythonShell.locals.containsKey(in)) {
                // Already has a locals created for this session, re-use
                sessionLocals = PythonShell.locals.get(in);
                isFirstSession = false;
            } else {
                // First python for this session. Create locals
                sessionLocals = new PyDictionary();
                PythonShell.locals.put(in,sessionLocals);
                // Sets the default search path
                PythonInterpreter python = new PythonInterpreter(sessionLocals);
                python.setIn(in);
                python.setOut(out);
                python.setErr(err);
                python.exec("import sys");
                python.exec("sys.path = sys.path + ['" + BootStrap.rootPath.resolve("bin/") + "']");
                python.exec("sys.path = sys.path + ['" + KernelThread.currentKernelThread().getUser().getHomePath()
                            + "']");
                try {
                    err.flush();
                } catch (IOException e) {
                    e.printStackTrace();
                }
            }
        }
        logger.debug("Starting Python");
        if (isFirstSession) {
            // Run profile
            PythonShell.execProfile(sessionLocals,in,out,err);
        }
        try {
            if ((args != null) && (args.length > 1)) {
                // A program is provided. Add the arguments into the python environment as command_args variable
                sessionLocals.put("command_args", args);
                PythonInterpreter python = new PythonInterpreter(sessionLocals);
                python.setIn(in);
                python.setOut(out);
                python.setErr(err);
                logger.info("Executes file " + args[1] + " for user " + KernelThread.currentKernelThread().getUser().getName());
                String filePath;
                if (args[1].startsWith(BootStrap.rootPath.toString())) {
                    // The file path already contains the ENOS Root.
                    filePath = args[1];
                } else {
                    // Need to prefix the file path with ENOS Root.
                    filePath = BootStrap.rootPath.toString() + args[1];
                }
                python.execfile(filePath);

            } else {
                // This is an interactive session
                if (!sessionLocals.containsKey("command_args"))  {
                    // Make sure that the variable exists
                    sessionLocals.put("command_args", new String[] {"python"});
                }
                InteractiveConsole console = new InteractiveConsole(sessionLocals);
                if (System.getProperty("python.home") == null) {
                    System.setProperty("python.home", "");
                }
                InteractiveConsole.initialize(System.getProperties(),
                        null, new String[0]);

                console.setOut(out);
                console.setErr(err);
                console.setIn(in);
                // Start the interactive session
                console.interact();
            }
        } catch (Exception e) {
            if ((e instanceof ExitSecurityException) || (e.toString().contains("SystemExit"))) {
                // This is simply due to sys.exit(). Ignore.
            } else {
                try {
                    err.write(e.toString().getBytes());
                } catch (IOException e1) {
                    e1.printStackTrace();
                }
                e.printStackTrace();
            }
        }
        try {
            err.flush();
            out.flush();
        } catch (IOException e) {
            e.printStackTrace();
        }
        if (in instanceof ShellInputStream) {
            ((ShellInputStream) in).setDoCompletion(true);
        }

        logger.debug("Exiting Python");
    }

    private static void execProfile(PyDictionary locals, InputStream in, OutputStream out, OutputStream err) {
        User user = KernelThread.currentKernelThread().getUser();
        Path homeDir = user.getHomePath();
        File profile = Paths.get(homeDir.toString(),"profile.py").toFile();
        if (!profile.exists()) {
            // No profile, nothing to do
            return;
        }
        // Execute the profile
        PythonInterpreter python = new PythonInterpreter(locals);
        python.setIn(in);
        python.setOut(out);
        python.setErr(err);
        logger.info("Executes file " + profile.toString() + " for user " + KernelThread.currentKernelThread().getUser().getName());
        python.execfile(profile.toString());
    }

    public static String getProgramPath(String cmd) {
        File path = null;
        // Make sure that the extension .py is in the name of the command.
        String command;
        if (cmd.endsWith(".py")) {
            command = cmd;
        } else {
            command = cmd + ".py";
        }
        // Retrieve the python search path
	    try {
		    path = new File(BootStrap.rootPath.resolve("bin").resolve(command).toString());
		    if (path.exists()) {
			    return path.toString();
		    }
	    } catch (SecurityException e) {
	    }
	    try {
		    path = new File(KernelThread.currentKernelThread().getUser().getHomePath().normalize().resolve(command).toString());
		    if (path.exists()) {
			    return path.toString();
		    }
		    return null;
	    } catch (SecurityException e) {
		    return null;
	    }
    }
}
