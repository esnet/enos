package net.es.enos.api;

/**
 * Created by davidhua on 6/12/14.
 */

import org.jgrapht.graph.ListenableDirectedGraph;
import java.util.Collections;
import java.util.HashMap;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.lang.Math;

/**
 * This class implements a modified Dijkstra algorithm that allows us to calculate the max bandwidth
 * possible from one node to another node (instead of calculating the shortest path).
 */

public class ModifiedDijkstra<Node, Link> {
	ListenableDirectedGraph graph;
	ArrayList<Link> path;
	HashMap<Node, Double> width;
	HashMap<Node, Node> prev;

	public ModifiedDijkstra(ListenableDirectedGraph graph, Node source, Node dest) {
		width = new HashMap<Node, Double>();
		prev = new HashMap<Node, Node>();
		findPath(graph, source, dest);
		this.path = bandwidth(source, dest);
	}

	public void findPath(ListenableDirectedGraph graph, Node source, Node dest) {
		List arrayQueue = new ArrayList ();

		this.graph = graph;
		Set<Node> vertices = this.graph.vertexSet();

		// Initialize weights of all vertices to neg inf, prev pointers to null, and the visited hashmap to false.
		// Create queue that will hold all vertices
		for (Node v : vertices) {
			width.put(v, Double.NEGATIVE_INFINITY);
			prev.put(v, null);
		}
		// Initialize source vertex with weight of pos inf (bandwidth from and to same place)
		width.put(source, Double.POSITIVE_INFINITY);

		Set<Link> neighborLink = graph.outgoingEdgesOf(source);
		ArrayList<Node> neighbors = new ArrayList();
		for (Link edge : neighborLink) {
			neighbors.add((Node)graph.getEdgeTarget(edge));
		}

		for (Node neighbor : neighbors) {
			Link link = (Link) graph.getEdge(source, neighbor);
			width.put(neighbor, graph.getEdgeWeight(link));
			prev.put(neighbor, source);
			arrayQueue.add(neighbor);
		}
		// Iterate through all vertices
		while (arrayQueue.size() != 0) {
			// Dijkstra normally uses a priority queue-- however, we need access to the max node, which
			// is at the end of the queue, which we cannot access. To go around this, an Array is used.
			// However, the array must be resorted everytime a change is made to simulate a priority queue.

			Node maxNode = (Node) Collections.max(arrayQueue); // Find the node with the maximum width, and remove it
			arrayQueue.remove(maxNode);

			// If the path has reached the destination, then stop.

			// Find all neighbors of the max node.
			neighborLink = graph.outgoingEdgesOf(maxNode);
			neighbors = new ArrayList();

			for (Link edge : neighborLink) {
				neighbors.add((Node)graph.getEdgeTarget(edge));
			}

			// Iterate through all the neighbors, checking to see if its width field
			// needs to be changed (similar to normal Dijkstra algorithm)
			for (Node neighbor : neighbors) {
				Link link = (Link) graph.getEdge(maxNode, neighbor);
				Double temp = Math.min(width.get(maxNode), graph.getEdgeWeight(link));

				if (width.get(neighbor) == Double.NEGATIVE_INFINITY) {
					prev.put(neighbor, maxNode);
					width.put(neighbor, temp);
					arrayQueue.add(neighbor);
				} else if (arrayQueue.contains(neighbor) && width.get(neighbor) < temp ) {
					prev.put(neighbor, maxNode);
					width.put(neighbor, temp);
				}
			}
		}
	}

	// As modified Dijkstra outputs an array of nodes to the destination,
	// we need to convert this to an array of links for the actual output.
	private ArrayList<Link> bandwidth(Node source, Node dest) {
		ArrayList<Node> finalNode = new ArrayList<Node>();
		Node current = dest;
		finalNode.add(dest);
		while (current != source && current != null) {
			current = prev.get(current);
			if (current != null) {
				finalNode.add(current);
			}
		}
		finalNode.add(source);
		Collections.reverse(finalNode);

		ArrayList<Link> finalPath = new ArrayList<Link>();
		for (int i = 1; i < finalNode.size()-1; i++ ) {
			finalPath.add((Link) graph.getEdge(finalNode.get(i), finalNode.get(i+1)));
		}
		return finalPath;
	}

	public ArrayList<Link> getBandwidth() {
		return this.path;
	}
}