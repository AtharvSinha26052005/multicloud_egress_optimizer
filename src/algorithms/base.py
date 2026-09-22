"""
Abstract base class for all placement solvers.
Every algorithm (Greedy, ILP, SA, TEAP) implements this interface.
"""

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict

from src.pricing.unified_model import PricingModel, CostBreakdown


@dataclass
class PlacementResult:
    """Result of running a placement algorithm."""
    placement: Dict[str, str]       # {component_name: provider_name}
    cost: CostBreakdown             # Detailed cost breakdown
    runtime_seconds: float = 0.0    # Wall-clock time to solve
    solver_name: str = ""           # Name of the algorithm
    metadata: Dict = field(default_factory=dict)  # Algorithm-specific info


class PlacementSolver(ABC):
    """
    Abstract base class for placement solvers.

    All algorithms implement solve() which takes a topology and pricing model,
    and returns a PlacementResult with the best placement found.
    """

    name: str = "AbstractSolver"

    @abstractmethod
    def _solve_impl(self, topology, pricing: PricingModel) -> Dict[str, str]:
        """
        Internal solve method. Subclasses implement this.

        Args:
            topology: Topology object with components and traffic_matrix
            pricing: PricingModel for computing costs

        Returns:
            Dict mapping component_name → provider_name
        """
        pass

    def solve(self, topology, pricing: PricingModel) -> PlacementResult:
        """
        Public solve method. Wraps _solve_impl with timing and cost calculation.

        Args:
            topology: Topology object
            pricing: PricingModel

        Returns:
            PlacementResult with placement, cost breakdown, and timing
        """
        start = time.perf_counter()
        placement = self._solve_impl(topology, pricing)
        elapsed = time.perf_counter() - start

        # Calculate total cost using the unified pricing model
        cost = pricing.get_total_cost(placement, topology)

        return PlacementResult(
            placement=placement,
            cost=cost,
            runtime_seconds=round(elapsed, 6),
            solver_name=self.name,
        )
