"""
Statistical Visualizer -- Error-bar charts and box plots for Review 3.

Produces Figures 7-10 (error bars, box plots, efficiency frontier, Wilcoxon).
These replace or supplement the single-run figures for the IEEE paper.
"""

import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from typing import List, Dict

OUTPUT_DIR = os.path.join("results", "figures")


def ensure_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def fig7_cost_errorbars(stat_results: List[dict], topology_filter: str = None)-> str:
    """
    Fig 7: Grouped bar chart with 95% CI error bars.
    One group per topology, bars per algorithm, error bars = CI width.
    This is the main statistical figure for Review 3 and the IEEE paper.
    """
    ensure_dir()

    data = stat_results
    if topology_filter:
        data = [r for r in data if r["topology"] == topology_filter]

    topologies = list(dict.fromkeys(r["topology"] for r in data))
    algorithms = list(dict.fromkeys(r["algorithm"] for r in data))

    fig, ax = plt.subplots(figsize=(14, 7))
    x = np.arange(len(topologies))
    width = 0.13
    colors = ["#e74c3c","#3498db","#2ecc71","#9b59b6","#f39c12","#1abc9c"]

    for i, algo in enumerate(algorithms):
        means, errs = [], []
        for topo in topologies:
            match = [r for r in data if r["topology"]==topo and r["algorithm"]==algo]
            if match:
                m = match[0]
                means.append(m["mean_cost"])
                half_ci = (m["ci_95_upper"] - m["ci_95_lower"]) / 2
                errs.append(half_ci)
            else:
                means.append(0); errs.append(0)

        bars = ax.bar(x + i*width, means, width, label=algo,
                      color=colors[i % len(colors)], alpha=0.85)
        ax.errorbar(x + i*width, means, yerr=errs, fmt="none",
                    color="black", capsize=4, linewidth=1.5, capthick=1.5)

    ax.set_xlabel("Application Topology", fontsize=12)
    ax.set_ylabel("Total Monthly Cost (USD)", fontsize=12)
    ax.set_title("Cost by Algorithm with 95% CI Error Bars (N=30 runs)", fontsize=14)
    ax.set_xticks(x + width*(len(algorithms)-1)/2)
    ax.set_xticklabels(topologies, rotation=15, ha="right")
    ax.legend(loc="upper left", fontsize=9)
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, "fig7_cost_errorbars.png")
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"  Saved: {path}")
    return path


def fig8_runtime_boxplots(raw_results: List) -> str:
    """
    Fig 8: Box plots of runtime distributions across algorithms.
    Shows ILP has high variance on large inputs; TEAP is consistent.
    raw_results: list of RunStats objects.
    """
    ensure_dir()
    # Group runtimes by algorithm
    algo_runtimes: Dict[str, List[float]] = {}
    for r in raw_results:
        if r.algorithm not in algo_runtimes:
            algo_runtimes[r.algorithm] = []
        algo_runtimes[r.algorithm].extend(r.all_runtimes_ms)

    algos = list(algo_runtimes.keys())
    data = [algo_runtimes[a] for a in algos]

    fig, ax = plt.subplots(figsize=(12, 6))
    bp = ax.boxplot(data, labels=algos, patch_artist=True, notch=False)
    colors = ["#e74c3c","#3498db","#2ecc71","#9b59b6","#f39c12","#1abc9c"]
    for patch, color in zip(bp["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    ax.set_xlabel("Algorithm", fontsize=12)
    ax.set_ylabel("Runtime (ms)", fontsize=12)
    ax.set_title("Runtime Distribution per Algorithm (Box Plots, N=30 runs per topology)", fontsize=13)
    ax.grid(axis="y", alpha=0.3)
    plt.xticks(rotation=20, ha="right")
    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, "fig8_runtime_boxplots.png")
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"  Saved: {path}")
    return path


def fig9_efficiency_frontier(stat_results: List[dict]) -> str:
    """
    Fig 9: Scatter plot -- mean cost vs std dev (efficiency frontier).
    Ideal algorithm: low cost AND low variance -> bottom-left of plot.
    """
    ensure_dir()
    fig, ax = plt.subplots(figsize=(9, 7))
    colors = {"Greedy":"#e74c3c","Single-Provider":"#3498db","Exhaustive":"#2ecc71",
              "ILP":"#9b59b6","Simulated Annealing":"#f39c12","TEAP":"#1abc9c"}

    algo_agg: Dict[str, list] = {}
    for r in stat_results:
        a = r["algorithm"]
        if a not in algo_agg:
            algo_agg[a] = {"costs":[], "stds":[]}
        algo_agg[a]["costs"].append(r["mean_cost"])
        algo_agg[a]["stds"].append(r["std_cost"])

    for algo, vals in algo_agg.items():
        mean_cost = sum(vals["costs"]) / len(vals["costs"])
        mean_std = sum(vals["stds"]) / len(vals["stds"])
        c = colors.get(algo, "#7f8c8d")
        ax.scatter(mean_std, mean_cost, color=c, s=200, zorder=5)
        ax.annotate(algo, (mean_std, mean_cost),
                    textcoords="offset points", xytext=(8, 4), fontsize=9)

    ax.set_xlabel("Cost Std Dev (USD) -- Lower is more consistent", fontsize=11)
    ax.set_ylabel("Mean Total Cost (USD) -- Lower is cheaper", fontsize=11)
    ax.set_title("Algorithm Efficiency Frontier: Cost vs Consistency", fontsize=13)
    ax.grid(alpha=0.3)
    ax.annotate("Ideal: bottom-left", xy=(0.05, 0.05), xycoords="axes fraction",
                fontsize=10, color="green",
                arrowprops=dict(arrowstyle="->", color="green"),
                xytext=(0.15, 0.15))
    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, "fig9_efficiency_frontier.png")
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"  Saved: {path}")
    return path


def fig10_wilcoxon_heatmap(wilcoxon_results: Dict) -> str:
    """
    Fig 10: Heatmap of Wilcoxon p-values: TEAP vs each baseline per topology.
    Green = significant (p<0.05), Red = not significant.
    """
    ensure_dir()
    topologies = list(wilcoxon_results.keys())
    if not topologies:
        return ""
    baselines = list(list(wilcoxon_results.values())[0].keys())
    if not baselines:
        return ""

    matrix = []
    for topo in topologies:
        row = [wilcoxon_results[topo].get(b, 1.0) for b in baselines]
        matrix.append(row)

    mat = np.array(matrix)
    fig, ax = plt.subplots(figsize=(max(8, len(baselines)*2), max(5, len(topologies)*1.2)))
    im = ax.imshow(mat, cmap="RdYlGn_r", vmin=0, vmax=0.1, aspect="auto")
    ax.set_xticks(range(len(baselines)))
    ax.set_yticks(range(len(topologies)))
    ax.set_xticklabels(baselines, rotation=30, ha="right", fontsize=10)
    ax.set_yticklabels(topologies, fontsize=10)
    ax.set_title("Wilcoxon p-values: TEAP vs Baselines\n(Green=significant p<0.05)", fontsize=12)
    for i in range(len(topologies)):
        for j in range(len(baselines)):
            pv = mat[i,j]
            sig = "*" if pv < 0.05 else "ns"
            ax.text(j, i, f"p={pv:.3f}\n{sig}", ha="center", va="center",
                    fontsize=9, fontweight="bold",
                    color="white" if pv < 0.05 else "black")
    plt.colorbar(im, label="p-value")
    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, "fig10_wilcoxon_heatmap.png")
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"  Saved: {path}")
    return path


def generate_statistical_figures(stat_results_dict: List[dict],
                                   raw_run_stats: List,
                                   wilcoxon_results: Dict) -> List[str]:
    """Generate all 4 statistical figures (Fig 7-10)."""
    paths = []
    paths.append(fig7_cost_errorbars(stat_results_dict))
    paths.append(fig8_runtime_boxplots(raw_run_stats))
    paths.append(fig9_efficiency_frontier(stat_results_dict))
    paths.append(fig10_wilcoxon_heatmap(wilcoxon_results))
    return [p for p in paths if p]