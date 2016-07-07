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

import java.util.Map;
import net.es.netshell.services.BundleVersionService;
import net.es.netshell.services.BundleVersionServiceImpl;
import org.osgi.framework.BundleContext;
import org.osgi.service.component.annotations.Activate;
import org.osgi.service.component.annotations.Component;
import org.osgi.service.component.annotations.Deactivate;
import org.osgi.service.component.annotations.Modified;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 *
 * @author hacksaw
 */
@Component(enabled = true, immediate = false, service = BundleVersionService.class)
public class VersionService extends BundleVersionServiceImpl {
    private final Logger logger = LoggerFactory.getLogger(getClass());

    @Activate
    void activate(BundleContext bc, Map<String,Object> map) {
        logger.info("Activating version service.");
    }

    @Deactivate
    void deactivate() {
        logger.info("Deactivating version service.");
    }

    @Modified
    void modified(Map<String,Object> config) {
        logger.info("Modifying version service configuration.");
    }
}
