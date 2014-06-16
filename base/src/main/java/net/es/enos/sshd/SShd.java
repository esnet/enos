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
import org.apache.mina.util.Base64;
import org.apache.sshd.SshServer;
import org.apache.sshd.common.Session;
import org.apache.sshd.server.PasswordAuthenticator;
import org.apache.sshd.server.PublickeyAuthenticator;
import org.apache.sshd.server.command.ScpCommandFactory;
import org.apache.sshd.server.keyprovider.SimpleGeneratorHostKeyProvider;
import org.apache.sshd.server.session.ServerSession;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Path;
import java.security.KeyFactory;
import java.security.PublicKey;
import java.security.interfaces.DSAPublicKey;
import java.security.interfaces.RSAPublicKey;
import java.security.spec.DSAPublicKeySpec;
import java.security.spec.RSAPublicKeySpec;


public class SShd {

    private static SShd sshd = null;
    private SshServer sshServer = null;
    public static final Session.AttributeKey<TokenId> TOKEN_ID = new Session.AttributeKey<TokenId>();
    private final Logger logger = LoggerFactory.getLogger(SShd.class);

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


    /**
     * Implement public key authentication.
     * TODO:  Is this really the right place for this?  Or should it be in the Users class?
     * Note that the Users class does the password authentication.  If we want to do this,
     * then just make Users implement the PublickeyAuthenticator interface and pass the
     *instance object to setPublickeyAuthenticator().
     */
    public class EnosPublickeyAuthenticator implements PublickeyAuthenticator{

        private final Logger logger = LoggerFactory.getLogger(EnosPublickeyAuthenticator.class);

        @Override
        public boolean authenticate(String username, PublicKey key, ServerSession session) {
            if (Users.getUsers().userExists(username)) {
                logger.debug("Username is {}, presented key is {}", username, key.toString());

                // Read lines in ~/.ssh/authorized_keys
                try {
                    Path authorizedKeysPath = Users.getUsers().getHomePath(username).resolve(".ssh").resolve("authorized_keys");
                    logger.debug("Read keys from {}", authorizedKeysPath.toString());
                    File authorizedKeysFile = new File(authorizedKeysPath.toString());
                    if (authorizedKeysFile.exists()) {

                        // At this point, OpenSSH sshd would probably do some permission checks
                        // on the authorized_keys file and the directories leading towards it.
                        // It's not clear what the analog is in the ENOS world.
                        BufferedReader reader = new BufferedReader(new FileReader(authorizedKeysFile));
                        String line = null;

                        // Read keys one per line, check each key to see if it matches.
                        while ((line = reader.readLine()) != null) {
                            logger.debug(line);
                            PublicKey publicKey = decodePublicKey(line);

                            // Algorithms need to match otherwise the keys aren't the same.
                            if (publicKey.getAlgorithm().equals(key.getAlgorithm())) {

                                logger.debug("Matching key with algorithm type {}", publicKey.getAlgorithm());

                                boolean match = false;

                                // RSA keys match if the modulus is the same
                                if (publicKey.getAlgorithm().equals("RSA")) {
                                    match = ((RSAPublicKey) publicKey).getModulus().equals(((RSAPublicKey) key).getModulus());
                                }
                                // Check for DSA key matches.  They match if the Y (public key) part is the same.
                                else if (publicKey.getAlgorithm().equals("DSA")) {
                                    match = ((DSAPublicKey) publicKey).getY().equals(((DSAPublicKey) key).getY());
                                }
                                // Unsupported (but matching) algorithm.
                                else {
                                    logger.error("Unsupported algorithm type {}", publicKey.getAlgorithm());
                                    match = false;
                                }

                                // This is what we do for a valid login.  If we don't find a match, then keep
                                // checking.
                                if (match) {
                                    logger.info("Matching user {} with {} key", username, publicKey.getAlgorithm());
                                    SShd.TokenId tokenId = new SShd.TokenId(username,
                                            true,
                                            Users.getUsers().isPrivileged(username));
                                    session.setAttribute(TOKEN_ID, tokenId);
                                    return true;
                                }
                            }
                        }
                    }
                }
                catch (Exception e) {
                    e.printStackTrace();
                }
            }
            return false;
        }

        // Adapted from org.apache.maven.wagon.providers.ssh.TestPublicKeyAuthenticator
        // That code is licensed as follows:
            /*
             * Licensed to the Apache Software Foundation (ASF) under one
             * or more contributor license agreements.  See the NOTICE file
             * distributed with this work for additional information
             * regarding copyright ownership.  The ASF licenses this file
             * to you under the Apache License, Version 2.0 (the
             * "License"); you may not use this file except in compliance
             * with the License.  You may obtain a copy of the License at
             *
             *   http://www.apache.org/licenses/LICENSE-2.0
             *
             * Unless required by applicable law or agreed to in writing,
             * software distributed under the License is distributed on an
             * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
             * KIND, either express or implied.  See the License for the
             * specific language governing permissions and limitations
             * under the License.
             */
        private byte[] bytes;
        private int pos;

        /**
         * @author Olivier Lamy
         */
        public PublicKey decodePublicKey( String keyLine ) throws Exception {
            bytes = null;
            pos = 0;

            for (String part : keyLine.split(" ")) {
                if (part.startsWith("AAAA")) {
                    bytes = Base64.decodeBase64(part.getBytes());
                    break;
                }
            }
            if (bytes == null) {
                throw new IllegalArgumentException("no Base64 part to decode");
            }

            String type = decodeType();
            if (type.equals("ssh-rsa")) {
                BigInteger e = decodeBigInt();
                BigInteger m = decodeBigInt();
                RSAPublicKeySpec spec = new RSAPublicKeySpec(m, e);
                return KeyFactory.getInstance("RSA").generatePublic(spec);
            } else if (type.equals("ssh-dss")) {
                BigInteger p = decodeBigInt();
                BigInteger q = decodeBigInt();
                BigInteger g = decodeBigInt();
                BigInteger y = decodeBigInt();
                DSAPublicKeySpec spec = new DSAPublicKeySpec(y, p, q, g);
                return KeyFactory.getInstance("DSA").generatePublic(spec);
            } else {
                throw new IllegalArgumentException("unknown type " + type);
            }
        }

        private String decodeType() {
            int len = decodeInt();
            String type = new String(bytes, pos, len);
            pos += len;
            return type;
        }

        private int decodeInt() {
            return ((bytes[pos++] & 0xFF) << 24) | ((bytes[pos++] & 0xFF) << 16) | ((bytes[pos++] & 0xFF) << 8)
                    | (bytes[pos++] & 0xFF);
        }

        private BigInteger decodeBigInt() {
            int len = decodeInt();
            byte[] bigIntBytes = new byte[len];
            System.arraycopy(bytes, pos, bigIntBytes, 0, len);
            pos += len;
            return new BigInteger(bigIntBytes);
        }

    }

    public void start() throws IOException {
        this.sshServer = SshServer.setUpDefaultServer();

        int sshPort = BootStrap.getMasterConfiguration().getGlobal().getSshPort();
        this.sshServer.setPort(sshPort);

        int sshIdleTimeout = BootStrap.getMasterConfiguration().getGlobal().getSshIdleTimeout();
        this.sshServer.getProperties().put(sshServer.IDLE_TIMEOUT, Integer.toString(sshIdleTimeout));

        PasswordAuthenticator passwordAuth = new PasswordAuthenticator() {
            @Override
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
        this.sshServer.setPasswordAuthenticator(passwordAuth);

        PublickeyAuthenticator publickeyAuth = new EnosPublickeyAuthenticator();
        this.sshServer.setPublickeyAuthenticator(publickeyAuth);

        String hostKeyFile = BootStrap.rootPath.resolve("etc").resolve("hostkey.ser").toString();
        logger.info("Host key file is {}", hostKeyFile);
        this.sshServer.setKeyPairProvider(new SimpleGeneratorHostKeyProvider(hostKeyFile));
        this.sshServer.setShellFactory(new ShellFactory());
        this.sshServer.setCommandFactory(new SshdScpCommandFactory());
        this.sshServer.start();
    }
}
