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

import net.es.netshell.api.Port;
import net.es.lookup.common.exception.RecordException;
import net.es.lookup.records.Network.InterfaceRecord;
import org.codehaus.jackson.annotate.JsonIgnore;

import java.net.InetAddress;
import java.util.LinkedList;
import java.util.List;

/**
 * Created by bmah on 6/30/14.
 */
public class PerfSONARInterface extends Port {

    private List<InetAddress> addresses;
    private String ifName;
    private int capacity;
    private String mac;
    private int mtu;

    @JsonIgnore
    private String queryServer; // which sLS server did this record come from?
    private String uri;

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

    public PerfSONARInterface() {
        super();
        addresses = new LinkedList<InetAddress>();
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

    public static final PerfSONARInterface parseInterfaceRecord(InterfaceRecord intf) {
        PerfSONARInterface esi = new PerfSONARInterface();

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
        esi.setUri(intf.getURI());
        esi.setResourceName(intf.getInterfaceName());

        return esi;
    }
}
