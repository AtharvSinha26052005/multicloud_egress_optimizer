#!/usr/bin/env python3
"""
P5 — Egress-Aware Cost-Optimal Multi-Cloud Placement
Main entry point: run all experiments, generate results.

Usage:
    python run_experiments.py              # Full benchmark (100 experiments)
    python run_experiments.py --quick      # Quick test (3-tier only, 1 traffic level)
    python run_experiments.py --live-apis  # Use live AWS/Azure/GCP pricing APIs

This script:
1. Loads pricing data (fallback or live APIs)
2. Defines 5 application topologies
3. Runs 5 algorithms on each topology at 4 traffic levels
4. Prints comparative results as tables
5. Saves results to CSV and JSON
"""

import sys
import os
import logging

# Fix Windows console encoding (cp1252 can't handle all characters)
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.pricing.unified_model import PricingModel
from src.topology import get_all_topologies
from src.topology.three_tier import create_three_tier_topology
from src.evaluation.benchmark import BenchmarkRunner


def setup_logging():
    """Configure logging to both console and file."""
    os.makedirs("results/logs", exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler("results/logs/experiment.log"),
            logging.StreamHandler(),
        ]
    )


def run_quick_test(pricing: PricingModel):
    """Quick smoke test: 3-tier topology, baseline traffic, all algorithms."""
    print("\n" + "="*70)
    print("  QUICK TEST - 3-Tier Web App, Baseline Traffic")
    print("="*70)

    topology = create_three_tier_topology()
    runner = BenchmarkRunner(pricing)
    runner.run_all([topology], traffic_multipliers=[1.0])

    # Regression check against Review 1 numbers
    print("\n--- REGRESSION CHECK (Review 1 Numbers) ---")
    greedy_results = runner.get_results_for_algorithm("Greedy")
    if greedy_results:
        greedy_total = greedy_results[0]["total_cost"]
        expected = 304.41
        match = abs(greedy_total - expected) < 0.10
        print(f"  Greedy total: ${greedy_total:.2f} (expected: ${expected}) {'PASS' if match else 'FAIL'}")

    exhaustive_results = runner.get_results_for_algorithm("Exhaustive")
    if exhaustive_results:
        optimal_total = exhaustive_results[0]["total_cost"]
        expected = 285.70
        match = abs(optimal_total - expected) < 0.10
        print(f"  Optimal total: ${optimal_total:.2f} (expected: ${expected}) {'PASS' if match else 'FAIL'}")

    # Check TEAP matches optimal
    teap_results = runner.get_results_for_algorithm("TEAP")
    if teap_results and exhaustive_results:
        teap_total = teap_results[0]["total_cost"]
        optimal_total = exhaustive_results[0]["total_cost"]
        match = abs(teap_total - optimal_total) < 0.10
        print(f"  TEAP total: ${teap_total:.2f} (optimal: ${optimal_total:.2f}) {'MATCHES' if match else 'GAP'}")

    return runner


def run_full_benchmark(pricing: PricingModel):
    """Full benchmark: all topologies, all traffic levels, all algorithms."""
    print("\n" + "="*70)
    print("  FULL BENCHMARK - 5 Topologies x 4 Traffic Levels x 5+ Algorithms")
    print("="*70)

    topologies = get_all_topologies()
    runner = BenchmarkRunner(pricing)

    # Traffic multipliers: 1.0=base, 2.0=2x, 3.5=3.5x, 5.0=5x
    # For 3-tier: base App→DB = 200GB, so 5x = 1000GB
    runner.run_all(topologies, traffic_multipliers=[1.0, 2.0, 3.5, 5.0])

    # Save results
    runner.save_results_csv()
    runner.save_results_json()

    # Print summary
    print("\n--- SUMMARY ---")
    print(f"Total experiments: {len(runner.results)}")

    # Find cases where TEAP beats Greedy
    teap_wins = 0
    total_comparisons = 0
    for topo_name in set(r["topology"] for r in runner.results):
        for mult in [1.0, 2.0, 3.5, 5.0]:
            greedy = [r for r in runner.results
                      if r["topology"] == topo_name
                      and r["traffic_multiplier"] == mult
                      and r["algorithm"] == "Greedy"]
            teap = [r for r in runner.results
                    if r["topology"] == topo_name
                    and r["traffic_multiplier"] == mult
                    and r["algorithm"] == "TEAP"]
            if greedy and teap:
                total_comparisons += 1
                if teap[0]["total_cost"] < greedy[0]["total_cost"]:
                    teap_wins += 1

    if total_comparisons > 0:
        print(f"TEAP beats Greedy in {teap_wins}/{total_comparisons} scenarios ({teap_wins/total_comparisons*100:.0f}%)")

    return runner


def main():
    setup_logging()

    # Parse arguments
    use_live = "--live-apis" in sys.argv
    quick = "--quick" in sys.argv

    print("\n" + "+" + "="*68 + "+")
    print("|  P5 - Egress-Aware Cost-Optimal Multi-Cloud Placement            |")
    print("|  Review 2: Implementation and Preliminary Results                 |")
    print("+" + "="*68 + "+")

    # Step 1: Load pricing
    print("\n[1/3] Loading pricing data...")
    pricing = PricingModel(use_live_apis=use_live)
    print(f"  Source: {pricing.source}")
    print(f"  Providers: {pricing.providers}")

    # Step 2: Run experiments
    print("\n[2/3] Running experiments...")
    if quick:
        runner = run_quick_test(pricing)
    else:
        runner = run_full_benchmark(pricing)

    # Step 3: Done
    print("\n[3/3] Complete!")
    print(f"  Results saved to: results/tables/")
    print(f"  Logs saved to: results/logs/")
    print(f"  Run 'python generate_figures.py' to create graphs")


if __name__ == "__main__":
    main()
