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
import java.util.HashMap;
import java.util.List;

/**
 * Created by lomax on 5/21/14.
 */
public class TopologyFactory extends Resource {
    public final static String TOPOLOGY_FACTORY_DIR = "topologies/factory";
    public final static String LOCAL_LAYER1 = "localLayer1";
    public final static String LOCAL_LAYER2 = "localLayer2";

    private List<TopologyProviderDescriptor> providers; // List of class name implementing topology providers
    private HashMap <String, TopologyProvider> topologyProviders = new HashMap<String,TopologyProvider>();
    private static TopologyFactory  instance;
    private static Object instanceLock = new Object();

    public TopologyFactory() throws IOException {
        // Initialize the topologies
        if (this.providers != null) {
            for (TopologyProviderDescriptor provider : this.providers) {
                try {
                    TopologyProvider topologyProvider =
                            (TopologyProvider) Class.forName(provider.getClassName()).newInstance();

                    this.topologyProviders.put(provider.getType(),topologyProvider);

                } catch (InstantiationException e) {
                    e.printStackTrace();
                } catch (IllegalAccessException e) {
                    e.printStackTrace();
                } catch (ClassNotFoundException e) {
                    e.printStackTrace();
                }
            }
        }
    }

    public TopologyProvider retrieveTopologyProvider (String type) {
        return this.topologyProviders.get(type);
    }

    public ListenableDirectedGraph retrieveTopology (String type) {
        return this.topologyProviders.get(type).retrieveTopology();
    }

    public static TopologyFactory instance() {
        synchronized (TopologyFactory.instanceLock) {
            if (TopologyFactory.instance == null) {
                try {
                    TopologyFactory.instance = (TopologyFactory) Resource.newResource(TopologyFactory.class,
                                                                                      TopologyFactory.TOPOLOGY_FACTORY_DIR);
                } catch (IOException e) {

                    throw new RuntimeException (e);
                } catch (InstantiationException e) {
                    throw new RuntimeException (e);
                }
            }

        }
        return TopologyFactory.instance;
    }
}
