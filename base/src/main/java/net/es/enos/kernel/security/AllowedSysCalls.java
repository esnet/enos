/*
 * Copyright (c) 2014, Regents of the University of California  All rights reserved.
 * Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
 * 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

package net.es.enos.kernel.security;

/**
 * Created by lomax on 2/28/14.
 */

import com.sun.org.apache.bcel.internal.generic.ALOAD;
import net.es.enos.kernel.exec.KernelThread;

import java.util.LinkedList;
import java.util.List;

/**
 * List of classes that are allowed to change the privileged status of an
 * application thread.
 */
public final class AllowedSysCalls {
    static private List<Class> allowedSysCallClasses = new LinkedList<Class>();

    static {
        allowedSysCallClasses.add(net.es.enos.kernel.exec.KernelThread.class);
        allowedSysCallClasses.add(net.es.enos.kernel.security.FileACL.class);
        allowedSysCallClasses.add(net.es.enos.kernel.users.Users.class);
    }

    public static List<Class> getAllowedClasses() {
        LinkedList<Class> ret = new LinkedList<Class>(AllowedSysCalls.allowedSysCallClasses);
        ret.add(KernelThread.class);
        return ret;
    }

    public static boolean isAllowed (Class c) {
        return AllowedSysCalls.allowedSysCallClasses.contains(c);
    }
}
