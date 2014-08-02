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

package net.es.enos.esnet;

import net.es.lookup.records.Network.ServiceRecord;
import org.codehaus.jackson.annotate.JsonIgnore;

import java.util.LinkedList;
import java.util.List;

/**
 * The object representation of a ServiceRecord in sLS.
 * Created by bmah on 7/3/14.
 */
public class ESnetPerfSONARService {

    // Service info
    private String serviceName;
    private String serviceType;
    private ESnetPerfSONARHost serviceHost;
    private List<String> serviceLocator;
    private String serviceVersion;
    private String eventTypes;

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

    public String getServiceName() {
        return serviceName;
    }

    public void setServiceName(String serviceName) {
        this.serviceName = serviceName;
    }

    public String getServiceType() {
        return serviceType;
    }

    public void setServiceType(String serviceType) {
        this.serviceType = serviceType;
    }

    public ESnetPerfSONARHost getServiceHost() {
        return serviceHost;
    }

    public void setServiceHost(ESnetPerfSONARHost serviceHost) {
        this.serviceHost = serviceHost;
    }

    public List<String> getServiceLocator() {
        return serviceLocator;
    }

    public void setServiceLocator(List<String> serviceLocator) {
        this.serviceLocator = serviceLocator;
    }

    public String getServiceVersion() {
        return serviceVersion;
    }

    public void setServiceVersion(String serviceVersion) {
        this.serviceVersion = serviceVersion;
    }

    public String getEventTypes() {
        return eventTypes;
    }

    public void setEventTypes(String eventTypes) {
        this.eventTypes = eventTypes;
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

    public ESnetPerfSONARService() {
        domains = new LinkedList<String>();
        communities = new LinkedList<String>();
    }

    public static final ESnetPerfSONARService parseServiceRecord(ServiceRecord serviceRecord) {

        ESnetPerfSONARService s = new ESnetPerfSONARService();

        // Grab members from the sLS ServiceRecord
        s.setServiceName(serviceRecord.getServiceName());
        s.setServiceType(serviceRecord.getServiceType());
        s.setServiceVersion(serviceRecord.getServiceVersion());

        // s.setServiceHost();
        s.setServiceLocator(serviceRecord.getServiceLocator());
        s.setEventTypes(serviceRecord.getEventTypes());

        s.setSiteName(serviceRecord.getSiteName());
        s.setCity(serviceRecord.getCity());
        s.setState(serviceRecord.getState());
        s.setCountry(serviceRecord.getCountry());
        s.setZipcode(serviceRecord.getZipcode());
        s.setDomains(serviceRecord.getDomains());
        s.setCommunities(serviceRecord.getCommunities());
        s.setUri(serviceRecord.getURI());
        // s.setQueryServer();

        return s;
    }
}
