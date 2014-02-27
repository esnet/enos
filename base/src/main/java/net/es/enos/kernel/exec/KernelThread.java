package net.es.enos.kernel.exec;

/**
 * Created by lomax on 2/7/14.
 */


import net.es.enos.boot.BootStrap;
import net.es.enos.kernel.net.es.enos.kernel.user.User;
import net.es.enos.kernel.security.KernelSecurityManager;
import org.python.util.InteractiveConsole;

import java.io.*;
import java.util.HashMap;
import java.util.UUID;

public class  KernelThread {

    private final static HashMap<Thread,KernelThread> kernelThreads = new HashMap<Thread, KernelThread>();
    private static boolean rootThreadInitialized = false;

    private Thread thread = null;

    private boolean privileged = false;
    private User user = null;

    public KernelThread (Thread thread) {
        this.thread = thread;
        this.init();

        if ((this.thread.getThreadGroup() == null)
           || this.thread.getThreadGroup().equals(BootStrap.getBootStrap().getSecurityManager().getEnosRootThreadGroup())) {
            // Threads in the root ThreadGroup run as privileged
            this.privileged = true;
        } else {
            this.privileged = false;
        }
    }

    private void init() {
        synchronized (KernelThread.kernelThreads) {
            KernelThread.kernelThreads.put(this.thread, this);
        }

    }

    public Thread getThread() {
        return this.thread;
    }

    public synchronized boolean isPrivileged() {
        return this.privileged;
    }

    public static KernelThread getKernelThread (Thread t) {
        synchronized (KernelThread.kernelThreads) {
            KernelThread kernelThread = KernelThread.kernelThreads.get(t);
            if (kernelThread == null) {
                // This is the first time we see this thread. Create a KernelThread to track it
                kernelThread = new KernelThread(t);
            }
            return kernelThread;
        }
    }


    public static KernelThread getCurrentKernelThread() {
        synchronized (KernelThread.kernelThreads) {
            KernelThread kernelThread = KernelThread.kernelThreads.get(Thread.currentThread());
            if (kernelThread == null) {
                // This is the first time we see this thread. Create a KernelThread to track it
                kernelThread = new KernelThread(Thread.currentThread());
            }
            return kernelThread;
        }
    }

    public synchronized void setPrivileged (boolean priv) throws SecurityException {
        if (this.isPrivileged()) {
            this.privileged = priv;
        } else {
            throw new SecurityException("Unprivileged thread attempts to change its privileged");
        }
    }

    // Can be invoke only once. Makes sure that the first ENOS thread is privileged so it can create user threads.
    public static void setRootThread (Thread t) throws SecurityException {
        KernelThread kernelThread = KernelThread.getKernelThread(t);

        synchronized (KernelThread.kernelThreads) {
            if (KernelThread.rootThreadInitialized) {
                // Already initialized
                throw new SecurityException("Attempt to re-create the root thread");
            }
            kernelThread.privileged = true;
       }
    }

    public User getUser() {
        return this.user;
    }

    public synchronized void setUser(User user) throws SecurityException {

        if (this.user == null) {
            this.user = user;
            this.privileged = false;
        } else {
            throw new SecurityException("Attempt to change the user");
        }
    }
}


