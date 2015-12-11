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
package net.es.enos.esnet;

import net.es.netshell.api.Port;

import java.util.List;

public class ESnetPort extends Port {
    private String id;
    private String capacity;
    private String maximumReservableCapacity;
    private String minimumReservableCapacity;
    private String ifName;
    private String ifDescription;
    private String ipAddress;
    private String netmask;
    private String granularity;
    private String over;
    private List<ESnetLink> links;

    public ESnetPort (Port port) {
        super(port);
    }

    public ESnetPort() {
        super();
    }

    public String getGranularity() {
        return granularity;
    }

    public void setGranularity(String granularity) {
        this.granularity = granularity;
    }

    public void setLinks(List<ESnetLink> links) {
        this.links = links;
    }

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
        this.setResourceName(id);
    }

    public String getCapacity() {
        return capacity;
    }

    public void setCapacity(String capacity) {
        this.capacity = capacity;
    }

    public String getMaximumReservableCapacity() {
        return maximumReservableCapacity;
    }

    public void setMaximumReservableCapacity(String maximumReservableCapacity) {
        this.maximumReservableCapacity = maximumReservableCapacity;
    }

    public String getMinimumReservableCapacity() {
        return minimumReservableCapacity;
    }

    public void setMinimumReservableCapacity(String minimumReservableCapacity) {
        this.minimumReservableCapacity = minimumReservableCapacity;
    }

    public String getIfName() {
        return ifName;
    }

    public void setIfName(String ifName) {
        this.ifName = ifName;
    }

    public String getIfDescription() {
        return ifDescription;
    }

    public void setIfDescription(String ifDescription) {
        this.ifDescription = ifDescription;
    }

    public String getIpAddress() {
        return ipAddress;
    }

    public void setIpAddress(String ipAddress) {
        this.ipAddress = ipAddress;
    }

    public String getNetmask() {
        return netmask;
    }

    public void setNetmask(String netmask) {
        this.netmask = netmask;
    }

    public String getOver() {
        return over;
    }

    public void setOver(String over) {
        this.over = over;
    }

    public List<ESnetLink> getLinks() {
        return links;
    }

    @Override
    public String toString() {
        return this.getId();
    }
}
