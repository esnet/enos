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
import org.codehaus.jackson.annotate.JsonIgnore;
import org.codehaus.jackson.map.ObjectMapper;

import java.io.*;
import java.nio.file.Paths;

/**
 * Created by lomax on 6/24/14.
 */
public class PersistentObject implements Serializable {

    @JsonIgnore
    private boolean isNewInstance = true;

    /**
     * Builds the correct pathname of a file, taking into account the ENOS_ROOT and the ENOS user
     * current directory
     */
    public static File buildFile(String filename) {
        File file = null;
        if (BootStrap.rootPath == null) {
            // Not yet initialized. Assume non ENOS path
            file = new File(filename);
        } else {
            if (new File(filename).isAbsolute()) {
                file = new File(Paths.get(BootStrap.rootPath.toString(), filename).toString());
            } else {
                // Relative path.
                file = new File(Paths.get(KernelThread.currentKernelThread().getUser().getCurrentPath().toString(),
                        filename).toString());
            }
        }
        return file;
    }

    /**
     * Save the resource in a file specified by the provided file name. ENOS root is added
     * to the file name if the filename is absolute.
     * @param filename
     * @throws java.io.IOException
     */
    public final void save(String filename) throws IOException {
        File file = PersistentObject.buildFile(filename);
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
        output.flush();
        output.close();
        // No longer a new resource.
        this.isNewInstance = false;
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
            return obj;
        }
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

}
