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

/**
 * Created by lomax on 5/16/14.
 */

import net.es.netshell.api.Node;

import java.util.List;

public class ESnetNode extends Node implements Comparable<ESnetNode> {

    private String id;
    private String hostName;
    private String latitude;
    private String longitude;
    private String address;
    private List<ESnetPort> ports;
	public double width;
    private String name;
	public ESnetNode prev; // Store previous node when calculating max bandwidth
    private String type;

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
        this.setResourceName(id);
        // Hostname is not defined in topology. Build it
        this.hostName = ESnetTopology.idToName(id) + "@" + ESnetTopology.idToDomain(id);
    }

    public String getAddress() {
        return address;
    }

    public void setAddress(String address) {
        this.address = address;
    }

    public String getHostName() {
        return hostName;
    }

    public void setHostName(String hostName) {
        this.hostName = hostName;
    }

    public String getLatitude() {
        return latitude;
    }

    public void setLatitude(String latitude) {
        this.latitude = latitude;
    }

    public String getLongitude() {
        return longitude;
    }

    public void setLongitude(String longitude) {
        this.longitude = longitude;
    }

    public List<ESnetPort> getPorts() {
        return ports;
    }

    public void setPorts(List<ESnetPort> ports) {
        this.ports = ports;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public int compareTo(ESnetNode other)
	{
		return Double.compare(width, other.width);
	}

    @Override
    public String toString() {
	    return ESnetTopology.idToName(this.getId());
    }

    @Override
    protected Object clone() throws CloneNotSupportedException {
        return super.clone();
    }
}
