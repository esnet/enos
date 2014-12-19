/*
 * Copyright (c) 2014, Regents of the University of California  All rights reserved.
 * Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
 * 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
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

    public ESnetLink createReverseLink() {
        ESnetLink reverseLink = new ESnetLink();
        reverseLink.setName("reverse-" + this.getName());
        reverseLink.setId(this.getRemoteLinkId());
        reverseLink.setRemoteLinkId(this.getId());
        reverseLink.setEncodingType(this.getEncodingType());
        reverseLink.setInterfaceMTU(this.getInterfaceMTU());
        reverseLink.setSwitchingcapType(this.getSwitchingcapType());
        reverseLink.setNameType(this.getNameType());
        reverseLink.setTrafficEngineeringMetric(this.getTrafficEngineeringMetric());
        reverseLink.setType(this.getType());
        reverseLink.setVlanRangeAvailability(this.getVlanRangeAvailability());
        reverseLink.setVlanTranslation(this.isVlanTranslation());
        reverseLink.setDescription("reverse-" + this.getDescription());
        reverseLink.setParentResources(this.getParentResources());
        return reverseLink;
    }
}
