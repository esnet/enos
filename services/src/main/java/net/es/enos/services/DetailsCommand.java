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
import net.es.netshell.services.BundleVersionResource;
import net.es.netshell.services.BundleVersionService;
import org.apache.karaf.shell.commands.Argument;
import org.apache.karaf.shell.commands.Command;
import org.apache.karaf.shell.console.OsgiCommandSupport;
import org.osgi.framework.InvalidSyntaxException;
import org.osgi.framework.ServiceReference;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * An example karaf shell command using a defined JAX-RS service.
 *
 * See: https://karaf.apache.org/manual/latest-3.0.x/developers-guide/extending.html
 */

@Command(scope = "enos", name = "details", description="List detailed bundle and version information for specified bundle ID.")
public class DetailsCommand extends OsgiCommandSupport {
    private final Logger logger = LoggerFactory.getLogger(getClass());

    @Argument(index = 0, name = "ID",
            description = "Bundle idenitifer to retrieve details.",
            required = true, multiValued = false)
    String id = null;

    @Override
    protected Object doExecute() throws Exception {
        id = id.trim();

        try {
            Collection<ServiceReference<BundleVersionService>> serviceReferences = getBundleContext().getServiceReferences(BundleVersionService.class, null);
            for (ServiceReference<BundleVersionService> serviceRef : serviceReferences) {
                BundleVersionService service = getBundleContext().getService(serviceRef);
                BundleVersionResource version = service.getVersion();
                if (version.getId().equalsIgnoreCase(id)) {
                    System.out.println(version.toString());
                }
            }
        } catch (InvalidSyntaxException ex) {
            logger.error("Could not get OSGI service references", ex);
            System.err.println("Error: Could not get OSGI service reference.");
        }

        ungetServices();
        return null;
    }
}

