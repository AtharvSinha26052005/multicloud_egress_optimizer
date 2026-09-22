"""
Single Provider Solver — Baseline.

Strategy: Try placing everything on a single provider. Evaluate all-AWS,
           all-GCP, all-Azure, and return the cheapest.

This eliminates egress entirely (same provider = free transfer) but may
overpay on compute. Represents the "just use one cloud" alternative.

Time complexity: O(P) where P=providers
"""

from typing import Dict
from src.algorithms.base import PlacementSolver
from src.pricing.unified_model import PricingModel


class SingleProviderSolver(PlacementSolver):
    """Try all-on-one-cloud for each provider, return the cheapest."""

    name = "Single-Provider"

    def _solve_impl(self, topology, pricing: PricingModel) -> Dict[str, str]:
        best_placement = None
        best_cost = float("inf")

        for provider in pricing.providers:
            # Place everything on this one provider
            placement = {comp.name: provider for comp in topology.components}
            cost = pricing.get_total_cost(placement, topology)

            if cost.total < best_cost:
                best_cost = cost.total
                best_placement = placement

        return best_placement
