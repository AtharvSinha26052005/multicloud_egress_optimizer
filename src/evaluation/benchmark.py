"""
Benchmark Runner — Runs all algorithms across all topologies and traffic levels.

This is the core evaluation framework that produces the comparative results
needed for Review 2 (rubric: "Comparative results vs baseline — 3 marks").
"""

import csv
import json
import os
import logging
from typing import List, Dict
from tabulate import tabulate

from src.pricing.unified_model import PricingModel
from src.algorithms.base import PlacementResult
from src.algorithms.greedy import GreedySolver
from src.algorithms.single_provider import SingleProviderSolver
from src.algorithms.exhaustive import ExhaustiveSolver
from src.algorithms.ilp_solver import ILPSolver
from src.algorithms.simulated_annealing import SASolver
from src.algorithms.teap import TEAPSolver

logger = logging.getLogger(__name__)


class BenchmarkRunner:
    """
    Runs all algorithms on all topologies at multiple traffic levels.
    Records results as structured data for visualization and analysis.
    """

    def __init__(self, pricing: PricingModel, output_dir: str = "results"):
        self.pricing = pricing
        self.output_dir = output_dir
        self.results: List[Dict] = []

        # Create output directories
        os.makedirs(os.path.join(output_dir, "figures"), exist_ok=True)
        os.makedirs(os.path.join(output_dir, "tables"), exist_ok=True)
        os.makedirs(os.path.join(output_dir, "logs"), exist_ok=True)

        # All solvers to benchmark
        self.solvers = [
            GreedySolver(),
            SingleProviderSolver(),
            ExhaustiveSolver(),
            ILPSolver(),
            SASolver(),
            TEAPSolver(),
        ]

    def run_single(self, topology, solver, traffic_multiplier: float = 1.0) -> Dict:
        """Run one algorithm on one topology at one traffic level."""
        # Scale traffic if needed
        if traffic_multiplier != 1.0:
            topo = topology.scale_traffic(traffic_multiplier)
        else:
            topo = topology

        # Solve
        result = solver.solve(topo, self.pricing)

        # Record
        record = {
            "topology": topology.name,
            "num_components": topology.num_components,
            "traffic_multiplier": traffic_multiplier,
            "algorithm": result.solver_name,
            "compute_cost": result.cost.compute,
            "egress_cost": result.cost.egress,
            "total_cost": result.cost.total,
            "runtime_seconds": result.runtime_seconds,
            "placement": result.placement,
        }

        self.results.append(record)
        return record

    def run_all(self, topologies, traffic_multipliers: List[float] = None):
        """
        Run all solvers on all topologies at all traffic levels.
        This is the main entry point for the full benchmark suite.
        """
        if traffic_multipliers is None:
            traffic_multipliers = [1.0, 2.0, 3.5, 5.0]  # ≈ 200, 400, 700, 1000 GB

        total_runs = len(topologies) * len(traffic_multipliers) * len(self.solvers)
        completed = 0

        print(f"\n{'='*70}")
        print(f"  BENCHMARK SUITE: {total_runs} experiments")
        print(f"  Topologies: {len(topologies)} | Traffic levels: {len(traffic_multipliers)} | Algorithms: {len(self.solvers)}")
        print(f"{'='*70}\n")

        for topology in topologies:
            for multiplier in traffic_multipliers:
                print(f"--- {topology.name} (traffic x{multiplier}) ---")
                rows = []

                for solver in self.solvers:
                    try:
                        record = self.run_single(topology, solver, multiplier)
                        rows.append([
                            record["algorithm"],
                            f"${record['compute_cost']:.2f}",
                            f"${record['egress_cost']:.2f}",
                            f"${record['total_cost']:.2f}",
                            f"{record['runtime_seconds']*1000:.1f}ms",
                        ])
                        completed += 1
                    except Exception as e:
                        logger.error(f"FAILED: {solver.name} on {topology.name}: {e}")
                        rows.append([solver.name, "ERROR", "ERROR", "ERROR", str(e)[:20]])
                        completed += 1

                # Print results table for this topology+traffic combo
                print(tabulate(rows,
                    headers=["Algorithm", "Compute", "Egress", "Total", "Runtime"],
                    tablefmt="grid"))

                # Find optimal and show % gap for each algorithm
                costs = [r["total_cost"] for r in self.results[-len(self.solvers):]
                         if isinstance(r.get("total_cost"), (int, float))]
                if costs:
                    optimal = min(costs)
                    print(f"  Optimal: ${optimal:.2f}")
                    for r in self.results[-len(self.solvers):]:
                        if isinstance(r.get("total_cost"), (int, float)):
                            gap = ((r["total_cost"] - optimal) / optimal) * 100
                            if gap > 0:
                                print(f"  {r['algorithm']}: +{gap:.1f}% over optimal")
                print()

        print(f"\n{'='*70}")
        print(f"  COMPLETED: {completed}/{total_runs} experiments")
        print(f"{'='*70}\n")

        return self.results

    def save_results_csv(self, filename: str = None):
        """Save all results to CSV for further analysis."""
        if filename is None:
            filename = os.path.join(self.output_dir, "tables", "benchmark_results.csv")

        with open(filename, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "topology", "num_components", "traffic_multiplier",
                "algorithm", "compute_cost", "egress_cost", "total_cost",
                "runtime_seconds",
            ])
            writer.writeheader()
            for r in self.results:
                row = {k: v for k, v in r.items() if k != "placement"}
                writer.writerow(row)

        print(f"Results saved to {filename}")

    def save_results_json(self, filename: str = None):
        """Save all results to JSON."""
        if filename is None:
            filename = os.path.join(self.output_dir, "tables", "benchmark_results.json")

        # Convert placement dicts to JSON-serializable format
        with open(filename, "w") as f:
            json.dump(self.results, f, indent=2, default=str)

        print(f"Results saved to {filename}")

    def get_results_for_topology(self, topology_name: str) -> List[Dict]:
        """Filter results by topology name."""
        return [r for r in self.results if r["topology"] == topology_name]

    def get_results_for_algorithm(self, algorithm_name: str) -> List[Dict]:
        """Filter results by algorithm name."""
        return [r for r in self.results if r["algorithm"] == algorithm_name]
