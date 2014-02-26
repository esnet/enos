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

        // Create a new Thread.
        this.thread = new Thread(this);

        User user = User.getUser(tokenId.username);
        if (user == null) {
            // First thread from this user
            user = new User(tokenId.username);
        }
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