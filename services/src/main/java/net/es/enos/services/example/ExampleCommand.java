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
package net.es.enos.services.example;

import org.apache.karaf.shell.commands.Argument;
import org.apache.karaf.shell.commands.Command;
import org.apache.karaf.shell.console.OsgiCommandSupport;
import org.osgi.framework.ServiceReference;

/**
 * An example karaf shell command using a defined JAX-RS service.
 *
 * See: https://karaf.apache.org/manual/latest-3.0.x/developers-guide/extending.html
 */

@Command(scope = "test", name = "hello", description="Says hello")
public class ExampleCommand extends OsgiCommandSupport {

    @Argument(index = 0, name = "name",
            description = "The name that sends the greet.",
            required = true, multiValued = false)
    String name = null;

    @Override
    protected Object doExecute() throws Exception {
        // Lookup the example service reference.
        ServiceReference ref = getBundleContext().getServiceReference(ExampleService.class.getName());
        ExampleService exampleService =(ExampleService) bundleContext.getService(ref);

        if (exampleService != null) {
            ExampleResource sayHello = exampleService.sayHello(name);
            System.out.println(sayHello.getMessage());
        }
        else {
            System.err.println("ExampleCommand: could not lookup service!");
        }

        ungetServices();
        return null;
    }
}

