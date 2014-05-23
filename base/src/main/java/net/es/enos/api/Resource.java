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
import org.codehaus.jackson.map.ObjectMapper;

import java.io.*;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

/**
 * Created by lomax on 5/21/14.
 */
public class Resource {
    private String uuid;
    private String name;
    private String resourceClassName;
    private String description;
    private List<User> hasWriteAccess;
    private List<User> hasReadAccess;
    private List<String> capabilities;
    private String resourceDir;
    public static final String CONFIG_FILE = "resource";

    public Resource() {
        // Set the classname.
        this.resourceClassName = this.getClass().getCanonicalName();
        // Create, if necessary, the capabilities List.
        if (this.capabilities == null) {
            this.capabilities = new ArrayList<String>();
        }
    }

    public void setUuid(String uuid) {
        if ((this.uuid != null) && !this.uuid.toString().equals(uuid.toString()) ){
            // It is illegal to try to change the UUID of a resource
            throw new RuntimeException("Cannot change UUID of a resource once it has been set. Resource= " + this.uuid +
                    " current UUID= " + uuid);
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

    public List<String> getCapabilities() {
        return capabilities;
    }

    public void setCapabilities(List<String> capabilities) {
        this.capabilities = capabilities;
    }

    public String getResourceDir() {
        return resourceDir;
    }

    public void setResourceDir(String resourceDir) {
        this.resourceDir = resourceDir;
    }

    public String getResourceClassName() {
        return resourceClassName;
    }

    public void setResourceClassName(String resourceClassName) {
        this.resourceClassName = resourceClassName;
    }

    public final void save() throws IOException {
        if (this.uuid == null) {
            // Generate new UUID: this is a new resource
            this.uuid = UUID.randomUUID().toString();
        }
        Paths.get(BootStrap.rootPath.toString(),this.getResourceDir()).toFile().mkdirs();
        File config = new File(Paths.get(BootStrap.rootPath.toString(),
                                         this.getResourceDir(),
                                         Resource.CONFIG_FILE).toString());
        // config.createNewFile();
        ObjectMapper mapper = new ObjectMapper();
        FileOutputStream output = new FileOutputStream(config);
        mapper.writeValue(output, this);
    }

    public synchronized void addProperties(String property) {
        this.capabilities.add(property);
    }
    public void addProperties(String[] properties) {
        for (String property : properties) {
            this.capabilities.add(property);
        }
    }

    public static final Resource newResource (Class c, String relativePath) throws IOException, InstantiationException {
        File config = new File(Paths.get(BootStrap.rootPath.toString(),relativePath).toString(),Resource.CONFIG_FILE);
        if ( ! config.exists() ) {
            // This is a new resource.
            Resource resource = TopologyFactory.newResource(c);
            resource.setResourceDir(relativePath);
            resource.save();
            return resource;
        }
        ObjectMapper mapper = new ObjectMapper();
        FileInputStream input = new FileInputStream(config);
        Resource resource = (Resource) mapper.readValue(input, c);
        return resource;
    }
    public static final Resource newResource (Class c) throws InstantiationException {
        Resource resource = null;
        try {
            resource = (Resource) Class.forName(c.getName()).newInstance();
            return resource;
        } catch (IllegalAccessException e) {
            throw new InstantiationException(e.toString());
        } catch (ClassNotFoundException e) {
            throw new InstantiationException(e.toString());
        }
    }


}
