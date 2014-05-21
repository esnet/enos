/*
 * Copyright (c) 2014, Regents of the University of California  All rights reserved.
 * Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
 * 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

package net.es.enos.kernel.exec;

/**
 * Created by lomax on 2/7/14.
 */


import net.es.enos.boot.BootStrap;
import net.es.enos.api.ENOSException;
import net.es.enos.kernel.exec.annotations.SysCall;
import net.es.enos.kernel.users.User;
import net.es.enos.kernel.security.AllowedSysCalls;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.lang.reflect.Method;
import java.util.HashMap;
import java.util.LinkedList;
import java.util.List;


/**
 * KernelThread implements the ENOS part of java.lang.Thread. It includes specific states, such as the User
 * owning the thread, its privilege status (system or user). It also implements the transition of a thread from
 * being executed in user space to execution into system space, in order to execute the ENOS API.
 *
 * KernelThread is critical to the overall security of ENOS: it cannot be extended. It is also one of the few
 * classes that are allowed to be accessed by user space thread.
 */
public final class  KernelThread {

    private final Logger logger = LoggerFactory.getLogger(KernelThread.class);
    private final static HashMap<Thread,KernelThread> kernelThreads = new HashMap<Thread, KernelThread>();
    private static LinkedList<Class> systemClasses = new LinkedList<Class>();

    private static boolean sysCallsInitialized = false;

    private Thread thread = null;

    private boolean privileged = false;
    private User user = null;

    /**
     * Creates a new KernelThread associated with the provided Thread t. Only one KernelThread per thread
     * is authorized. An attempt to create a new a new KernelThread will result into a SecurityException.
     * @param thread the Thread to be associated with the new KernelThread.
     * @throws SecurityException when a KernelThread has already been created for the provided Thread.
     */
    public KernelThread (Thread thread) throws SecurityException {
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

    /**
     * Initialize the KernelThread. If a KernelThread already exist for the Thread, throw a SecurityException.
     */
    private void init() throws SecurityException {
        synchronized (KernelThread.kernelThreads) {
            if (KernelThread.kernelThreads.get(this.thread) != null) {
                // This is an illegal attempt to create a second KernelThread for the
                // same Thread. Potentially an attempt to gain unauthorized privilege.
                throw new SecurityException (Thread.currentThread().getName() +
                        " is trying to create new KernelThread for thread " + this.thread.getName() +
                        " which already has one");
            }
            KernelThread.kernelThreads.put(this.thread, this);
        }
    }

    /**
     * Returns the Thread associated with this KernelThread
     * @return the Thread associated with this KernelThread
     */
    public Thread getThread() {
        return this.thread;
    }

    /**
     * Returns the current privilege of the thread. Some special care needs to be done in order to
     * support ENOS bootstrapping process, when the SecurityManager is already in place but not all of
     * the system is setup yet.
     *
     * IMPORTANT: correctness of this method is critical to the overall security of ENOS
     *
     * @return the privilege status of the KernelThread.
     */
    public synchronized boolean isPrivileged() {
        return this.privileged;
    }

    /**
     * Returns the KernelThread associated with the provided thread.
     * @param t given Thread
     * @return KernelThread associated with Thread t
     */
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


    /**
     * Returns the KernelThread associated to the current thread .
     * @return the KernelThread associated to the current thread
     */
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

    /**
     * initSysCalls sets the list of authorized classes to invoke doSysCall. This method can
     * be invoked only once during the ENOS bootstrap
     * @param classes
     * @throws SecurityException when executed more than once
     */
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

    /**
     * Returns the user owning this thread
     * @return Returns the user owning this thread
     */
    public synchronized User getUser() {

        if (this.user == null) {
            // Retrieve, when possible, the User associated to this thread
            this.user = User.getUser(Thread.currentThread().getThreadGroup());
            if (this.user != null) {
                logger.info("Adopting thread " + Thread.currentThread().getId() + " user= " + this.user.getName());
            } else {
                logger.warn("Cannot find user for thread " + Thread.currentThread().getId());
            }
        }

        return this.user;

    }

    /**
     * sets a user to the current thread. This can be done only once, when the thread is
     * created
     * @param user
     * @throws SecurityException when the thread was already set
     */
    public synchronized void setUser(User user) throws SecurityException {

        if (this.user == null) {
            this.user = user;
            this.privileged = user.isPrivileged();
        } else {
            throw new SecurityException("Attempt to change the user");
        }
    }

    /**
     * doSysCall is the only manner for a Thread to gain privileged status. Only classes that are defined
     * in net.es.enos.kernel.security.AllowedSysCalls are allowed to become privileged. doSysCall inspects
     * the current thread's execution stack to verify that the invoker is authorized.
     * Once the invoker is authorized, doSysCall is responsible for insuring that the thread will return to
     * not privileged mode upon completion of the system call: doSysCall, after granting privileged access
     * to the thread, invokes the provided method within a catch all try statement enforcing the reset of the
     * privilege.
     *
     * IMPORTANT: this methog is critical to the overall security of enos. Be careful when modifying it.
     *
     * TODO: is it sufficient to just authorize the invoking class, or should the methodToCall also be
     * authorized ? Likely the later.
     *
     * @param methodToCall
     * @param args
     * @throws Exception Throws any exception that methodToCall may have thrown, or SecurityException when
     * the invoker class is not authorized to perform a system call.
     */
    public static void doSysCall (Object obj, Method methodToCall, Object... args) throws Exception {

        // System.out.println("doSysCall");
        KernelThread kernelThread = KernelThread.getCurrentKernelThread();

        StackTraceElement[] stackTraceElements = Thread.currentThread().getStackTrace();
        // The third element is the class/method that is invoking doSysCall
        StackTraceElement elem = stackTraceElements[2];
        Exception exception = null;
        Class c = Class.forName(elem.getClassName());
        if (AllowedSysCalls.isAllowed(c)) {
            // Allowed. Set privilege and execute the method
            boolean wasPrivileged = kernelThread.privileged;

            try {
                synchronized (kernelThread) {
                    kernelThread.privileged = true;
                }
                // Call the system call

                // System.out.println("doSysCall is invoking " + methodToCall.getName());
                methodToCall.invoke(obj, args);

            } catch (Exception e) {
                // Catch all
                exception = e;
            } finally {
                // Reverse privilege
                kernelThread.privileged = wasPrivileged;
                if (exception != null) {
                    throw exception;
                }
            }
        } else {
            // Not allowed
            throw new ENOSException(obj.getClass().getCanonicalName() + "'s method " + methodToCall.getName() +
                " is not allowed to be a privileged call.");
        }
    }

    public static Method getSysCallMethod (Class targetClass, String name) {
        Method[] methods = targetClass.getDeclaredMethods();
        for (Method method : methods) {

            SysCall syscall = method.getAnnotation(SysCall.class);
            if (syscall != null) {
               if (syscall.name().equals(name)) {

                   return method;
               }
            }
        }
        return null;
    }
}


