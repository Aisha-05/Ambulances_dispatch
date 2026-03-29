"""
graph.py — City graph structure for the Ambulance Dispatch system.

Loads nodes and edges from JSON files and exposes:
  - Adjacency list for pathfinding
  - Travel time calculation (accounts for road type + traffic mode)
  - Haversine distance (used as A* heuristic)
  - Neighbor lookup for A*

Team A owns this file. Team B1 will plug in real data by swapping the JSON
files — no code changes needed here.
"""

import json
import math
import random


# Base speed limits in km/h per road type
BASE_SPEED_KMH = {
    "highway": 90,
    "main": 50,
    "small": 30,
}

# Legacy mode multipliers for backward compatibility with set_traffic().
MODE_TRAFFIC_MULTIPLIER = {
    "normal": {"highway": 1.0, "main": 1.0, "small": 1.0},
    "rush_hour": {"highway": 1.8, "main": 2.0, "small": 2.0},
}


class CityGraph:
    def __init__(self, nodes_path, edges_path):
        """
        Load graph from JSON files.

        Args:
            nodes_path (str): path to nodes.json
            edges_path (str): path to edges.json
        """
        with open(nodes_path, encoding="utf-8-sig") as f:
            nodes_data = json.load(f)
        with open(edges_path, encoding="utf-8-sig") as f:
            edges_data = json.load(f)

        # nodes: dict { node_id -> {id, lat, lon, type, name} }
        self.nodes = {n["id"]: n for n in nodes_data}

        # adjacency: dict { node_id -> list of (neighbor_id, edge_dict) }
        self.adjacency = {n["id"]: [] for n in nodes_data}
        for edge in edges_data:
            # Backward compatibility: default to uncongested roads.
            edge.setdefault("traffic", 1.0)
            self.adjacency[edge["from"]].append((edge["to"], edge))

        self.edges = edges_data
        self.traffic_mode = "normal"  # "normal" or "rush_hour"

    # ------------------------------------------------------------------
    # Traffic control
    # ------------------------------------------------------------------

    def set_traffic(self, mode):
        """
        Legacy compatibility helper that applies a static city-wide profile.

        Dynamic per-edge traffic from update_traffic() should be preferred.

        Args:
            mode (str): "normal" or "rush_hour"
        """
        if mode not in ("normal", "rush_hour"):
            raise ValueError(f"Unknown traffic mode: {mode}")
        self.traffic_mode = mode

        # Keep old behavior available by setting edge-level traffic directly.
        profile = MODE_TRAFFIC_MULTIPLIER[mode]
        for edge in self.edges:
            edge["traffic"] = profile[edge["type"]]

    def update_traffic(self, current_time):
        """
        Dynamically update per-edge traffic based on time of day.

        Rush windows (24h clock):
            - 07:00 to 09:00
            - 16:00 to 19:00

        Effects:
            - Highways get strongest rush-hour congestion
            - Main roads moderate congestion
            - Small roads lighter congestion
            - Small random incidents can temporarily spike an edge
            - Smoothing avoids abrupt jumps between steps

        Args:
            current_time (float): simulation time in seconds
        """
        hour = (current_time / 3600.0) % 24.0
        is_rush = (7 <= hour < 9) or (16 <= hour < 19)
        self.traffic_mode = "rush_hour" if is_rush else "normal"

        if is_rush:
            ranges = {
                "highway": (1.6, 2.5),
                "main": (1.4, 2.1),
                "small": (1.1, 1.6),
            }
        else:
            ranges = {
                "highway": (0.85, 1.15),
                "main": (0.9, 1.2),
                "small": (0.85, 1.1),
            }

        for edge in self.edges:
            low, high = ranges[edge["type"]]
            target = random.uniform(low, high)

            # Rare incident can temporarily increase congestion.
            if random.random() < 0.02:
                target = max(target, random.uniform(2.0, 2.8))

            old = float(edge.get("traffic", 1.0))
            smoothed = 0.7 * old + 0.3 * target
            edge["traffic"] = max(0.7, min(3.0, smoothed))

    # ------------------------------------------------------------------
    # Core calculations
    # ------------------------------------------------------------------

    def travel_time(self, edge):
        """
        Compute travel time in seconds for a given edge.

        Formula: time = (distance / base_speed) * traffic_factor

        Args:
            edge (dict): an edge dict with keys 'length', 'type', and optional
                         'traffic' congestion factor.

        Returns:
            float: travel time in seconds
        """
        speed_kmh = BASE_SPEED_KMH[edge["type"]]
        speed_ms = speed_kmh * 1000 / 3600  # convert km/h to m/s
        traffic = float(edge.get("traffic", 1.0))
        return (edge["length"] / speed_ms) * traffic

    def haversine(self, node_a_id, node_b_id):
        """
        Straight-line geographic distance between two nodes in meters.
        Uses the Haversine formula for Earth-surface distance.

        Used as the A* heuristic — always admissible because straight-line
        distance never overestimates the true road distance.

        Args:
            node_a_id (int): source node ID
            node_b_id (int): target node ID

        Returns:
            float: distance in meters
        """
        a = self.nodes[node_a_id]
        b = self.nodes[node_b_id]
        R = 6_371_000  # Earth radius in meters
        lat1 = math.radians(a["lat"])
        lat2 = math.radians(b["lat"])
        dlat = lat2 - lat1
        dlon = math.radians(b["lon"] - a["lon"])
        x = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        return 2 * R * math.asin(math.sqrt(x))

    def heuristic(self, node_a_id, node_b_id):
        """
        Time-based A* heuristic: optimistic travel time assuming highway speed.

        Admissible because we assume the best possible speed everywhere,
        so we never overestimate the true travel time.

        Args:
            node_a_id (int): current node ID
            node_b_id (int): goal node ID

        Returns:
            float: estimated travel time in seconds
        """
        dist = self.haversine(node_a_id, node_b_id)
        max_speed_ms = 90 * 1000 / 3600  # highway speed in m/s
        return dist / max_speed_ms

    # ------------------------------------------------------------------
    # Graph traversal helpers
    # ------------------------------------------------------------------

    def neighbors(self, node_id):
        """
        Return all neighbors of a node with their travel times.
        Used by A* to expand nodes.

        Args:
            node_id (int): the node to expand

        Returns:
            list of (neighbor_id, travel_time_seconds)
        """
        return [
            (neighbor, self.travel_time(edge))
            for neighbor, edge in self.adjacency[node_id]
        ]

    def get_node_ids(self):
        """Return all node IDs in the graph."""
        return list(self.nodes.keys())

    def get_nodes_by_type(self, node_type):
        """
        Return node IDs filtered by type.

        Args:
            node_type (str): "intersection", "hospital", or "depot"

        Returns:
            list of node IDs
        """
        return [nid for nid, n in self.nodes.items() if n["type"] == node_type]

    # ------------------------------------------------------------------
    # Debug helper
    # ------------------------------------------------------------------

    def summary(self):
        """Print a summary of the graph."""
        print(f"CityGraph loaded:")
        print(f"  Nodes       : {len(self.nodes)}")
        print(f"  Edges       : {len(self.edges)}")
        print(f"  Hospitals   : {len(self.get_nodes_by_type('hospital'))}")
        print(f"  Depots      : {len(self.get_nodes_by_type('depot'))}")
        print(f"  Traffic mode: {self.traffic_mode}")
