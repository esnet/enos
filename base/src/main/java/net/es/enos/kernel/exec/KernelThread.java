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
    private static final String ENOS_THREAD="ENOS Thread id=";


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
        this.setName(ENOS_THREAD + UUID.randomUUID().toString());

        // Set SecurityManager
        this.securityManager = new KernelSecurityManager(System.getSecurityManager());
        System.setSecurityManager(this.securityManager);


    }

    public static boolean isENOSThread (Thread thread) {
        return (thread!=null &&  thread.getName().startsWith(ENOS_THREAD));
    }

    public static boolean isENOSThread() {
        return Thread.currentThread().getName().startsWith(ENOS_THREAD);
    }

}


