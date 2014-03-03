/*
 * Copyright (c) 2014, Regents of the University of California  All rights reserved.
 * Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
 * 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

package net.es.enos.shell;

import jline.console.ConsoleReader;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;

/**
 * Created by lomax on 2/20/14.
 */
public class ShellInputStream extends InputStream {

    private InputStream in = null;
    private OutputStream echoOut = null;
    private boolean last = false;
    private int lastRead = 0;
    private boolean doEcho = false;
    private ConsoleReader consoleReader = null;

    public ShellInputStream(InputStream in, OutputStream echoOut) {
        this.in = in;
        this.echoOut = echoOut;
    }

    public ShellInputStream(InputStream in, ConsoleReader consoleReader) {
        this.in = in;
        this.consoleReader = consoleReader;
    }

    public int read() throws IOException {

        if (this.last) {
            this.last = false;
            return -1;
        }
        int c = this.in.read();
        this.lastRead += 1;
        if (this.doEcho && this.echoOut != null) {
            this.echoOut.write(c);
            this.echoOut.flush();
        }
        switch (c) {
            case 13:
                if (this.doEcho && this.echoOut != null) {
                    this.echoOut.write('\n');
                    this.echoOut.flush();
                }
                this.last = true;
                if (this.lastRead == 1) {
                    this.lastRead = 0;
                    return 10;
                }
                this.lastRead = 0;
                return 10;
        }
        return c;
    }

    @Override
    public int read(byte[] b) throws IOException {
        int index=0;
        while (true) {
            int c = this.in.read();
            if (c==13) c=10;
            if (c==10) {
                return index;
            }
            if (index < b.length) {
                b[index++] = (byte) c;
            } else {
                return index;
            }
        }
    }

    @Override
    public int read(byte[] b, int off, int len) throws IOException {
            String prompt = consoleReader.getPrompt();
            String line = consoleReader.readLine("\000\000\000\000");
            for (int i=0; i < line.length(); ++i) {
                 b[off+i] = (byte) line.charAt(i);
            }
            b[line.length()] = 10;
            consoleReader.setPrompt(prompt);
            return line.length() + 1;
    }

    @Override
    public long skip(long n) throws IOException {
        System.out.println("skip " + n);
        return this.in.skip(n);
    }

    @Override
    public int available() throws IOException {
        return this.in.available();
    }

    @Override
    public synchronized void mark(int readlimit) {
        System.out.println("readlimit");
        this.mark(readlimit);
    }

    @Override
    public synchronized void reset() throws IOException {
        System.out.println("reset");
        this.in.reset();
    }

    @Override
    public boolean markSupported() {
        System.out.println("markSupported");
        return this.in.markSupported();
    }
}
