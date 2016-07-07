/*
 * ESnet Network Operating System (ENOS) Copyright (c) 2016, The Regents
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
 *
 */
package net.es.enos.services;

import java.util.Collection;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import net.es.netshell.services.BundleVersionResource;

/**
 * A simple resource for the example service.
 */
public class VersionResource {
    private final Map<String, BundleVersionResource> bundles = new ConcurrentHashMap<>();

    public Map<String, BundleVersionResource> getMap() {
        return bundles;
    }

    public Collection<BundleVersionResource> values() {
        return bundles.values();
    }

    public BundleVersionResource put(String key, BundleVersionResource resource) {
        return bundles.put(key, resource);
    }

    public BundleVersionResource get(String key) {
        return bundles.get(key);
    }
}
