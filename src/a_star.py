

"""
a_star.py — Real-Time A* pathfinding.
Team B2 implementation.

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
        goal  (int): goal node ID

    Returns:
        list[int]: ordered list of node IDs from start to goal (inclusive),
                   or empty list if no path exists.

    How it works
    ------------
    Every node gets two scores:
      g(n) = actual travel time from start to n (what we've paid so far)
      h(n) = heuristic estimate from n to goal  (optimistic guess)
      f(n) = g(n) + h(n)                        (total estimated cost)

    We always expand the node with the lowest f(n) first (min-heap).
    The moment we pop the goal node, the path is guaranteed optimal
    because h is admissible (never overestimates).
    """
    if start == goal:
        return [start]

    # g_cost[node] = best travel time found so far from start to that node
    g_cost = {start: 0.0}

    # came_from[node] = the node we arrived from; used to reconstruct the path
    came_from = {}

    # Min-heap: (f_score, g_score, node_id)
    # g_score as tiebreaker: equal f → prefer the node with lower actual cost
    heap = [(graph.heuristic(start, goal), 0.0, start)]

    while heap:
        f, g, current = heapq.heappop(heap)

        # Goal reached — reconstruct and return the path
        if current == goal:
            return _reconstruct_path(came_from, start, goal)

        # Stale heap entry: we already found a cheaper route to this node
        if g > g_cost.get(current, float("inf")):
            continue

        for neighbor, edge_time in graph.neighbors(current):
            new_g = g + edge_time

            if new_g < g_cost.get(neighbor, float("inf")):
                g_cost[neighbor] = new_g
                came_from[neighbor] = current
                new_f = new_g + graph.heuristic(neighbor, goal)
                heapq.heappush(heap, (new_f, new_g, neighbor))

    return []  # No path exists


def real_time_a_star(graph, start, goal):
    """
    Real-Time A*: re-plans the path if traffic changes while en route.

    Args:
        graph (CityGraph): the city graph (traffic_mode may change mid-run)
        start (int): start node ID
        goal  (int): goal node ID

    Returns:
        list[int]: path from start to goal (may include mid-route replans).

    How it works
    ------------
    We compute an initial path with standard A*, then step along it one node
    at a time. Before each step we check whether traffic_mode has changed.
    If it has, we replan from the current position — staying reactive to
    the environment changing beneath us, as happens when traffic spikes
    mid-dispatch.
    """
    if start == goal:
        return [start]

    path = a_star(graph, start, goal)
    if not path:
        return []

    travelled = [path[0]]
    remaining = path[1:]
    last_traffic_mode = graph.traffic_mode

    while remaining:
        current = travelled[-1]

        if graph.traffic_mode != last_traffic_mode:
            new_path = a_star(graph, current, goal)
            if not new_path:
                break  # No path under new conditions; return progress so far
            # new_path[0] == current, so skip it to avoid duplication
            remaining = new_path[1:]
            last_traffic_mode = graph.traffic_mode

        travelled.append(remaining.pop(0))

    return travelled


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------

def _reconstruct_path(came_from, start, goal):
    """Walk came_from backwards from goal to start, then reverse."""
    path = []
    node = goal
    while node != start:
        path.append(node)
        node = came_from[node]
    path.append(start)
    path.reverse()
    return path
