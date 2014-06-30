/*
 * Copyright (c) 2014, Regents of the University of California  All rights reserved.
 * Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
 * 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

package net.es.enos.esnet;

import net.es.enos.api.Node;
import net.es.enos.api.PersistentObject;
import org.codehaus.jackson.annotate.JsonIgnore;

import java.io.IOException;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;

/**
 * This class represents a Data Transfer Node that is deployed within ESnet.
 * The type, which is a long, represent the type or class of the DTN expressed
 * in byte/sec. That means the machine is capable of this kind of bandwidth, network,
 * i/o, cpu.
 */
public class DataTransferNode extends ESnetHost {

    private long type;
    @JsonIgnore
    public static String DTN_DIR="/dtn";
    private ArrayList<DataTransferNodeInterface> interfaces = new ArrayList<DataTransferNodeInterface>();
    public long getType() {
        return type;
    }

    public void setType(long type) {
        this.type = type;
    }

    public List<DataTransferNodeInterface> getInterfaces() {
        return interfaces;
    }

    public void setInterfaces(ArrayList<DataTransferNodeInterface> interfaces) {
        this.interfaces = interfaces;
    }

    /**
     * If a file describing the DataTransferNode exists in DTN_DIR, this method will return a
     * DataTransferNode object loaded from that file. Returns null otherwise
     * @param name of the DataTransferNode
     * @return if existing, a DataTransferNode
     */
    @JsonIgnore
    public static DataTransferNode getDataTransferNode(String name) {
        // Load from local file system
        DataTransferNode dtn = null;
        try {
            dtn = (DataTransferNode) PersistentObject.newObject(DataTransferNode.class,
                                                                Paths.get(DTN_DIR, name).toString());
        } catch (IOException e) {
            e.printStackTrace();
        } catch (InstantiationException e) {
            e.printStackTrace();
        }

        return dtn;
    }

    public void save() throws IOException {
        this.save(Paths.get(DTN_DIR, this.getName()).toString());
    }

}
