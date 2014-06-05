/*
 * Copyright (c) 2014, Regents of the University of California  All rights reserved.
 * Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
 * 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

package net.es.enos.kernel.users;

/**
 * Created by lomax on 5/16/14.
 */
public class UserProfile {
    /**
     * Representation of a user in the password file.
     * Essentially this is analogous to a single line in /etc/passwd on a UNIX system.
     */

    private String username; // Username, must be a valid UNIX filename.
    private String password; // Encrypted password
    private String privilege; // Privilege, currently either "root" or "user"
    private String name; // Name of user
    private String organization; // Organization of User
    private String email; // Email of User

    public String getName() {
        return username;
    }

    public void setName(String username) {
        this.username = username;
    }

    public String getPassword() {
        return password;
    }

    public void setPassword(String password) {
        this.password = password;
    }

    public String getPrivilege() {
        return privilege;
    }

    public void setPrivilege(String privilege) {
        this.privilege = privilege;
    }

    public String getRealName() {
        return name;
    }

    public void setRealName(String name) {
        this.name = name;
    }

    public String getorganization() {
        return organization;
    }

    public void setOrganization(String organization) {
        this.organization = organization;
    }

    public String getemail() {
        return email;
    }

    public void setEmail(String email) {
        this.email = email;
    }

    public UserProfile(String line) {
        String[] elements = line.split(":");
        if (elements.length != 6) {
            // Incorrect format. Ignore
            return;
        }
        username = elements[0];
        password = elements[1];
        privilege = elements[2];
        name = elements[3];
        organization = elements[4];
        email = elements[5];
    }

    public UserProfile(String username, String password, String privilege, String name, String organization, String email) {
        this.username = username;
        this.password = password;
        this.privilege = privilege;
        this.name = name;
        this.organization = organization;
        this.email = email;
    }

    @Override
    public String toString() {
        String line = "";
        line += username + ":";
        line += password + ":";
        line += privilege + ":";
        line += name + ":";
        line += organization + ":";
        line += email;

        return line;
    }

}
