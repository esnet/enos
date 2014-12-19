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

package net.es.enos.perfsonar;

import net.es.netshell.api.Host;
import net.es.lookup.records.Network.HostRecord;
import org.codehaus.jackson.annotate.JsonIgnore;

import java.util.LinkedList;
import java.util.List;

/**
 * Created by bmah on 6/19/14.
 */
public class PerfSONARHost extends Host {

    private String id;

    // Hardware info
    private List<String> hostNames;
    private double hostMemory;
    private double hostProcessorSpeed;
    private int hostProcessorCount;
    private int hostProcessorCore;
    private String osName;
    private String osVersion; // uname -r
    private String osKernel; // uname -s
    private List<String> addresses;
    private List<PerfSONARInterface> interfaces;
    private List<String> interfaceUris;
    private List<PerfSONARService> services;

    // TCP info
    private String tcpCongestionAlgorithm;
    private int sendTcpMaxBuffer;
    private int receiveTcpMaxBuffer;
    private int sendTcpAutotuneMaxBuffer;
    private int receiveTcpAutotuneMaxBuffer;
    private int tcpMaxBacklog;

    // Location info
    private String siteName;
    private String city;
    private String state;
    private String country;
    private String zipcode;
    private double latitude;
    private double longitude;

    // Group info
    private List<String> domains;
    private List<String> communities;

    // Other metadata
    @JsonIgnore
    private String queryServer; // which sLS server did this record come from?
    private String uri;

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public List<String> getHostNames() {
        return hostNames;
    }

    public void setHostNames(List<String> hostNames) {
        this.hostNames = hostNames;
    }

    public double getHostMemory() {
        return hostMemory;
    }

    public void setHostMemory(double hostMemory) {
        this.hostMemory = hostMemory;
    }

    public double getHostProcessorSpeed() {
        return hostProcessorSpeed;
    }

    public void setHostProcessorSpeed(double hostProcessorSpeed) {
        this.hostProcessorSpeed = hostProcessorSpeed;
    }

    public int getHostProcessorCount() {
        return hostProcessorCount;
    }

    public void setHostProcessorCount(int hostProcessorCount) {
        this.hostProcessorCount = hostProcessorCount;
    }

    public int getHostProcessorCore() {
        return hostProcessorCore;
    }

    public void setHostProcessorCore(int hostProcessorCore) {
        this.hostProcessorCore = hostProcessorCore;
    }

    public String getOsName() {
        return osName;
    }

    public void setOsName(String osName) {
        this.osName = osName;
    }

    public String getOsVersion() {
        return osVersion;
    }

    public void setOsVersion(String osVersion) {
        this.osVersion = osVersion;
    }

    public String getOsKernel() {
        return osKernel;
    }

    public void setOsKernel(String osKernel) {
        this.osKernel = osKernel;
    }

    public List<String> getAddresses() {
        return addresses;
    }

    public void setAddresses(List<String> addresses) {
        this.addresses = addresses;
    }

    public List<PerfSONARInterface> getInterfaces() {
        return interfaces;
    }

    public void setInterfaces(List<PerfSONARInterface> interfaces) {
        this.interfaces = interfaces;
    }

    public List<String> getInterfaceUris() {
        return interfaceUris;
    }

    public void setInterfaceUris(List<String> interfaceUris) {
        this.interfaceUris = interfaceUris;
    }

    public List<PerfSONARService> getServices() {
        return services;
    }

    public void setServices(List<PerfSONARService> services) {
        this.services = services;
    }

    public String getTcpCongestionAlgorithm() {
        return tcpCongestionAlgorithm;
    }

    public void setTcpCongestionAlgorithm(String tcpCongestionAlgorithm) {
        this.tcpCongestionAlgorithm = tcpCongestionAlgorithm;
    }

    public int getSendTcpMaxBuffer() {
        return sendTcpMaxBuffer;
    }

    public void setSendTcpMaxBuffer(int sendTcpMaxBuffer) {
        this.sendTcpMaxBuffer = sendTcpMaxBuffer;
    }

    public int getReceiveTcpMaxBuffer() {
        return receiveTcpMaxBuffer;
    }

    public void setReceiveTcpMaxBuffer(int receiveTcpMaxBuffer) {
        this.receiveTcpMaxBuffer = receiveTcpMaxBuffer;
    }

    public int getSendTcpAutotuneMaxBuffer() {
        return sendTcpAutotuneMaxBuffer;
    }

    public void setSendTcpAutotuneMaxBuffer(int sendTcpAutotuneMaxBuffer) {
        this.sendTcpAutotuneMaxBuffer = sendTcpAutotuneMaxBuffer;
    }

    public int getReceiveTcpAutotuneMaxBuffer() {
        return receiveTcpAutotuneMaxBuffer;
    }

    public void setReceiveTcpAutotuneMaxBuffer(int receiveTcpAutotuneMaxBuffer) {
        this.receiveTcpAutotuneMaxBuffer = receiveTcpAutotuneMaxBuffer;
    }

    public int getTcpMaxBacklog() {
        return tcpMaxBacklog;
    }

    public void setTcpMaxBacklog(int tcpMaxBacklog) {
        this.tcpMaxBacklog = tcpMaxBacklog;
    }

    public String getSiteName() {
        return siteName;
    }

    public void setSiteName(String siteName) {
        this.siteName = siteName;
    }

    public String getCity() {
        return city;
    }

    public void setCity(String city) {
        this.city = city;
    }

    public String getState() {
        return state;
    }

    public void setState(String state) {
        this.state = state;
    }

    public String getCountry() {
        return country;
    }

    public void setCountry(String country) {
        this.country = country;
    }

    public String getZipcode() {
        return zipcode;
    }

    public void setZipcode(String zipcode) {
        this.zipcode = zipcode;
    }

    public double getLatitude() {
        return latitude;
    }

    public void setLatitude(double latitude) {
        this.latitude = latitude;
    }

    public double getLongitude() {
        return longitude;
    }

    public void setLongitude(double longitude) {
        this.longitude = longitude;
    }

    public List<String> getDomains() {
        return domains;
    }

    public void setDomains(List<String> domains) {
        this.domains = domains;
    }

    public List<String> getCommunities() {
        return communities;
    }

    public void setCommunities(List<String> communities) {
        this.communities = communities;
    }

    public String getQueryServer() {
        return queryServer;
    }

    public void setQueryServer(String queryServer) {
        this.queryServer = queryServer;
    }

    public String getUri() {
        return uri;
    }

    public void setUri(String uri) {
        this.uri = uri;
    }

    public PerfSONARHost() {
        hostNames = new LinkedList<String>();
        addresses = new LinkedList<String>();
        domains = new LinkedList<String>();
        communities = new LinkedList<String>();
        interfaceUris = new LinkedList<String>();
    }

    public static final PerfSONARHost parseHostRecord(HostRecord hostRecord) {

        PerfSONARHost h = new PerfSONARHost();

        // Pull some stuff out of the sLS HostRecord
        h.setHostMemory(hostRecord.getHostMemory());
        h.setHostProcessorSpeed(hostRecord.getHostProcessorSpeed());
        h.setHostProcessorCount(hostRecord.getHostProcessorCount());
        h.setHostProcessorCore(hostRecord.getHostProcessorCore());
        h.setOsName(hostRecord.getOSName());
        h.setOsVersion(hostRecord.getOSVersion());
        h.setOsKernel(hostRecord.getOSKernel());
        h.setLatitude(hostRecord.getLatitude());
        h.setLongitude(hostRecord.getLongitude());
        h.setSiteName(hostRecord.getSiteName());
        for (String hostname : hostRecord.getHostName()) {
            h.getHostNames().add(hostname);
        }
        for (String intf : hostRecord.getInterfaces()) {
            h.getInterfaceUris().add(intf);
        }
        h.setTcpCongestionAlgorithm(hostRecord.getTcpCongestionAlgorithm());
        h.setSendTcpMaxBuffer(hostRecord.getSendTcpMaxBuffer());
        h.setReceiveTcpMaxBuffer(hostRecord.getReceiveTcpMaxBuffer());
        h.setSendTcpAutotuneMaxBuffer(hostRecord.getSendTcpAutotuneMaxBuffer());
        h.setReceiveTcpAutotuneMaxBuffer(hostRecord.getReceiveTcpAutotuneMaxBuffer());
        h.setTcpMaxBacklog(hostRecord.getTcpMaxBackLog());
        h.setSiteName(hostRecord.getSiteName());
        h.setCity(hostRecord.getCity());
        h.setState(hostRecord.getState());
        h.setCountry(hostRecord.getCountry());
        h.setZipcode(hostRecord.getZipcode());
        h.setDomains(hostRecord.getDomains());
        h.setCommunities(hostRecord.getCommunities());
        h.setUri(hostRecord.getURI());

        // Need to come up with an identifier for the host.  By convention we'll take the first hostname
        // and chop the domain parts off of it.  This part is definitely ESnet specific.
        String fqdn = h.getHostNames().get(0);
        String hid = fqdn;
        if (fqdn.indexOf('.') != -1) {
            hid = fqdn.substring(0, fqdn.indexOf('.'));
        }
        h.setId(hid);

        return h;

    }

}
