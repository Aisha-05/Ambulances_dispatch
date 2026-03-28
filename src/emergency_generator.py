"""
emergency_generator.py — Poisson-process emergency event generator.

Emergencies arrive randomly but with a known average rate (lambda).
The Poisson process is the standard model for random arrivals in
operations research and emergency services.

Key concept:
    If emergencies arrive at rate lambda per hour, the TIME BETWEEN
    consecutive emergencies follows an Exponential distribution with
    mean = 1/lambda. This is what random.expovariate() models.

Team A owns this file.
"""

import random


class EmergencyGenerator:
    def __init__(self, node_ids, rate_per_hour=6, seed=None):
        """
        Args:
            node_ids (list): list of node IDs where emergencies can occur.
                             Should only be intersection nodes (not hospitals/depots).
            rate_per_hour (float): average number of emergencies per hour (lambda).
                                   Default 6 = one every ~10 minutes, realistic for
                                   a mid-sized city district.
            seed (int, optional): random seed for reproducibility during testing.
        """
        if seed is not None:
            random.seed(seed)

        self.node_ids = node_ids
        self.rate_per_hour = rate_per_hour
        self.rate_per_second = rate_per_hour / 3600
        self._next_id = 0

    def time_until_next(self):
        """
        Sample the waiting time (in seconds) until the next emergency.

        Uses the Exponential distribution: inter-arrival times of a
        Poisson process are exponentially distributed.

        Returns:
            float: seconds until next emergency
        """
        return random.expovariate(self.rate_per_second)

    def generate(self, current_time):
        """
        Create a new emergency event at a random node.

        Args:
            current_time (float): current simulation time in seconds

        Returns:
            dict: emergency event with all required fields
        """
        emergency = {
            "id":           self._next_id,
            "node":         random.choice(self.node_ids),
            "call_time":    current_time,
            "arrival_time": None,    # set when ambulance reaches the scene
            "hospital_time": None,   # set when patient is dropped at hospital
            "status":       "waiting",  # waiting | assigned | resolved
            "ambulance_id": None,    # set when an ambulance is assigned
        }
        self._next_id += 1
        return emergency

    def set_rate(self, rate_per_hour):
        """
        Adjust emergency rate at runtime (e.g., simulate rush-hour surge).

        Args:
            rate_per_hour (float): new arrival rate
        """
        self.rate_per_hour = rate_per_hour
        self.rate_per_second = rate_per_hour / 3600
