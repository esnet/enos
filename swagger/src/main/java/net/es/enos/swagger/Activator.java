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
package net.es.enos.swagger;

import java.util.Dictionary;
import java.util.Hashtable;
import org.osgi.framework.BundleActivator;
import org.osgi.framework.BundleContext;
import org.osgi.framework.ServiceReference;
import org.osgi.service.cm.Configuration;
import org.osgi.service.cm.ConfigurationAdmin;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * Activator for the swagger-ui bundle.
 *
 * @author hacksaw
 */
 public class Activator implements BundleActivator {
    private final static Logger logger = LoggerFactory.getLogger(Activator.class);
    private final static String TITLE = "ENOS Services API";

    /**
     * Make sure the swagger framework has been properly configured.
     *
     * @param context
     * @throws Exception
     */
    @Override
    public void start(BundleContext context) throws Exception {
        ServiceReference reference = context.getServiceReference(ConfigurationAdmin.class.getName());
        ConfigurationAdmin configAdmin = (ConfigurationAdmin) context.getService(reference);

        // Get the swagger configuration to verify it exists.
        Configuration swagger = configAdmin.getConfiguration("com.eclipsesource.jaxrs.swagger.config");
        Dictionary<String, Object> properties = swagger.getProperties();

        // if null, the configuration is new.
        if (properties == null) {
            properties = new Hashtable();
            logger.info("enos-swagger: creating a new configuration.");
        }

        // Populate the bare minimum.
        String title = getProperty(properties, "swagger.info.title", TITLE);
        logger.info("enos-swagger: starting configuration \"" + title + "\".");
        properties.put("swagger.info.title", title);

        // Get the web service configuration so we can properly set the http port.
        Configuration http = configAdmin.getConfiguration("org.ops4j.pax.web");
        Dictionary<String, Object> httpProperties = http.getProperties();

        String host = getProperty(httpProperties, "org.ops4j.pax.web.listening.addresses", "localhost");
        String port = getProperty(httpProperties, "org.osgi.service.http.port", "8181");
        String hp = host + ":" + port;
        properties.put("swagger.host", hp);

        logger.info("enos-swagger: bound to http service " + hp);

        // Lastly we set the relative path to our swagger managed services.
        Configuration jaxrs = configAdmin.getConfiguration("com.eclipsesource.jaxrs.connector");
        Dictionary<String, Object> jaxrsProperties = jaxrs.getProperties();
        String root = getProperty(jaxrsProperties, "root", "/services");

        logger.info("enos-swagger: bound REST services to basePath " + root);
        properties.put("swagger.basePath", root);

        swagger.update(properties);

        // We are done with the configuration service.
        context.ungetService(reference);
    }

    @Override
    public void stop(BundleContext context) throws Exception {
        logger.info("enos-swagger: stopped");
    }

    public String getProperty(Dictionary<String, Object> properties, String key, String defaultValue) {
        if (properties == null) {
            return defaultValue;
        }

        Object value = properties.get(key);
        if (value == null || !(value instanceof String)) {
            return defaultValue;
        }

        return (String) value;
    }
 }
