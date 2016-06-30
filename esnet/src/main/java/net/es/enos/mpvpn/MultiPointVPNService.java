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
package net.es.enos.mpvpn;

import net.es.netshell.api.Resource;

import java.util.Map;

/**
 * Interface defining the MultiPoint VPN service.
 *
 */

public interface MultiPointVPNService {

    public void setTopologies (String pops, String inventory);

    public MultiPointVPN createVPN(String name);

    public boolean deleteVPN(String name);

    public MultiPointVPN getVPN(String name);

    public Map<String,Object> getSite(String name);

    public boolean addSite(MultiPointVPN vpn,Map<String,Object> site,String vlan);

    public boolean deleteSite(MultiPointVPN vpn,Map<String,Object> site);

    public Map<String,Object> getHost(String name);

    public boolean addPOP(MultiPointVPN vpn,Resource pop);

    public boolean removePOP(MultiPointVPN vpn,Resource pop);
}
