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
import java.nio.file.Path;
import java.nio.file.Paths;

/**
 * Simple resolver for Log4j configuration file.
 *
 * @author hacksaw
 */
public class Log4jHelper {
    public static String getLog4jConfig(String configPath) throws IOException {
        String log4jConfig = System.getProperty("log4j.configuration");
        if (log4jConfig == null) {
            Path realPath = Paths.get(configPath, "log4j.xml").toRealPath();
            log4jConfig = realPath.toString();
        }
        return log4jConfig;
    }
}