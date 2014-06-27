/*
 * Copyright (c) 2014, Regents of the University of California  All rights reserved.
 * Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
 * 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

package net.es.enos.esnet;

import net.es.enos.api.Link;
import net.es.enos.api.Node;
import net.es.enos.api.Path;
import net.es.enos.api.PersistentObject;
import org.jgrapht.GraphPath;
import org.joda.time.DateTime;

import java.io.IOException;
import java.util.List;

/**
 * Created by lomax on 6/27/14.
 */
public final class OSCARS {

    public static String USERS_DIR = "/oscars/users";

    /**
     * Checks if the user can provision the provided path. A user is authorized to
     * provision a path only if it has the right to provision each of links of the
     * path and within the provided time range and is authorized to terminate the
     * path at the provided endpoints.
     * @param path
     * @return
     */
    public boolean canProvision (Path path) {
        OSCARSUser oscarsUser = null;
        // Check if the current user is an authorized user to use OSCARS
        try {
            oscarsUser = (OSCARSUser) PersistentObject.newObject(OSCARSUser.class,USERS_DIR);
            if (oscarsUser.isNewInstance()) {
                // does not exist.
                return false;
            }
        } catch (IOException e) {
            return false;
        } catch (InstantiationException e) {
            return false;
        }

        GraphPath<Node,Link> graphPath = path.getGraphPath();
        DateTime start = path.getStart();
        DateTime end = path.getEnd();
        Node startNode = graphPath.getStartVertex();
        Node endNode = graphPath.getEndVertex();
        List<Link> links = graphPath.getEdgeList();

        return false;
    }


}
