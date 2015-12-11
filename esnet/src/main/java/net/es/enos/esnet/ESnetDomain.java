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

import net.es.netshell.api.Domain;

import java.util.List;

/**
 * Created by lomax on 5/16/14.
 */
public class ESnetDomain extends Domain {
    private String Id;

    public List<ESnetNode> getNodes() {
        return nodes;
    }

    public ESnetDomain (Domain domain) {
        super(domain);
    }

    public ESnetDomain () {
        super();
    }

    public void setNodes(List<ESnetNode> nodes) {
        this.nodes = nodes;
    }

    public String getId() {
        return Id;
    }

    public void setId(String id) {
        Id = id;
        this.setResourceName(id);
    }

    List <ESnetNode>  nodes;

    @Override
    public String toString() {
        return super.toString();
    }

    @Override
    protected Object clone() throws CloneNotSupportedException {
        return super.clone();
    }

    @Override
    public boolean equals(Object obj) {
        if ( ! (obj instanceof ESnetDomain) ) {
            return false;
        }
        return ((ESnetDomain) obj).getId().equals(this.getId());
    }
}
