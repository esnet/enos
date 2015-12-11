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

/**
 * Created by lomax on 7/2/14.
 */


/**
 * {"leaf": false,
 * "children": [{"ifSpeed": 1000000000, "leaf": false, "name": "ge-9/0/1", "descr": "lbl-mr2->perfsonar-test:ge:site-ex:show:na",
 * "ifAlias": "lbl-mr2->perfsonar-test:ge:site-ex:show:na", "device_uri": "/snmp/lbl-mr2", "ipAddr": null, "uri": "/snmp/lbl-mr2/interface/ge-9_0_1",
 * "ifHighSpeed": 1000, " ": "ge-9/0/1", "begin_time": 1242128123, "ifIndex": 151, "speed": 1000000000, "end_time": 2147483647},
 */
public class ESnetSNMPInterface extends Port {
    private boolean leaf;
    private String ifSpeed;
    private String descr;
    private String ifAlias;
    private String device_uri;
    private String ipAddr;
    private String ifHighSpeed;
    private String uri;
    private String ifDescr;
    private String begin_time;
    private String ifIndex;
    private String speed;
    private String end_time;

    public ESnetSNMPInterface(Port port) {
        super(port);
    }
    public boolean isLeaf() {
        return leaf;
    }

    public void setLeaf(boolean leaf) {
        this.leaf = leaf;
    }

    public String getIfSpeed() {
        return ifSpeed;
    }

    public void setIfSpeed(String ifSpeed) {
        this.ifSpeed = ifSpeed;
    }

    public String getDescr() {
        return descr;
    }

    public void setDescr(String descr) {
        this.descr = descr;
    }

    public String getIfAlias() {
        return ifAlias;
    }

    public void setIfAlias(String ifAlias) {
        this.ifAlias = ifAlias;
    }

    public String getDevice_uri() {
        return device_uri;
    }

    public void setDevice_uri(String device_uri) {
        this.device_uri = device_uri;
    }

    public String getIpAddr() {
        return ipAddr;
    }

    public void setIpAddr(String ipAddr) {
        this.ipAddr = ipAddr;
    }

    public String getIfHighSpeed() {
        return ifHighSpeed;
    }

    public void setIfHighSpeed(String ifHighSpeed) {
        this.ifHighSpeed = ifHighSpeed;
    }

    public String getUri() {
        return uri;
    }

    public void setUri(String uri) {
        this.uri = uri;
    }

    public String getIfDescr() {
        return ifDescr;
    }

    public void setIfDescr(String ifDescr) {
        this.ifDescr = ifDescr;
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

    public String getSpeed() {
        return speed;
    }

    public void setSpeed(String speed) {
        this.speed = speed;
    }

    public String getEnd_time() {
        return end_time;
    }

    public void setEnd_time(String end_time) {
        this.end_time = end_time;
    }
}
