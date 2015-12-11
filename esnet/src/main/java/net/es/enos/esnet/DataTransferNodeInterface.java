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
 * Created by lomax on 6/30/14.
 */
public class DataTransferNodeInterface {

    private String ifName;
    private String speed;
    private List<String> vlans;
    private List<DataTransferNodeLink> ifLinks;

    public String getIfName() {
        return ifName;
    }

    public void setIfName(String ifName) {
        this.ifName = ifName;
    }

    public String getSpeed() {
        return speed;
    }

    public void setSpeed(String speed) {
        this.speed = speed;
    }
    public List<DataTransferNodeLink> getIfLinks() {
        return ifLinks;
    }
    public void setIfLinks(List<DataTransferNodeLink> links) {
        this.ifLinks = links;
    }
    public void setVlans(List<String> vlans) {
        this.vlans = vlans;
    }
    public List<String> getVlans() {
        return vlans;
    }

}
