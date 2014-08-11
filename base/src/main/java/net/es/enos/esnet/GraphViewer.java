/*
 * Copyright (c) 2014, Regents of the University of California All rights
reserved.
 * Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
 * 1. Redistributions of source code must retain the above copyright
notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright
notice, this list of conditions and the following disclaimer in the
documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the copyright holder nor the names of its
contributors may be used to endorse or promote products derived from this
software without specific prior written permission.
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

package net.es.enos.esnet;
// Todo: Generify later.

/**
 * Created by davidhua on 7/17/14.
 */

import java.awt.event.*;
import com.mxgraph.layout.*;
import com.mxgraph.model.mxGeometry;
import com.mxgraph.model.mxICell;
import com.mxgraph.swing.*;
import com.mxgraph.swing.handler.mxCellMarker;
import com.mxgraph.swing.handler.mxKeyboardHandler;
import com.mxgraph.swing.handler.mxRubberband;

import java.awt.*;

import javax.swing.*;

import com.mxgraph.util.mxConstants;
import com.mxgraph.view.mxStylesheet;
import net.es.enos.api.Link;
import net.es.enos.api.Node;
import org.jgrapht.GraphPath;
import org.jgrapht.Graphs;
import org.jgrapht.ext.*;
import org.jgrapht.graph.*;
import org.jgrapht.Graph;

import java.awt.event.MouseEvent;
import java.util.*;

/*
 * Visualize topology

 * Todo: Highlight problem links
 *       Figure out what to do with nodes in very close proximity to each
other
 *       Can't show infopane when zoomed in
 *       Combine routers at same location to obtain GPS coordinates
 *       Normalize and center location of nodes.
 *
 */

public class GraphViewer
		extends JFrame implements MouseListener, MouseWheelListener, KeyListener{

	private final Dimension DEFAULT_SIZE = new Dimension(1500, 1500);

	private JGraphXAdapter<ESnetNode, ESnetLink> jgxAdapter;
	private Graph<ESnetNode, ESnetLink> g;
	private Set<ESnetNode> vertices;

	HashMap<mxICell, ESnetNode> finalCellToNode;
	HashMap<ESnetNode, mxICell> finalNodeToCell;
	HashMap<mxICell, ESnetLink> finalCellToEdge;

	private mxGraphComponent graphC;
	private JScrollPane leftPane;
	private JScrollPane rightPane;
	private JSplitPane splitPane;
	private JPanel panel;
	private boolean shiftDown = false;
	private ArrayList<ESnetLink> nodeArray;
	private int totalLatency;
	private String orgNode;
	private String endNode;
	private int sizeField = 7;

	private JLabel areaLabel1 = new JLabel();
	private JLabel areaLabel2 = new JLabel();
	private JLabel areaLabel3 = new JLabel();
	private JLabel areaLabel4 = new JLabel();

	private JTextField textField1 = new JTextField(sizeField);
	private JTextField textField2 = new JTextField(sizeField);
	private JTextField textField3 = new JTextField(sizeField);
	private JTextField textField4 = new JTextField(sizeField);

	public GraphViewer(DefaultListenableGraph<ESnetNode, ESnetLink> graph) {
		this.g = graph;
		this.vertices = g.vertexSet();
	}

	public GraphViewer(GraphPath<ESnetNode, ESnetLink> path, DefaultListenableGraph<ESnetNode, ESnetLink> graph) {
		this.vertices = new HashSet<>(Graphs.getPathVertexList(path));
		Set<ESnetLink> edges = new HashSet<>(path.getEdgeList());
		Subgraph<ESnetNode, ESnetLink, DefaultListenableGraph<ESnetNode, ESnetLink>> subgraph = new Subgraph(graph, vertices, edges);
		this.g = subgraph;
	}

	public void init() {
		jgxAdapter = new JGraphXAdapter<>(g);
		this.setExtendedState(this.getExtendedState() | JFrame.MAXIMIZED_BOTH);
		HashMap<mxICell, ESnetNode> cellToNode = jgxAdapter.getCellToVertexMap();
		finalCellToNode = jgxAdapter.getCellToVertexMap();
		finalNodeToCell = jgxAdapter.getVertexToCellMap();
		finalCellToEdge = jgxAdapter.getCellToEdgeMap();

		Map<String, Object> edge = new HashMap<String, Object>();
		edge.put(mxConstants.STYLE_SHAPE, mxConstants.SHAPE_CONNECTOR);
		edge.put(mxConstants.STYLE_ENDARROW, "none");
		edge.put(mxConstants.STYLE_VERTICAL_ALIGN, mxConstants.ALIGN_MIDDLE);
		edge.put(mxConstants.STYLE_ALIGN, mxConstants.ALIGN_CENTER);
		edge.put(mxConstants.STYLE_STROKECOLOR, "#6482B9");
		edge.put(mxConstants.STYLE_FONTSIZE, 0);
		//edge.put(mxConstants.STYLE_INDICATOR_COLOR, "#15a76a");

		mxStylesheet edgeStyle = new mxStylesheet();
		edgeStyle.setDefaultEdgeStyle(edge);
		jgxAdapter.setStylesheet(edgeStyle);

		jgxAdapter.setKeepEdgesInBackground(true); // Edges will not appear above vertices

		//jgxAdapter.setCellsSelectable(false); // All edges and vertices are no longer selectable

		graphC = new mxGraphComponent(jgxAdapter);
		getContentPane().add(graphC);
		graphC.setConnectable(false);
		graphC.setDragEnabled(false);
		graphC.setPanning(true);
		jgxAdapter.setConnectableEdges(false);
		jgxAdapter.setCellsDisconnectable(false);

		//jgxAdapter.isAutoOrigin();

		rightPane = new JScrollPane(graphC);

		//rightPane.setPreferredSize(new Dimension(1200, 1000));
		leftPane = new JScrollPane();
		//leftPane.setPreferredSize(new Dimension(100,1000));
		leftPane.setVisible(true);
		splitPane = new JSplitPane(JSplitPane.HORIZONTAL_SPLIT,
				rightPane, leftPane);
		add(splitPane);

		splitPane.setResizeWeight(.89d);

		splitPane.setVisible(true);
		splitPane.repaint();

		//new mxRubberband(graphC);
		new mxKeyboardHandler(graphC);

		new mxRubberband(graphC) {

			public void mouseReleased(MouseEvent e)
			{
				// get bounds before they are reset
				Rectangle rect = bounds;

				// invoke usual behaviour
				super.mouseReleased(e);

				if( rect != null) {

					double newScale = 1;

					Dimension graphSize = new Dimension( rect.width, rect.height);
					Dimension viewPortSize = graphC.getViewport().getSize();

					int graphWidth = (int) graphSize.getWidth();
					int graphHeight = (int) graphSize.getHeight();

					if (graphWidth > 0 && graphHeight > 0) {
						int viewportWidth = (int) viewPortSize.getWidth();
						int viewportHeight = (int) viewPortSize.getHeight();

						newScale = Math.min((double) viewportWidth / graphWidth, (double) viewportHeight / graphHeight);
					}

					// zoom to fit selected area
					graphC.zoom(newScale);

					// make selected area visible
					graphC.getGraphControl().scrollRectToVisible( new Rectangle( (int) (rect.x * newScale), (int) (rect.y * newScale),  (int) (rect.width * newScale),  (int) (rect.height * newScale)));
					graphC.getGraphControl().setVisible(true);
					graphC.getGraphControl().repaint();
					graphC.refresh();
				}

			}

		};

		//Show background
//		String value = (String) JOptionPane.showInputDialog(
//				graphC, mxResources.get("backgroundImage"),
//				"URL", JOptionPane.PLAIN_MESSAGE, null, null,
//				"http://2.bp.blogspot.com/-D7KzB34Z7Hg/TuQ_BU_yruI/AAAAAAAACt4/9asOk60f3wI/s1600/blank-map-of-the-continental-united-states.PNG");
//
//
//		Image background = mxUtils.loadImage(value);
//		if (background != null)
//		{
//			graphC.setBackgroundImage(new ImageIcon(
//					background));
//		}

		graphC.setFocusable(true);
		graphC.requestFocus();

		graphC.getGraphControl().addMouseWheelListener(this);
		graphC.getGraphControl().addMouseListener(this);
		graphC.addKeyListener(this);

//		mxFastOrganicLayout layout = new mxFastOrganicLayout(jgxAdapter);
//		layout.setUseInputOrigin(false);

		for (mxICell cell : cellToNode.keySet()) {
			ESnetNode node = cellToNode.get(cell);

			try {
				Double longitude = 122.8 - (Double.parseDouble(node.getLongitude()) * -1);
				Double latitude = 50 - ((Double.parseDouble(node.getLatitude())));
				mxGeometry newGeom = new mxGeometry(longitude* 25.3,
						latitude * 36, 70, 22);
				cell.setGeometry(newGeom);
			} catch (java.lang.NumberFormatException e) {
				continue;
			} catch (NullPointerException e) {
				// No coordinates found--put in default location
				mxGeometry newGeom = new mxGeometry(500, 500, 150, 25);
				cell.setGeometry(newGeom);
			}
		}

		this.setVisible(true);
		this.repaint();
		graphC.refresh();
	}

	public void mouseReleased(MouseEvent e) {
		return;
	}

	public void mouseExited(MouseEvent e) {
		return;
	}

	public void mouseEntered(MouseEvent e) {
		return;
	}

	public void mouseClicked(MouseEvent e) {
		return;
	}

	public void mouseWheelMoved(MouseWheelEvent e) {
		// Zoom with mouse wheel
		if (e.getWheelRotation() < 0) {
			graphC.zoomIn();
		} else {
			graphC.zoomOut();
		}
	}

	public void mousePressed(MouseEvent e) {
		int numRow = 0;
		if (SwingUtilities.isLeftMouseButton(e)) {
			if (shiftDown) {
				int x = e.getX(), y = e.getY();
				Object cell = graphC.getCellAt(x, y);
				final ESnetLink ESlink = finalCellToEdge.get(cell);
				if (nodeArray.size() == 0) {
					orgNode = g.getEdgeSource(ESlink).getId().split(":")[4];
				}
				if (ESlink != null) {
					panel.removeAll();
					double latency;
					try {
						double lat1 = Double.parseDouble(g.getEdgeSource(ESlink).getLatitude());
						double lat2 = Double.parseDouble(g.getEdgeTarget(ESlink).getLatitude());
						double lon1 = Double.parseDouble(g.getEdgeSource(ESlink).getLongitude());
						double lon2 = Double.parseDouble(g.getEdgeTarget(ESlink).getLongitude());
						latency = expectedLatency(lat1, lon1, lat2, lon2);
					} catch (NullPointerException q) {
						latency = 0;
					}
					nodeArray.add(ESlink);
					totalLatency += latency;
					endNode = g.getEdgeTarget(ESlink).getId().split(":")[4];

					areaLabel1.setText("Length: ");
					areaLabel2.setText("Origin: ");
					areaLabel3.setText("Destination: ");
					areaLabel4.setText("Expected Latency: ");
					areaLabel1.setLabelFor(textField1);
					areaLabel2.setLabelFor(textField2);
					areaLabel3.setLabelFor(textField3);
					areaLabel4.setLabelFor(textField4);
					textField1.setText(String.valueOf(nodeArray.size()));
					textField2.setText(orgNode);
					textField3.setText(endNode);
					String latencyString = String.valueOf(totalLatency);
					if (latencyString.length() < 6) {
						textField4.setText(latencyString + " ms");
					} else {
						textField4.setText(latencyString.substring(0, 6) + " ms");
					}
					panel.add(areaLabel1);
					panel.add(textField1);
					panel.add(areaLabel2);
					panel.add(textField2);
					panel.add(areaLabel3);
					panel.add(textField3);
					panel.add(areaLabel4);
					panel.add(textField4);

					SpringUtilities.makeCompactGrid(panel,
							4, 2,
							0, 0,
							0, 0);
					leftPane.removeAll();

					splitPane.remove(splitPane.getRightComponent());

					splitPane.setRightComponent(panel);
					splitPane.getRightComponent().setSize(panel.getSize());
					splitPane.setResizeWeight(.96d);
					splitPane.repaint();
					splitPane.revalidate();
					leftPane.repaint();
					splitPane.repaint();
					repaint();
					graphC.refresh();
				}
			} else {

			}
		}

		if (SwingUtilities.isRightMouseButton(e)) {
			int x = e.getX(), y = e.getY();

			Object cell = graphC.getCellAt(x, y);

			final ESnetNode EScell = finalCellToNode.get(cell);
			final ESnetLink ESlink = finalCellToEdge.get(cell);

			JPanel panel = new JPanel(new SpringLayout());

			panel.add(areaLabel3);
			panel.add(textField3);
			panel.add(areaLabel2);
			panel.add(textField2);
			panel.add(areaLabel1);
			panel.add(textField1);
			if (EScell != null) {
				numRow = 3;
				areaLabel1.setText("Latitude");
				areaLabel2.setText("Longitude");
				areaLabel3.setText("ID:");
				areaLabel1.setLabelFor(textField1);
				areaLabel2.setLabelFor(textField2);
				areaLabel3.setLabelFor(textField3);
				textField1.setText(EScell.getLatitude());
				textField2.setText(EScell.getLongitude());
				textField3.setText(EScell.getId().split(":")[4]);
				textField1.setEditable(false);
				textField2.setEditable(false);
				textField3.setEditable(false);
			} else if (ESlink != null) {
				numRow = 4;
				areaLabel1.setText("Network Metric: ");
				areaLabel2.setText("Destination: ");
				areaLabel3.setText("Origin: ");
				areaLabel4.setText("Expected Latency: ");
				areaLabel1.setLabelFor(textField1);
				areaLabel2.setLabelFor(textField2);
				areaLabel3.setLabelFor(textField3);
				areaLabel4.setLabelFor(textField4);

				textField1.setText(String.valueOf(ESlink.getTrafficEngineeringMetric()));
				textField2.setText(ESlink.getId().split(":")[4]);
				textField3.setText(ESlink.getRemoteLinkId().split(":")[4]);

				double lat1 = Double.parseDouble(g.getEdgeSource(ESlink).getLatitude());
				double lat2 = Double.parseDouble(g.getEdgeTarget(ESlink).getLatitude());
				double lon1 = Double.parseDouble(g.getEdgeSource(ESlink).getLongitude());
				double lon2 = Double.parseDouble(g.getEdgeTarget(ESlink).getLongitude());
				double latency = expectedLatency(lat1, lon1, lat2, lon2);

				String latencyString = String.valueOf(latency);
				if (latencyString.length() < 6) {
					textField4.setText(latencyString + " ms");
				} else {
					textField4.setText(latencyString.substring(0, 6) + " ms");
				}

				panel.add(areaLabel4);
				panel.add(textField4);

			} else {
				return;
			}
			textField1.setEditable(false);
			textField2.setEditable(false);
			textField3.setEditable(false);
			textField4.setEditable(false);

			leftPane.removeAll();

			SpringUtilities.makeCompactGrid(panel,
					numRow, 2,
					0, 0,
					2, 0);
			splitPane.remove(splitPane.getRightComponent());
			splitPane.setRightComponent(panel);
			splitPane.setResizeWeight(1d);
			splitPane.repaint();
			splitPane.revalidate();

			leftPane.repaint();
			splitPane.repaint();
			repaint();
			graphC.refresh();
		}
	}

	public void keyTyped(KeyEvent e) {
	}

	public void keyPressed(KeyEvent e) {
		if (e.getKeyCode() == KeyEvent.VK_SHIFT && shiftDown == false) {
			shiftDown = true;
			nodeArray = new ArrayList ();
			panel = new JPanel(new SpringLayout());
			totalLatency = 0;
			orgNode = null;
			endNode = null;
		}
		else if (e.getKeyCode() == KeyEvent.VK_SHIFT && shiftDown == true) {
			shiftDown = false;
			nodeArray = new ArrayList<> ();
			totalLatency = 0;
			orgNode = null;
			endNode = null;
		} else if (e.getKeyCode() == KeyEvent.VK_COMMA) {
			graphC.zoomIn();
		} else if (e.getKeyCode() == KeyEvent.VK_PERIOD) {
			graphC.zoomOut();
		} else if (e.getKeyCode() == KeyEvent.VK_NUMPAD0) {
			double scale = 1d;
			graphC.zoomTo(scale, graphC
					.isCenterZoom());
		}
	}

	public void keyReleased(KeyEvent e) {
	}

	public double expectedLatency(double lat1, double lon1, double lat2, double
			lon2) {
		double earthRadius = 6371;
		double speedOfLight = 299.792458; // Speed of light in kilometers per millisecond
		double Rlon1 = Math.toRadians(lon1);

		double Rlon2 = Math.toRadians(lon2);
		double Rlat1 = Math.toRadians(lat1);
		double Rlat2 = Math.toRadians(lat2);

		double latSubt = Rlat2-Rlat1;
		double lonSubt = Rlon2-Rlon1;
		double a = Math.sin(latSubt/2) * Math.sin(latSubt/2) + Math.cos(Rlat1)  *
				Math.cos(Rlat2) * Math.sin(lonSubt/2) * Math.sin(lonSubt/2);
		double c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
		double dist = earthRadius * c;

		return dist/(speedOfLight);
	}
}