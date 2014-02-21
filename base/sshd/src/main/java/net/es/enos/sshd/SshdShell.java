package net.es.enos.sshd;

import net.es.enos.shell.Shell;
import org.apache.sshd.server.Command;
import org.apache.sshd.server.Environment;
import org.apache.sshd.server.ExitCallback;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;

public class SshdShell extends Shell implements Command {

    private OutputStream err;
    private ExitCallback callback;
    private Environment environment;

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
        environment = env;
        super.start();
    }

    public void destroy() {
        Thread.dumpStack();
    }
}