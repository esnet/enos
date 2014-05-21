/*
 * Copyright (c) 2014, Regents of the University of California.
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 * 1. Redistributions of source code must retain the above copyright notice,
 * this list of conditions and the following disclaimer.
 *
 * 2. Redistributions in binary form must reproduce the above copyright notice,
 * this list of conditions and the following disclaimer in the documentation
 * and/or other materials provided with the distribution.
 *
 * 3. Neither the name of the copyright holder nor the names of its contributors
 * may be used to endorse or promote products derived from this software without
 * specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 * DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
 * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
 * CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
 * OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

package net.es.enos.configuration;

import net.es.enos.common.PropertyKeys;
import org.codehaus.jackson.map.ObjectMapper;
import org.codehaus.jackson.type.TypeReference;
import org.codehaus.jettison.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;

/**
 * ENOS configuration manager class.
 * This class is a singleton.  It implements everything needed to read
 * ENOS configurations.
 *
 * At the moment this implementation reads a single configuration file in JSON, with JSON objects
 * corresponding to different sections of the configuration.  We envision an eventual, more complex,
 * configuration where portions of the configuration space can be overridden by per-user or per-slice
 * configuration files.  There will necessarily be some policy involved to allow only selected
 * parameters in the master configuration file to be overridden.
 *
 * TODO:  Implement logic to allow slices or users to override parts of the configuration space.
 */
public class EnosConfigurationManager {

    private static EnosConfigurationManager instance;
    private EnosConfigurationManager() { } // private constructor to defeat instantiation
    public static EnosConfigurationManager getInstance() {
        if (instance == null) {
            instance = new EnosConfigurationManager();
        }
        return instance;
    }

    private final Logger logger = LoggerFactory.getLogger(EnosConfigurationManager.class);

    EnosJSONConfiguration masterConfiguration = new EnosJSONConfiguration();

    /**
     * Read the main configuration file.
     */
    public EnosJSONConfiguration getConfiguration() {
        String configurationFilePath = System.getProperty(PropertyKeys.ENOS_CONFIGURATION);

        if (configurationFilePath == null) {
            logger.info("No configuration file property!");
            configurationFilePath = "./enos.json.default";
        }

        logger.info("Master configuration file is {}", configurationFilePath);

        /*
         * This following try/catch block should probably be made a function or something
         * like that, for handling the cases where we have multiple configuration files.
         */
        try {
            File configurationFile = new File(configurationFilePath);
            BufferedReader reader = new BufferedReader(new FileReader(configurationFile));
            String line = null;
            StringBuilder configlines = new StringBuilder();
            while ((line = reader.readLine()) != null) {
                configlines.append(line);
            }
            logger.debug("Configuration:\n{}", configlines.toString());
            JSONObject jsonObj = new JSONObject(configlines.toString());
            ObjectMapper mapper = new ObjectMapper();
            EnosJSONConfiguration conf = mapper.readValue(jsonObj.toString(),
                    new TypeReference<EnosJSONConfiguration>() { });

            return conf;
        } catch (Exception e) {
            // If there's a problem reading the file or parsing it, our configuration is in an undefined state.
            // We might be able to get away with having some sane and sensible defaults so we could continue
            // operation, but for now, just blow up.
            e.printStackTrace();
            System.exit(1);
            return null;
        }
    }
}
