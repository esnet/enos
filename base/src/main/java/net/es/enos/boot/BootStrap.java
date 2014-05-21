/*
 * Copyright (c) 2014, Regents of the University of California  All rights reserved.
 * Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
 * 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

package net.es.enos.boot;

import net.es.enos.api.DefaultValues;
import net.es.enos.api.PropertyKeys;
import net.es.enos.kernel.exec.KernelThread;
import net.es.enos.kernel.security.AllowedSysCalls;
import net.es.enos.kernel.security.KernelSecurityManager;
import net.es.enos.python.PythonShell;
import net.es.enos.shell.ShellBuiltinCommands;
import net.es.enos.shell.ShellCommandsFactory;
import net.es.enos.sshd.SShd;
import net.es.enos.shell.Shell;
import net.es.enos.kernel.users.UserShellCommands;

import java.io.IOException;
import java.nio.file.Path;
import java.nio.file.Paths;

import org.slf4j.LoggerFactory;
import org.slf4j.Logger;

/**
 * Created by lomax on 2/20/14.
 */
public class BootStrap implements Runnable {
    private static BootStrap bootStrap = null;
    private String[] args = null;
    private SShd sshd = null;
    private static Thread thread;
    final private Logger logger = LoggerFactory.getLogger(BootStrap.class);
    public final static Path rootPath = Paths.get(
            System.getProperty(PropertyKeys.ENOS_ROOTDIR) != null ?
            System.getProperty(PropertyKeys.ENOS_ROOTDIR) :
            DefaultValues.ENOS_DEFAULT_ROOTDIR ).normalize();

    private static final KernelSecurityManager securityManager = new KernelSecurityManager();

    public Shell getShell() {
        return shell;
    }

    private Shell shell = null;

    public SShd getSshd() {
        return sshd;
    }

    public String[] getArgs() {
        return args;
    }

    public KernelSecurityManager getSecurityManager() {
        return securityManager;
    }

    public void init() {


        BootStrap.thread = new Thread(BootStrap.getBootStrap().getSecurityManager().getEnosRootThreadGroup(),
                                      this,
                                      "ENOS Bootstrap");
        logger.info("Starting BootStrap thread");
        BootStrap.thread.start();

    }
    public static void main(String[] args) {

        final Logger logger = LoggerFactory.getLogger(BootStrap.class);
        logger.info("Starting ENOS");

        BootStrap.bootStrap = new BootStrap(args);
        BootStrap.bootStrap.init();
        BootStrap.bootStrap.postInitialization();
        // System.out.println("Bootstrap thread exits");
        logger.info("Bootstrap thread exits");
    }

    private BootStrap (String[] args) {
        this.args = args;
    }


    public static BootStrap getBootStrap() {
        return BootStrap.bootStrap;
    }

    public void startServices() {

        this.sshd = SShd.getSshd();
        try {
            this.sshd.start();
        } catch (IOException e) {
            e.printStackTrace();
        }
        // Add Shell Modules
        addShellModules();

        // Initialize SystemCalls
        KernelThread.initSysCalls(AllowedSysCalls.getAllowedClasses());
    }

    private void addShellModules() {
        ShellCommandsFactory.registerShellModule(ShellBuiltinCommands.class);
        ShellCommandsFactory.registerShellModule(PythonShell.class);
        ShellCommandsFactory.registerShellModule(UserShellCommands.class);
    }
    public void stop() {
        synchronized (this) {
            notify();
        }
    }
    private void postInitialization() {
        synchronized (this) {
            try {
                wait();
            } catch (InterruptedException e) {
                e.printStackTrace();
            }
        }
    }

    @Override
    public void run() {
        // System.out.println("Starting services");
        logger.info("Starting services");
        this.startServices();
    }

    public boolean test (String tt) {
       return false;
    }
}
