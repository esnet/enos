/*
 * ESnet Network Operating System (ENOS) Copyright (c) 2015, The Regents
 * of the University of California, through Lawrence Berkeley National
 * Laboratory (subject to receipt of any required approvals from the
 * U.S. Dept. of Energy).  All rights reserved.
 *
 * If you have questions about your rights to use or distribute this
 * software, please contact Berkeley Lab's Innovation & Partnerships
 * Office at IPO@lbl.gov.
 *
 * NOTICE.  This Software was developed under funding from the
 * U.S. Department of Energy and the U.S. Government consequently retains
 * certain rights. As such, the U.S. Government has been granted for
 * itself and others acting on its behalf a paid-up, nonexclusive,
 * irrevocable, worldwide license in the Software to reproduce,
 * distribute copies to the public, prepare derivative works, and perform
 * publicly and display publicly, and to permit other to do so.
 */
package net.es.enos.perfsonar;

import net.es.lookup.records.Network.ServiceRecord;
import org.codehaus.jackson.annotate.JsonIgnore;

import java.util.LinkedList;
import java.util.List;

/**
 * The object representation of a ServiceRecord in sLS.
 * Created by bmah on 7/3/14.
 */
public class PerfSONARService {

    // Service info
    private String serviceName;
    private String serviceType;
    private PerfSONARHost serviceHost;
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

    public PerfSONARHost getServiceHost() {
        return serviceHost;
    }

    public void setServiceHost(PerfSONARHost serviceHost) {
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

    public PerfSONARService() {
        domains = new LinkedList<String>();
        communities = new LinkedList<String>();
    }

    public static final PerfSONARService parseServiceRecord(ServiceRecord serviceRecord) {

        PerfSONARService s = new PerfSONARService();

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
