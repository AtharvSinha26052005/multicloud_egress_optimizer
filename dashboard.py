#!/usr/bin/env python3
"""
P5 Interactive CLI Dashboard
Live demo tool for Review 2 presentation.

Usage: python dashboard.py

Features:
- Menu-driven interface
- Run individual algorithms and see results instantly
- Compare algorithms side-by-side
- Show live parameter sweep with progress
- Display placement decisions visually
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from tabulate import tabulate
from src.pricing.unified_model import PricingModel
from src.topology import get_all_topologies
from src.topology.three_tier import create_three_tier_topology
from src.topology.codecourt import create_codecourt_topology
from src.algorithms.greedy import GreedySolver
from src.algorithms.single_provider import SingleProviderSolver
from src.algorithms.exhaustive import ExhaustiveSolver
from src.algorithms.ilp_solver import ILPSolver
from src.algorithms.simulated_annealing import SASolver
from src.algorithms.teap import TEAPSolver


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header():
    print()
    print("=" * 65)
    print("  P5 - Egress-Aware Cost-Optimal Multi-Cloud Placement")
    print("  Interactive Dashboard | Review 2 Demo")
    print("=" * 65)


def print_menu():
    print()
    print("  [1] Run all algorithms on a topology (side-by-side)")
    print("  [2] Show placement decisions (which component -> which cloud)")
    print("  [3] Live parameter sweep (watch cost grow with traffic)")
    print("  [4] Ablation study (which TEAP phase matters most)")
    print("  [5] Egress rate comparison (why direction matters)")
    print("  [6] CodeCourt case study (your real project)")
    print("  [7] Run full benchmark (120 experiments)")
    print("  [8] Pricing data explorer")
    print("  [0] Exit")
    print()


def choose_topology():
    topologies = get_all_topologies()
    print("\n  Available topologies:")
    for i, t in enumerate(topologies):
        print(f"    [{i+1}] {t.name} ({t.num_components} components, "
              f"{len(t.traffic_matrix)} edges)")
    choice = input("\n  Select topology [1-5]: ").strip()
    idx = int(choice) - 1 if choice.isdigit() else 0
    idx = max(0, min(idx, len(topologies) - 1))
    return topologies[idx]


def option1_compare_algorithms(pricing):
    """Run all algorithms on a topology and compare side-by-side."""
    topology = choose_topology()

    mult_input = input("  Traffic multiplier [1.0]: ").strip()
    mult = float(mult_input) if mult_input else 1.0

    scaled = topology.scale_traffic(mult) if mult != 1.0 else topology

    solvers = [
        GreedySolver(),
        SingleProviderSolver(),
        ExhaustiveSolver(),
        ILPSolver(),
        SASolver(),
        TEAPSolver(),
    ]

    print(f"\n  Running {len(solvers)} algorithms on {topology.name} (traffic x{mult})...\n")

    rows = []
    results = []
    for solver in solvers:
        start = time.time()
        result = solver.solve(scaled, pricing)
        elapsed = time.time() - start
        results.append(result)
        rows.append([
            result.solver_name,
            f"${result.cost.compute:.2f}",
            f"${result.cost.egress:.2f}",
            f"${result.cost.total:.2f}",
            f"{elapsed*1000:.1f}ms",
        ])

    print(tabulate(rows,
        headers=["Algorithm", "Compute", "Egress", "Total", "Runtime"],
        tablefmt="grid"))

    # Show gap analysis
    optimal = min(r.cost.total for r in results)
    print(f"\n  Optimal cost: ${optimal:.2f}")
    for r in results:
        gap = ((r.cost.total - optimal) / optimal) * 100
        if gap > 0:
            print(f"  {r.solver_name}: +${r.cost.total - optimal:.2f}/mo (+{gap:.1f}%) WASTED")
        else:
            print(f"  {r.solver_name}: OPTIMAL")


def option2_show_placements(pricing):
    """Show exactly which component goes to which cloud."""
    topology = choose_topology()

    solvers = [
        ("Greedy", GreedySolver()),
        ("TEAP", TEAPSolver()),
        ("ILP", ILPSolver()),
    ]

    print(f"\n  Placement decisions for: {topology.name}\n")

    for name, solver in solvers:
        result = solver.solve(topology, pricing)
        print(f"  --- {name} (Total: ${result.cost.total:.2f}) ---")

        rows = []
        for comp in topology.components:
            provider = result.placement[comp.name]
            cost = pricing.get_compute_cost(comp.component_type, provider)
            rows.append([comp.name, comp.description, provider, f"${cost:.2f}"])

        print(tabulate(rows,
            headers=["Component", "Role", "Provider", "Compute$/mo"],
            tablefmt="grid"))

        # Show egress details
        print(f"  Compute: ${result.cost.compute:.2f} | Egress: ${result.cost.egress:.2f}\n")


def option3_live_sweep(pricing):
    """Live parameter sweep - watch the gap grow in real-time."""
    topology = choose_topology()

    greedy = GreedySolver()
    teap = TEAPSolver()

    print(f"\n  Live Sweep: {topology.name}")
    print(f"  Watching Greedy vs TEAP as traffic increases...\n")
    print(f"  {'Traffic':>10} {'Greedy':>10} {'TEAP':>10} {'Savings':>10} {'Gap%':>8}  Bar")
    print("  " + "-" * 65)

    for mult in [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0, 6.0, 7.0, 8.0, 10.0]:
        scaled = topology.scale_traffic(mult)

        g = greedy.solve(scaled, pricing)
        t = teap.solve(scaled, pricing)

        savings = g.cost.total - t.cost.total
        gap = (savings / g.cost.total) * 100 if g.cost.total > 0 else 0

        # Visual bar
        bar_len = int(gap * 2)
        bar = "#" * bar_len

        marker = " <-- 15% threshold" if abs(gap - 15.0) < 1.5 else ""
        print(f"  {mult:>8.1f}x ${g.cost.total:>8.2f} ${t.cost.total:>8.2f} "
              f"${savings:>8.2f} {gap:>7.1f}%  {bar}{marker}")

        time.sleep(0.3)  # Slight delay for "live" effect

    print(f"\n  Result: As traffic grows, greedy's egress penalty grows linearly")
    print(f"          while TEAP keeps cost flat by co-locating components.")


def option4_ablation(pricing):
    """Show which TEAP phases contribute most."""
    topology = choose_topology()

    mult_input = input("  Traffic multiplier [3.5]: ").strip()
    mult = float(mult_input) if mult_input else 3.5
    scaled = topology.scale_traffic(mult) if mult != 1.0 else topology

    variants = [
        ("Greedy (baseline)", GreedySolver()),
        ("TEAP-full", TEAPSolver(use_clustering=True, use_asymmetry=True, use_ilp_refinement=True)),
        ("TEAP (no clustering)", TEAPSolver(use_clustering=False, use_asymmetry=True, use_ilp_refinement=True)),
        ("TEAP (no asymmetry)", TEAPSolver(use_clustering=True, use_asymmetry=False, use_ilp_refinement=True)),
        ("TEAP (no ILP refine)", TEAPSolver(use_clustering=True, use_asymmetry=True, use_ilp_refinement=False)),
    ]

    print(f"\n  Ablation Study: {topology.name} (traffic x{mult})\n")

    rows = []
    for name, solver in variants:
        result = solver.solve(scaled, pricing)
        rows.append([name, f"${result.cost.compute:.2f}", f"${result.cost.egress:.2f}",
                     f"${result.cost.total:.2f}"])

    print(tabulate(rows,
        headers=["Variant", "Compute", "Egress", "Total"],
        tablefmt="grid"))

    # Explain
    greedy_cost = float(rows[0][3].replace("$", ""))
    teap_cost = float(rows[1][3].replace("$", ""))
    savings = greedy_cost - teap_cost
    if savings > 0:
        print(f"\n  TEAP saves ${savings:.2f}/mo ({savings/greedy_cost*100:.1f}%) over Greedy")
    else:
        print(f"\n  Same cost - this topology benefits from single-provider placement")


def option5_egress_rates(pricing):
    """Show why egress rate direction matters."""
    print("\n  Egress Rates ($/GB) - Why Direction Matters\n")

    providers = pricing.providers
    rows = []
    for src in providers:
        row = [src]
        for dst in providers:
            rate = pricing.get_egress_rate(src, dst)
            row.append(f"${rate:.3f}" if rate > 0 else "FREE")
        rows.append(row)

    print(tabulate(rows,
        headers=["From \\ To"] + providers,
        tablefmt="grid"))

    print(f"""
  KEY INSIGHT (TEAP Phase 3):
  - GCP charges $0.120/GB to send data out (MOST EXPENSIVE)
  - AWS charges $0.090/GB to send data out
  - Azure charges $0.087/GB to send data out (CHEAPEST)

  For 500 GB/month of traffic:
  - If sender is on GCP:   500 x $0.12  = $60.00/mo in egress
  - If sender is on Azure: 500 x $0.087 = $43.50/mo in egress
  - Savings by swapping direction: $16.50/mo (27% less egress!)

  TEAP exploits this: when components MUST be on different clouds,
  it puts the high-traffic sender on the cheaper-egress provider.
""")


def option6_codecourt(pricing):
    """CodeCourt case study."""
    topology = create_codecourt_topology()

    print(f"\n  CodeCourt Online Judge - Real-World Case Study")
    print(f"  Components: {', '.join(c.name for c in topology.components)}\n")

    greedy = GreedySolver().solve(topology, pricing)
    teap = TEAPSolver().solve(topology, pricing)

    print("  --- GREEDY Placement (how most people deploy) ---")
    for comp in topology.components:
        prov = greedy.placement[comp.name]
        print(f"    {comp.name:20s} -> {prov:6s} (${pricing.get_compute_cost(comp.component_type, prov):.2f}/mo)")
    print(f"    {'TOTAL':20s}    Compute=${greedy.cost.compute:.2f} + Egress=${greedy.cost.egress:.2f} = ${greedy.cost.total:.2f}/mo")

    print(f"\n  --- TEAP Placement (our optimized placement) ---")
    for comp in topology.components:
        prov = teap.placement[comp.name]
        print(f"    {comp.name:20s} -> {prov:6s} (${pricing.get_compute_cost(comp.component_type, prov):.2f}/mo)")
    print(f"    {'TOTAL':20s}    Compute=${teap.cost.compute:.2f} + Egress=${teap.cost.egress:.2f} = ${teap.cost.total:.2f}/mo")

    savings = greedy.cost.total - teap.cost.total
    print(f"\n  SAVINGS: ${savings:.2f}/mo ({savings/greedy.cost.total*100:.1f}%)")
    if savings > 0:
        print(f"  ANNUAL: ${savings*12:.2f}/year")

    # Show at higher traffic
    print(f"\n  --- At Higher Traffic (5x) ---")
    scaled = topology.scale_traffic(5.0)
    g5 = GreedySolver().solve(scaled, pricing)
    t5 = TEAPSolver().solve(scaled, pricing)
    s5 = g5.cost.total - t5.cost.total
    print(f"  Greedy: ${g5.cost.total:.2f} | TEAP: ${t5.cost.total:.2f} | Savings: ${s5:.2f}/mo ({s5/g5.cost.total*100:.1f}%)")
    print(f"  Annual savings at 5x traffic: ${s5*12:.2f}/year")


def option7_full_benchmark(pricing):
    """Run the full 120-experiment benchmark."""
    from src.evaluation.benchmark import BenchmarkRunner
    topologies = get_all_topologies()
    runner = BenchmarkRunner(pricing)
    runner.run_all(topologies, traffic_multipliers=[1.0, 2.0, 3.5, 5.0])
    runner.save_results_csv()
    runner.save_results_json()


def option8_pricing_explorer(pricing):
    """Explore pricing data interactively."""
    from src.pricing.fallback_data import COMPUTE_CATALOG

    print(f"\n  Pricing Source: {pricing.source}")
    print(f"  Providers: {', '.join(pricing.providers)}\n")

    print("  Available component types:")
    comp_types = list(COMPUTE_CATALOG.keys())
    for i, ct in enumerate(comp_types):
        print(f"    [{i+1}] {ct}")

    choice = input(f"\n  Select type [1-{len(comp_types)}]: ").strip()
    idx = int(choice) - 1 if choice.isdigit() else 0
    idx = max(0, min(idx, len(comp_types) - 1))
    selected = comp_types[idx]

    rows = []
    for provider in pricing.providers:
        info = COMPUTE_CATALOG[selected][provider]
        rows.append([
            provider,
            info["instance"],
            info["vcpu"],
            f"{info['ram_gb']} GB",
            f"${info['price_monthly']:.2f}",
        ])

    print(f"\n  Pricing for: {selected}\n")
    print(tabulate(rows,
        headers=["Provider", "Instance", "vCPU", "RAM", "$/month"],
        tablefmt="grid"))

    cheapest = min(rows, key=lambda r: float(r[4].replace("$", "")))
    print(f"\n  Cheapest: {cheapest[0]} ({cheapest[1]}) at {cheapest[4]}/mo")


def main():
    pricing = PricingModel()

    while True:
        clear_screen()
        print_header()
        print_menu()

        choice = input("  Enter choice [0-8]: ").strip()

        if choice == "0":
            print("\n  Bye!\n")
            break
        elif choice == "1":
            option1_compare_algorithms(pricing)
        elif choice == "2":
            option2_show_placements(pricing)
        elif choice == "3":
            option3_live_sweep(pricing)
        elif choice == "4":
            option4_ablation(pricing)
        elif choice == "5":
            option5_egress_rates(pricing)
        elif choice == "6":
            option6_codecourt(pricing)
        elif choice == "7":
            option7_full_benchmark(pricing)
        elif choice == "8":
            option8_pricing_explorer(pricing)
        else:
            print("  Invalid choice")

        input("\n  Press Enter to continue...")


if __name__ == "__main__":
    main()
