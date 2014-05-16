/*
 * Copyright (c) 2014, Regents of the University of California  All rights reserved.
 * Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
 * 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

package net.es.enos.python;

import net.es.enos.kernel.exec.KernelThread;
import net.es.enos.shell.ShellInputStream;
import net.es.enos.shell.annotations.ShellCommand;


import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.ByteBuffer;
import java.util.Arrays;

import org.python.util.PythonInterpreter;
import org.python.util.InteractiveConsole;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
// import org.python.util.JLineConsole;

import javax.print.DocFlavor;

/**
 * Created by lomax on 2/20/14.
 */
public class PythonShell {

    @ShellCommand(
            name="python",
            forwardLines=false,
            shortHelp="Invoke interactive Python shell",
            longHelp="EOF in the shell exits the shell and returns control to the top-level\n" +
                    "ENOS shell."
    )
    public static void startPython (String[] args, InputStream in, OutputStream out, OutputStream err) {

        final Logger logger = LoggerFactory.getLogger(PythonShell.class);
        logger.debug("Starting Python");

        if ((args != null) && (args.length > 1)) {
            // A program is provided.
            PythonInterpreter python = new PythonInterpreter();
            python.setIn(in);
            python.setOut(out);
            python.setErr(err);
            logger.info("Executes file " + args[1] + " for user " + KernelThread.getCurrentKernelThread().getUser().getName());
            python.execfile(args[1]);

        } else {
            // This is an interactive session
            try {
                InteractiveConsole console = new InteractiveConsole();

                console.setOut(out);
                console.setErr(err);
                console.setIn(in);
                // Start the interactive session
                console.interact();
            } catch (Exception e) {
                // Nothing has to be done. This happens when the jython shell exits, obviously not too gracefully.
                // e.printStackTrace();
            }
        }

        logger.debug("Exiting Python");
    }

}
