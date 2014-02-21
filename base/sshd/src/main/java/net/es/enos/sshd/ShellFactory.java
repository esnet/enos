package net.es.enos.sshd;

/**
 * Created by lomax on 2/10/14.
 */



import org.apache.sshd.common.Factory;
import org.apache.sshd.server.Command;

import java.io.IOException;


public class ShellFactory implements Factory<Command> {

    public Command create() {

        try {
            return new SshdShell();
        } catch (IOException e) {
            e.printStackTrace();
            return null;
        }
    }
}