/*
 * Copyright (c) 2014, Regents of the University of California  All rights reserved.
 * Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
 * 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

package net.es.enos.api;

import net.es.enos.boot.BootStrap;
import net.es.enos.kernel.users.User;
import org.codehaus.jackson.JsonGenerationException;
import org.codehaus.jackson.JsonParseException;
import org.codehaus.jackson.map.ObjectMapper;

import java.io.*;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

/**
 * Created by lomax on 5/21/14.
 */
public class Resource {
    private String uuid;
    private String name;
    private String description;
    private List<User> hasWriteAccess;
    private List<User> hasReadAccess;
    private List<String> properties;
    private String homeDir;

    /**
     * All classes that extend Resources must implement this constructor and call super to initialize
     * the path name of the directory that will contain the configuration of the resource. The path is
     * relative to ENOS_HOME. An empty will generate an IOException.
     * @param relativePath
     * @param properties
     */
    public Resource(String relativePath, List<String> properties) throws IOException {
        this.homeDir = relativePath;
        this.load();
        if (this.uuid == null) {
            // Generate new UUID: this is a new resource
            this.uuid = UUID.randomUUID().toString();
            this.save();
        }
        // Create, if necessary, the properties List.
        if (this.properties == null) {
            this.properties = new ArrayList<String>();
        }
        if (this.properties != null) {
            this.properties.addAll(this.properties);
        }
    }

    public void setUuid(String uuid) {
        if (this.uuid != null) {
            // It is illegal to try to change the UUID of a resource
            throw new RuntimeException("Cannot change UUID of a resource once it has been set. Resource= " + this.uuid);
        }
        this.uuid = uuid;
    }

    public String getUuid() {
        return uuid;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }

    public List<User> getHasWriteAccess() {
        return hasWriteAccess;
    }

    public void setHasWriteAccess(List<User> hasWriteAccess) {
        this.hasWriteAccess = hasWriteAccess;
    }

    public List<User> getHasReadAccess() {
        return hasReadAccess;
    }

    public void setHasReadAccess(List<User> hasReadAccess) {
        this.hasReadAccess = hasReadAccess;
    }

    public List<String> getProperties() {
        return properties;
    }

    public void setProperties(List<String> properties) {
        this.properties = properties;
    }

    public final void save() throws IOException {
        ObjectMapper mapper = new ObjectMapper();
        FileOutputStream output = new FileOutputStream(this.homeDir);
        mapper.writeValue(output, this);
    }
    public final void load() throws IOException {
        if ( ! new File(this.homeDir).exists()){
            // Configuration directory does not exist yet. This is a new Resource
            return;
        }
        ObjectMapper mapper = new ObjectMapper();
        FileInputStream input = new FileInputStream(this.homeDir);
        mapper.readValue(input, this.getClass());
    }
}
