package net.es.enos.sshd;

/**
 * Created by lomax on 2/9/14.
 */

import org.apache.sshd.SshServer;
import org.apache.sshd.server.PasswordAuthenticator;
import org.apache.sshd.server.keyprovider.SimpleGeneratorHostKeyProvider;
import org.apache.sshd.server.session.ServerSession;

import java.io.IOException;


public class SShd {

    private static SShd sshd = null;
    private SshServer sshServer = null;

    public static SShd getSshd() {
        if (SShd.sshd == null) {
            SShd.sshd = new SShd();
        }
        return SShd.sshd;
    }



    public void start() throws IOException {
        this.sshServer = SshServer.setUpDefaultServer();
        this.sshServer.setPort(8000);

        PasswordAuthenticator auth = new PasswordAuthenticator() {
            public boolean authenticate(String string, String string1, ServerSession ss) {
                System.out.println ("Auth " + string + ":" + string1);
                return true;
            }
        };

        this.sshServer.setPasswordAuthenticator(auth);

        this.sshServer.setKeyPairProvider(new SimpleGeneratorHostKeyProvider("hostkey.ser"));
        this.sshServer.setShellFactory(new ShellFactory());
        this.sshServer.start();
    }
}
