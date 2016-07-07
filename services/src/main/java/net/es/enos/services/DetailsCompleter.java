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
import java.util.List;
import net.es.netshell.services.BundleVersionResource;
import net.es.netshell.services.BundleVersionService;
import org.apache.karaf.shell.console.Completer;
import org.apache.karaf.shell.console.completer.StringsCompleter;
import org.osgi.framework.BundleContext;
import org.osgi.framework.FrameworkUtil;
import org.osgi.framework.InvalidSyntaxException;
import org.osgi.framework.ServiceReference;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * A very simple karaf command completer.
 *
 * See: https://karaf.apache.org/manual/latest-3.0.x/developers-guide/extending.html
 */
public class DetailsCompleter implements Completer {
    private final Logger logger = LoggerFactory.getLogger(getClass());
    private final BundleContext bundleContext;

    public DetailsCompleter() {
        bundleContext = FrameworkUtil.getBundle(this.getClass()).getBundleContext();
    }

    /**
     * @param buffer the beginning string typed by the user
     * @param cursor the position of the cursor
     * @param candidates the list of completions proposed to the user
     * @return
     */
    @Override
    public int complete(String buffer, int cursor, List candidates) {
        StringsCompleter delegate = new StringsCompleter();
        try {
            Collection<ServiceReference<BundleVersionService>> serviceReferences = bundleContext.getServiceReferences(BundleVersionService.class, null);
            for (ServiceReference<BundleVersionService> serviceRef : serviceReferences) {
                BundleVersionService service = bundleContext.getService(serviceRef);
                BundleVersionResource version = service.getVersion();
                delegate.getStrings().add(version.getId());
                bundleContext.ungetService(serviceRef);
            }
        } catch (InvalidSyntaxException ex) {
            logger.error("Could not get OSGI service references", ex);
        }

        return delegate.complete(buffer, cursor, candidates);
    }

}