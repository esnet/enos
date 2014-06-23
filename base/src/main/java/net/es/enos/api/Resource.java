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
import net.es.enos.kernel.exec.KernelThread;
import net.es.enos.kernel.users.User;
import org.codehaus.jackson.map.ObjectMapper;

import java.io.*;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;

/**
 * Created by lomax on 5/21/14.
 */
public class Resource {
    protected String name;
    private String resourceClassName;
    protected String description;
    private List<User> hasWriteAccess;
    private List<User> hasReadAccess;
    private List<String> capabilities;
    private String configFile;
    private List<String> parentResources;
    private boolean isNewInstance = true;

    public Resource() {
        // Set the classname.
        this.resourceClassName = this.getClass().getCanonicalName();
        // Create, if necessary, the capabilities List.
        if (this.capabilities == null) {
            this.capabilities = new ArrayList<String>();
        }
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

    public String getConfigFile() {
        return configFile;
    }

    public void setConfigFile(String configFile) {
        this.configFile = configFile;
    }

    public String getResourceClassName() {
        return resourceClassName;
    }

    public void setResourceClassName(String resourceClassName) {
        this.resourceClassName = resourceClassName;
    }


    /**
     * Save the resource in a file specified by the provided file name. ENOS root is added
     * to the file name if the filename is absolute.
     * @param filename
     * @throws IOException
     */
    public final void save(String filename) throws IOException {
        File file = null;
        if (BootStrap.rootPath == null) {
            // Not yet initialized. Assume non ENOS path
            file = new File(filename);
        } else {
            if (new File(filename).isAbsolute()) {
                file = new File(Paths.get(BootStrap.rootPath.toString(),filename).toString());

            } else {
                // Relative path.
                file = new File(Paths.get(KernelThread.getCurrentKernelThread().getUser().getCurrentPath().toString(),
                                          filename).toString());
            }
        }
        this.save(file);
    }

    /**
     * Saves the resource into the provided File
     * @param file
     * @throws IOException
     */
    public void save(File file) throws IOException {
        /* Make sure all directories exist */
        file.getParentFile().mkdirs();
        /* Write JSON */
        ObjectMapper mapper = new ObjectMapper();
        FileOutputStream output = new FileOutputStream(file);
        mapper.writeValue(output, this);
        // No longer a new resource.
        this.isNewInstance = false;
    }

    public synchronized void addProperties(String property) {
        this.capabilities.add(property);
    }
    public void addProperties(String[] properties) {
        for (String property : properties) {
            this.capabilities.add(property);
        }
    }

    /**
     * Creates a resource from a file specified by the provided file name. ENOS root is added
     * to the file name if the filename is absolute.
     * @param c
     * @param filename
     * @return
     * @throws IOException
     * @throws InstantiationException
     */
    public static final Resource newResource (Class c, String filename) throws IOException, InstantiationException {
        File file = null;
        if (new File(filename).isAbsolute()) {
            // This is an absolute path nane, add ENOS root.
            if (BootStrap.rootPath == null) {
                // rootPath is not set yet. Just create the resource, do not associate a file and return
                // This is a new resource.
                Resource resource = Resource.newResource(c);
                resource.isNewInstance = true;
                return resource;
            } else {
                file = new File(Paths.get(BootStrap.rootPath.toString(),filename).toString());
            }
        } else {
            // Relative path
            file = new File(Paths.get(KernelThread.getCurrentKernelThread().getUser().getCurrentPath().toString(),
                    filename).toString());
        }
        if ( ! file.exists() ) {
            // This is a new resource.
            Resource resource = Resource.newResource(c);
            resource.setConfigFile(file.getAbsolutePath());
            resource.save(file.getAbsolutePath());
            resource.isNewInstance = true;
            return resource;
        } else {
            ObjectMapper mapper = new ObjectMapper();
            FileInputStream input = new FileInputStream(file);
            Resource resource = (Resource) mapper.readValue(input, c);
            resource.isNewInstance = false;
            return resource;
        }
    }

    /**
     * Returns true if the resource did not have persistent store file. False if the resource was loaded from
     * an existing file.
     * @return whether the resource was loaded or not from a file.
     */
    public boolean isNewInstance() {
        return isNewInstance;
    }

    public static final Resource newResource (Class c) throws InstantiationException {
        Resource resource = null;
        try {
            resource = (Resource) Class.forName(c.getName()).newInstance();
            resource.isNewInstance = true;
            return resource;
        } catch (IllegalAccessException e) {
            throw new InstantiationException(e.toString());
        } catch (ClassNotFoundException e) {
            throw new InstantiationException(e.toString());
        }
    }


    public List<String> getParentResources() {
        return parentResources;
    }

    public void setParentResources(List<String> parentResources) {
        this.parentResources = parentResources;
    }

}
