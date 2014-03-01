package net.es.enos.kernel.exec;

/**
 * Created by lomax on 2/7/14.
 */


import net.es.enos.boot.BootStrap;
import net.es.enos.kernel.net.es.enos.kernel.user.User;
import net.es.enos.kernel.security.AllowedSysCalls;

import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.util.HashMap;
import java.util.LinkedList;
import java.util.List;


public final class  KernelThread {

    private final static HashMap<Thread,KernelThread> kernelThreads = new HashMap<Thread, KernelThread>();
    private static LinkedList<Class> systemClasses = new LinkedList<Class>();

    private static boolean sysCallsInitialized = false;

    private Thread thread = null;

    private boolean privileged = false;
    private User user = null;

    public KernelThread (Thread thread) {
        this.thread = thread;
        this.init();

        if ((this.thread == null)
           || (BootStrap.getBootStrap() == null)
           || (BootStrap.getBootStrap().getSecurityManager() == null)
           || (this.thread.getThreadGroup() == null)
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

        ThreadGroup enosRootThreadGroup = null;
        // BootStrap may be null when running within an IDE: the SecurityManager is changed by ENOS.
        if ((BootStrap.getBootStrap() == null) || (BootStrap.getBootStrap().getSecurityManager() == null)) {
            // Still bootstrapping
            return true;
        }

        enosRootThreadGroup = BootStrap.getBootStrap().getSecurityManager().getEnosRootThreadGroup();

        if (true) {
            if (this.getThread().getThreadGroup() == null) System.out.println("No ThreadGroup");
                    else if (!enosRootThreadGroup.parentOf(this.getThread().getThreadGroup())) System.out.println("ThreadGroup= " + this.getThread().getThreadGroup().getName());
                    else System.out.println("Is privileged: " + this.privileged);
        }
        return  enosRootThreadGroup == null ||    // Not created yet, this is still bootstapping
                this.getThread().getThreadGroup() == null ||  // This thread has no group: not an ENOS thread
                !enosRootThreadGroup.parentOf(this.getThread().getThreadGroup()) || // This thread has a group, but not an ENOS group
                this.privileged; // This is an ENOS thread.
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

    public synchronized void setPrivileged (KernelThread kernelThread, boolean priv) throws SecurityException {
        if (this.isPrivileged()) {
            kernelThread.privileged = priv;
        } else {
            throw new SecurityException("Unprivileged thread attempts to change its privileged");
        }
    }

    // Can be invoked only once. Makes sure that the first ENOS thread is privileged so it can create user threads.
    public static void initSysCalls (List<Class> classes) throws SecurityException {

        synchronized (KernelThread.systemClasses) {
            if (KernelThread.sysCallsInitialized) {
                // Already initialized
                throw new SecurityException("Attempt to re-initialize System Calls");
            }
            for (Class c : systemClasses) {
                KernelThread.systemClasses.add(c);
            }
            KernelThread.sysCallsInitialized = true;
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

    public static void doSysCall (Method methodToCall, Object... args) throws Exception {

        KernelThread kernelThread = KernelThread.getCurrentKernelThread();
        StackTraceElement[] stackTraceElements = Thread.currentThread().getStackTrace();
        // The third element is the class/method that is invoking doSysCall
        StackTraceElement elem = stackTraceElements[2];
        Exception exception = null;
        if (kernelThread.isPrivileged() ||
            AllowedSysCalls.isAllowed(elem.getClass())) {
            // Allowed. Set privilege and execute the method
            try {
                synchronized (kernelThread) {
                    kernelThread.privileged = true;
                }
                // Call the system call
                methodToCall.invoke(args);

            } catch (Exception e) {
                // Catch all
                exception = e;
            } finally {
                kernelThread.privileged = false;
                if (exception != null) {
                    throw exception;
                }
            }
        }
    }
}


