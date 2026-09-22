"""
Parameter Sweep — How does cost change as traffic volume increases?

Sweeps traffic from 100 to 2000 GB/month and compares Greedy vs TEAP.
Finds the crossover point where TEAP's advantage exceeds 15%.
"""

from typing import List, Dict
from src.pricing.unified_model import PricingModel
from src.algorithms.greedy import GreedySolver
from src.algorithms.teap import TEAPSolver
from src.algorithms.ilp_solver import ILPSolver


class ParameterSweeper:
    """Sweep traffic volume and compare algorithms."""

    def __init__(self, pricing: PricingModel):
        self.pricing = pricing
        self.results: List[Dict] = []

    def sweep_traffic(self, topology, volumes: List[float] = None) -> List[Dict]:
        """
        Run greedy, ILP, and TEAP at each traffic volume.

        Args:
            topology: Base topology to scale
            volumes: List of traffic multipliers. Default: 0.5x to 10x

        Returns:
            List of result dicts with traffic_multiplier, greedy_cost, teap_cost, gap
        """
        if volumes is None:
            volumes = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]

        print(f"\n--- Parameter Sweep: {topology.name} ---")
        print(f"{'Multiplier':>12} {'Greedy':>10} {'ILP':>10} {'TEAP':>10} {'Gap%':>8}")
        print("-" * 55)

        greedy = GreedySolver()
        ilp = ILPSolver()
        teap = TEAPSolver()

        for mult in volumes:
            scaled = topology.scale_traffic(mult)

            g_result = greedy.solve(scaled, self.pricing)
            i_result = ilp.solve(scaled, self.pricing)
            t_result = teap.solve(scaled, self.pricing)

            gap = ((g_result.cost.total - t_result.cost.total) / g_result.cost.total) * 100

            record = {
                "topology": topology.name,
                "traffic_multiplier": mult,
                "greedy_cost": g_result.cost.total,
                "ilp_cost": i_result.cost.total,
                "teap_cost": t_result.cost.total,
                "gap_pct": round(gap, 2),
            }
            self.results.append(record)

            print(f"{mult:>12.1f}x ${g_result.cost.total:>8.2f} ${i_result.cost.total:>8.2f} "
                  f"${t_result.cost.total:>8.2f} {gap:>7.1f}%")

        # Find crossover point where gap > 15%
        crossover = None
        for r in self.results:
            if r["topology"] == topology.name and r["gap_pct"] >= 15.0:
                crossover = r["traffic_multiplier"]
                break

        if crossover:
            print(f"\n  >> 15% threshold crossed at {crossover}x traffic multiplier")
        else:
            print(f"\n  >> 15% threshold not reached in this sweep range")

        return self.results
