package net.es.enos.api;

/**
 * Created by davidhua on 6/12/14.
 */

import net.es.enos.esnet.ESnetNode;
import net.es.enos.esnet.ESnetLink;
import org.jgrapht.graph.ListenableDirectedGraph;
import java.util.Collections;
import java.util.HashMap;
import java.util.*;
import java.lang.Math;


public class ModifiedDijkstra {
	ListenableDirectedGraph graph;
	ArrayList<ESnetLink> path;
	//HashMap<ESnetNode, ESnetNode> prev;

	public ModifiedDijkstra(ListenableDirectedGraph graph, ESnetNode source, ESnetNode dest) {
		findPath(graph, source, dest);
		this.path = bandwidth(source, dest);
	}

	public void findPath(ListenableDirectedGraph graph1, ESnetNode source, ESnetNode dest) {
		ArrayList<ESnetNode> path = new ArrayList<ESnetNode>();
		//HashMap<ESnetNode, ESnetNode> findPrev = new HashMap<ESnetNode, ESnetNode>();
		HashMap<ESnetNode, Boolean> visited = new HashMap<ESnetNode, Boolean>();
		this.graph = graph1;
		Set<ESnetNode> vertices = graph.vertexSet();
		//ArrayList<ESnetNode> vertexArray = new ArrayList();
		List<ESnetNode> arrayQueue = new ArrayList<ESnetNode> ();
		for (ESnetNode v : vertices) {
			//width.put(v, Double.MIN_VALUE);
			v.width = Double.NEGATIVE_INFINITY;
			v.prev = null;
			visited.put(v, false);
			arrayQueue.add(v);
		}
		//width.put(source, Double.MAX_VALUE);
		source.width = Double.POSITIVE_INFINITY;

		while (!arrayQueue.isEmpty()) {
			Collections.sort(arrayQueue);
			ESnetNode maxNode = Collections.max(arrayQueue);
			arrayQueue.remove(maxNode);

			//System.out.println(maxNode.getId());

			//if ((maxNode.width == Double.NEGATIVE_INFINITY) || maxNode == dest) {
			if (maxNode == dest) {
				break;
			}
			Set<ESnetLink> neighborEdge = graph.outgoingEdgesOf(maxNode);
			ArrayList<ESnetNode> neighbors = new ArrayList();

			for (ESnetLink edge : neighborEdge) {
				neighbors.add((ESnetNode)graph.getEdgeTarget(edge));
			}

			for (ESnetNode neighbor : neighbors) {
				if (!visited.get(neighbor)) {
					ESnetLink link = (ESnetLink) graph.getEdge(maxNode, neighbor);
					Double temp = Math.min(maxNode.width, graph.getEdgeWeight(link));
					if (temp > neighbor.width) {
						neighbor.width = temp;
						neighbor.prev = maxNode;
						Collections.sort(arrayQueue);
					}
					visited.put(neighbor, true);
				} else {
					continue;
				}
			}
		}
	}

	private ArrayList<ESnetLink> bandwidth(ESnetNode source, ESnetNode dest) {
		ArrayList<ESnetNode> finalNode = new ArrayList<ESnetNode>();
		ESnetNode current = dest;
		finalNode.add(dest);
		while (current != source && current != null) {
			current = current.prev;
			if (current != null) {
				finalNode.add(current);
			}
		}
		finalNode.add(source);
		Collections.reverse(finalNode);

		ArrayList<ESnetLink> finalPath = new ArrayList<ESnetLink>();
		for (int i = 1; i < finalNode.size()-1; i++ ) {
			finalPath.add((ESnetLink) graph.getEdge(finalNode.get(i), finalNode.get(i+1)));
		}
		return finalPath;
	}

	public ArrayList<ESnetLink> getBandwidth() {
		return this.path;
	}
}