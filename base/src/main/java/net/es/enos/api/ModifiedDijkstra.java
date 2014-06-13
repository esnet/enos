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

/**
 * This class implements a modified Dijkstra algorithm that allows us to calculate the max bandwidth
 * possible from one node to another node (instead of calculating the shortest path).
 */

public class ModifiedDijkstra {
	ListenableDirectedGraph graph;
	ArrayList<ESnetLink> path;

	public ModifiedDijkstra(ListenableDirectedGraph graph, ESnetNode source, ESnetNode dest) {
		findPath(graph, source, dest);
		this.path = bandwidth(source, dest);
	}

	public void findPath(ListenableDirectedGraph graph, ESnetNode source, ESnetNode dest) {
		HashMap<ESnetNode, Boolean> visited = new HashMap<ESnetNode, Boolean>();
		List<ESnetNode> arrayQueue = new ArrayList<ESnetNode> ();

		this.graph = graph;
		Set<ESnetNode> vertices = this.graph.vertexSet();

		// Initialize weights of all vertices to neg inf, prev pointers to null, and the visited hashmap to false.
		// Create queue that will hold all vertices
		for (ESnetNode v : vertices) {
			v.width = Double.NEGATIVE_INFINITY;
			v.prev = null;
			visited.put(v, false);
			arrayQueue.add(v);
		}
		// Initialize source vertex with weight of pos inf (bandwidth from and to same place)
		source.width = Double.POSITIVE_INFINITY;

		// Iterate through all vertices
		while (!arrayQueue.isEmpty()) {
			// Dijkstra normally uses a priority queue-- however, we need access to the max node, which
			// is at the end of the queue, which we cannot access. To go around this, an Array is used.
			// However, the array must be resorted everytime a change is made to simulate a priority queue.
			Collections.sort(arrayQueue);
			ESnetNode maxNode = Collections.max(arrayQueue); // Find the node with the maximum width, and remove it
			arrayQueue.remove(maxNode);

			// If the path has reached the destination, then stop.
			if (maxNode == dest) {
				break;
			}

			// Find all neighbors of the max node.
			Set<ESnetLink> neighborEdge = graph.outgoingEdgesOf(maxNode);
			ArrayList<ESnetNode> neighbors = new ArrayList();

			for (ESnetLink edge : neighborEdge) {
				neighbors.add((ESnetNode)graph.getEdgeTarget(edge));
			}

			// Iterate through all the neighbors, checking to see if its width field
			// needs to be changed (similar to normal Dijkstra algorithm)
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

	// As modified Dijkstra outputs an array of nodes to the destination,
	// we need to convert this to an array of links for the actual output.
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