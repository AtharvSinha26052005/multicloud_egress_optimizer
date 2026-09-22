"""
Visualizer — Generates all 6 charts for the Review 2 paper.

Graph 1: Bar chart — cost by algorithm per topology
Graph 2: Line chart — cost vs traffic (greedy/ILP/TEAP on same axes)
Graph 3: Runtime comparison across algorithms
Graph 4: Ablation — TEAP variants
Graph 5: Egress cost heatmap by provider-pair
Graph 6: CodeCourt case study — before vs after
"""

import os
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for saving files
import matplotlib.pyplot as plt

from src.pricing.fallback_data import EGRESS_RATES, PROVIDERS

OUTPUT_DIR = os.path.join("results", "figures")


def ensure_output_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def fig1_cost_by_algorithm(benchmark_results, traffic_mult=1.0):
    """Bar chart: Total cost by algorithm for each topology at baseline traffic."""
    ensure_output_dir()

    # Filter for the specified traffic multiplier
    data = [r for r in benchmark_results if r["traffic_multiplier"] == traffic_mult]

    # Get unique topologies and algorithms
    topologies = list(dict.fromkeys(r["topology"] for r in data))
    algorithms = list(dict.fromkeys(r["algorithm"] for r in data))

    fig, ax = plt.subplots(figsize=(14, 6))

    x = np.arange(len(topologies))
    width = 0.12
    colors = ['#e74c3c', '#3498db', '#2ecc71', '#9b59b6', '#f39c12', '#1abc9c']

    for i, algo in enumerate(algorithms):
        costs = []
        for topo in topologies:
            match = [r for r in data if r["topology"] == topo and r["algorithm"] == algo]
            costs.append(match[0]["total_cost"] if match else 0)

        bars = ax.bar(x + i * width, costs, width, label=algo, color=colors[i % len(colors)])

        # Add value labels on bars
        for bar, cost in zip(bars, costs):
            if cost > 0:
                ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 2,
                        f'${cost:.0f}', ha='center', va='bottom', fontsize=7)

    ax.set_xlabel('Application Topology', fontsize=12)
    ax.set_ylabel('Total Monthly Cost (USD)', fontsize=12)
    ax.set_title(f'Total Cost by Algorithm and Topology (Traffic x{traffic_mult})', fontsize=14)
    ax.set_xticks(x + width * (len(algorithms) - 1) / 2)
    ax.set_xticklabels(topologies, rotation=15, ha='right')
    ax.legend(loc='upper left', fontsize=9)
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, "fig1_cost_by_algorithm.png")
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"  Saved: {path}")


def fig2_cost_vs_traffic(sweep_results, topology_name="3-Tier Web App"):
    """Line chart: Cost vs traffic volume (greedy/ILP/TEAP on same axes)."""
    ensure_output_dir()

    data = [r for r in sweep_results if r["topology"] == topology_name]
    if not data:
        print(f"  No sweep data for {topology_name}")
        return

    mults = [r["traffic_multiplier"] for r in data]
    greedy = [r["greedy_cost"] for r in data]
    ilp = [r["ilp_cost"] for r in data]
    teap = [r["teap_cost"] for r in data]

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.plot(mults, greedy, 'o-', color='#e74c3c', linewidth=2, markersize=6, label='Greedy')
    ax.plot(mults, ilp, 's-', color='#3498db', linewidth=2, markersize=6, label='ILP (Exact)')
    ax.plot(mults, teap, '^-', color='#2ecc71', linewidth=2, markersize=6, label='TEAP (Ours)')

    # Shade the gap between greedy and TEAP
    ax.fill_between(mults, greedy, teap, alpha=0.15, color='#e74c3c', label='Egress penalty')

    ax.set_xlabel('Traffic Multiplier', fontsize=12)
    ax.set_ylabel('Total Monthly Cost (USD)', fontsize=12)
    ax.set_title(f'Cost vs Traffic Volume - {topology_name}', fontsize=14)
    ax.legend(fontsize=10)
    ax.grid(alpha=0.3)

    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, "fig2_cost_vs_traffic.png")
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"  Saved: {path}")


def fig3_runtime_comparison(benchmark_results, traffic_mult=1.0):
    """Bar chart: Runtime by algorithm (showing TEAP scales better than ILP)."""
    ensure_output_dir()

    data = [r for r in benchmark_results if r["traffic_multiplier"] == traffic_mult]

    algorithms = list(dict.fromkeys(r["algorithm"] for r in data))
    topologies = list(dict.fromkeys(r["topology"] for r in data))

    fig, ax = plt.subplots(figsize=(10, 6))

    x = np.arange(len(topologies))
    width = 0.12
    colors = ['#e74c3c', '#3498db', '#2ecc71', '#9b59b6', '#f39c12', '#1abc9c']

    for i, algo in enumerate(algorithms):
        runtimes = []
        for topo in topologies:
            match = [r for r in data if r["topology"] == topo and r["algorithm"] == algo]
            runtimes.append(match[0]["runtime_seconds"] * 1000 if match else 0)  # ms

        ax.bar(x + i * width, runtimes, width, label=algo, color=colors[i % len(colors)])

    ax.set_xlabel('Application Topology', fontsize=12)
    ax.set_ylabel('Runtime (milliseconds)', fontsize=12)
    ax.set_title(f'Solver Runtime by Algorithm and Topology', fontsize=14)
    ax.set_xticks(x + width * (len(algorithms) - 1) / 2)
    ax.set_xticklabels(topologies, rotation=15, ha='right')
    ax.legend(fontsize=9)
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, "fig3_runtime_comparison.png")
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"  Saved: {path}")


def fig4_ablation(ablation_results):
    """Bar chart: TEAP variants comparison (ablation study)."""
    ensure_output_dir()

    topologies = list(dict.fromkeys(r["topology"] for r in ablation_results))
    variants = list(dict.fromkeys(r["variant"] for r in ablation_results))

    fig, ax = plt.subplots(figsize=(12, 6))

    x = np.arange(len(topologies))
    width = 0.15
    colors = ['#95a5a6', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6']

    for i, variant in enumerate(variants):
        costs = []
        for topo in topologies:
            match = [r for r in ablation_results
                     if r["topology"] == topo and r["variant"] == variant]
            costs.append(match[0]["total_cost"] if match else 0)

        ax.bar(x + i * width, costs, width, label=variant, color=colors[i % len(colors)])

    ax.set_xlabel('Application Topology', fontsize=12)
    ax.set_ylabel('Total Monthly Cost (USD)', fontsize=12)
    ax.set_title('TEAP Ablation Study - Phase Contribution', fontsize=14)
    ax.set_xticks(x + width * (len(variants) - 1) / 2)
    ax.set_xticklabels(topologies, rotation=15, ha='right')
    ax.legend(fontsize=8, loc='upper left')
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, "fig4_ablation.png")
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"  Saved: {path}")


def fig5_egress_heatmap():
    """Heatmap: Egress rates by provider pair."""
    ensure_output_dir()

    providers = PROVIDERS
    matrix = np.zeros((len(providers), len(providers)))

    for i, src in enumerate(providers):
        for j, dst in enumerate(providers):
            matrix[i][j] = EGRESS_RATES.get((src, dst), 0)

    fig, ax = plt.subplots(figsize=(7, 5))

    im = ax.imshow(matrix, cmap='YlOrRd', aspect='auto')

    ax.set_xticks(np.arange(len(providers)))
    ax.set_yticks(np.arange(len(providers)))
    ax.set_xticklabels(providers, fontsize=12)
    ax.set_yticklabels(providers, fontsize=12)
    ax.set_xlabel('Destination Provider', fontsize=12)
    ax.set_ylabel('Source Provider', fontsize=12)
    ax.set_title('Egress Rates ($/GB) by Provider Pair', fontsize=14)

    # Add text annotations
    for i in range(len(providers)):
        for j in range(len(providers)):
            text = f"${matrix[i, j]:.3f}"
            color = "white" if matrix[i, j] > 0.06 else "black"
            ax.text(j, i, text, ha="center", va="center", color=color, fontsize=13, fontweight='bold')

    plt.colorbar(im, label='$/GB')
    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, "fig5_egress_heatmap.png")
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"  Saved: {path}")


def fig6_codecourt_case_study(benchmark_results):
    """Side-by-side: Greedy vs TEAP for CodeCourt at different traffic levels."""
    ensure_output_dir()

    cc_data = [r for r in benchmark_results if r["topology"] == "CodeCourt"]
    if not cc_data:
        print("  No CodeCourt data available")
        return

    mults = sorted(set(r["traffic_multiplier"] for r in cc_data))

    greedy_costs = []
    teap_costs = []
    for m in mults:
        g = [r for r in cc_data if r["traffic_multiplier"] == m and r["algorithm"] == "Greedy"]
        t = [r for r in cc_data if r["traffic_multiplier"] == m and r["algorithm"] == "TEAP"]
        greedy_costs.append(g[0]["total_cost"] if g else 0)
        teap_costs.append(t[0]["total_cost"] if t else 0)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # Left: absolute costs
    x = np.arange(len(mults))
    width = 0.35
    ax1.bar(x - width/2, greedy_costs, width, label='Greedy', color='#e74c3c', alpha=0.8)
    ax1.bar(x + width/2, teap_costs, width, label='TEAP', color='#2ecc71', alpha=0.8)
    ax1.set_xlabel('Traffic Multiplier')
    ax1.set_ylabel('Total Monthly Cost (USD)')
    ax1.set_title('CodeCourt: Greedy vs TEAP')
    ax1.set_xticks(x)
    ax1.set_xticklabels([f'{m}x' for m in mults])
    ax1.legend()
    ax1.grid(axis='y', alpha=0.3)

    # Right: savings percentage
    savings = [(g - t) / g * 100 if g > 0 else 0 for g, t in zip(greedy_costs, teap_costs)]
    bars = ax2.bar(x, savings, color='#2ecc71', alpha=0.8)
    ax2.set_xlabel('Traffic Multiplier')
    ax2.set_ylabel('Savings (%)')
    ax2.set_title('CodeCourt: TEAP Savings Over Greedy')
    ax2.set_xticks(x)
    ax2.set_xticklabels([f'{m}x' for m in mults])
    ax2.axhline(y=15, color='#e74c3c', linestyle='--', label='15% hypothesis threshold')
    ax2.legend()
    ax2.grid(axis='y', alpha=0.3)

    # Add value labels
    for bar, s in zip(bars, savings):
        ax2.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.3,
                f'{s:.1f}%', ha='center', va='bottom', fontsize=10, fontweight='bold')

    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, "fig6_codecourt_case.png")
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"  Saved: {path}")


def generate_all_figures(benchmark_results, ablation_results=None, sweep_results=None):
    """Generate all 6 figures."""
    print("\n--- Generating Figures ---")

    fig1_cost_by_algorithm(benchmark_results, traffic_mult=1.0)
    fig3_runtime_comparison(benchmark_results, traffic_mult=1.0)
    fig5_egress_heatmap()
    fig6_codecourt_case_study(benchmark_results)

    if sweep_results:
        fig2_cost_vs_traffic(sweep_results)

    if ablation_results:
        fig4_ablation(ablation_results)

    print(f"\nAll figures saved to {OUTPUT_DIR}/")
