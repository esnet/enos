package net.es.enos.kernel.exec;

/**
 * Created by lomax on 2/7/14.
 */


import net.es.enos.kernel.security.KernelSecurityManager;
import org.python.util.InteractiveConsole;

import java.io.*;
import java.util.UUID;

public class KernelThread extends Thread {

    private SecurityManager securityManager = null;
    private InteractiveConsole console = null;
    private InputStream in;
    private OutputStream out;



    private KernelThread () {
        this.init();
    }

    public KernelThread(InputStream in, OutputStream out) {
        this.in = in;
        this.out = out;
        this.init();
    }
    private void init() {
        // Set first what will be protected.
        this.setName(UUID.randomUUID().toString());

        // Set SecurityManager
        this.securityManager = new KernelSecurityManager(System.getSecurityManager());
        System.setSecurityManager(this.securityManager);


    }

}


