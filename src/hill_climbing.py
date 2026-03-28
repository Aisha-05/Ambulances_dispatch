"""
hill_climbing.py — Hill Climbing optimizer for ambulance standby positions.

STUB FILE — Team B2 implements this.

Goal: when ambulances are idle, where should they wait to minimize average
      response time to future emergencies?

Method:
    1. Start: place idle ambulances at random intersection nodes.
    2. Evaluate: compute objective(emergencies, ambulances, graph).
    3. Move: for each idle ambulance, try all neighboring nodes.
    4. If moving to a neighbor improves the objective → move there.
    5. Repeat until no improvement is found (local optimum).

Interface contract (do not change function signatures).
"""


def hill_climbing(graph, ambulances, emergencies, max_iterations=100):
    """
    Hill Climbing to find optimal standby positions for idle ambulances.

    Args:
        graph (CityGraph): the city graph
        ambulances (list): list of ambulance dicts (only idle ones are moved)
        emergencies (list): historical emergency records (used for scoring)
        max_iterations (int): stop after this many iterations even if not converged

    Returns:
        dict: { ambulance_id -> optimal_node_id }
    """
    # TODO: Team B2 — implement Hill Climbing here
    # Hints:
    #   from objective import objective
    #   - Only move ambulances with status == "idle"
    #   - Use graph.adjacency[node_id] to find neighbors of current position
    #   - Evaluate objective() after each candidate move
    #   - Keep the move if it strictly improves (lowers) the objective value
    #   - Stop when no move improves (local optimum reached)
    #   - Try running from multiple random starting positions to escape local optima
    raise NotImplementedError("hill_climbing() not yet implemented — Team B2 task.")


def voronoi_initial_positions(graph, ambulances):
    """
    Alternative starting point: spread ambulances using a Voronoi-inspired
    approach (each ambulance claims the region of the city closest to it).

    Args:
        graph (CityGraph): the city graph
        ambulances (list): list of ambulance dicts

    Returns:
        list of node IDs (one per ambulance) as starting positions
    """
    # TODO: Team B2 — implement Voronoi-based initialization
    # Hint: use k-means style placement on intersection nodes,
    # or just evenly distribute ambulances across the node list.
    raise NotImplementedError("voronoi_initial_positions() not yet implemented — Team B2 task.")
