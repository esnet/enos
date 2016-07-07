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

import java.io.IOException;
import org.apache.log4j.xml.DOMConfigurator;
import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;
import org.junit.Before;
import org.junit.Test;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * This is a test class for the enos-services bundle configuration.
 *
 * @author hacksaw
 */
public class ConfigurationTest {
    private Logger logger;

    @Before
    public void init() throws IOException {
        DOMConfigurator.configureAndWatch(Log4jHelper.getLog4jConfig("src/test/resources/"), 45 * 1000);
        logger = LoggerFactory.getLogger(ConfigurationTest.class);
    }

    @Test
    public void testBean() {
        Configuration bean = new Configuration();
        assertNotNull(bean);

        bean.setUriTransform("( http://localhost:8181 | http://transformed.com:8182 )");
        assertEquals("( http://localhost:8181 | http://transformed.com:8182 )", bean.getUriTransform());
        assertEquals("http://localhost:8181", bean.getFromURI());
        assertEquals("http://transformed.com:8182", bean.getToURI());

        bean.setUriTransform("(http://localhost:8181|http://transformed.com:8182)");
        assertEquals("(http://localhost:8181|http://transformed.com:8182)", bean.getUriTransform());
        assertEquals("http://localhost:8181", bean.getFromURI());
        assertEquals("http://transformed.com:8182", bean.getToURI());

        bean.setUriTransform("(    http://localhost:8181    |    http://transformed.com:8182    )");
        assertEquals("(    http://localhost:8181    |    http://transformed.com:8182    )", bean.getUriTransform());
        assertEquals("http://localhost:8181", bean.getFromURI());
        assertEquals("http://transformed.com:8182", bean.getToURI());
    }
}
