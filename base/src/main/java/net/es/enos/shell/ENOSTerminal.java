/*
 * Copyright (c) 2014, Regents of the University of California  All rights reserved.
 * Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
 * 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

/**
 * lomax@es.net: This class is a clone of JLINE's UnixTerminal, but the TerminalLineSettings is disabled since it required to
 * execute a UNIX shell. Perhaps, in the future, terminal settings might be implemented by retrieving the x/y values
 * from the SSHD session.
 */

package net.es.enos.shell;


import jline.TerminalSupport;
import jline.internal.Log;


/**
 * ENOS Terminal emulation
 */
public class ENOSTerminal extends TerminalSupport {

    public ENOSTerminal() throws Exception {
        super(true);
    }


    @Override
    public void init() throws Exception {
        super.init();
        setAnsiSupported(true);
        setEchoEnabled(false);
    }


    @Override
    public void restore() throws Exception {
        super.restore();
    }

    @Override
    public int getWidth() {
        // TODO: should be a option of the constructor
        return 80;
    }

    /**
     * Returns the value of <tt>stty rows>/tt> param.
     */
    @Override
    public int getHeight() {
        // TODO: should be a option of the constructor
        return 25;
    }

    @Override
    public synchronized void setEchoEnabled(final boolean enabled) {
        try {
            super.setEchoEnabled(enabled);
        }
        catch (Exception e) {
            Log.error("Failed to ", (enabled ? "enable" : "disable"), " echo", e);
        }
    }

    public void disableInterruptCharacter() {
        // TODO to be implemented
    }

    public void enableInterruptCharacter() {
        // TODO to be implemented
    }
}