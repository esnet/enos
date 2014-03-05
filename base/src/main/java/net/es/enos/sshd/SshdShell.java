/*
 * Copyright (c) 2014, Regents of the University of California  All rights reserved.
 * Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
 * 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

package net.es.enos.sshd;

import net.es.enos.kernel.exec.KernelThread;
import net.es.enos.kernel.net.es.enos.kernel.user.User;
import net.es.enos.shell.Shell;
import org.apache.sshd.common.Session;
import org.apache.sshd.server.Command;
import org.apache.sshd.server.Environment;
import org.apache.sshd.server.ExitCallback;
import org.apache.sshd.server.SessionAware;
import org.apache.sshd.server.session.ServerSession;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;

public class SshdShell extends Shell implements Command, SessionAware {

    private OutputStream err;
    private ExitCallback callback;
    private Environment environment;
    private Thread thread;
    private ServerSession session;

    public SshdShell() throws IOException {
        super(null, null);
    }


    public Environment getEnvironment() {
        return environment;
    }

    public void setInputStream(InputStream in) {
        super.setIn (in);
    }

    public void setOutputStream(OutputStream out) {
        super.setOut(out);
    }

    public void setErrorStream(OutputStream err) {
        this.err = err;
    }

    public void setExitCallback(ExitCallback callback) {
        this.callback = callback;
    }

    public void start(Environment env) throws IOException {
        this.environment = env;
        // Retrieve user
        SShd.TokenId tokenId = this.session.getAttribute(SShd.TOKEN_ID);
        if (tokenId == null) {
            // Should not happen
            throw new RuntimeException("Trying to start an SSH session without users");
        }

        if (!tokenId.accepted) {
            // Not authenticated
            return;
        }
        User user = User.getUser(tokenId.username);
        if (user == null) {
            // First thread from this user
            user = new User(tokenId.username);
        }

        // Create a new Thread.
        this.thread = new Thread(user.getThreadGroup(),
                                 this,
                                 "ENOS Shell User= " + user.getName() );
        KernelThread.getKernelThread(this.thread).setUser(user);
        this.thread.start();
    }

    @Override
    public void destroy() {

    }

    @Override
    public void setSession(ServerSession serverSession) {
        this.session = serverSession;
    }
}