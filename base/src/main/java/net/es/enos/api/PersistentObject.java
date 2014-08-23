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
import org.codehaus.jackson.annotate.JsonIgnore;
import org.codehaus.jackson.map.ObjectMapper;

import java.io.*;
import java.util.ArrayList;
import java.util.List;

/**
 * Created by lomax on 6/24/14.
 */
public class PersistentObject implements Serializable {

    @JsonIgnore
    private boolean isNewInstance = true;
    @JsonIgnore
    private File file;
    private String resourceClassName;

    /**
     * Builds the correct pathname of a file, taking into account the ENOS_ROOT and the ENOS user
     * current directory
     */
    public static File buildFile(String filename) {
        File file = null;
        filename = ResourceUtils.normalizeResourceName(filename);
        if (BootStrap.rootPath == null) {
            // Not yet initialized. Assume non ENOS path
            file = new File(filename);
        } else {
            file = new File(FileUtils.toRealPath(filename).toString());
        }
        return file;
    }

    public boolean exists() {
        if (this.file == null) {
            return false;
        }
        return this.file.exists();
    }

    public static boolean exists(String name) {
        File f = buildFile(name);
        if (f == null) {
            return false;
        }
        return f.exists();
    }

    /**
     * Save the resource in a file specified by the provided file name. ENOS root is added
     * to the file name if the filename is absolute.
     * @param filename
     * @throws java.io.IOException
     */
    public final void save(String filename) throws IOException {
        this.file = PersistentObject.buildFile(ResourceUtils.normalizeResourceName(filename));
        this.save(file);
    }

    /**
     * Saves the resource into the provided File
     * @param file
     * @throws IOException
     */
    private void save(File file) throws IOException {
        this.file = file;
        // Set the classname.
        this.resourceClassName = this.getClass().getCanonicalName();
        /* Make sure all directories exist */
        file.getParentFile().mkdirs();
        /* Write JSON */
        ObjectMapper mapper = new ObjectMapper();
        FileOutputStream output = new FileOutputStream(file);
        mapper.writeValue(output, this);
        output.flush();
        output.close();
        // No longer a new resource.
        this.isNewInstance = false;
    }

    public void delete() {
        if (this.file != null) {
            file.delete();
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
    public static final PersistentObject newObject (Class c, String filename) throws IOException, InstantiationException {
        File file = PersistentObject.buildFile(filename);
        if ( ! file.exists() ) {
            // This is a new resource.
            PersistentObject obj = PersistentObject.newObject(c);
            obj.isNewInstance = true;
            return obj;
        } else {
            ObjectMapper mapper = new ObjectMapper();
            FileInputStream input = new FileInputStream(file);
            PersistentObject obj = (PersistentObject) mapper.readValue(input, c);
            obj.isNewInstance = false;
            obj.file = file;
            return obj;
        }
    }

    private static final String getClassName (String filename) throws IOException {
        // Without loading the file, retrieve the className
        File file = PersistentObject.buildFile(filename);
        if (! file.exists()) {
            return null;
        }
        BufferedReader br = null;

        br = new BufferedReader(new FileReader(file));
        String line;
        while ((line = br.readLine()) != null) {
            String[] items = line.split(":");
            if (items.length == 2) {
                if (items[0].equals("resourceClassName")) {
                    return items[1];
                }
            }
        }
        br.close();
        return null;
    }

    /**
     * Returns true if the resource did not have persistent store file. False if the resource was loaded from
     * an existing file.
     * @return whether the resource was loaded or not from a file.
     */
    @JsonIgnore
    public boolean isNewInstance() {
        return isNewInstance;
    }

    public static final PersistentObject newObject (Class c) throws InstantiationException {
        PersistentObject obj = null;
        try {
            obj = (PersistentObject) Class.forName(c.getName()).newInstance();
            obj.isNewInstance = true;
            return obj;
        } catch (IllegalAccessException e) {
            throw new InstantiationException(e.toString());
        } catch (ClassNotFoundException e) {
            throw new InstantiationException(e.toString());
        }
    }

    public static final PersistentObject newObject (String fileName) throws InstantiationException {
        PersistentObject obj = null;
        try {
            String className = PersistentObject.getClassName(fileName);
            return PersistentObject.newObject(Class.forName(className),fileName);

        } catch (ClassNotFoundException e) {
            throw new InstantiationException(e.toString());
        } catch (IOException e) {
            throw new InstantiationException(e.toString());
        }
    }
    public void setNewInstance(boolean isNewInstance) {
        this.isNewInstance = isNewInstance;
    }

    public String getResourceClassName() {
        return resourceClassName;
    }

    public void setResourceClassName(String resourceClassName) {
        this.resourceClassName = resourceClassName;
    }

    @JsonIgnore
    public File getFile() {
        return this.file;
    }

    @JsonIgnore
    public String getFileName() {
        if (this.file != null) {
            return this.file.getName();
        } else {
            return null;
        }
    }

    @JsonIgnore
    public  List<PersistentObject> getObjects(String directory, Class filteredClass) throws IOException {
        File directoryFile = PersistentObject.buildFile(directory);
        if ( ! directoryFile.exists() || ! directoryFile.isDirectory()) {
            return null;
        }
        ArrayList<PersistentObject> objects = new ArrayList<PersistentObject>();
        for (File file : directoryFile.listFiles()) {
            if (PersistentObject.getClassName(file.getPath()).equals(filteredClass.getCanonicalName())) {
                try {
                    objects.add(PersistentObject.newObject(filteredClass, file.getPath()));
                } catch (InstantiationException e) {
                    continue;
                }
            }
        }
        return objects;
    }
}
