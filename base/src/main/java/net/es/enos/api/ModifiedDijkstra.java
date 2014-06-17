package net.es.enos.api;

/**
 * Created by davidhua on 6/12/14.
 */

import net.es.enos.esnet.ESnetNode;
import net.es.enos.esnet.ESnetLink;
import org.jgrapht.graph.ListenableDirectedGraph;
import java.util.Collections;
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
		List<ESnetNode> arrayQueue = new ArrayList<ESnetNode> ();

		this.graph = graph;
		Set<ESnetNode> vertices = this.graph.vertexSet();

		// Initialize weights of all vertices to neg inf, prev pointers to null, and the visited hashmap to false.
		// Create queue that will hold all vertices
		for (ESnetNode v : vertices) {
			v.width = Double.NEGATIVE_INFINITY;
			v.prev = null;
		}
		// Initialize source vertex with weight of pos inf (bandwidth from and to same place)
		source.width = Double.POSITIVE_INFINITY;

		Set<ESnetLink> neighborEdge = graph.outgoingEdgesOf(source);
		ArrayList<ESnetNode> neighbors = new ArrayList();
		for (ESnetLink edge : neighborEdge) {
			neighbors.add((ESnetNode)graph.getEdgeTarget(edge));
		}

		for (ESnetNode neighbor : neighbors) {
			ESnetLink link = (ESnetLink) graph.getEdge(source, neighbor);
			neighbor.width = graph.getEdgeWeight(link);
			neighbor.prev = source;
			arrayQueue.add(neighbor);
		}
		System.out.println(arrayQueue.contains(dest));
		// Iterate through all vertices
		while (arrayQueue.size() != 0) {
			ESnetNode maxNode = Collections.max(arrayQueue); // Find the node with the maximum width, and remove it
			arrayQueue.remove(maxNode);

			// Find all neighbors of the max node.
			neighborEdge = graph.outgoingEdgesOf(maxNode);
			neighbors = new ArrayList();

			for (ESnetLink edge : neighborEdge) {
				neighbors.add((ESnetNode)graph.getEdgeTarget(edge));
			}

			// Iterate through all the neighbors, checking to see if its width field
			// needs to be changed (similar to normal Dijkstra algorithm)
			for (ESnetNode neighbor : neighbors) {
				ESnetLink link = (ESnetLink) graph.getEdge(maxNode, neighbor);
				Double temp = Math.min(maxNode.width, graph.getEdgeWeight(link));

				if (neighbor.width == Double.NEGATIVE_INFINITY) {
					neighbor.prev = maxNode;
					neighbor.width = temp;
					arrayQueue.add(neighbor);
				} else if (arrayQueue.contains(neighbor) && neighbor.width < temp ) {
					neighbor.prev = maxNode;
					neighbor.width = temp;
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
