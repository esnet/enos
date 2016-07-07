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

import com.google.common.base.Strings;
import java.io.IOException;
import java.util.Dictionary;
import java.util.Hashtable;
import org.osgi.framework.BundleContext;
import org.osgi.framework.FrameworkUtil;
import org.osgi.framework.ServiceReference;
import org.osgi.service.cm.ConfigurationAdmin;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 *
 * @author hacksaw
 */
public class Configuration {
    private final Logger logger = LoggerFactory.getLogger(getClass());
    public final static String PID = "net.es.enos.swagger.config";

    // Last resort defaults.
    public final static String DEFAULT_HOST = "localhost";
    public final static String DEFAULT_PORT = "8181";
    public final static String DEFAULT_PATH = "/services";

    // Swagger configuration property keys.
    public final static String KEY_BASEPATH = "swagger.basePath";
    public final static String KEY_HOST = "swagger.host";
    public final static String KEY_TITLE = "swagger.info.title";
    public final static String KEY_DESCRIPTION = "swagger.info.description";
    public final static String KEY_VERSION = "swagger.info.version";
    public final static String KEY_TERMSOFSERVICE = "swagger.info.termsOfService";
    public final static String KEY_CONTACTNAME = "swagger.info.contact.name";
    public final static String KEY_CONTACTURL = "swagger.info.contact.url";
    public final static String KEY_CONTACTEMAIL = "swagger.info.contact.email";
    public final static String KEY_LICENSENAME = "swagger.info.license.name";
    public final static String KEY_LICENSEURL = "swagger.info.license.url";

    // Configuration values.
    private String basePath;
    private String host;
    private String title;
    private String description;
    private String version;
    private String termsOfService;
    private String contactName;
    private String contactURL;
    private String contactEmail;
    private String licenseName;
    private String licenseURL;

    public Configuration() {

    }

    public void refresh() {
        logger.info("net.es.enos.swagger.Configuration refresh, basePath=" + basePath);

        BundleContext bundleContext = FrameworkUtil.getBundle(this.getClass()).getBundleContext();
        ServiceReference reference = bundleContext.getServiceReference(ConfigurationAdmin.class.getName());
        ConfigurationAdmin configAdmin = (ConfigurationAdmin) bundleContext.getService(reference);

        // Get the swagger configuration to verify it exists.
        org.osgi.service.cm.Configuration swagger;
        try {
            swagger = configAdmin.getConfiguration("com.eclipsesource.jaxrs.swagger.config");
        } catch (IOException ex) {
            logger.error("Could not read com.eclipsesource.jaxrs.swagger.config configuration", ex);
            bundleContext.ungetService(reference);
            return;
        }

        Dictionary<String, Object> properties = swagger.getProperties();

        // if null, the configuration is new.
        if (properties == null) {
            properties = new Hashtable();
            logger.info("enos-swagger: creating a new configuration.");
        }

        // We are considered the master of the swagger config to overwrite
        // the com.eclipsesource.jaxrs.swagger.config version.
        properties.put(KEY_HOST, Strings.isNullOrEmpty(host) ? getHost(configAdmin) : host);
        properties.put(KEY_BASEPATH, Strings.isNullOrEmpty(basePath) ? getPath(configAdmin) : basePath);

        if (!Strings.isNullOrEmpty(title)) {
            properties.put(KEY_TITLE, title);
        }

        if (!Strings.isNullOrEmpty(description)) {
            properties.put(KEY_DESCRIPTION, description);
        }

        if (!Strings.isNullOrEmpty(version)) {
            properties.put(KEY_VERSION, version);
        }

        if (!Strings.isNullOrEmpty(termsOfService)) {
            properties.put(KEY_TERMSOFSERVICE, termsOfService);
        }

        if (!Strings.isNullOrEmpty(contactName)) {
            properties.put(KEY_CONTACTNAME, contactName);
        }

        if (!Strings.isNullOrEmpty(contactURL)) {
            properties.put(KEY_CONTACTURL, contactURL);
        }

        if (!Strings.isNullOrEmpty(contactEmail)) {
            properties.put(KEY_CONTACTEMAIL, contactEmail);
        }

        if (!Strings.isNullOrEmpty(licenseName)) {
            properties.put(KEY_LICENSENAME, licenseName);
        }

        if (!Strings.isNullOrEmpty(licenseURL)) {
            properties.put(KEY_LICENSEURL, licenseURL);
        }

        try {
            swagger.update(properties);
        } catch (IOException ex) {
            logger.error("Could not update com.eclipsesource.jaxrs.swagger.config configuration", ex);
        }

        // We are done with the configuration service.
        bundleContext.ungetService(reference);
    }

    private String getProperty(Dictionary<String, Object> properties, String key, String defaultValue) {
        if (properties == null) {
            return defaultValue;
        }

        Object value = properties.get(key);
        if (value == null || !(value instanceof String)) {
            return defaultValue;
        }

        String vstring = (String) value;
        if (vstring.isEmpty()) {
            return defaultValue;
        }

        return vstring;
    }

    private String getHost(ConfigurationAdmin configAdmin) {
        String ahost;
        String port;

        // Get the web service configuration so we can properly set the http port.
        try {
            org.osgi.service.cm.Configuration http = configAdmin.getConfiguration("org.ops4j.pax.web");
            Dictionary<String, Object> httpProperties = http.getProperties();
            ahost = getProperty(httpProperties, "org.ops4j.pax.web.listening.addresses", DEFAULT_HOST);
            port = getProperty(httpProperties, "org.osgi.service.http.port", DEFAULT_PORT);
        } catch (IOException ex) {
            logger.error("Could not read org.ops4j.pax.web configuration", ex);
            ahost = DEFAULT_HOST;
            port = DEFAULT_PORT;
        }

        String hp = ahost + ":" + port;
        logger.info("enos-swagger: bound to http service " + hp);
        return hp;
    }

    private String getPath(ConfigurationAdmin configAdmin) {
        String root;

        // Get the relative path to our swagger managed services.
        try {
            org.osgi.service.cm.Configuration jaxrs = configAdmin.getConfiguration("com.eclipsesource.jaxrs.connector");
            Dictionary<String, Object> jaxrsProperties = jaxrs.getProperties();
            root = getProperty(jaxrsProperties, "root", DEFAULT_PATH);
        } catch (IOException ex) {
            logger.error("Could not read com.eclipsesource.jaxrs.connector configuration", ex);
            root = DEFAULT_PATH;
        }

        logger.info("enos-swagger: bound REST services to basePath " + root);
        return root;
    }

    /**
     * @return the basePath
     */
    public String getBasePath() {
        return basePath;
    }

    /**
     * @param basePath the basePath to set
     */
    public void setBasePath(String basePath) {
        this.basePath = basePath;
    }

    /**
     * @return the host
     */
    public String getHost() {
        return host;
    }

    /**
     * @param host the host to set
     */
    public void setHost(String host) {
        this.host = host;
    }

    /**
     * @return the title
     */
    public String getTitle() {
        return title;
    }

    /**
     * @param title the title to set
     */
    public void setTitle(String title) {
        this.title = title;
    }

    /**
     * @return the description
     */
    public String getDescription() {
        return description;
    }

    /**
     * @param description the description to set
     */
    public void setDescription(String description) {
        this.description = description;
    }

    /**
     * @return the version
     */
    public String getVersion() {
        return version;
    }

    /**
     * @param version the version to set
     */
    public void setVersion(String version) {
        this.version = version;
    }

    /**
     * @return the termsOfService
     */
    public String getTermsOfService() {
        return termsOfService;
    }

    /**
     * @param termsOfService the termsOfService to set
     */
    public void setTermsOfService(String termsOfService) {
        this.termsOfService = termsOfService;
    }

    /**
     * @return the contactName
     */
    public String getContactName() {
        return contactName;
    }

    /**
     * @param contactName the contactName to set
     */
    public void setContactName(String contactName) {
        this.contactName = contactName;
    }

    /**
     * @return the contactURL
     */
    public String getContactURL() {
        return contactURL;
    }

    /**
     * @param contactURL the contactURL to set
     */
    public void setContactURL(String contactURL) {
        this.contactURL = contactURL;
    }

    /**
     * @return the contactEmail
     */
    public String getContactEmail() {
        return contactEmail;
    }

    /**
     * @param contactEmail the contactEmail to set
     */
    public void setContactEmail(String contactEmail) {
        this.contactEmail = contactEmail;
    }

    /**
     * @return the licenseName
     */
    public String getLicenseName() {
        return licenseName;
    }

    /**
     * @param licenseName the licenseName to set
     */
    public void setLicenseName(String licenseName) {
        this.licenseName = licenseName;
    }

    /**
     * @return the licenseURL
     */
    public String getLicenseURL() {
        return licenseURL;
    }

    /**
     * @param licenseURL the licenseURL to set
     */
    public void setLicenseURL(String licenseURL) {
        this.licenseURL = licenseURL;
    }
}
