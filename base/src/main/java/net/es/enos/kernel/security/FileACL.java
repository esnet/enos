/*
 * Copyright (c) 2014, Regents of the University of California  All rights reserved.
 * Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
 * 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

package net.es.enos.kernel.security;

import net.es.enos.common.DefaultValues;
import net.es.enos.common.PropertyKeys;
import net.es.enos.kernel.exec.KernelThread;

import java.io.*;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Properties;
/**
 * ENOS cannot rely on the native file system to provide user access control, since the JVM runs with a
 * single user. ENOS implements File ACL by storing metadata associated  to the file in a separated
 * file which contains ACL.
 */

public final class FileACL extends Properties {

    public static final String PREFIX = ".acl."; // prefix of the acl file
    public static final String CAN_READ = "read";
    public static final String CAN_WRITE = "write";

    private Path path;
    private static Path rootPath;

    static {
        String rootdir = System.getProperty(PropertyKeys.ENOS_ROOTDIR);
        if (rootdir == null) {
            // This happens when running within an IDE (not running script/start-enos.sh
            rootdir= DefaultValues.ENOS_DEFAULT_ROOTDIR;
        }
        rootPath = Paths.get(rootdir).normalize();
    }

    public FileACL (Path file) throws IOException {
        super ();

        this.path = Paths.get(file.normalize().getParent().toString(),
                              FileACL.PREFIX,
                              file.getFileName().toString());
        System.out.println("FILE ACL= " + this.path.toString());
        this.loadACL();
    }

    private void loadACL() throws IOException {
        File aclFile = new File(this.path.toString());
        if (!aclFile.exists()) {
            // It is ok for a file to not have an ACL file: it then inherits its parents.
            this.inheritParent();
            return;
        }
        this.load(new FileInputStream(aclFile));
    }

    private void inheritParent() throws IOException {
        FileACL parentACL = this.getParentFileACL();
        if (parentACL != null) {
            this.putAll(parentACL);
        }
    }

    private FileACL getParentFileACL() throws IOException {
        if (this.path.getParent().equals(FileACL.rootPath)) {
            // The parent is the ENOS root directory. Cannot inherit. No ACL
            return null;
        }
        FileACL parentACL = new FileACL(this.path.getParent());
        return parentACL;
    }

    public void store() throws IOException {
        // By default inherit parent's ACL
        this.inheritParent();
        // Create the file and save it
        this.store(new FileOutputStream(this.path.toString()),"ENOS File ACL");
    }

    public boolean canRead() {
        String[] users = this.getCanRead();
        for (String user : users) {
            if (user.equals(KernelThread.getCurrentKernelThread().getUser().getName())) {
                return true;
            }
        }
        return false;
    }

    public boolean canWrite() {
        String[] users = this.getCanWrite();
        for (String user : users) {
            if (user.equals(KernelThread.getCurrentKernelThread().getUser().getName())) {
                return true;
            }
        }
        return false;
    }
    public String[] getCanRead() {
        String users = this.getProperty(FileACL.CAN_READ);
        if (users == null) {
            return new String[0];
        }
        return users.split(",");
    }

    public String[] getCanWrite() {
        String users = this.getProperty(FileACL.CAN_WRITE);
        if (users == null) {
            return new String[0];
        }
        return users.split(",");
    }

    public static boolean canRead (String file) {
        try {
            FileACL fileACL = new FileACL(Paths.get(file));
            return fileACL.canRead();
        } catch (IOException e) {
            return false;
        }
    }

    public static boolean canWrite (String file) {
        try {
            FileACL fileACL = new FileACL(Paths.get(file));
            return fileACL.canWrite();
        } catch (IOException e) {
            return false;
        }
    }

    public static boolean canParentRead (String file) {
        try {
            FileACL fileACL = new FileACL(Paths.get(file));
            FileACL parentACL = fileACL.getParentFileACL();
            if (parentACL == null) {
                return false;
            }
            return parentACL.canRead();
        } catch (IOException e) {
            return false;
        }

    }

    public static boolean canParentWrite (String file) {
        try {
            FileACL fileACL = new FileACL(Paths.get(file));
            FileACL parentACL = fileACL.getParentFileACL();
            if (parentACL == null) {
                return false;
            }
            return parentACL.canWrite();
        } catch (IOException e) {
            return false;
        }

    }

}







