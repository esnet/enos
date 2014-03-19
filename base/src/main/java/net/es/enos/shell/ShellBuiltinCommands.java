/*
 * Copyright (c) 2014, Regents of the University of California  All rights reserved.
 * Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
 * 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

package net.es.enos.shell;

import net.es.enos.common.ENOSException;
import net.es.enos.shell.annotations.ShellCommand;

import java.io.InputStream;
import java.io.OutputStream;

public class ShellBuiltinCommands {
    /**
     * Dummy command method for shell exit command.
     *
     * This functionality is really handled internally within the shell itself, but
     * we make a command object for it here to allow internal commands to get
     * command completion and help in a consistent way.  This method should never
     * get called.
     *
     * @param args unused
     * @param in unused
     * @param out unused
     * @param err unused
     * @throws ENOSException
     */
    @ShellCommand(name = "exit",
    shortHelp = "Exit login shell")
    public static void exitCommand(String[] args, InputStream in, OutputStream out, OutputStream err) throws ENOSException {
        throw new ENOSException("Built-in command not handled by shell");
    }

    @ShellCommand(name = "help",
    shortHelp = "Print command information and help",
    longHelp = "With no arguments, print the complete list of commands and abbreviated help.\n" +
            "With one argument, print detailed help on a given command.")
    public static void helpCommand(String[] args, InputStream in, OutputStream out, OutputStream err) throws ENOSException {
        throw new ENOSException("Built-in command not handled by shell");
    }
}
