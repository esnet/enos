/*
 * Copyright (c) 2014, Regents of the University of California.
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 * 1. Redistributions of source code must retain the above copyright notice,
 * this list of conditions and the following disclaimer.
 *
 * 2. Redistributions in binary form must reproduce the above copyright notice,
 * this list of conditions and the following disclaimer in the documentation
 * and/or other materials provided with the distribution.
 *
 * 3. Neither the name of the copyright holder nor the names of its contributors
 * may be used to endorse or promote products derived from this software without
 * specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 * DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
 * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
 * CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
 * OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

package net.es.enos.sshd;

/**
 * Created by lomax on 2/9/14.
 */

import net.es.enos.boot.BootStrap;
import net.es.enos.kernel.users.Users;
import org.apache.sshd.SshServer;
import org.apache.sshd.common.Session;
import org.apache.sshd.server.PasswordAuthenticator;
import org.apache.sshd.server.command.ScpCommandFactory;
import org.apache.sshd.server.keyprovider.SimpleGeneratorHostKeyProvider;
import org.apache.sshd.server.session.ServerSession;

import java.io.IOException;


public class SShd {

    private static SShd sshd = null;
    private SshServer sshServer = null;
    public static final Session.AttributeKey<TokenId> TOKEN_ID = new Session.AttributeKey<TokenId>();

    public static SShd getSshd() {
        if (SShd.sshd == null) {
            SShd.sshd = new SShd();
        }
        return SShd.sshd;
    }

    static public class TokenId {
        public String username;
        public boolean privileged = false;
        public boolean accepted = false;
        public TokenId (String username, boolean accepted, boolean privileged) {
            this.username = username;
            this.accepted = accepted;
            this.privileged = false;
        }
    }

    public void start() throws IOException {
        this.sshServer = SshServer.setUpDefaultServer();

        int sshPort;
        try {
            sshPort = BootStrap.getMasterConfiguration().getGlobal().getSshPort();
        }
        catch (NullPointerException e) {
            sshPort = 8000;
        }
        this.sshServer.setPort(sshPort);

        PasswordAuthenticator auth = new PasswordAuthenticator() {
            public boolean authenticate(String username, String password, ServerSession ss) {
                    if (Users.getUsers().authUser(username, password)) {
                        TokenId tokenId = new TokenId(username,
                                                      true,
                                                      Users.getUsers().isPrivileged(username));
                        ss.setAttribute(TOKEN_ID, tokenId);
                        return true;
                    } else {
                        return false;
                    }
            }
        };

        this.sshServer.setPasswordAuthenticator(auth);

        this.sshServer.setKeyPairProvider(new SimpleGeneratorHostKeyProvider("hostkey.ser"));
        this.sshServer.setShellFactory(new ShellFactory());
        this.sshServer.setCommandFactory(new SshdScpCommandFactory());
        this.sshServer.start();
    }
}
