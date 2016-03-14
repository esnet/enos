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

import net.es.netshell.api.Link;
import net.es.netshell.boot.BootStrap;

/**
 * Created by lomax on 5/16/14.
 */

public class ESnetLink extends Link {
    private String id;
    private String type;
    private String remoteLinkId;
    private int trafficEngineeringMetric;
    private String switchingcapType;
    private String encodingType;
    private String vlanRangeAvailability;
    private String interfaceMTU;
    private boolean vlanTranslation;
    private String  nameType;
    private String  name;

    public ESnetLink (Link link) {
        super(link);
    }

    public ESnetLink() {
        super();
    }
    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getNameType() {
        return nameType;
    }

    public void setNameType(String nameType) {
        this.nameType = nameType;
    }

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
        this.setResourceName(id);
    }

    public String getType() {
        return type;
    }

    public void setType(String type) {
        this.type = type;
    }

    public String getRemoteLinkId() {
        return remoteLinkId;
    }

    public void setRemoteLinkId(String remoteLinkId) {
        this.remoteLinkId = remoteLinkId;
    }

    public int getTrafficEngineeringMetric() {
        return trafficEngineeringMetric;
    }

    public void setTrafficEngineeringMetric(int trafficEngineeringMetric) {
        this.trafficEngineeringMetric = trafficEngineeringMetric;
    }

    public String getSwitchingcapType() {
        return switchingcapType;
    }

    public void setSwitchingcapType(String switchingcapType) {
        this.switchingcapType = switchingcapType;
    }

    public String getEncodingType() {
        return encodingType;
    }

    public void setEncodingType(String encodingType) {
        this.encodingType = encodingType;
    }

    public String getVlanRangeAvailability() {
        return vlanRangeAvailability;
    }

    public void setVlanRangeAvailability(String vlanRangeAvailability) {
        this.vlanRangeAvailability = vlanRangeAvailability;
    }

    public String getInterfaceMTU() {
        return interfaceMTU;
    }

    public void setInterfaceMTU(String interfaceMTU) {
        this.interfaceMTU = interfaceMTU;
    }

    public boolean isVlanTranslation() {
        return vlanTranslation;
    }

    public void setVlanTranslation(boolean vlanTranslation) {
        this.vlanTranslation = vlanTranslation;
    }

    @Override
    public String toString() {
        return this.getId();
    }

    @Override
    protected Object clone() throws CloneNotSupportedException {
        return super.clone();
    }

    @Override
    public int hashCode() {
        return super.hashCode();
    }

    @Override
    public boolean equals(Object obj) {
        if ( ! (obj instanceof ESnetLink) ) {
            return false;
        }
        return ((ESnetLink) obj).getId().equals(this.getId());
    }

}
