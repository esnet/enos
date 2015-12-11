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

import net.es.netshell.api.Host;
import net.es.netshell.api.Link;
import net.es.netshell.api.Node;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;

/**
 * Created by lomax on 6/27/14.
 */
public class PerfSONARTester extends Host {
    private ArrayList<Link> links = new ArrayList<Link>();
    private HashMap<String,PerfSONARTester> testers = new HashMap<String,PerfSONARTester>();

    public PerfSONARTester() {}

    public PerfSONARTester(String name) {
        super(name);
    }

    public List<Link> getLinks() {
        return links;
    }

    public void setLinks(ArrayList<Link> links) {
        this.links = links;
    }

    public void addLink(Link link) {
        this.links.add(link);
    }


}
