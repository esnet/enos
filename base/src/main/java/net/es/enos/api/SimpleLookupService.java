/*
 * Copyright (c) 2014, Regents of the University of California.
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 * 1. Redistributions of source code must retain the above copyright notice,
 * this list of conditions and the following disclaimer.
 *
 * 2. Redistributions in binary form must reproduce the above copyright notice,
 * this list of conditions and the following disclaimer in the documentation
 * and/or other materials provided with the distribution.
 *
 * 3. Neither the name of the copyright holder nor the names of its contributors
 * may be used to endorse or promote products derived from this software without
 * specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 * DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
 * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
 * CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
 * OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

package net.es.enos.api;

import net.es.enos.esnet.ESnetPerfSONARInterface;
import net.es.enos.esnet.ESnetPerfSONARHost;
import net.es.enos.esnet.ESnetPerfSONARService;
import net.es.lookup.client.QueryClient;
import net.es.lookup.client.SimpleLS;
import net.es.lookup.queries.Network.HostQuery;
import net.es.lookup.queries.Network.InterfaceQuery;
import net.es.lookup.queries.Network.ServiceQuery;
import net.es.lookup.records.Network.HostRecord;
import net.es.lookup.records.Network.InterfaceRecord;
import net.es.lookup.records.Network.ServiceRecord;
import net.es.lookup.records.Record;
import org.codehaus.jackson.map.ObjectMapper;
import org.codehaus.jackson.type.TypeReference;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.net.URI;
import java.net.URL;
import java.util.*;

/**
 * Simple Lookup Service client for ENOS
 * Created by bmah on 6/18/14.
 */
public class SimpleLookupService {

    static final String SLS_HOSTS_DEFAULT_URL = "http://ps1.es.net:8096/lookup/activehosts.json";

    static final Logger logger = LoggerFactory.getLogger(SimpleLookupService.class);

    private List<ESnetPerfSONARHost> allHosts = new LinkedList<ESnetPerfSONARHost>();
    public List<ESnetPerfSONARInterface> allInterfaces = new LinkedList<ESnetPerfSONARInterface>();

    private List<ESnetPerfSONARService> allServices = new LinkedList<ESnetPerfSONARService>();

    public List<ESnetPerfSONARHost> getAllHosts() {
        return allHosts;
    }

    public List<ESnetPerfSONARInterface> getAllInterfaces() {
        return allInterfaces;
    }

    public List<ESnetPerfSONARService> getAllServices() {
        return allServices;
    }

    public SimpleLookupService() {
        init();
    }

    /**
     * SLS Host
     * Corresponds to one record in the hosts array in activehosts.json.
     */
    public static class SlsHost {

        private int priority;
        private String locator;
        private String status;

        public int getPriority() {
            return priority;
        }

        public void setPriority(int priority) {
            this.priority = priority;
        }

        public String getLocator() {
            return locator;
        }

        public void setLocator(String locator) {
            this.locator = locator;
        }

        public String getStatus() {
            return status;
        }

        public void setStatus(String status) {
            this.status = status;
        }
    }

    /**
     * Object representation of the activehosts.json file.
     * Note:  Inner classes must be static for JSON deserialization to work, see
     * http://cowtowncoder.com/blog/archives/2010/08/entry_411.html.
     */
    public static class SlsActiveHosts {
        private SlsHost[] hosts;

        public SlsHost[] getHosts() {
            return hosts;
        }

        public void setHosts(SlsHost[] hosts) {
            this.hosts = hosts;
        }
    }

    private SlsActiveHosts conf;

    private void init() {

        try {
            // Get the set of SLS lookup servers and parse its JSON representation onto objects.
            ObjectMapper mapper = new ObjectMapper();
            conf = mapper.readValue(new URL(SLS_HOSTS_DEFAULT_URL), new TypeReference<SlsActiveHosts>() {
            });

        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    /**
     * Return the list of servers to query.  We need to perform queries across all of the
     * servers in this list to get a complete answer.
     * @return selected servers (null if we can't find anything)
     */
    public String [] getSlsLocators() {

        String [] locators = new String[conf.getHosts().length];

        if (conf.getHosts().length < 1) {
            return null;
        }
        // TODO:  Actually select something in a reasonable way.
        // TODO:  What if one of these hosts doesn't have active status?
        for (int i = 0; i < conf.getHosts().length; i++) {
            locators[i] = conf.getHosts()[i].getLocator();
        }
        return locators;
    }

    /**
     * Get all of the hosts and associated records
     *
     * TODO:  Can we do these in parallel somehow?
     */
    public List<ESnetPerfSONARHost> retrieveHosts() {

        allHosts = new ArrayList<ESnetPerfSONARHost>();
        allServices = new ArrayList<ESnetPerfSONARService>();

        if ((conf == null) || (conf.getHosts().length < 1)) {
            return null;
        }

        // Iterate over all of the sLS servers
        for (int i = 0; i < conf.getHosts().length; i++) {
            try {
                SimpleLS server = new SimpleLS(new URI(conf.getHosts()[i].getLocator()));
                QueryClient queryClient = new QueryClient(server);

                // Only get type=host records
                HostQuery query = new HostQuery();

                // ESnet specific stuff here...
                LinkedList<String> domains = new LinkedList<String>();
                domains.add("es.net");
                query.setDomains(domains);

                queryClient.setQuery(query);
                List<Record> results = null;
                results = queryClient.query();

                logger.debug("Retrieved {} results from {}{}", results.size(), conf.getHosts()[i].getLocator(), query.toURL().toString());

                for (Record r : results) {

                    ESnetPerfSONARHost eh = ESnetPerfSONARHost.parseHostRecord((HostRecord) r);
                    eh.setQueryServer(server.getHost()); // keep track of from where we got the HostRecord

                    // Query for the interface info.  Do this here so we can reuse our existing
                    // QueryClient object.
                    setInterfacesOnHostFromQueryServer(eh, queryClient);

                    // Query for services on this host.
                    setServicesOnHostFromQueryServer(eh, queryClient);

                    allHosts.add(eh);

                    logger.debug("Host {}", eh.getId());
                }
            }
            catch (Exception e) {
                e.printStackTrace();
            }
        }

        return allHosts;
    }

    /**
     * Get interfaces corresponding to a list of interface URIs.
     *
     * Note that this function cannot set the node member of the newly-constructed interfaces
     * because we don't know what host object these interfaces belong to.  The caller needs
     * to handle this.
     *
     * TODO:  Figure out if there's actually a use case for this function.
     */
    public List<ESnetPerfSONARInterface> retrieveInterfaces(List<String> uris) {
        List<ESnetPerfSONARInterface> intfs = new ArrayList<ESnetPerfSONARInterface>();

        if (conf.getHosts().length < 1) {
            return null;
        }

        // Iterate over all of the sLS servers
        for (int i = 0; i < conf.getHosts().length; i++) {
            try {
                SimpleLS server = new SimpleLS(new URI(conf.getHosts()[i].getLocator()));
                QueryClient queryClient = new QueryClient(server);

                // Only get type=host records
                InterfaceQuery query = new InterfaceQuery();

                // Query for specific records.
                query.setURI(uris);

                queryClient.setQuery(query);
                List<Record> results = null;
                results = queryClient.query();
                logger.debug("Retrieved {} results from {}{}", results.size(), conf.getHosts()[i].getLocator(), query.toURL().toString());

                for (Record r : results) {
                    ESnetPerfSONARInterface eh = ESnetPerfSONARInterface.parseInterfaceRecord((InterfaceRecord) r);
                    eh.setQueryServer(queryClient.getServer().getHost());
                    intfs.add(eh);
                    logger.debug("Interface {}", eh.getName());
                }
            }
            catch (Exception e) {
                e.printStackTrace();
            }
        }

        return intfs;

    }

    /**
     * Get interface records for a host, but we don't know which sLS query server
     * @param h
     */
    public void setInterfacesOnHost(ESnetPerfSONARHost h) {
        h.setInterfaces(retrieveInterfaces(h.getInterfaceUris()));
        for (ESnetPerfSONARInterface i : h.getInterfaces()) {
            i.setNode(h);
        }
    }

    /**
     * Get interface records for a host while we're still talking to the sLS query server
     * Designed for use from getHosts().
     */
    protected void setInterfacesOnHostFromQueryServer(ESnetPerfSONARHost h, QueryClient queryClient) {
        List<ESnetPerfSONARInterface> intfs = new LinkedList<ESnetPerfSONARInterface>();
        try {
            InterfaceQuery query = new InterfaceQuery();
            query.setURI(h.getInterfaceUris());

            queryClient.setQuery(query);
            List<Record> results = null;
            results = queryClient.query();
            logger.debug("Retrieved {} results from {}", results.size(), query.toURL().toString());

            for (Record r : results) {
                ESnetPerfSONARInterface eh = ESnetPerfSONARInterface.parseInterfaceRecord((InterfaceRecord) r);
                eh.setNode(h);
                eh.setQueryServer(queryClient.getServer().getHost());
                intfs.add(eh);
                allInterfaces.add(eh);
                logger.debug("Interface {}", eh.getName());
            }

            h.setInterfaces(intfs);
        }
        catch (Exception e) {
            e.printStackTrace();
        }
    }

    protected void setServicesOnHostFromQueryServer(ESnetPerfSONARHost h, QueryClient queryClient) {
        List<ESnetPerfSONARService> services = new LinkedList<ESnetPerfSONARService>();
        try {
            ServiceQuery query = new ServiceQuery();
            List<String> hlist = new LinkedList<String>();
            hlist.add(h.getUri());
            query.setHost(hlist);

            queryClient.setQuery(query);
            List<Record> results = null;
            results = queryClient.query();
            logger.debug("Retrieved {} results from {}", results.size(), query.toURL().toString());

            for (Record r : results) {
                ESnetPerfSONARService es = ESnetPerfSONARService.parseServiceRecord((ServiceRecord) r);
                es.setServiceHost(h);
                es.setQueryServer(queryClient.getServer().getHost());
                services.add(es);
                allServices.add(es);
                logger.debug("Service {}", es.getServiceName());
            }

            h.setServices(services);

        }
        catch (Exception e) {
            e.printStackTrace();
        }
    }
}

