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

import java.io.File;
import java.io.IOException;
import java.nio.file.Path;
import java.nio.file.Paths;

/**
 * Helper class providing methods to manipulate ENOS files
 */
public class FileUtils {

    /**
     * Normalize a file path:
     *  1) Makes sure that the path hides the host path to ENOS_ROOT
     *  2) parses . and ..
     * @param fileName The provided name is an ENOS file name, i.e, hides the host path to
     * ENOS root.
     * @return normalized pathName
     */
    static public String normalize(String fileName) {
        if (fileName == null) {
            return null;
        }
        String normalized;

        if (Paths.get(fileName).startsWith(BootStrap.rootPath)) {
            normalized = fileName.substring(BootStrap.rootPath.toString().length());
        } else {
            if (fileName.startsWith(File.separator)) {
                normalized = fileName;
            } else {
            String currentDirectory = KernelThread.currentKernelThread().getCurrentDirectory();
                if (currentDirectory == null) {
                    // Assumes root
                    normalized =  new File("/", fileName).toString();
                } else {
                    normalized =  new File(currentDirectory, fileName).toString();
                }
            }
        }

        try {
            normalized = new File(normalized).getCanonicalFile().toString();
        } catch (IOException e) {
            throw new RuntimeException(e.getMessage());
        }

        return normalized;
    }

    /**
     * Returns a Path to a provided fileName that refers to a file on the host file system that can later be used
     * for performance I/O.
     * @param fileName The provided name is an ENOS file name, i.e, hides the host path to
     * ENOS root.
     * @return
     */
    static public java.nio.file.Path toRealPath(String fileName) {
        if (fileName == null) {
            return null;
        }
        String realPathName = fileName;
        if ( ! Paths.get(fileName).startsWith(BootStrap.rootPath)) {
            realPathName = new File (BootStrap.rootPath.toString(), realPathName).toString();
        }
        try {
            realPathName = new File(realPathName).getCanonicalFile().toString();
        } catch (IOException e) {
            throw new RuntimeException(e.getMessage());
        }

        return Paths.get(realPathName);
    }

    /**
     * Verifies if fileName exists. The provided name is an ENOS file name, i.e, hides the host path to
     * ENOS root.
     * @param fileName The provided name is an ENOS file name, i.e, hides the host path to
     * ENOS root.
     * @return true if the file exists, false otherwise.
     */
    static public boolean exists(String fileName) {
        Path path = FileUtils.toRealPath(fileName);
        if (path == null) {
            return false;
        }
        return path.toFile().exists();
    }
}
