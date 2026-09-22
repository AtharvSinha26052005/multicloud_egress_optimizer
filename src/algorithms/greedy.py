"""
Greedy Solver — Baseline algorithm.

Strategy: For each component independently, pick the provider with the
           lowest compute cost. Ignore egress entirely.

This is the "standard practice" baseline that our research aims to beat.
Cloud cost calculators (AWS, GCP, Azure) all work this way — they show
you the cheapest VM without considering data transfer between services.

Time complexity: O(N × P) where N=components, P=providers
"""

from typing import Dict
from src.algorithms.base import PlacementSolver
from src.pricing.unified_model import PricingModel


class GreedySolver(PlacementSolver):
    """
    Cheapest-per-vCPU baseline.
    For each component, independently select the provider with lowest compute cost.
    Egress between components is NOT considered — this is the flaw we expose.
    """

    name = "Greedy"

    def _solve_impl(self, topology, pricing: PricingModel) -> Dict[str, str]:
        placement = {}
        for component in topology.components:
            # Pick the cheapest provider for this component's type
            best_provider, _ = pricing.get_cheapest_provider(component.component_type)
            placement[component.name] = best_provider
        return placement
