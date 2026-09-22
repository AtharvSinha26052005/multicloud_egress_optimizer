"""
Simulated Annealing Solver — Metaheuristic.

Strategy: Start from greedy solution. Iteratively make random changes
           (swap one component to a random provider). Accept improvements
           always; accept worse solutions with decreasing probability.
           This avoids getting stuck in local minima.

Based on: Kirkpatrick et al., "Optimization by Simulated Annealing", Science 1983.

Time complexity: O(iterations × N × P) — configurable, default 1000 iterations
"""

import random
import math
from typing import Dict
from src.algorithms.base import PlacementSolver
from src.algorithms.greedy import GreedySolver
from src.pricing.unified_model import PricingModel


class SASolver(PlacementSolver):
    """
    Simulated Annealing heuristic for placement optimisation.

    Starts from greedy solution, makes random swaps, uses temperature-based
    acceptance to escape local minima. Converges to near-optimal solution.
    """

    name = "Simulated Annealing"

    def __init__(self, iterations: int = 1000, initial_temp: float = 100.0,
                 cooling_rate: float = 0.995, seed: int = 42):
        self.iterations = iterations
        self.initial_temp = initial_temp
        self.cooling_rate = cooling_rate
        self.seed = seed

    def _solve_impl(self, topology, pricing: PricingModel) -> Dict[str, str]:
        random.seed(self.seed)

        # Start from greedy solution as the initial state
        current = GreedySolver()._solve_impl(topology, pricing)
        current_cost = pricing.get_total_cost(current, topology).total

        best = current.copy()
        best_cost = current_cost

        temp = self.initial_temp

        for iteration in range(self.iterations):
            # Generate neighbour: swap one random component to a random provider
            neighbour = current.copy()
            comp = random.choice(topology.components)
            new_provider = random.choice(
                [p for p in pricing.providers if p != current[comp.name]]
            )
            neighbour[comp.name] = new_provider

            # Evaluate neighbour
            neighbour_cost = pricing.get_total_cost(neighbour, topology).total
            delta = neighbour_cost - current_cost

            # Accept or reject
            if delta < 0:
                # Improvement — always accept
                current = neighbour
                current_cost = neighbour_cost
            elif temp > 0:
                # Worse — accept with probability e^(-delta/T)
                acceptance_prob = math.exp(-delta / temp)
                if random.random() < acceptance_prob:
                    current = neighbour
                    current_cost = neighbour_cost

            # Track best solution found
            if current_cost < best_cost:
                best = current.copy()
                best_cost = current_cost

            # Cool down
            temp *= self.cooling_rate

        return best
