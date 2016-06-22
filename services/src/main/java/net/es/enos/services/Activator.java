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

import net.es.enos.services.example.ExampleService;
import org.osgi.framework.BundleActivator;
import org.osgi.framework.BundleContext;
import org.osgi.framework.ServiceRegistration;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;


/**
 * Activator class for the example enos-services module.
 */

 public class Activator implements BundleActivator {
    private final static Logger logger = LoggerFactory.getLogger(Activator.class);
    private ServiceRegistration serviceRegistration;

    @Override
    public void start(BundleContext context) throws Exception {
        // Register the example service with the OSGi registry so the JAX-RS
        // connector can discover our annotated interfaces.  This example
        // registers a singleton service.  A factory could be used to generate
        // a service instance be invoke if desired.
        ExampleService exampleService = new ExampleService();
        serviceRegistration = context.registerService(ExampleService.class.getName(),
                exampleService, null);
        logger.info("enos-services: started");
    }

    @Override
    public void stop(BundleContext context) throws Exception {
        // We need to unregister any services and listeners.
        serviceRegistration.unregister();
        logger.info("enos-services: stopped");
    }
 }
