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
import javax.ws.rs.WebApplicationException;
import net.es.netshell.services.BundleVersionResource;
import net.es.netshell.services.BundleVersionService;
import org.apache.karaf.shell.commands.Command;
import org.apache.karaf.shell.commands.Option;
import org.apache.karaf.shell.console.OsgiCommandSupport;
import org.apache.karaf.shell.table.Col;
import org.apache.karaf.shell.table.ShellTable;
import org.osgi.framework.InvalidSyntaxException;
import org.osgi.framework.ServiceReference;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * An example karaf shell command using a defined JAX-RS service.
 *
 * See: https://karaf.apache.org/manual/latest-3.0.x/developers-guide/extending.html
 */

@Command(scope = "enos", name = "list", description="List active ENOS bundles and version information")
public class ListCommand extends OsgiCommandSupport {
    private final Logger logger = LoggerFactory.getLogger(getClass());

    @Option(name = "--no-format", description = "Disable table rendered output", required = false, multiValued = false)
    boolean noFormat;

    @Override
    protected Object doExecute() throws Exception {
        ShellTable table = new ShellTable();
        table.column(new Col("ID"));
        table.column(new Col("Bundle Name"));
        table.column(new Col("Build User"));
        table.column(new Col("Build Time"));
        table.column(new Col("Branch"));
        table.column(new Col("Dirty"));

        try {
            Collection<ServiceReference<BundleVersionService>> serviceReferences = getBundleContext().getServiceReferences(BundleVersionService.class, null);
            for (ServiceReference<BundleVersionService> serviceRef : serviceReferences) {
                BundleVersionService service = getBundleContext().getService(serviceRef);
                BundleVersionResource version = service.getVersion();
                table.addRow().addContent(
                        version.getId(), version.getBundleName(),
                        version.getBuildUserName(),
                        version.getBuildTime(), version.getBranch(), version.getDirty());
            }
        } catch (InvalidSyntaxException ex) {
            // Internal server error.
            logger.error("list: could not lookup version service!");
            throw new WebApplicationException(ex);
        }

        table.print(System.out, !noFormat);

        ungetServices();
        return null;
    }
}
