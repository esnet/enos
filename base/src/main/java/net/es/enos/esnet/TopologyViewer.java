/*
 * Copyright (c) 2014, Regents of the University of California  All rights reserved.
 * Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
 * 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

package net.es.enos.esnet;
// Todo: Generify later.

/**
 * Created by davidhua on 7/17/14.
 */

import com.mxgraph.layout.*;
import com.mxgraph.swing.*;
import com.mxgraph.util.mxCellRenderer;

import java.awt.*;

import javax.swing.*;

import org.jgrapht.ext.*;
import org.jgrapht.graph.*;

import net.es.enos.esnet.ESnetNode;
import net.es.enos.esnet.ESnetLink;

import java.util.Set;

import java.awt.image.BufferedImage;
import java.io.BufferedOutputStream;
import java.io.FileOutputStream;
import javax.imageio.ImageIO;


// Note sample code at https://sites.google.com/site/martinbaeumer/programming/java/graph-visualization-with-java

/*
 * Visualize topology
 *
 * Bugs: Applet does not initialize--no interactivity
 *       Unable to remove link names from link (visualization gets very crowded)
 * Todo: Highlight problem links
 *       Figure out what to do with nodes in very close proximity to each other
 *       Combine routers at same location to obtain GPS coordinates
 *       Normalize and center location of nodes.
 *
 */

public class TopologyViewer
		extends JApplet {

	private final Dimension DEFAULT_SIZE = new Dimension(265, 160);

	private JGraphXAdapter<ESnetNode, ESnetLink> jgxAdapter;
	private DefaultListenableGraph<ESnetNode, ESnetLink> g;
	private Set<ESnetNode> vertices;

	// File location for stored png image (for debugging without applet)
	private String fileLocation = "/users/davidhua/Desktop/test/image.png";

	public TopologyViewer(DefaultListenableGraph<ESnetNode, ESnetLink> graph) {
		this.g = graph;
		this.vertices = g.vertexSet();
	}


	public void init() {
		jgxAdapter = new JGraphXAdapter<ESnetNode, ESnetLink>(g);
		mxGraphComponent graphC = new mxGraphComponent(jgxAdapter);
		getContentPane().add(graphC);
		resize(DEFAULT_SIZE);

		//for (ESnetNode node : vertices) {
		//	Set<ESnetLink> outEdge = g.outgoingEdgesOf(node);
		//}

		mxOrganicLayout layout = new mxOrganicLayout(jgxAdapter);
		for (ESnetNode node : g.vertexSet()) {
			try {
				layout.setVertexLocation(node, Integer.parseInt(node.getLatitude()), Integer.parseInt(node.getLongitude()));
			} catch (java.lang.NumberFormatException e) {
				continue;
			} catch (NullPointerException e) {
				continue;
			}
		}
		//layout.setOptimizeEdgeDistance(true);
		layout.execute(jgxAdapter.getDefaultParent());
		saveToPng(graphC);
	}


	/*
	 * Output visualization to png.
	 */
	public void saveToPng(mxGraphComponent graphComponent) {
		try {
			Color bg = Color.white;
			BufferedOutputStream out = new BufferedOutputStream(new FileOutputStream(fileLocation));
			BufferedImage image = mxCellRenderer.createBufferedImage(graphComponent.getGraph(),
					null, 1, bg, graphComponent.isAntiAlias(), null,
					graphComponent.getCanvas());
			ImageIO.write(image, "png", out);
		} catch (Exception e) {
			e.printStackTrace();
		}

	}

/*
	private int noneFinder(ESnetNode node) {
		String[] nodeEndings = ["cr", "rt", "sdn", "mr"];
		String nodeName = node.getId().split(":")[4].split("-")[0];
		Set<ESnetNode> graphNodes = g.vertexSet();
	}
*/

}