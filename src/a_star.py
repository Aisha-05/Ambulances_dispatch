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
 
    # came_from[node] = which node we arrived from
    # Used at the end to reconstruct the full path by walking backwards
    came_from = {}
 
    # Min-heap entries: (f_score, g_score, node_id)
    # g_score is the tiebreaker — same f -> prefer the node with lower actual cost
    h0 = graph.heuristic(start, goal)
    heap = [(h0, 0.0, start)]
 
    # visited = nodes we have already expanded with their best g_cost.
    # If we reach a node again with a worse (higher) cost, we skip it.
    visited = set()
 
    while heap:
        f, g, current = heapq.heappop(heap)
 
        # Goal reached — reconstruct path by walking came_from backwards
        if current == goal:
            return _reconstruct_path(came_from, start, goal)
 
        # Already expanded this node with a cheaper route — skip
        if current in visited:
            continue
        visited.add(current)
 
        # Expand all neighbours
        # graph.neighbors() returns (neighbor_id, travel_time_seconds)
        for neighbor, edge_time in graph.neighbors(current):
            if neighbor in visited:
                continue
 
            new_g = g + edge_time
 
            # Only worth pursuing if this is cheaper than any route we know
            if new_g < g_cost.get(neighbor, float("inf")):
                g_cost[neighbor] = new_g
                came_from[neighbor] = current
                new_f = new_g + graph.heuristic(neighbor, goal)
                heapq.heappush(heap, (new_f, new_g, neighbor))
 
    # Heap exhausted — no path exists
    return []
 
 
def real_time_a_star(graph, start, goal):
    """
    Real-Time A*: re-plans the path if traffic changes while en route.
 
    Args:
        graph (CityGraph): the city graph (traffic mode may change)
        start (int): start node ID
        goal  (int): goal node ID
 
    Returns:
        list[int]: path from start to goal.
 
    How it works
    ------------
    We compute an initial path with standard A*.
    Then we simulate stepping along that path one node at a time.
    At each step we check if the traffic mode has changed since we last
    planned. If it has, we throw away the remaining route and re-run A*
    from our current position with the updated edge weights.
 
    This is the key idea behind Real-Time A*: instead of committing to
    a full plan upfront, we stay reactive to the environment changing
    underneath us — exactly what happens when traffic spikes mid-dispatch.
    """
    if start == goal:
        return [start]
 
    # Compute initial path
    path = a_star(graph, start, goal)
    if not path:
        return []
 
    # Remember the traffic mode we planned under
    last_traffic_mode = graph.traffic_mode
 
    # Walk along the path node by node
    travelled = [path[0]]       # nodes we have physically passed through
    remaining = path[1:]        # nodes still ahead of us
 
    while remaining:
        current = travelled[-1]
 
        # Check if traffic changed since we last planned
        if graph.traffic_mode != last_traffic_mode:
            # Re-plan from current position with the new edge weights
            new_remaining = a_star(graph, current, goal)
            if not new_remaining:
                # No path found under new conditions — return what we have
                break
            # new_remaining starts at current, so skip the first element
            # (we're already there) and use the rest as our new route
            remaining = new_remaining[1:]
            last_traffic_mode = graph.traffic_mode
 
        # Take the next step
        next_node = remaining.pop(0)
        travelled.append(next_node)
 
    return travelled
 
 
# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------
 
def _reconstruct_path(came_from, start, goal):
    """
    Walk the came_from dict backwards from goal to start,
    then reverse to get the forward path.
    """
    path = [goal]
    node = goal
    while node != start:
        node = came_from[node]
        path.append(node)
    path.reverse()
    return path
