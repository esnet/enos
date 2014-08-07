/*
 * Copyright (c) 2014, Regents of the University of California  All rights reserved.
 * Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
 * 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

package net.es.enos.api;

import com.mxgraph.layout.hierarchical.mxHierarchicalLayout;
import com.mxgraph.layout.mxFastOrganicLayout;
import com.mxgraph.layout.mxParallelEdgeLayout;
import com.mxgraph.swing.mxGraphComponent;
import org.jgrapht.Graph;
import org.jgrapht.ext.JGraphXAdapter;

import javax.swing.*;
import java.awt.*;
import java.util.Set;

/**
 * Created by lomax on 8/7/14.
 */
public class GraphViewer extends JFrame {

    private JGraphXAdapter<Node, Link> jgxAdapter;
    private Graph<Node, Link> graph;
    private Set<Node> vertices;
    private boolean bidirectional = false;
    private boolean fast = true;

    public GraphViewer(Graph<Node, Link> graph) {
        this.graph = graph;
        this.vertices = graph.vertexSet();
    }

    public GraphViewer(Graph<Node, Link> graph, int x, int y, int width, int height) {
        this.graph = graph;
        this.vertices = graph.vertexSet();
        this.setBounds(x,y,width,height);
    }


    public void display() {
        jgxAdapter = new JGraphXAdapter<Node, Link>(graph);
        mxGraphComponent graphComponent = new mxGraphComponent(jgxAdapter);
        getContentPane().add(new JScrollPane(graphComponent));

        if (fast) {
            //define layout
            mxFastOrganicLayout layout = new mxFastOrganicLayout(jgxAdapter);

            //set all properties
            layout.setMinDistanceLimit(200);
            layout.setInitialTemp(200);
            layout.setForceConstant(200);
            layout.setDisableEdgeStyle(true);
            layout.execute(jgxAdapter.getDefaultParent());
        } else {
            new mxHierarchicalLayout(jgxAdapter).execute(jgxAdapter.getDefaultParent());
        }
        if (bidirectional) {
            new mxParallelEdgeLayout(jgxAdapter).execute(jgxAdapter.getDefaultParent());
        }

        this.getContentPane().add(BorderLayout.CENTER, graphComponent);

        this.setVisible(true);
    }

    public void display(int x, int y, int width, int height) {
        this.setBounds(x,y,width,height);
        this.display();
    }

    public boolean isBidirectional() {
        return bidirectional;
    }

    public void setBidirectional(boolean bidrectional) {
        this.bidirectional = bidrectional;
    }

    public boolean isFast() {
        return fast;
    }

    public void setFast(boolean fast) {
        this.fast = fast;
    }
}
