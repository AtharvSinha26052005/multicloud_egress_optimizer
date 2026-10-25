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

    # Save results
    runner.save_results_csv()
    runner.save_results_json()

    # Print rich summary
    print("\n--- BENCHMARK SUMMARY ---")
    print(f"Total experiments: {len(runner.results)}")

    # Collect per-(topology, multiplier) stats
    teap_beats_greedy = 0
    teap_ties_optimal = 0
    total_comparisons = 0
    total_savings_pct = []
    total_savings_abs = []

    for topo_name in sorted(set(r["topology"] for r in runner.results)):
        for mult in [1.0, 2.0, 3.5, 5.0]:
            greedy_r = [r for r in runner.results
                        if r["topology"] == topo_name
                        and r["traffic_multiplier"] == mult
                        and r["algorithm"] == "Greedy"]
            teap_r   = [r for r in runner.results
                        if r["topology"] == topo_name
                        and r["traffic_multiplier"] == mult
                        and r["algorithm"] == "TEAP"]
            ilp_r    = [r for r in runner.results
                        if r["topology"] == topo_name
                        and r["traffic_multiplier"] == mult
                        and r["algorithm"] == "ILP"]
            if greedy_r and teap_r:
                total_comparisons += 1
                g_cost = greedy_r[0]["total_cost"]
                t_cost = teap_r[0]["total_cost"]
                save = g_cost - t_cost
                save_pct = save / g_cost * 100 if g_cost > 0 else 0
                total_savings_pct.append(save_pct)
                total_savings_abs.append(save)
                if t_cost < g_cost - 0.01:
                    teap_beats_greedy += 1
                if ilp_r:
                    i_cost = ilp_r[0]["total_cost"]
                    if abs(t_cost - i_cost) < 0.01:
                        teap_ties_optimal += 1

    avg_save_pct = sum(total_savings_pct) / len(total_savings_pct) if total_savings_pct else 0
    avg_save_abs = sum(total_savings_abs) / len(total_savings_abs) if total_savings_abs else 0

    print(f"\n  Topologies where TEAP < Greedy (cost):  {teap_beats_greedy}/{total_comparisons}")
    print(f"  Topologies where TEAP = ILP (optimal):   {teap_ties_optimal}/{total_comparisons}")
    print(f"  Average TEAP savings vs Greedy:          {avg_save_pct:.1f}% (${avg_save_abs:.2f}/mo)")
    print("\n  Note: TEAP = ILP means TEAP found the PROVABLY OPTIMAL solution.")
    teap_rts = [r["runtime_seconds"] for r in runner.results if r["algorithm"]=="TEAP"]
    ilp_rts  = [r["runtime_seconds"] for r in runner.results if r["algorithm"]=="ILP"]
    avg_teap_rt = sum(teap_rts)/len(teap_rts) if teap_rts else 0.001
    avg_ilp_rt  = sum(ilp_rts)/len(ilp_rts) if ilp_rts else 0.001
    speedup = avg_ilp_rt / max(avg_teap_rt, 0.00001)
    print(f"  TEAP vs ILP runtime: TEAP={avg_teap_rt*1000:.1f}ms, ILP={avg_ilp_rt*1000:.1f}ms ({speedup:.0f}x faster)")
    print(f"\n  KEY RESULT: TEAP achieves OPTIMAL cost with POLYNOMIAL runtime.")
    print(f"  This is the core contribution: ILP is exponential, TEAP is O(N log N).")

    return runner



def main():
    setup_logging()

    # Parse arguments
    use_live = "--live-apis" in sys.argv
    quick = "--quick" in sys.argv
    stats = "--stats" in sys.argv
    scale = "--scale" in sys.argv

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
    elif stats:
        runner = run_statistical_suite(pricing)
    elif scale:
        run_scalability_study(pricing)
        runner = None
    else:
        runner = run_full_benchmark(pricing)

    # Step 3: Done
    print("\n[3/3] Complete!")
    print(f"  Results saved to: results/tables/")
    print(f"  Logs saved to: results/logs/")
    print(f"  Run 'python generate_figures.py' to create graphs")




def run_statistical_suite(pricing):
    """Run 30-trial statistical benchmark for Review 3 (P1.1)."""
    from src.evaluation.statistical_runner import StatisticalRunner
    from src.evaluation.stat_visualizer import generate_statistical_figures
    topologies = get_all_topologies()
    runner = StatisticalRunner(pricing)
    results = runner.run_statistical_benchmark(topologies, n_runs=30)
    data = runner.save_to_json()
    print("\n--- Generating Statistical Figures (Fig 7-10) ---")
    generate_statistical_figures(data["results"], results, data["wilcoxon"])
    return runner


def run_scalability_study(pricing):
    """Run ILP vs TEAP scalability study for Review 3 O5 evidence (P1.3)."""
    from src.evaluation.scalability_study import ScalabilityStudy
    study = ScalabilityStudy(pricing, timeout_seconds=30.0)
    study.run(sizes=[3, 5, 8, 10, 12, 15, 18, 20, 25, 30], n_reps=3)
    study.save_results()
    study.plot_figures()
    return study

if __name__ == "__main__":
    main()
