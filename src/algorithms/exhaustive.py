"""
Exhaustive Solver — Brute-force enumeration.

Strategy: Try every possible placement (P^N combinations), compute
           total cost for each, return the global minimum.

Purpose: Ground truth. Used to verify that ILP and TEAP actually find
         the optimal solution for small topologies.

Time complexity: O(P^N) — only feasible for N ≤ 6 components
"""

import itertools
from typing import Dict
from src.algorithms.base import PlacementSolver
from src.pricing.unified_model import PricingModel


class ExhaustiveSolver(PlacementSolver):
    """
    Enumerate all P^N placements and return the cheapest.
    Only runs if num_components ≤ 6 (otherwise falls back to greedy).
    """

    name = "Exhaustive"
    MAX_COMPONENTS = 6  # 3^6 = 729, still fast. 3^7 = 2187, borderline.

    def _solve_impl(self, topology, pricing: PricingModel) -> Dict[str, str]:
        components = topology.components

        # Safety check: don't brute-force huge topologies
        if len(components) > self.MAX_COMPONENTS:
            # Fall back to ILP for large topologies
            from src.algorithms.ilp_solver import ILPSolver
            return ILPSolver()._solve_impl(topology, pricing)

        best_placement = None
        best_cost = float("inf")
        total_evaluated = 0

        # Generate all possible assignments: each component → one of P providers
        provider_options = [pricing.providers for _ in components]

        for assignment in itertools.product(*provider_options):
            placement = {
                comp.name: provider
                for comp, provider in zip(components, assignment)
            }
            cost = pricing.get_total_cost(placement, topology)
            total_evaluated += 1

            if cost.total < best_cost:
                best_cost = cost.total
                best_placement = placement

        return best_placement
