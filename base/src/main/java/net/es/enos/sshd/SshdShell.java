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
import net.es.enos.kernel.users.User;
import net.es.enos.shell.Shell;
import org.apache.sshd.common.file.FileSystemAware;
import org.apache.sshd.common.file.FileSystemView;
import org.apache.sshd.server.Command;
import org.apache.sshd.server.Environment;
import org.apache.sshd.server.ExitCallback;
import org.apache.sshd.server.SessionAware;
import org.apache.sshd.server.command.ScpCommand;
import org.apache.sshd.server.session.ServerSession;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;

public class SshdShell extends Shell implements Command, SessionAware, FileSystemAware, Runnable {

    private OutputStream err;
    private ExitCallback callback;
    private Environment environment;
    private Thread thread;
    private ServerSession session;
    private ScpCommand scpCommand;
    private final Logger logger = LoggerFactory.getLogger(SshdShell.class);
    public SshdShell() throws IOException {
        // Constructor for ssh
        super(null, null, null);
        logger.debug("Accepted new SSH connection");
    }

    public SshdShell(String[] command) throws IOException {
        // Constructor for scp (or ssh with a command)
	    super(null, null, command);

	    if (command[0].startsWith("scp")) {
		    scpCommand = new ScpCommand(command[0]);
		    logger.debug("Accepted new SCP connection " + command[0]);
	    } else {
		    logger.debug("Accepted new SSH connection");
	    }
    }

    public Environment getEnvironment() {
        return environment;
    }

    public void setInputStream(InputStream in) {
        super.setIn (in);
        if (this.scpCommand != null) {
            this.scpCommand.setInputStream(in);
        }
    }

    public void setOutputStream(OutputStream out) {
        super.setOut(out);
        if (this.scpCommand != null) {
            this.scpCommand.setOutputStream(out);
        }
    }

    public void setErrorStream(OutputStream err) {
        this.err = err;
        if (this.scpCommand != null) {
            this.scpCommand.setErrorStream(err);
        }
    }

    public void setExitCallback(ExitCallback callback) {
        this.callback = callback;
        if (this.scpCommand != null) {
            this.scpCommand.setExitCallback(callback);
        }
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
            // First login from this user
            user = new User(tokenId.username);
        }
        if (this.scpCommand != null) {
            logger.info("Accepted new SCP user=" + user.getName() + " command=" + scpCommand.toString());
        } else {
            logger.info("Accepted new SSH user=" + user.getName());
        }
        // Create a new Thread.
        this.thread = new Thread(user.getThreadGroup(),
                                 this,
                                 "ENOS Shell User= " + user.getName() );
        Thread currentThread = Thread.currentThread();
        KernelThread kt = KernelThread.getKernelThread(this.thread);
        kt.setUser(user);
        this.thread.start();
    }

    public void run() {
        if (this.scpCommand == null) {
            // SSH
            this.startShell();
        } else {
            // SCP
            try {
                scpCommand.start(this.environment);
            } catch (IOException e) {
                e.printStackTrace();
                logger.warn("Exception while scp " + this.scpCommand.toString());
            }

        }
    }

    @Override
    public void destroy() {
        this.callback.onExit(0);
    }

    @Override
    public void setSession(ServerSession serverSession) {
        this.session = serverSession;
    }

    @Override
    public void setFileSystemView(FileSystemView view) {
        if (scpCommand != null) {
            scpCommand.setFileSystemView(view);
        }
    }
}