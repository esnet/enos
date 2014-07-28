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

package net.es.enos.kernel.security;

import net.es.enos.api.DefaultValues;
import net.es.enos.boot.BootStrap;
import net.es.enos.configuration.ENOSConfiguration;
import net.es.enos.configuration.GlobalConfiguration;
import net.es.enos.kernel.exec.KernelThread;
import net.es.enos.kernel.exec.annotations.SysCall;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import java.lang.String;

import java.io.*;
import java.lang.reflect.Method;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Properties;
/**
 * ENOS cannot rely on the native file system to provide user access control, since the JVM runs with a
 * single user. ENOS implements File ACL by storing metadata associated  to the file in a separated
 * file which contains ACL.
 */

public class FileACL extends Properties {

    public static final String ACLDIR = ".acl"; // prefix of the acl file
    public static final String CAN_READ = "read";
    public static final String CAN_WRITE = "write";
    public static final String CAN_EXECUTE = "execute";

    private Path aclPath;
    private Path filePath;
    private static Path rootPath;
    private final Logger logger = LoggerFactory.getLogger(FileACL.class);

    static {
        // Figure out the ENOS root directory.
        String rootdir = ENOSConfiguration.getInstance().getGlobal().getRootDirectory();
        rootPath = Paths.get(rootdir).normalize();
    }

    public FileACL (Path file) throws IOException {
        super ();
        if (file == null) {
            // root of the file system, no parent
            return;
        }
        this.filePath = file;
        if (this.filePath.equals(FileACL.rootPath)) {
            // This is ENOS root.
            return;
        }
        this.aclPath = Paths.get(file.normalize().getParent().toString(),
                                 FileACL.ACLDIR,
                                 file.getFileName().toString());

        this.loadACL();
    }


    /**
     * Loads the ACL rules from the ACL file. This will require privilege access and be
     * implemented by a SysCall, do_loadACL.
     * @throws IOException
     */
    public void loadACL() throws IOException {

        Method method;
        try {
            method = KernelThread.getSysCallMethod(this.getClass(), "do_loadACL");

            KernelThread.doSysCall(this, method);

        } catch (Exception e) {
            // Nothing particular to do.
            e.printStackTrace();
        }
    }

    /**
     * SysCall implementing the privileged access to the ACL file. If the file does not exist, do_loadACL will
     * attempt to retrieve ACL from parent directories until reaching ENOS root.
     * @throws IOException
     */
    @SysCall(
            name="do_loadACL"
    )
    public void do_loadACL () throws IOException {
        logger.debug("Try to load ACL file " + this.aclPath);

        File aclFile = new File(this.aclPath.toString());
        if (!aclFile.exists()) {

            if (!this.filePath.startsWith(FileACL.rootPath.toString())) {
                // The file is not part of the ENOS file system. Cannot inherit permission from parent
                return;
            }
            // It is ok for a file to not have an ACL file: it then inherits its parents.
            this.inheritParent();
            return;
        }
        logger.debug("loads file");
        this.load(new FileInputStream(aclFile));
    }

    /**
     * Loads the parent ACL.
     * @throws IOException
     */
    private void inheritParent() throws IOException {
	    if ( !this.filePath.toString().startsWith(FileACL.rootPath.toString())){
		    // Not ENOS file system
            return;
        }
        FileACL parentACL = this.getParentFileACL();
        if (parentACL != null) {
            this.putAll(parentACL);
        }
    }

    /**
     * Attempts to read the parent ACL.
     * @return
     * @throws IOException
     */
    private FileACL getParentFileACL() throws IOException {

        if (this.filePath.getParent().equals(FileACL.rootPath)) {
            // The parent is the ENOS root directory. Cannot inherit. No ACL
            return null;
        }
        FileACL parentACL;
        parentACL = new FileACL(this.filePath.getParent());
        return parentACL;
    }

    /**
     * Stores the ACL into ACL file.
     * @throws IOException
     */
    public void store() throws IOException {
        // By default inherit parent's ACL
        this.inheritParent();
        // Create the file and save it
        this.aclPath.getParent().toFile().mkdirs();
        this.aclPath.toFile().createNewFile();
        this.store(new FileOutputStream(this.aclPath.toString()),"ENOS File ACL");
    }

    /**
     * Checks if the ACL allows the user of the current thread to read the file.
     * @return true if the thread can read the file, false otherwise.
     */
    public boolean canRead() {
        return this.canRead(KernelThread.getCurrentKernelThread().getUser().getName());
    }

    /**
     * Checks if the ACL allows the user of the current thread to read the file.
     * @param username
     * @return
     */
    public boolean canRead(String username) {
        String[] users = this.getCanRead();
        for (String user : users) {
            if (user.equals("*") || user.equals(username)) {
                return true;
            }
        }
        return false;
    }

    public boolean canWrite(String username) {
        String[] users = this.getCanWrite();
        for (String user : users) {
            if (user.equals("*") || user.equals(username)) {
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

    public String[] getCanExecute() {
        String users = this.getProperty(FileACL.CAN_EXECUTE);
        if (users == null) {
            return new String[0];
        }
        return users.split(",");
    }

    public boolean canExecute(String username) {
        String[] users = this.getCanExecute();
        for (String user : users) {
            if (user.equals("*") || user.equals(username)) {
                return true;
            }
        }
        return false;
    }

    protected static String[] addUser(String[] users, String username) {
        String[] newUsers = new String[users.length + 1];
        int index = 0;
        for (String user : users) {
            newUsers[index] = user;
            ++index;
        }
        newUsers[index] = username;
        return newUsers;
    }

    protected static String makeString(String [] strings) {
        String result = "";
        for (String u : strings) {
            result += u + ",";
        }
        return result.substring(0,result.length() - 1);
    }

    public synchronized void allowUserRead(String username) {
        if (this.canRead(username)) {
            // is already allowed
            return;
        }
        // Add user to the list
        this.setProperty(FileACL.CAN_READ,
                FileACL.makeString(FileACL.addUser(this.getCanRead(),username)));

    }
    public synchronized void allowUserWrite(String username) {
        if (this.canWrite(username)) {
            // is already allowed
            return;
        }
        // Add user to the list
        this.setProperty(FileACL.CAN_WRITE,
                FileACL.makeString(FileACL.addUser(this.getCanWrite(),username)));

    }

    public synchronized void allowUserExecute(String username) {
        if (this.canExecute(username)) {
            // is already allowed
            return;
        }
        // Add user to the list
        this.setProperty(FileACL.CAN_EXECUTE,
                FileACL.makeString(FileACL.addUser(this.getCanExecute(),username)));

    }


}







