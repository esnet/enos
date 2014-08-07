package net.es.enos.api;

import net.es.enos.rabbitmq.BrokerInfo;
import net.es.enos.rabbitmq.Consume;
import org.apache.sshd.ClientChannel;
import org.apache.sshd.ClientSession;
import org.apache.sshd.SshClient;
import org.apache.sshd.common.KeyPairProvider;
import org.apache.sshd.common.keyprovider.FileKeyPairProvider;
import org.apache.sshd.common.util.NoCloseOutputStream;
import org.apache.sshd.common.util.SecurityUtils;
import org.bouncycastle.openssl.PasswordFinder;

import java.io.*;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;
import java.util.concurrent.Callable;

/**
 * Created by davidhua on 7/29/14.
 */
public class SSHConnection {

	private String username = "admin";
	private String hostName = "summer1.es.net";
	private String password = "enos";
	private String privKeyLocation = ".ssh/test2";
	private String selfQueue;
	private String command = "GET_TOPOLOGY";
	private int port = 8000;
	OutputStream bOut;

	public SSHConnection(String command) throws Exception{
		this.selfQueue = UUID.randomUUID().toString();
		this.command = command;
		runStart();
	}

	public SSHConnection() throws Exception {
		this.selfQueue = UUID.randomUUID().toString();
		runStart();
	}

	public void runStart() throws Exception{
		KeyPairProvider provider = null;
		final List<String> files = new ArrayList<>();

		File f = new File(System.getProperty("user.home"), privKeyLocation);
		if (f.exists() && f.isFile() && f.canRead()) {
			files.add(f.getAbsolutePath());
		}

		if (files.size() > 0) {
			try {
				if (SecurityUtils.isBouncyCastleRegistered()) {
					class KeyPairProviderLoader implements Callable<KeyPairProvider> {
						public KeyPairProvider call() throws Exception {
							return new FileKeyPairProvider(files.toArray(new String[files.size()]), new PasswordFinder() {
								public char[] getPassword() {
									try {
										System.out.println("Enter password for private key: ");
										BufferedReader r = new BufferedReader(new InputStreamReader(System.in));
										String password = r.readLine();
										return password.toCharArray();
									} catch (IOException e) {
										return null;
									}
								}
							});
						}
					};
					provider = new KeyPairProviderLoader().call();
					System.out.println(provider.toString());
				}
			} catch (Throwable t) {
				System.out.println("Error loading user keys: " + t.getMessage());
			}
		}
		SshClient client = SshClient.setUpDefaultClient();
		client.start();
		ClientSession session;
		try {
			// If no keys available for key-based auth, try password.
			if (files.size() == 0) {
				session = client.connect(username, hostName, port).await().getSession();
				session.auth().verify();

				int ret = ClientSession.WAIT_AUTH;
				while ((ret & ClientSession.WAIT_AUTH) != 0) {
					session.authPassword(username, password);
					ret = session.waitFor(ClientSession.WAIT_AUTH | ClientSession.CLOSED | ClientSession.AUTHED, 0);
				}
				if ((ret & ClientSession.CLOSED) != 0) {
					System.err.println("ERROR");
					return;
				}
			} else {
				client.setKeyPairProvider(provider);
				session = client.connect(username, hostName, port).await().getSession();
				session.auth().verify();
			}

			ClientChannel channel = session.createChannel(ClientChannel.CHANNEL_EXEC, (command + " " + selfQueue));
			bOut = new ByteArrayOutputStream();
			channel.setOut(bOut);
			channel.setErr(new NoCloseOutputStream(System.err));
			channel.open();
			channel.waitFor(ClientChannel.CLOSED, 0);
			session.close(false);
			channel.close(true);
		} catch (IOException | InterruptedException e) {
			System.err.println("ERROR");
			return;
		} finally {
			client.stop();

			BrokerInfo info = new BrokerInfo("summer1.es.net", "david2", "123", 5672, false);
			Consume thisrecv = new Consume(info, selfQueue);
			thisrecv.consumeMessage();
		}
	}
}