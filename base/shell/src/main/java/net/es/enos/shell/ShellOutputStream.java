package net.es.enos.shell;

import java.io.IOException;
import java.io.OutputStream;

public class ShellOutputStream extends OutputStream {
    private OutputStream out = null;


    public ShellOutputStream (OutputStream out) {
        this.out = out;
    }

    public void write(int c) throws IOException {
        if (c==10) {
            this.out.write(13);
            this.out.write(10);
            this.out.flush();
        } else {
            this.out.write(c);
            this.out.flush();
        }
    }
}
