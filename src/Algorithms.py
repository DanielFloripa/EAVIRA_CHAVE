#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CHAVE-Sim: The simulator for research based in clouds architecture
    CHAVE: Consolidation with High Availability on virtualyzed environments
"""
__author__ = "Daniel Camargo and Denivy Ruck"
__license__ = "GPL-v3"
__version__ = "2.0.1"
__maintainer__ = "Daniel Camargo"
__email__ = "daniel@colmeia.udesc.br"
__status__ = "Test"

from Priodict import priorityDictionary
# from Graph import DiGraph
from operator import itemgetter


def ksp_yen(graph, node_start, node_end, min_bw, max_k=10):
    distances, previous = dijkstra(graph, node_start, min_bw)

    if node_end not in distances:
        return [{'cost': 0, 'path': []}]
    A = [{'cost': distances[node_end],
          'path': get_path(previous, node_start, node_end)}]
    B = []

    if not A[0]['path']: return A

    for k in range(1, max_k):
        for i in range(0, len(A[-1]['path']) - 1):
            node_spur = A[-1]['path'][i]
            path_root = A[-1]['path'][:i + 1]

            edges_removed = []
            for path_k in A:
                curr_path = path_k['path']
                if len(curr_path) > i and path_root == curr_path[:i + 1]:
                    # cost = graph.remove_edge(curr_path[i], curr_path[i+1])
                    cost = remove_edge(graph, curr_path[i], curr_path[i + 1])
                    if cost == -1:
                        continue
                    edges_removed.append([curr_path[i], curr_path[i + 1], cost])

            path_spur = dijkstra(graph, node_spur, min_bw, node_end)

            if path_spur['path']:
                path_total = path_root[:-1] + path_spur['path']
                dist_total = distances[node_spur] + path_spur['cost']
                potential_k = {'cost': dist_total, 'path': path_total}

                if not (potential_k in B):
                    B.append(potential_k)

            for edge in edges_removed:
                # graph.add_edge(edge[0], edge[1], edge[2])
                add_edge(graph, edge[0], edge[1], edge[2])

        if len(B):
            B = sorted(B, key=itemgetter('cost'))
            A.append(B[0])
            B.pop(0)
        else:
            break

    return A


def add_node(graph, node):
    if node in graph:
        return False
    graph[node] = {}
    return True


def add_edge(graph, node_from, node_to, cost):
    add_node(graph, node_from)
    add_node(graph, node_to)
    graph[node_from][node_to] = cost
    return True


def remove_edge(graph, node_from, node_to):
    if not node_from in graph:
        return -1

    if node_to in graph[node_from]:
        cost = graph[node_from][node_to]

        if cost == float('inf'):
            return -1
        else:
            graph[node_from][node_to] = {'res': float('inf'), 'usage': float('inf')}
            return cost
    else:
        return -1


"""
Method: Implements dijkstra algorithm. Usage represents the
		link's bandwidth status. The lowest => the better in
		terms of bandwidth. So, it'll search for the shortest
		path (in terms of usage), in which each link has at least
		min_bw of bandwidth
"""


def dijkstra(graph, node_start, min_bw, node_end=None):
    distances = {}
    previous = {}
    Q = priorityDictionary()

    # Visited nodes
    Q[node_start] = 0.0

    for u in Q:
        distances[u] = Q[u]
        if u == node_end: break

        for v in graph[u]:
            cost_uv = distances[u] + graph[u][v]['usage']

            if v not in distances and graph[u][v]['res'] >= min_bw:
                if v not in Q or cost_uv < Q[v]:
                    Q[v] = cost_uv
                    previous[v] = u

    if node_end:
        if node_end in distances:
            return {'cost': distances[node_end],
                    'path': get_path(previous, node_start, node_end)}
        else:
            return {'cost': 0, 'path': []}
    else:
        return (distances, previous)


## Finds a paths from a source to a sink using a supplied previous node list.
#
# @param previous A list of node predecessors.
# @param node_start The source node of the graph.
# @param node_end The sink node of the graph.
#
# @retval [] Array of nodes if a path is found, an empty list if no path is 
# found from the source to sink.
#
def get_path(previous, start, end):
    route = [end]

    if end == start:
        return route

    curr = previous[end]
    while curr != start:
        route.append(curr)
        curr = previous[curr]
    route.append(curr)
    route.reverse()

    return route


##########################
# Uniform Search
##########################
def uniform_search(self, root, dest, bw):
    G = self.build_uniform_graph()

    nodes = [root]
    visited = []

    while len(nodes) != 0:
        lowest = min(nodes, key=lambda n: n.acc)

        visited.append(lowest)

        if lowest == dest:
            return self.backtrack(lowest, root)
        # return lowest, len(visited)

        # Remove from nodes list and append all its adjacencies
        nodes.remove(lowest)
        for link in lowest.get_links():
            node = link.get_destination()
            if not node in nodes and not node in visited:
                node.father = lowest
                node.acc += lowest.acc + G[lowest][node]
                nodes.append(node)

            # If the following path has at least bw
            # if G[lowest][node][1] >= bw and G[lowest][node][0] != float('inf'):
            # print(G[lowest][node][0])


def backtrack(self, node, root):
    physical_path = []
    while node != root:
        physical_path.append(node)
        node = node.father
    physical_path.append(node)
    physical_path.reverse()

    return physical_path
