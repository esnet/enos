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

import java.util.List;
/**
 * Created by lomax on 7/10/14.
 */
public class ESnetSNMPInterfaceDetails {
    private String ifSpeed;
    private boolean leaf;
    private String device_uri;
    private String ifHighSpeed;
    private String ifDescr;
    private String ipAddr;
    private String uri;
    private String end_time;
    private String begin_time;
    private String ifIndex;
    private String ifAlias;
    private List<ESnetSNMPInterfaceStats> children;

    public String getIfSpeed() {
        return ifSpeed;
    }

    public void setIfSpeed(String ifSpeed) {
        this.ifSpeed = ifSpeed;
    }

    public boolean isLeaf() {
        return leaf;
    }

    public void setLeaf(boolean leaf) {
        this.leaf = leaf;
    }

    public String getDevice_uri() {
        return device_uri;
    }

    public void setDevice_uri(String device_uri) {
        this.device_uri = device_uri;
    }

    public String getIfHighSpeed() {
        return ifHighSpeed;
    }

    public void setIfHighSpeed(String ifHighSpeed) {
        this.ifHighSpeed = ifHighSpeed;
    }

    public String getIfDescr() {
        return ifDescr;
    }

    public void setIfDescr(String ifDescr) {
        this.ifDescr = ifDescr;
    }

    public String getIpAddr() {
        return ipAddr;
    }

    public void setIpAddr(String ipAddr) {
        this.ipAddr = ipAddr;
    }

    public String getUri() {
        return uri;
    }

    public void setUri(String uri) {
        this.uri = uri;
    }

    public String getEnd_time() {
        return end_time;
    }

    public void setEnd_time(String end_time) {
        this.end_time = end_time;
    }

    public String getBegin_time() {
        return begin_time;
    }

    public void setBegin_time(String begin_time) {
        this.begin_time = begin_time;
    }

    public String getIfIndex() {
        return ifIndex;
    }

    public void setIfIndex(String ifIndex) {
        this.ifIndex = ifIndex;
    }

    public String getIfAlias() {
        return ifAlias;
    }

    public void setIfAlias(String ifAlias) {
        this.ifAlias = ifAlias;
    }

    public List<ESnetSNMPInterfaceStats> getChildren() {
        return children;
    }

    public void setChildren(List<ESnetSNMPInterfaceStats> children) {
        this.children = children;
    }
}
