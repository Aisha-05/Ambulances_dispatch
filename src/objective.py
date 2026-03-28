"""
objective.py — Scoring functions for the dispatch system.

These functions define what "good performance" means:
    1. Response Time  — how fast do ambulances reach emergencies?
    2. Coverage       — are idle ambulances spread across the city?
    3. Combined       — weighted sum used by Hill Climbing (Team B2).

Team A owns this file.
Team B2 (Hill Climbing) will call objective() to evaluate candidate positions.
"""


def compute_response_time(emergencies):
    """
    Average response time across all resolved emergencies.

    Response time = time from call to ambulance arrival at scene.

    Args:
        emergencies (list): list of emergency dicts

    Returns:
        float: average response time in seconds (0.0 if none resolved yet)
    """
    resolved = [e for e in emergencies if e["arrival_time"] is not None]
    if not resolved:
        return 0.0
    total = sum(e["arrival_time"] - e["call_time"] for e in resolved)
    return total / len(resolved)


def compute_coverage(ambulances, graph):
    """
    Coverage score: measures how well idle ambulances are spread across the city.

    Method: for every node in the graph, find the nearest idle ambulance
    (by haversine distance). Sum all those distances. A lower sum means
    better coverage. We return the negative so that HIGHER = BETTER,
    consistent with maximization-style objective functions.

    Args:
        ambulances (list): list of ambulance dicts
        graph (CityGraph): the city graph (for haversine calculations)

    Returns:
        float: negative total distance (higher = better coverage).
               Returns -inf if no idle ambulances.
    """
    idle = [a for a in ambulances if a["status"] == "idle"]
    if not idle:
        return float("-inf")

    total_distance = 0.0
    for node_id in graph.get_node_ids():
        min_dist = min(
            graph.haversine(node_id, a["position"]) for a in idle
        )
        total_distance += min_dist

    return -total_distance  # negate so higher = better


def objective(emergencies, ambulances, graph, w1=0.7, w2=0.3):
    """
    Combined objective function (lower = better overall performance).

    Minimizes: w1 * response_time + w2 * coverage_cost

    This is what Hill Climbing (Team B2) will minimize when finding
    optimal standby positions for idle ambulances.

    Args:
        emergencies (list): list of emergency dicts
        ambulances (list): list of ambulance dicts
        graph (CityGraph): the city graph
        w1 (float): weight for response time (default 0.7)
        w2 (float): weight for coverage (default 0.3)

    Returns:
        float: combined cost (lower is better)
    """
    rt = compute_response_time(emergencies)
    cov = compute_coverage(ambulances, graph)
    coverage_cost = -cov  # convert back to positive (lower = better coverage)
    return w1 * rt + w2 * coverage_cost


def print_metrics(emergencies, ambulances, graph):
    """
    Print a human-readable performance report.

    Args:
        emergencies (list): list of emergency dicts
        ambulances (list): list of ambulance dicts
        graph (CityGraph): the city graph
    """
    total = len(emergencies)
    resolved = sum(1 for e in emergencies if e["arrival_time"] is not None)
    waiting = sum(1 for e in emergencies if e["status"] == "waiting")
    avg_rt = compute_response_time(emergencies)
    cov = compute_coverage(ambulances, graph)

    print("=== Performance Metrics ===")
    print(f"  Total emergencies : {total}")
    print(f"  Resolved          : {resolved}")
    print(f"  Still waiting     : {waiting}")
    print(f"  Avg response time : {avg_rt:.1f} seconds ({avg_rt/60:.2f} minutes)")
    print(f"  Coverage score    : {cov:.0f}")
    print("===========================")
