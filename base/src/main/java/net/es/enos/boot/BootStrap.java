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
import net.es.enos.api.ENOSException;
import net.es.enos.configuration.ENOSConfiguration;
import net.es.enos.configuration.GlobalConfiguration;
import net.es.enos.kernel.exec.KernelThread;
import net.es.enos.kernel.security.AllowedSysCalls;
import net.es.enos.kernel.security.KernelSecurityManager;
import net.es.enos.python.PythonShell;
import net.es.enos.shell.*;
import net.es.enos.sshd.SShd;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.slf4j.impl.SimpleLogger;

import java.io.File;
import java.io.IOException;
import java.nio.file.Path;
import java.nio.file.Paths;

/**
 * Created by lomax on 2/20/14.
 */
public final class BootStrap implements Runnable {
    private static BootStrap bootStrap = null;
    private String[] args = null;
    private SShd sshd = null;
    private static Thread thread;

    // We need to be sure the global configuration gets instantiated before the security manager,
    // because the former controls the initialization actions of the latter.
    private static final GlobalConfiguration masterConfiguration = ENOSConfiguration.getInstance().getGlobal();
    private static final KernelSecurityManager securityManager = new KernelSecurityManager();

    public final static Path rootPath = BootStrap.toRootRealPath();

    final private Logger logger = LoggerFactory.getLogger(BootStrap.class);

    static public Path toRootRealPath() {

        Path realPathName;
        try {
            if (masterConfiguration.getRootDirectory() != null) {
                realPathName = Paths.get(
                        new File(masterConfiguration.getRootDirectory()).getCanonicalFile().toString());
            } else {
                realPathName = Paths.get(new File(DefaultValues.ENOS_DEFAULT_ROOTDIR).getCanonicalFile().toString());
            }
        } catch (IOException e) {
            throw new RuntimeException(e.getMessage());
        }
        return realPathName;
    }

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
        logger.info("Current directory: {}", System.getProperty("user.dir"));
        BootStrap.thread.start();

    }
    public static void main(String[] args) throws ENOSException {

        final Logger logger = LoggerFactory.getLogger(BootStrap.class);

        // Set default logging level.
        // TODO:  This doesn't work.  It appears that setting the default logging level has no effect, possibly because all the various loggers have already been created?
        String defaultLogLevel = ENOSConfiguration.getInstance().getGlobal().getDefaultLogLevel();

        // Make sure the root directory exists and that we can write to it.
        File root = new File(BootStrap.rootPath.toString());
        if (root.isDirectory()) {
            if (root.canWrite()) {
                logger.info("Starting ENOS root= " + BootStrap.rootPath.toString());
            }
            else {
                logger.error("ENOS root directory " + BootStrap.rootPath + " not writable");
                throw new ENOSException("ENOS root directory " + BootStrap.rootPath + " not writable");
            }
        }
        else {
            logger.error("ENOS root directory " + BootStrap.rootPath + " not found");
            throw new ENOSException("ENOS root directory " + BootStrap.rootPath + " not found");
        }

        ENOSConfiguration enosConfiguration = ENOSConfiguration.getInstance();

        System.setProperty(SimpleLogger.DEFAULT_LOG_LEVEL_KEY, defaultLogLevel);

        BootStrap.bootStrap = new BootStrap(args);
        BootStrap.bootStrap.init();
        BootStrap.bootStrap.postInitialization();

        logger.info("Bootstrap thread exits");
    }

    private BootStrap (String[] args) {
        this.args = args;
    }


    public static BootStrap getBootStrap() {
        return BootStrap.bootStrap;
    }

    public void startServices() {

        // Start sshd if it's not disabled.
        int sshDisabled = ENOSConfiguration.getInstance().getGlobal().getSshDisabled();
        if (sshDisabled == 0) {
            this.sshd = SShd.getSshd();
            try {
                this.sshd.start();
            } catch (IOException e) {
                e.printStackTrace();
            }
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
        ShellCommandsFactory.registerShellModule(ContainerShellCommands.class);
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
        logger.info("Starting services");
        this.startServices();
    }

    public boolean test (String tt) {
       return false;
    }
}
