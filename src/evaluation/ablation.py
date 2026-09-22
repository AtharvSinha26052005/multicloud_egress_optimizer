"""
Ablation Study — Tests which phases of TEAP contribute most to its performance.

For the Review 2 rubric: "Ablation or parameter sweep — Which component
actually causes the gain, or how the result moves with load, scale or cost."

We run 4 TEAP variants:
1. TEAP-full (all 5 phases) — the complete algorithm
2. TEAP-no-clustering (skip Phase 2) — no Louvain community detection
3. TEAP-no-asymmetry (skip Phase 3) — ignore egress rate differences
4. TEAP-no-ILP (skip Phase 4) — no ILP refinement, use greedy assignment
"""

import logging
from typing import List, Dict

from src.pricing.unified_model import PricingModel
from src.algorithms.teap import TEAPSolver
from src.algorithms.greedy import GreedySolver

logger = logging.getLogger(__name__)


class AblationRunner:
    """Runs TEAP with different phases disabled to measure their contribution."""

    def __init__(self, pricing: PricingModel):
        self.pricing = pricing
        self.results: List[Dict] = []

        # TEAP variants for ablation
        self.variants = [
            ("Greedy (baseline)", GreedySolver()),
            ("TEAP-full", TEAPSolver(use_ilp_refinement=True, use_clustering=True, use_asymmetry=True)),
            ("TEAP-no-clustering", TEAPSolver(use_ilp_refinement=True, use_clustering=False, use_asymmetry=True)),
            ("TEAP-no-asymmetry", TEAPSolver(use_ilp_refinement=True, use_clustering=True, use_asymmetry=False)),
            ("TEAP-no-ILP", TEAPSolver(use_ilp_refinement=False, use_clustering=True, use_asymmetry=True)),
        ]

    def run(self, topologies, traffic_multiplier: float = 3.5) -> List[Dict]:
        """
        Run ablation study across all topologies at a fixed traffic level.

        Args:
            topologies: List of Topology objects
            traffic_multiplier: Traffic scaling factor (3.5x = medium-high traffic)

        Returns:
            List of result dicts
        """
        print("\n" + "="*70)
        print("  ABLATION STUDY - TEAP Phase Contribution Analysis")
        print(f"  Traffic: x{traffic_multiplier}")
        print("="*70 + "\n")

        for topology in topologies:
            scaled = topology.scale_traffic(traffic_multiplier) if traffic_multiplier != 1.0 else topology
            print(f"--- {topology.name} ---")

            for variant_name, solver in self.variants:
                result = solver.solve(scaled, self.pricing)

                record = {
                    "topology": topology.name,
                    "variant": variant_name,
                    "compute_cost": result.cost.compute,
                    "egress_cost": result.cost.egress,
                    "total_cost": result.cost.total,
                    "runtime_seconds": result.runtime_seconds,
                }
                self.results.append(record)
                print(f"  {variant_name:25s} -> ${result.cost.total:.2f} "
                      f"(compute=${result.cost.compute:.2f}, egress=${result.cost.egress:.2f})")

            # Show phase contribution
            full = [r for r in self.results if r["topology"] == topology.name and r["variant"] == "TEAP-full"]
            greedy = [r for r in self.results if r["topology"] == topology.name and r["variant"] == "Greedy (baseline)"]
            if full and greedy:
                saving = greedy[0]["total_cost"] - full[0]["total_cost"]
                pct = (saving / greedy[0]["total_cost"]) * 100
                if saving > 0:
                    print(f"  >> TEAP saves ${saving:.2f}/mo ({pct:.1f}%) over Greedy")
                else:
                    print(f"  >> Same cost (topology favors single-provider)")
            print()

        return self.results
