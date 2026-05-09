"""
assignment.py — Ambulance assignment strategies.

Two strategies to implement and compare:
    1. greedy_assign  — closest by Euclidean (haversine) distance (BASELINE)
    2. astar_assign   — closest by actual A* travel time (SMART)

Interface contract (do not change function signatures):
    Both functions receive the same arguments and return the same type.
    This lets simulation.py swap between them with one line change.
"""


def greedy_assign(graph, ambulances, emergency):
    """
    BASELINE: assign the idle ambulance with the shortest straight-line distance.

    Args:
        graph (CityGraph): the city graph
        ambulances (list): list of ambulance dicts
        emergency (dict): the emergency to respond to

    Returns:
        dict or None: the selected ambulance, or None if none are idle
    """
    idle = [a for a in ambulances if a["status"] == "idle"]
    if not idle:
        return None
    return min(idle, key=lambda a: graph.haversine(a["position"], emergency["node"]))


def astar_assign(graph, ambulances, emergency):
    """
    SMART: assign the idle ambulance with the shortest A* travel time.

    Args:
        graph (CityGraph): the city graph
        ambulances (list): list of ambulance dicts
        emergency (dict): the emergency to respond to

    Returns:
        dict or None: the selected ambulance, or None if none are idle
    """
    # TODO: Team B2 — implement A*-based assignment
    # Hint: for each idle ambulance, call a_star(graph, ambulance["position"],
    # emergency["node"]) and sum the edge travel times along the returned path.
    # Return the ambulance with the minimum total travel time.
    raise NotImplementedError("astar_assign() not yet implemented — Team B2 task.")
