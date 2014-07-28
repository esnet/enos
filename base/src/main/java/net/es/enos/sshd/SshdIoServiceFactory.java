/*
 * Copyright (c) 2014, Regents of the University of California  All rights reserved.
 * Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
 * 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

package net.es.enos.sshd;

import net.es.enos.configuration.ENOSConfiguration;
import org.apache.mina.core.service.IoProcessor;
import org.apache.mina.core.service.SimpleIoProcessorPool;
import org.apache.mina.transport.socket.nio.NioProcessor;
import org.apache.mina.transport.socket.nio.NioSession;
import org.apache.sshd.common.FactoryManager;
import org.apache.sshd.common.future.CloseFuture;
import org.apache.sshd.common.io.IoAcceptor;
import org.apache.sshd.common.io.IoConnector;
import org.apache.sshd.common.io.IoHandler;
import org.apache.sshd.common.io.IoServiceFactory;
import org.apache.sshd.common.io.mina.MinaAcceptor;
import org.apache.sshd.common.io.mina.MinaConnector;
import org.apache.sshd.common.util.CloseableUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;

/**
 * SSHD IoServiceFactory. Mina's default two IoServiceFactory (mina and nio2) cannot be used due
 * a problem with the thread creation within the ThreadPool they use: the thread pool is configured
 * with no pre-started threads. Threads are then dynamically created when need. This cannot work
 * with ENOS security model since threads are set with a specific user ThreadGroup: once an Thread is
 * created for a user, it will not be able to be changed to another user and therefore creating SecurityExceptions
 * when another user is trying to log into ENOS and re-using threads from the pool.
 *
 * The current implementation creates a ThreadPool with a fixed size and immediately pre start
 * all of them while being privileged. This is not a perfect solution. Using a custom ThreadFactory
 * running with a background thread to create the thread would be better
 */
public class SshdIoServiceFactory implements IoServiceFactory {
    private final Logger logger = LoggerFactory.getLogger(SshdIoServiceFactory.class);
    private final FactoryManager manager;
    private final ExecutorService executor;
    private final IoProcessor<NioSession> ioProcessor;

    public static final int DEFAULT_NB_WORKER_THREADS = 20;

    public SshdIoServiceFactory(FactoryManager manager) {
        this.manager = manager;
        int nbOfWorkerThreads = ENOSConfiguration.getInstance().getGlobal().getSshNbWorkerThreads();
        if (nbOfWorkerThreads == 0) {
            nbOfWorkerThreads = DEFAULT_NB_WORKER_THREADS;
        }
        this.executor = Executors.newFixedThreadPool( nbOfWorkerThreads);
        ((ThreadPoolExecutor) this.executor).prestartAllCoreThreads();
        // Set a default reject handler
        ((ThreadPoolExecutor) this.executor).setRejectedExecutionHandler(new ThreadPoolExecutor.CallerRunsPolicy());
        this.ioProcessor = new SimpleIoProcessorPool<NioSession>(NioProcessor.class, getNioWorkers());
    }

    public IoConnector createConnector(IoHandler handler) {
        return new MinaConnector(manager, handler, ioProcessor);
    }

    public IoAcceptor createAcceptor(IoHandler handler) {
        return new MinaAcceptor(manager, handler, ioProcessor);
    }

    public CloseFuture close(boolean immediately) {
        try {
            executor.shutdownNow();
            executor.awaitTermination(5, TimeUnit.SECONDS);
        } catch (Exception e) {
            logger.debug("Exception caught while closing executor", e);
        }
        return CloseableUtils.closed();
    }

    public int getNioWorkers() {
        String nioWorkers = manager.getProperties().get(FactoryManager.NIO_WORKERS);
        if (nioWorkers != null && nioWorkers.length() > 0) {
            int nb = Integer.parseInt(nioWorkers);
            if (nb > 0) {
                return nb;
            }
        }
        return FactoryManager.DEFAULT_NIO_WORKERS;
    }
}
