package net.es.enos.sshd;

/**
 * Created by lomax on 2/9/14.
 */

import net.es.enos.kernel.net.es.enos.kernel.user.User;
import org.apache.sshd.SshServer;
import org.apache.sshd.common.Session;
import org.apache.sshd.server.PasswordAuthenticator;
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
        public TokenId (String username) {
            this.username = username;
        }
    }

    public void start() throws IOException {
        this.sshServer = SshServer.setUpDefaultServer();
        this.sshServer.setPort(8000);

        PasswordAuthenticator auth = new PasswordAuthenticator() {
            public boolean authenticate(String username, String string1, ServerSession ss) {
                System.out.println ("Auth " + username + ":" + string1);
                TokenId tokenId = new TokenId(username);
                ss.setAttribute(TOKEN_ID, tokenId);
                return true;
            }
        };

        this.sshServer.setPasswordAuthenticator(auth);

        this.sshServer.setKeyPairProvider(new SimpleGeneratorHostKeyProvider("hostkey.ser"));
        this.sshServer.setShellFactory(new ShellFactory());
        this.sshServer.start();
    }
}
