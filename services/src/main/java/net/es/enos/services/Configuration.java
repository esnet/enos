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

import java.util.regex.Matcher;
import java.util.regex.Pattern;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * Configuration bean for the enos-services bundle.
 *
 * @author hacksaw
 */
public class Configuration {
    private final Logger logger = LoggerFactory.getLogger(getClass());

    // The process identifier for this configuration.
    public final static String PID = "net.es.enos.services.config";

    // Configuration key names.
    public final static String KEY_URITRANSFORM = "uriTransform";

    // Transform patterns.
    public final static Pattern PATTERN_FROM = Pattern.compile("\\(.*?\\|");
    public final static Pattern PATTERN_TO = Pattern.compile("\\|.*?\\)");
    public final static Pattern PATTERN_URI = Pattern.compile("^(https?|ftp|file)://[-a-zA-Z0-9+&@#/%?=~_|!:,.;]*[-a-zA-Z0-9+&@#/%=~_|]");

    // Configuration values.
    private String uriTransform;

    /**
     * Setter for uriTransform configuration option.
     *
     * @param uriTransform
     */
    public void setUriTransform(String uriTransform) {
        this.uriTransform = uriTransform;
    }

    /**
     * Getter for uriTransform configuration option.
     * @return
     */
    public String getUriTransform() {
        return this.uriTransform;
    }

    /**
     * Called whenever a configuration change has been completed.
     */
    public void refresh() {
        // We currently have no actions for this.
        logger.info(PID + " updated, uriTransform = " + this.uriTransform);
    }

    /**
     * Get the fromURI component of the transform.
     *
     * @return fromURI component of the transform.
     */
    public String getFromURI() {
        return getURI(PATTERN_FROM, uriTransform);
    }

    /**
     * Get the toURI component of the transform.
     *
     * @return toURI component of the transform.
     */
    public String getToURI() {
        return getURI(PATTERN_TO, uriTransform);
    }

    /**
     * Get the fromURI component from the specified transform.
     *
     * @param transform Transform from which to extract the fromURI.
     * @return
     */
    public static String getFromURI(String transform) {
        return getURI(PATTERN_FROM, transform);
    }

    /**
     * Get the toURI component from the specified transform.
     *
     * @param transform Transform from which to extract the toURI.
     * @return
     */
    public static String getToURI(String transform) {
        return getURI(PATTERN_TO, transform);
    }

    /**
     * Get the URI from the specified transform using the provided pattern.
     *
     * @param pattern Regex pattern to apply to transform.
     * @param transform Transform requiring URI extraction.
     * @return The extracted URI.
     */
    private static String getURI(Pattern pattern, String transform) {
        Matcher matcher = pattern.matcher(transform);

        if (matcher.find()) {
            String uri = matcher.group().subSequence(1, matcher.group().length()-1).toString().trim();
            Matcher mURI = PATTERN_URI.matcher(uri);
            if (mURI.find()) {
                return mURI.group();
            }
        }

        return null;
    }
}
