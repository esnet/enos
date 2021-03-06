/*
 * ESnet Network Operating System (ENOS) Copyright (c) 2015, The Regents
 * of the University of California, through Lawrence Berkeley National
 * Laboratory (subject to receipt of any required approvals from the
 * U.S. Dept. of Energy).  All rights reserved.
 *
 * If you have questions about your rights to use or distribute this
 * software, please contact Berkeley Lab's Innovation & Partnerships
 * Office at IPO@lbl.gov.
 *
 * NOTICE.  This Software was developed under funding from the
 * U.S. Department of Energy and the U.S. Government consequently retains
 * certain rights. As such, the U.S. Government has been granted for
 * itself and others acting on its behalf a paid-up, nonexclusive,
 * irrevocable, worldwide license in the Software to reproduce,
 * distribute copies to the public, prepare derivative works, and perform
 * publicly and display publicly, and to permit other to do so.
 */
package net.es.enos.esnet;
// Todo: Generify later.

/**
 * Created by davidhua on 7/17/14.
 */

import com.mxgraph.model.mxGeometry;
import com.mxgraph.model.mxICell;
import com.mxgraph.swing.handler.mxKeyboardHandler;
import com.mxgraph.swing.handler.mxRubberband;
import com.mxgraph.swing.mxGraphComponent;
import com.mxgraph.util.mxConstants;
import com.mxgraph.view.mxStylesheet;
import org.jgrapht.Graph;
import org.jgrapht.GraphPath;
import org.jgrapht.Graphs;
import org.jgrapht.ext.JGraphXAdapter;
import org.jgrapht.graph.DefaultListenableGraph;
import org.jgrapht.graph.Subgraph;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import javax.swing.*;
import java.awt.*;
import java.awt.event.*;
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

    public final Logger logger = LoggerFactory.getLogger(GraphViewer.class);
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

    /*
     * Note: the function is precise enough for our application so far (05/29/15),
     *       but it should be modified in the future.
     * @return if the geolocation is in the United State
     */
    public boolean isUS( double latitude, double longitude) {
        return longitude < -60.0;
    }

    /*
     * adjust position of cells based on nodes' latitude and longitude
     */
    public void project(HashMap<mxICell, ESnetNode> cellToNode) {
        int width = 1280;
        int height = 960;
        int US_left = (int) (width * 0.1); // PNWG's x
        int US_right = (int) (width * 0.65); // BOST's x
        int Europe_left = (int) (width * 0.8); // LONG's x
        // Europe_right = not used with the same ratio as US
        int US_top = (int) (height * 0.3); // PNWG's y
        int US_bottom = (int) (height * 0.8); // HOUS's y
        int Europe_top = (int) (height * 0.35); // AMST's y
        // Europe_bottom = not used with the same ratio as US
        int default_left = (int) (0.05 * width); // default cell position with geolocation information
        int default_top = (int) (0.1 * height);
        int cell_width = 70;
        int cell_height = 22;
        double US_leftmost_longitude = 180.0;
        double US_rightmost_longitude = -180.0;
        double US_bottommost_latitude = 90.0;
        double US_topmost_latitude = -90.0;
        double Europe_leftmost_longitude = 180.0;
        // double Europe_rightmost_longitude = -180.0;
        // double Europe_bottommost_latitude = 90.0;
        double Europe_topmost_latitude = -90.0;

        // get boundary information
        for (mxICell cell : cellToNode.keySet()) {
            ESnetNode node = cellToNode.get(cell);
            if (node.getLongitude() == null) {
                logger.warn("node[" + node.toString() + "] has no geolocation information!");
                continue;
            }
            double longitude = Double.parseDouble(node.getLongitude());
            double latitude = Double.parseDouble(node.getLatitude());

            if  (isUS(latitude, longitude)) {
                US_leftmost_longitude = Math.min(longitude, US_leftmost_longitude);
                US_rightmost_longitude = Math.max(longitude, US_rightmost_longitude);
                US_bottommost_latitude = Math.min(latitude, US_bottommost_latitude);
                US_topmost_latitude = Math.max(latitude, US_topmost_latitude);
            }
            else{
                // Europe
                Europe_leftmost_longitude = Math.min(longitude, Europe_leftmost_longitude);
                Europe_topmost_latitude = Math.max(latitude, Europe_topmost_latitude);
            }
        }

        double width_ratio = 0;
        if (US_rightmost_longitude != US_leftmost_longitude)
            width_ratio = (US_right - US_left) / (US_rightmost_longitude - US_leftmost_longitude);
        double height_ratio = 0;
        if (US_topmost_latitude != US_bottommost_latitude)
            height_ratio = (US_bottom - US_top) / (US_topmost_latitude - US_bottommost_latitude);
        for (mxICell cell : cellToNode.keySet()) {
            ESnetNode node = cellToNode.get(cell);
            if (node.getLongitude() == null) {
                cell.setGeometry(new mxGeometry(default_left, default_top, cell_width, cell_height));
                continue;
            }
            double longitude = Double.parseDouble(node.getLongitude());
            double latitude = Double.parseDouble(node.getLatitude());
            if (isUS(latitude, longitude)) {
                cell.setGeometry(new mxGeometry((longitude - US_leftmost_longitude) * width_ratio + US_left,
                        (US_topmost_latitude - latitude) * height_ratio + US_top, cell_width, cell_height));
            } else {
                // Europe
                cell.setGeometry(new mxGeometry((longitude - Europe_leftmost_longitude) * width_ratio + Europe_left,
                        (Europe_topmost_latitude - latitude) * height_ratio + Europe_top, cell_width, cell_height));
            }
        }
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

        project(cellToNode);

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
