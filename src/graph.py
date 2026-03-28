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


# Speed limits in km/h per road type and traffic mode
SPEED_KMH = {
    "highway": {"normal": 90, "rush_hour": 50},
    "main":    {"normal": 50, "rush_hour": 25},
    "small":   {"normal": 30, "rush_hour": 15},
}


class CityGraph:
    def __init__(self, nodes_path, edges_path):
        """
        Load graph from JSON files.

        Args:
            nodes_path (str): path to nodes.json
            edges_path (str): path to edges.json
        """
        with open(nodes_path) as f:
            nodes_data = json.load(f)
        with open(edges_path) as f:
            edges_data = json.load(f)

        # nodes: dict { node_id -> {id, lat, lon, type, name} }
        self.nodes = {n["id"]: n for n in nodes_data}

        # adjacency: dict { node_id -> list of (neighbor_id, edge_dict) }
        self.adjacency = {n["id"]: [] for n in nodes_data}
        for edge in edges_data:
            self.adjacency[edge["from"]].append((edge["to"], edge))

        self.edges = edges_data
        self.traffic_mode = "normal"  # "normal" or "rush_hour"

    # ------------------------------------------------------------------
    # Traffic control
    # ------------------------------------------------------------------

    def set_traffic(self, mode):
        """
        Switch traffic mode. Affects all subsequent travel_time() calls.

        Args:
            mode (str): "normal" or "rush_hour"
        """
        if mode not in ("normal", "rush_hour"):
            raise ValueError(f"Unknown traffic mode: {mode}")
        self.traffic_mode = mode

    # ------------------------------------------------------------------
    # Core calculations
    # ------------------------------------------------------------------

    def travel_time(self, edge):
        """
        Compute travel time in seconds for a given edge.

        Formula: time = distance / speed
        Speed is determined by road type and current traffic mode.

        Args:
            edge (dict): an edge dict with keys 'length' and 'type'

        Returns:
            float: travel time in seconds
        """
        speed_kmh = SPEED_KMH[edge["type"]][self.traffic_mode]
        speed_ms = speed_kmh * 1000 / 3600  # convert km/h to m/s
        return edge["length"] / speed_ms

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
