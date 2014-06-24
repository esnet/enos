
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

import java.nio.file.Paths;
import java.io.FilePermission;
import java.util.LinkedList;

/**
 * This class sets the file permission that KernelSecurityManager will use when doing checkRead/checkWrite.
 */
public final class Authorized {
    private static LinkedList<FilePermission> filePermissions;

    private static void init() {
        if (filePermissions != null) {
            return;
        }
        filePermissions = new LinkedList<FilePermission>();

        // Figure out the ENOS root directory.
        String rootdir = ENOSConfiguration.getInstance().getGlobal().getRootDirectory();
        filePermissions.add(new FilePermission(Paths.get(rootdir).normalize().toString() + "/-",
                            "read,write"));

    }

    /**
     * Checks if the provided FilePermission is implied by any of the authorized FilePermissions
     * @param filePermission  is Permission that is requested
     * @return true if authorized
     */
    public static boolean isAuthorized (FilePermission filePermission) {
        // System.out.println ("isAuthorized ");
        init();
        for (FilePermission perm : filePermissions) {
            if (perm.implies(filePermission)) {
                // System.out.println("Authorized ");
                // TODO: log
                return true;
            }
        }
        return false;
    }
}
