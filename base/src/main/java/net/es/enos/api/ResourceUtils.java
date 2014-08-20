/*
 * Copyright (c) 2014, Regents of the University of California  All rights reserved.
 * Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
 * 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

package net.es.enos.api;

import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Helper methods to manipulate Resources.
 */
public class ResourceUtils {


    /**
     * Verifies that a name is valid for a ResourceName. ResourceName can be used as part of an URL
     * @param name
     * @return
     */
    public static boolean isValidResourceName(String name) {
        if (name == null) {
            // This can happen when creating a new Resource
            return true;
        }
        Pattern pattern = Pattern.compile("[<>?]");
        Matcher matcher = pattern.matcher(name);
        return ! matcher.find();
    }

    /**
     * Special handling of characters such as *
     * @param name
     * @return
     */
    public static String normalizeResourceName (String name) {
        String tmp = name.replace("*","_any_");
        return tmp;
    }

    public static String parseResourceName (String name) {
        String tmp = name.replace("_any_","*");
        return tmp;
    }


}
