"""
a_star.py — Real-Time A* pathfinding.

STUB FILE — Team B2 implements this.

Interface contract (do not change function signatures):
    - a_star(graph, start, goal) → list of node IDs (the path)
    - real_time_a_star(graph, start, goal) → same, but recalculates
      dynamically if edge weights change during traversal.

The graph.neighbors(node_id) method returns (neighbor_id, travel_time_seconds).
The graph.heuristic(node_a, node_b) method returns an admissible time estimate.
"""

import heapq


def a_star(graph, start, goal):
    """
    Standard A* shortest-time pathfinding.

    Args:
        graph (CityGraph): the city graph
        start (int): start node ID
        goal (int): goal node ID

    Returns:
        list[int]: ordered list of node IDs from start to goal (inclusive),
                   or empty list if no path exists.
    """
    # TODO: Team B2 — implement A* here
    # Hints:
    #   - Use heapq (min-heap) for the open set
    #   - g_cost[node] = best travel time found so far from start to node
    #   - f_cost = g_cost + graph.heuristic(node, goal)
    #   - Track came_from[node] to reconstruct the path
    raise NotImplementedError("a_star() not yet implemented — Team B2 task.")


def real_time_a_star(graph, start, goal):
    """
    Real-Time A*: re-plans if traffic weights change mid-route.

    Args:
        graph (CityGraph): the city graph (traffic mode may change)
        start (int): start node ID
        goal (int): goal node ID

    Returns:
        list[int]: path from start to goal.
    """
    # TODO: Team B2 — implement Real-Time A* here
    # Hint: call a_star() initially, then monitor graph.traffic_mode
    # and re-run if it changes while the ambulance is en route.
    raise NotImplementedError("real_time_a_star() not yet implemented — Team B2 task.")
