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

import com.mxgraph.layout.mxFastOrganicLayout;
import com.mxgraph.swing.mxGraphComponent;
import com.mxgraph.util.mxConstants;
import com.mxgraph.view.mxStylesheet;
import org.codehaus.jettison.json.JSONArray;
import org.codehaus.jettison.json.JSONException;
import org.codehaus.jettison.json.JSONObject;
import org.codehaus.jettison.json.JSONTokener;
import org.jgrapht.ListenableGraph;
import org.jgrapht.ext.JGraphXAdapter;
import org.jgrapht.graph.DefaultEdge;
import org.jgrapht.graph.ListenableDirectedGraph;

import javax.swing.*;
import java.awt.event.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.HashMap;
import java.util.Map;

/**
 * Created by rueiminl on 8/10/15.
 */
public class Visualization extends JFrame implements MouseListener, MouseWheelListener, KeyListener {

    public static void main(String[] args) throws JSONException, IOException {
        // System.out.print(System.getProperty("user.dir"));
        if (args.length <= 0) {
            System.out.print("Invalid arguments");
            return;
        }
        String content = new String(Files.readAllBytes(Paths.get(args[0])));
        JSONObject obj = new JSONObject(new JSONTokener(content));
        Visualization v = new Visualization(obj);
    }

    int canvasWidth = 800;
    int canvasHeight = 600;
    HashMap<String, JSONObject> nodeIndex;
    HashMap<String, JSONObject> linkIndex;
    HashMap<String, JSONObject> objIndex;
    HashMap<String, JPanel> infoIndex;
    JSONObject obj;
    mxGraphComponent graphC;
    JGraphXAdapter jgxAdapter;
    JSplitPane splitPane;

    Visualization(JSONObject obj) throws JSONException {
        this.obj = obj;
        nodeIndex = new HashMap<String, JSONObject>();
        linkIndex = new HashMap<String, JSONObject>();
        objIndex = new HashMap<String, JSONObject>();
        infoIndex = new HashMap<String, JPanel>();

        JSONArray nodes = obj.getJSONArray("nodes");
        for (int i = 0; i < nodes.length(); i++) {
            JSONObject node = nodes.getJSONObject(i);
            nodeIndex.put(node.getString("name"), node);
        }
        JSONArray links = obj.getJSONArray("links");
        for (int i = 0; i < links.length(); i++) {
            JSONObject link = links.getJSONObject(i);
            linkIndex.put(link.getString("name"), link);
        }

        for (Map.Entry<String, JSONObject> entry : nodeIndex.entrySet()) {
            objIndex.put(entry.getKey(), entry.getValue());
        }
        for (Map.Entry<String, JSONObject> entry : linkIndex.entrySet()) {
            objIndex.put(entry.getKey(), entry.getValue());
        }

        ListenableGraph g = new ListenableDirectedGraph(DefaultEdge.class);
        for (JSONObject node : nodeIndex.values()) {
            g.addVertex(node.getString("name"));
        }
        for (JSONObject link : linkIndex.values()) {
            g.addEdge(link.getString("endpoint1"), link.getString("endpoint2"), link.getString("name"));
        }
        jgxAdapter = new JGraphXAdapter<>(g);

        setExtendedState(getExtendedState() | JFrame.MAXIMIZED_BOTH);
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

        JScrollPane rightPane = new JScrollPane(graphC);
        JScrollPane leftPane = new JScrollPane();
        leftPane.setVisible(true);
        splitPane = new JSplitPane(JSplitPane.HORIZONTAL_SPLIT, rightPane, leftPane);
        add(splitPane);

        splitPane.setResizeWeight(.89d);

        splitPane.setVisible(true);
        splitPane.repaint();

        graphC.getGraphControl().addMouseWheelListener(this);
        graphC.getGraphControl().addMouseListener(this);
        graphC.addKeyListener(this);

        new mxFastOrganicLayout(jgxAdapter).execute(jgxAdapter.getDefaultParent());

        this.setVisible(true);
        this.repaint();
        graphC.refresh();
    }

    @Override
    public void keyTyped(KeyEvent e) {

    }

    @Override
    public void keyPressed(KeyEvent e) {
        if (e.getKeyCode() == KeyEvent.VK_COMMA) {
            graphC.zoomIn();
        } else if (e.getKeyCode() == KeyEvent.VK_PERIOD) {
            graphC.zoomOut();
        } else if (e.getKeyCode() == KeyEvent.VK_NUMPAD0) {
            double scale = 1d;
            graphC.zoomTo(scale, graphC.isCenterZoom());
        }
    }

    @Override
    public void keyReleased(KeyEvent e) {
    }

    @Override
    public void mouseClicked(MouseEvent e) {
        try {
            int x = e.getX(), y = e.getY();
            Object cell = graphC.getCellAt(x, y);
            if (cell != null) {
                String name = (String) jgxAdapter.getCellToVertexMap().get(cell);
                if (name == null) {
                    name = (String) jgxAdapter.getCellToEdgeMap().get(cell);
                }
                JPanel infoPanel;
                if (infoIndex.containsKey(name)) {
                    infoPanel = infoIndex.get(name);
                } else {
                    infoPanel = new JPanel(new SpringLayout());
                    JSONObject obj = objIndex.get(name);
                    JSONArray infos = obj.getJSONArray("info");
                    for (int i = 0; i < infos.length(); i++) {
                        JSONObject info = infos.getJSONObject(i);
                        JTextField text = new JTextField(7);
                        JLabel label = new JLabel();
                        label.setText(info.getString("attr"));
                        text.setText(info.getString("value"));
                        label.setLabelFor(text);
                        infoPanel.add(label);
                        infoPanel.add(text);
                    }
                    SpringUtilities.makeCompactGrid(infoPanel, infos.length(), 2, 3, 3, 3, 3);
                    infoIndex.put(name, infoPanel);
                }
                splitPane.setRightComponent(infoPanel);
                splitPane.repaint();
            }
        } catch (JSONException e1) {
            e1.printStackTrace();
        }
    }

    @Override
    public void mousePressed(MouseEvent e) {

    }

    @Override
    public void mouseReleased(MouseEvent e) {

    }

    @Override
    public void mouseEntered(MouseEvent e) {

    }

    @Override
    public void mouseExited(MouseEvent e) {

    }

    @Override
    public void mouseWheelMoved(MouseWheelEvent e) {
        // Zoom with mouse wheel
        if (e.getWheelRotation() < 0) {
            graphC.zoomIn();
        } else {
            graphC.zoomOut();
        }
    }
}

