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

import net.es.enos.esnet.ESnetHost;
import net.es.lookup.client.QueryClient;
import net.es.lookup.client.SimpleLS;
import net.es.lookup.common.ReservedValues;
import net.es.lookup.queries.Network.HostQuery;
import net.es.lookup.queries.Query;
import net.es.lookup.records.Network.HostRecord;
import net.es.lookup.records.Record;
import org.codehaus.jackson.map.ObjectMapper;
import org.codehaus.jackson.type.TypeReference;
import org.codehaus.jettison.json.JSONObject;
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

        if ((conf == null) || (conf.getHosts().length < 1)) {
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
     * Get all of the hosts
     */
    public List<ESnetHost> getHosts() {
        List<ESnetHost> hosts = new ArrayList<ESnetHost>(); // for now try to get all the hostnames

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

                    ESnetHost eh = ESnetHost.parseHostRecord((HostRecord) r);
                    hosts.add(eh);

                    logger.debug("Host {}", eh.getId());
                }
            }
            catch (Exception e) {
                e.printStackTrace();
            }
        }

        return hosts;
    }

}

