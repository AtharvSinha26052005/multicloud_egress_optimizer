#!/usr/bin/env python3
"""
Generate all figures for Review 2.
Runs: full benchmark + ablation study + parameter sweep + 6 charts.

Usage: python generate_figures.py
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Fix Windows console encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from src.pricing.unified_model import PricingModel
from src.topology import get_all_topologies
from src.topology.three_tier import create_three_tier_topology
from src.topology.codecourt import create_codecourt_topology
from src.evaluation.benchmark import BenchmarkRunner
from src.evaluation.ablation import AblationRunner
from src.evaluation.parameter_sweep import ParameterSweeper
from src.evaluation.visualizer import generate_all_figures


def main():
    print("=" * 60)
    print("  P5 Review 2 - Full Results + Figure Generation")
    print("=" * 60)

    # 1. Load pricing
    pricing = PricingModel()
    print(f"\nPricing: {pricing.source}")

    # 2. Run full benchmark
    print("\n[1/4] Running full benchmark...")
    topologies = get_all_topologies()
    runner = BenchmarkRunner(pricing)
    runner.run_all(topologies, traffic_multipliers=[1.0, 2.0, 3.5, 5.0])
    runner.save_results_csv()
    runner.save_results_json()

    # 3. Run ablation study
    print("\n[2/4] Running ablation study...")
    ablation = AblationRunner(pricing)
    ablation_results = ablation.run(topologies, traffic_multiplier=3.5)

    # 4. Run parameter sweep on 3-Tier and CodeCourt
    print("\n[3/4] Running parameter sweep...")
    sweeper = ParameterSweeper(pricing)
    sweep_results = sweeper.sweep_traffic(create_three_tier_topology())
    sweep_results += sweeper.sweep_traffic(create_codecourt_topology())

    # 5. Generate all figures
    print("\n[4/4] Generating figures...")
    generate_all_figures(
        benchmark_results=runner.results,
        ablation_results=ablation_results,
        sweep_results=sweep_results,
    )

    print("\n" + "=" * 60)
    print("  DONE! All results and figures generated.")
    print(f"  Figures: results/figures/")
    print(f"  Tables:  results/tables/")
    print("=" * 60)


if __name__ == "__main__":
    main()
