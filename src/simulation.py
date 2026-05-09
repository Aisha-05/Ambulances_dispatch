"""
simulation.py — Core simulation loop for the Ambulance Dispatch system.

This module ties together all components:
    - CityGraph (road network)
    - EmergencyGenerator (Poisson arrivals)
    - Ambulance state machine (idle → en_route → transporting → idle)
    - Objective scoring

The simulation runs in discrete time steps (default: 30 seconds per tick).
At each tick:
    1. New emergencies may arrive (Poisson process).
    2. The dispatcher assigns idle ambulances to waiting emergencies.
    3. Ambulances in transit move closer to their destination.
    4. Arrived ambulances update the emergency record.

dispatch_mode controls which assignment strategy is used:
    - "simple"  : baseline haversine dispatcher (built-in, no import needed)
    - "greedy"  : greedy_assign() from assignment.py (haversine, same as simple but modular)
    - "astar"   : astar_assign() from assignment.py (actual A* travel time)

Team A owns this file.
"""

import json
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from graph import CityGraph
from emergency_generator import EmergencyGenerator
from objective import compute_avg_response_time, compute_coverage, print_metrics
from assignment import greedy_assign, astar_assign


class Simulation:
    def __init__(self, data_dir, time_step=30, dispatch_mode="greedy"):
        """
        Initialize the simulation from JSON data files.

        Args:
            data_dir (str): path to the Data/ folder containing JSON files
            time_step (int): seconds per simulation tick (default: 30)
            dispatch_mode (str): "simple", "greedy", or "astar"
        """
        nodes_path      = os.path.join(data_dir, "nodes.json")
        edges_path      = os.path.join(data_dir, "edges.json")
        hospitals_path  = os.path.join(data_dir, "hospitals.json")
        ambulances_path = os.path.join(data_dir, "ambulances.json")

        self.graph = CityGraph(nodes_path, edges_path)

        with open(hospitals_path) as f:
            self.hospitals = json.load(f)

        with open(ambulances_path) as f:
            self.ambulances = json.load(f)

        if dispatch_mode not in ("simple", "greedy", "astar"):
            raise ValueError(f"Unknown dispatch_mode '{dispatch_mode}'. Choose 'simple', 'greedy', or 'astar'.")
        self.dispatch_mode = dispatch_mode

        intersection_ids = self.graph.get_nodes_by_type("intersection")
        self.generator = EmergencyGenerator(intersection_ids, rate_per_hour=6)

        self.emergencies = []
        self.current_time = 0
        self.time_step = time_step
        self._pending_arrivals = {}
        self._next_emergency_time = self.generator.time_until_next()

        print("Simulation initialized.")
        print(f"  Dispatch mode: {self.dispatch_mode.upper()}")
        self.graph.summary()

    # ------------------------------------------------------------------
    # Traffic control
    # ------------------------------------------------------------------

    def set_rush_hour(self):
        """Legacy helper: apply static rush-hour profile."""
        self.graph.set_traffic("rush_hour")
        print(f"[t={self.current_time}s] Traffic mode: RUSH HOUR")

    def set_normal_traffic(self):
        """Legacy helper: apply static normal profile."""
        self.graph.set_traffic("normal")
        print(f"[t={self.current_time}s] Traffic mode: NORMAL")

    # ------------------------------------------------------------------
    # Ambulance state helpers
    # ------------------------------------------------------------------

    def get_idle_ambulances(self):
        """Return all ambulances currently idle."""
        return [a for a in self.ambulances if a["status"] == "idle"]

    def get_ambulance_by_id(self, ambulance_id):
        """Look up an ambulance by its ID."""
        return next((a for a in self.ambulances if a["id"] == ambulance_id), None)

    def nearest_hospital_node(self, node_id):
        """
        Find the hospital node closest to a given node by haversine distance.

        Args:
            node_id (int): the node to find a hospital near

        Returns:
            int: hospital node ID
        """
        return min(
            self.hospitals,
            key=lambda h: self.graph.haversine(node_id, h["node_id"])
        )["node_id"]

    # ------------------------------------------------------------------
    # Dispatcher (baseline — kept for "simple" mode and fallback)
    # ------------------------------------------------------------------

    def simple_assign(self, emergency):
        """
        BASELINE dispatcher: assign the closest idle ambulance by haversine distance.
        Used when dispatch_mode == "simple".

        Args:
            emergency (dict): the emergency event to assign

        Returns:
            dict or None: the assigned ambulance, or None if all are busy
        """
        idle = self.get_idle_ambulances()
        if not idle:
            return None
        return min(
            idle,
            key=lambda a: self.graph.haversine(a["position"], emergency["node"])
        )

    def assign_ambulance(self, ambulance, emergency):
        """
        Mark an ambulance as assigned to an emergency and schedule its arrival.

        Args:
            ambulance (dict): the ambulance to assign
            emergency (dict): the emergency to respond to
        """
        ambulance["status"] = "en_route"
        ambulance["target_emergency"] = emergency["id"]
        emergency["status"] = "assigned"
        emergency["ambulance_id"] = ambulance["id"]

        dist = self.graph.haversine(ambulance["position"], emergency["node"])
        travel_time = self.graph.travel_time({"length": dist, "type": "main"})

        arrival_time = self.current_time + travel_time
        self._pending_arrivals[ambulance["id"]] = ("scene", arrival_time, emergency["id"])

        print(f"  [ASSIGN] Ambulance {ambulance['id']} → Emergency {emergency['id']} "
              f"at node {emergency['node']} (ETA: {travel_time:.0f}s)")

    def resolve_emergency(self, ambulance, emergency):
        """
        Ambulance has reached the scene. Record arrival, begin transport.

        Args:
            ambulance (dict): the arriving ambulance
            emergency (dict): the emergency being resolved
        """
        emergency["arrival_time"] = self.current_time
        emergency["status"] = "resolved"
        ambulance["status"] = "transporting"
        ambulance["position"] = emergency["node"]

        hospital_id = self.nearest_hospital_node(emergency["node"])
        ambulance["destination"] = hospital_id

        dist = self.graph.haversine(emergency["node"], hospital_id)
        transport_time = self.graph.travel_time({"length": dist, "type": "main"})

        arrival_time = self.current_time + transport_time
        self._pending_arrivals[ambulance["id"]] = ("hospital", arrival_time, hospital_id)

        response_time = emergency["arrival_time"] - emergency["call_time"]
        print(f"  [ARRIVE] Ambulance {ambulance['id']} reached scene. "
              f"Response time: {response_time:.0f}s. "
              f"Transporting to hospital node {hospital_id}.")

    def finish_transport(self, ambulance, hospital_node):
        """
        Ambulance has dropped the patient at hospital. Return to idle.

        Args:
            ambulance (dict): the ambulance finishing transport
            hospital_node (int): the hospital node ID
        """
        emergency_id = ambulance.get("target_emergency")
        if emergency_id is not None:
            emergency = next((e for e in self.emergencies if e["id"] == emergency_id), None)
            if emergency is not None:
                emergency["hospital_time"] = self.current_time

        ambulance["status"] = "idle"
        ambulance["position"] = hospital_node
        ambulance.pop("destination", None)
        ambulance.pop("target_emergency", None)
        print(f"  [FREE]   Ambulance {ambulance['id']} is now idle at node {hospital_node}.")

    # ------------------------------------------------------------------
    # Main simulation loop
    # ------------------------------------------------------------------

    def _process_arrivals(self):
        """Check if any in-transit ambulances have reached their destination."""
        due = [
            (amb_id, phase, target)
            for amb_id, (phase, arrival_time, target) in list(self._pending_arrivals.items())
            if self.current_time >= arrival_time
        ]

        for amb_id, phase, target in due:
            entry = self._pending_arrivals.pop(amb_id, None)
            if entry is None:
                continue

            ambulance = self.get_ambulance_by_id(amb_id)
            if phase == "scene":
                emergency = next(e for e in self.emergencies if e["id"] == target)
                self.resolve_emergency(ambulance, emergency)
            elif phase == "hospital":
                self.finish_transport(ambulance, target)

    def _try_dispatch(self):
        """
        Assign idle ambulances to waiting emergencies using the chosen dispatch mode:
            - "simple" : built-in haversine baseline
            - "greedy" : greedy_assign() from assignment.py
            - "astar"  : astar_assign() from assignment.py
        """
        waiting = [e for e in self.emergencies if e["status"] == "waiting"]
        for emergency in waiting:
            if self.dispatch_mode == "astar":
                ambulance = astar_assign(self.graph, self.ambulances, emergency)
            elif self.dispatch_mode == "greedy":
                ambulance = greedy_assign(self.graph, self.ambulances, emergency)
            else:
                ambulance = self.simple_assign(emergency)

            if not ambulance:
                break
            self.assign_ambulance(ambulance, emergency)

    def step(self):
        """
        Advance the simulation by one time step.

        Order of operations each tick:
            1. Advance clock.
            2. Check if a new emergency arrives this tick.
            3. Process ambulances that have reached their destination.
            4. Dispatch idle ambulances to waiting emergencies.
        """
        tick_end = self.current_time + self.time_step

        while self._next_emergency_time <= tick_end:
            event_time = self._next_emergency_time
            new_e = self.generator.generate(event_time)
            self.emergencies.append(new_e)
            print(f"\n[t={event_time:.1f}s] *** EMERGENCY {new_e['id']} at node {new_e['node']} ***")
            self._next_emergency_time += self.generator.time_until_next()

        self.current_time = tick_end

        self.graph.update_traffic(self.current_time)

        self._process_arrivals()

        self._try_dispatch()

    def run(self, duration_seconds=3600, verbose=True):
        """
        Run the simulation for a given duration.

        Args:
            duration_seconds (int): how long to simulate (default: 1 hour)
            verbose (bool): print step-by-step output
        """
        print(f"\n{'='*50}")
        print(f"Starting simulation: {duration_seconds}s ({duration_seconds/3600:.1f} hours)")
        print(f"Dispatch mode: {self.dispatch_mode.upper()}")
        print(f"Traffic mode : {self.graph.traffic_mode}")
        print(f"{'='*50}\n")

        end_time = self.current_time + duration_seconds
        while self.current_time < end_time:
            self.step()

        print(f"\n{'='*50}")
        print("Simulation complete.")
        print_metrics(self.emergencies, self.ambulances, self.graph)

    def reset(self):
        """Reset simulation state (keep graph and config, clear events)."""
        for a in self.ambulances:
            a["status"] = "idle"
            a["position"] = a["depot"]
            a.pop("target_emergency", None)
            a.pop("destination", None)
        self.emergencies = []
        self.current_time = 0
        self._pending_arrivals = {}
        self.generator._next_id = 0
        self._next_emergency_time = self.generator.time_until_next()
        print("Simulation reset.")
