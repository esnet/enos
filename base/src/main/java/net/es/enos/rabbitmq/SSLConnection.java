/*
 * Copyright (c) 2014, Regents of the University of California  All rights reserved.
 * Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
 * 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

package net.es.enos.rabbitmq;

import java.io.*;
import javax.net.ssl.*;
import java.security.*;
import com.rabbitmq.client.ConnectionFactory;

/**
 * Created by davidhua on 7/2/14.
 */

/**
 * Creates a SSL connection from RabbitMQ broker to producer/consumer
 */
public class SSLConnection {

	private String host;
	private String user;
	private String password;
	private int port;
	private boolean ssl = false;
	private final String TRUSTPASS = "123456";
	private final String KEYPASS = "MySecretPassword";
	private final String KEYCERT = "/Users/davidhua/Desktop/ssl/client/keycert.p12"; // Replace with location of key cert
	private final String KEYSTORE = "/Users/davidhua/Desktop/ssl/rabbitstore";

	public SSLConnection(BrokerInfo info) {
		host = info.getHost();
		user = info.getUser();
		password = info.getPassword();
		port = info.getPort();
		ssl = info.getSSL();
	}

	public ConnectionFactory createConnection() throws Exception {
		ConnectionFactory factory = new ConnectionFactory();
		factory.setHost(host);
		factory.setUsername(user);
		factory.setPassword(password);
		factory.setPort(port);

		if (ssl) {
			char[] keyPassphrase = KEYPASS.toCharArray();
			KeyStore ks = KeyStore.getInstance("PKCS12");
			ks.load(new FileInputStream(KEYCERT), keyPassphrase);

			KeyManagerFactory kmf = KeyManagerFactory.getInstance("SunX509");
			kmf.init(ks, keyPassphrase);

			char[] trustPassphrase = TRUSTPASS.toCharArray();
			KeyStore tks = KeyStore.getInstance("JKS");
			tks.load(new FileInputStream(KEYSTORE), trustPassphrase);

			TrustManagerFactory tmf = TrustManagerFactory.getInstance("SunX509");
			tmf.init(tks);

			SSLContext c = SSLContext.getInstance("SSLv3");
			c.init(kmf.getKeyManagers(), tmf.getTrustManagers(), null);

			factory.useSslProtocol(c);
		}
		return factory;
	}
}