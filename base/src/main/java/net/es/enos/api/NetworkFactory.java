/*
 * Copyright (c) 2014, Regents of the University of California  All rights reserved.
 * Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
 * 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

package net.es.enos.api;

import org.jgrapht.graph.ListenableDirectedGraph;

import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;

/**
 * Created by lomax on 6/6/14.
 */
public class NetworkFactory extends Resource {
    public final static String NETWORK_FACTORY_DIR = "networks/factory";
    public final static String LOCAL_LAYER1 = "localLayer1";
    public final static String LOCAL_LAYER2 = "localLayer2";

    private List<NetworkProviderDescriptor> providers; // List of class name implementing network providers
    private HashMap<String, NetworkProvider> networkProviders = new HashMap<String,NetworkProvider>();
    private static NetworkFactory  instance;
    private static Object instanceLock = new Object();

    public NetworkFactory() throws IOException {

    }

    private void startProviders() {
        // Initialize the networks
        if (this.providers != null) {
            for (NetworkProviderDescriptor provider : this.providers) {
                this.startProvider(provider);
            }
        }
    }
    private void startProvider(NetworkProviderDescriptor provider) {
        try {
            NetworkProvider networkProvider =
                    (NetworkProvider) Class.forName(provider.getClassName()).newInstance();

            this.networkProviders.put(provider.getType(),networkProvider);

        } catch (InstantiationException e) {
            e.printStackTrace();
        } catch (IllegalAccessException e) {
            e.printStackTrace();
        } catch (ClassNotFoundException e) {
            e.printStackTrace();
        }
    }

    public NetworkProvider retrieveNetworkProvider (String type) {
        return this.networkProviders.get(type);
    }

    public static NetworkFactory instance() {
        synchronized (NetworkFactory.instanceLock) {
            if (NetworkFactory.instance == null) {
                try {
                    NetworkFactory.instance = (NetworkFactory) Resource.newResource(NetworkFactory.class,
                            NetworkFactory.NETWORK_FACTORY_DIR);
                    NetworkFactory.instance().startProviders();
                } catch (IOException e) {

                    throw new RuntimeException (e);
                } catch (InstantiationException e) {
                    throw new RuntimeException (e);
                }
            }

        }
        return NetworkFactory.instance;
    }

    public List<NetworkProviderDescriptor> getProviders() {
        return providers;
    }

    public void setProviders(List<NetworkProviderDescriptor> providers) {
        this.providers = providers;
    }

    public synchronized void registerNetworkProvider(String className, String type) throws IOException {
        if (this.providers == null) {
            this.providers = new ArrayList<NetworkProviderDescriptor>();
        }
        NetworkProviderDescriptor provider = new NetworkProviderDescriptor(className,type);
        this.providers.add(provider);
        this.save();
        this.startProvider(provider);
    }
}
