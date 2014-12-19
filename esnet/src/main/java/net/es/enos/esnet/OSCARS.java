/*
 * Copyright (c) 2014, Regents of the University of California  All rights reserved.
 * Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
 * 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

package net.es.enos.esnet;

import net.es.netshell.api.*;
import net.es.netshell.kernel.container.Container;
import net.es.netshell.kernel.exec.KernelThread;
import org.codehaus.jackson.annotate.JsonIgnore;
import org.jgrapht.GraphPath;
import org.joda.time.DateTime;

import java.io.IOException;
import java.lang.reflect.Method;
import java.util.List;

/**
 * Created by lomax on 6/27/14.
 */
public final class OSCARS {

    public static String OSCARS_CONTAINER = "/sys/services/oscars";

    /**
     * Checks if the user can provision the provided path. A user is authorized to
     * provision a path only if it has the right to provision each of links of the
     * path and within the provided time range and is authorized to terminate the
     * path at the provided endpoints.
     * @param path
     * @return
     */
    public boolean canProvision (Path path) {

        GraphPath<Node,Link> graphPath = path.getGraphPath();
        DateTime start = path.getStart();
        DateTime end = path.getEnd();
        Node startNode = graphPath.getStartVertex();
        Node endNode = graphPath.getEndVertex();
        List<Link> links = graphPath.getEdgeList();

        Container currentContainer = KernelThread.currentKernelThread().getCurrentContainer();
        String authName = OSCARS.getAuthorizationName(currentContainer);
        try {
            OSCARSAuthorizationResource oscarsAuth =
                    (OSCARSAuthorizationResource) PersistentObject.newObject(OSCARSAuthorizationResource.class,
                                                                             authName);
            oscarsAuth.getAuthorizedGraph().pathExists(startNode, endNode);
        } catch (IOException e) {
            return false;
        } catch (InstantiationException e) {
            return false;
        }

        return false;
    }

    /**
     * Creates an OSCARSAuthorizationResource for a list of GraphResources. Those GraphResource describes the
     * topologies that the container will be allowed to provision. This SysCall will throw a SecurityException
     * when:
     *
     *     - the current thread does not have ADMIN access to the current container.
     *     - there is a least one Link in the list of GraphResources that the current container does not have
     *     the right to provision.
     *
     * Upon creation, a new container is created within the OSCARS container and the requester container is set
     * to be able to join but not administrate. The authorized resources are stored in that new container and a
     * OSCARSAuthorizationResource is created for the authorized GraphResource. Once done, the container will be
     * able to provision OSCARS circuits within the GraphResources.
     *
     * @param container
     * @param graphResource
     * @throws IOException
     */
    public static void createAuthorization (Container container, GraphResource graphResource) throws IOException {
        Method method;

        method = KernelThread.getSysCallMethod(OSCARS.class, "do_shareResource");
        try {
            KernelThread.doSysCall(OSCARS.class, method, container,graphResource);

        } catch (Exception e) {
            if (e instanceof RuntimeException) {
                throw (RuntimeException) e;
            }
            throw new RuntimeException(e.getMessage());
        }
    }

    public static void do_createAuthorization (Container container, GraphResource graphResource) throws IOException {

        Container currentContainer = KernelThread.currentKernelThread().getCurrentContainer();
        Container oscarsContainer = new Container(OSCARS_CONTAINER);

        boolean authorized = false;

        if (oscarsContainer.getName().equals(currentContainer.getName())) {
            // The thread runs within the OSCARS container, therefore it is authorized to create an Authorization
            authorized = true;
        } else {
            // TODO: lomax@es.net to be implemented
            throw new RuntimeException("not yet implemenged");
        }
        if (! authorized) {
            throw new SecurityException("not authorized");
        }
        String authName = OSCARS.getAuthorizationName(currentContainer);
        if (PersistentObject.exists(authName)) {
            throw new SecurityException("Already exists");
        }
        OSCARSAuthorizationResource authResource = new OSCARSAuthorizationResource(container.getName(),
                                                                                   graphResource,
                                                                                   container);

        authResource.save(authName);
    }

    @JsonIgnore
    public static String getAuthorizationName(Container container) {
        String name = OSCARS_CONTAINER + "/" + container.getName().replace("/",".");
        return name;
    }



}
