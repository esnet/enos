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

import net.es.enos.api.Port;
import net.es.lookup.common.exception.RecordException;
import net.es.lookup.records.Network.InterfaceRecord;
import org.codehaus.jackson.annotate.JsonIgnore;

import java.net.InetAddress;
import java.util.LinkedList;
import java.util.List;

/**
 * Created by bmah on 6/30/14.
 */
public class ESnetPerfSONARInterface extends Port {

    private List<InetAddress> addresses;
    private String ifName;
    private int capacity;
    private String mac;
    private int mtu;

    @JsonIgnore
    private String queryServer; // which sLS server did this record come from?

    public List<InetAddress> getAddresses() {
        return addresses;
    }

    public void setAddresses(List<InetAddress> addresses) {
        this.addresses = addresses;
    }

    public String getIfName() {
        return ifName;
    }

    public void setIfName(String ifName) {
        this.ifName = ifName;
    }

    public int getCapacity() {
        return capacity;
    }

    public void setCapacity(int capacity) {
        this.capacity = capacity;
    }

    public String getMac() {
        return mac;
    }

    public void setMac(String mac) {
        this.mac = mac;
    }

    public int getMtu() {
        return mtu;
    }

    public void setMtu(int mtu) {
        this.mtu = mtu;
    }

    public ESnetPerfSONARInterface() {
        addresses = new LinkedList<InetAddress>();
    }

    public String getQueryServer() {
        return queryServer;
    }

    public void setQueryServer(String queryServer) {
        this.queryServer = queryServer;
    }

    public static final ESnetPerfSONARInterface parseInterfaceRecord(InterfaceRecord intf) {
        ESnetPerfSONARInterface esi = new ESnetPerfSONARInterface();

        try {
            esi.setAddresses(intf.getAddresses());
        }
        catch (RecordException e) {
            esi.getAddresses().clear();
        }
        esi.setIfName(intf.getInterfaceName());
        esi.setCapacity(intf.getCapacity());
        esi.setMac(intf.getMacAddress());
        esi.setMtu(intf.getMtu());

        return esi;
    }
}
