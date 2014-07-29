/*
 * Copyright (c) 2014, Regents of the University of California  All rights reserved.
 * Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
 * 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

package net.es.enos.kernel.container;

import net.es.enos.kernel.security.FileACL;

import java.io.IOException;
import java.nio.file.Path;

/**
 * Created by lomax on 7/21/14.
 */
public class ContainerACL extends FileACL {
    public static final String CAN_ADMIN = "admin";
    public ContainerACL(Path file) {
        super(file);
    }

    public synchronized void allowAdmin(String username) {
        if (this.canAdmin(username)) {
            // is already allowed
            return;
        }
        // Add user to the list
        this.setProperty(CAN_ADMIN,
                FileACL.makeString(FileACL.addUser(this.getCanAdmin(),username)));

    }



    public String[] getCanAdmin() {
        String users = this.getProperty(CAN_ADMIN);
        if (users == null) {
            return new String[0];
        }
        return users.split(",");
    }

    public boolean canAdmin(String username) {
        String[] users = this.getCanAdmin();
        for (String user : users) {
            if (user.equals("*") || user.equals(username)) {
                return true;
            }
        }
        return false;
    }
}
