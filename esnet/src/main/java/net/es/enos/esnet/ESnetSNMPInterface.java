/*
 * Copyright (c) 2014, Regents of the University of California  All rights reserved.
 * Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
 * 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
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
