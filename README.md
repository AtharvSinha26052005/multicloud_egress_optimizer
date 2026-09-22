# P5 — Egress-Aware Cost-Optimal Multi-Cloud Placement

> **Capstone Project | Review 2** — Research-grade implementation of the TEAP algorithm for egress-aware multi-cloud workload placement.

## What This Project Does

Cloud cost calculators (AWS, GCP, Azure) show you the cheapest VM — but they ignore **data transfer (egress) costs** between services on different clouds. When your web tier is on GCP and your DB is on Azure, every byte of data crossing that boundary costs money.

This project:
1. **Models** the problem mathematically (ILP formulation)
2. **Implements TEAP** — a novel 5-phase algorithm that finds cheaper placements by co-locating tightly-communicating components
3. **Proves** the algorithm saves up to **43.9% cost** over the standard greedy approach at high traffic

---

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Quick test (6 experiments, verifies Review 1 numbers)
python run_experiments.py --quick

# Interactive CLI dashboard (live demo)
python dashboard.py

# Full benchmark + all 6 charts
python generate_figures.py
```

---

## Project Structure

```
p5-egress-optimizer/
|
|-- dashboard.py          <- Interactive CLI dashboard (demo tool)
|-- run_experiments.py    <- Main benchmark entry point
|-- generate_figures.py   <- Full benchmark + ablation + 6 charts
|-- requirements.txt
|
|-- src/
|   |-- pricing/          <- Unified cost model (AWS + GCP + Azure)
|   |   |-- fallback_data.py    # Verified Aug 2026 prices (regression baseline)
|   |   |-- unified_model.py    # PricingModel class — compute + egress costs
|   |   |-- aws_pricing.py      # AWS Bulk API fetcher
|   |   |-- azure_pricing.py    # Azure Retail API fetcher
|   |   `-- gcp_pricing.py      # GCP pricing (cached)
|   |
|   |-- topology/         <- Application topology definitions
|   |   |-- base.py             # Component + Topology base classes
|   |   |-- three_tier.py       # 3-Tier Web App (Review 1 baseline)
|   |   |-- microservice_mesh.py # 5-service e-commerce mesh
|   |   |-- data_pipeline.py    # 4-stage ETL pipeline
|   |   |-- ml_training.py      # ML training workflow
|   |   `-- codecourt.py        # CodeCourt online judge (real case study)
|   |
|   |-- algorithms/       <- All placement solvers
|   |   |-- base.py             # Abstract PlacementSolver interface
|   |   |-- greedy.py           # Baseline: cheapest compute, ignore egress
|   |   |-- single_provider.py  # Baseline: best all-on-one-cloud
|   |   |-- exhaustive.py       # Brute-force (ground truth for small N)
|   |   |-- ilp_solver.py       # ILP exact solver (PuLP/CBC)
|   |   |-- simulated_annealing.py # SA metaheuristic
|   |   `-- teap.py             # TEAP: our novel 5-phase algorithm
|   |
|   `-- evaluation/       <- Benchmarking and analysis
|       |-- benchmark.py        # Runs all algo x topology x traffic combos
|       |-- ablation.py         # TEAP phase contribution analysis
|       |-- parameter_sweep.py  # Traffic volume sweep
|       `-- visualizer.py       # matplotlib chart generation
|
|-- results/
|   |-- figures/          <- 6 generated PNG charts
|   |-- tables/           <- benchmark_results.csv + .json
|   `-- logs/             <- experiment.log
|
`-- docs/
    |-- Architecture.md   # System design and data flow
    |-- Decisions.md      # Why each design choice was made
    |-- Flow.md           # Execution trace through the code
    |-- Bug.md            # Bug tracker
    |-- Feature.md        # Feature tracker (Rev 2/3 scope)
    `-- TestChecklist.md  # Unit + regression tests
```

---

## The TEAP Algorithm (Our Contribution)

TEAP = **T**raffic-aware **E**gress-**A**ware **P**lacement

A 5-phase hybrid algorithm that outperforms pure ILP (on large instances) and always beats greedy:

| Phase | What it does |
|---|---|
| **Phase 1** | Build weighted traffic graph (edge weight = traffic × egress rate) |
| **Phase 2** | Louvain community detection — cluster tightly-communicating components |
| **Phase 3** | Egress-asymmetry assignment — high-traffic senders go on cheaper-egress providers |
| **Phase 4** | ILP refinement on clusters (solves P^K not P^N — tractable at any scale) |
| **Phase 5** | Local search — component-level swaps to catch edge cases |

---

## Key Results

| Topology | Traffic Level | Greedy Cost | TEAP Cost | Savings |
|---|---|---|---|---|
| 3-Tier Web App | 10x | $528.24 | $296.50 | **43.9%** |
| 3-Tier Web App | 2.5x | $341.71 | $287.50 | **15.9%** |
| CodeCourt | 5x | $458.34 | $379.30 | **17.2%** |
| CodeCourt | 3.5x | $430.44 | $376.60 | **14.3%** |

> TEAP matches the ILP exact solution on **all 5 topologies**. The 15% cost-reduction hypothesis is verified at 2.5x traffic for 3-Tier and 5x traffic for CodeCourt.

---

## CLI Dashboard — Menu Options

Run `python dashboard.py` to get the interactive demo:

| Option | What to show during review |
|---|---|
| `[1]` Run all algorithms | Proves TEAP matches optimal, Greedy wastes money |
| `[2]` Show placements | Shows exactly which component goes to AWS/GCP/Azure |
| `[3]` Live sweep | Watch the cost gap grow in real-time as traffic increases |
| `[4]` Ablation study | Shows which TEAP phases cause the savings |
| `[5]` Egress rates | Proves why egress direction matters (GCP=$0.12 vs Azure=$0.087) |
| `[6]` CodeCourt case study | Saves $948/year annually at 5x traffic |

---

## Generated Figures

| File | Description |
|---|---|
| `fig1_cost_by_algorithm.png` | Bar chart: cost comparison across all algorithms and topologies |
| `fig2_cost_vs_traffic.png` | Line chart: Greedy diverges from TEAP/ILP as traffic grows |
| `fig3_runtime_comparison.png` | Runtime: Greedy fastest, ILP slowest, TEAP middle |
| `fig4_ablation.png` | TEAP with phases removed — shows each phase's contribution |
| `fig5_egress_heatmap.png` | Egress rate matrix — GCP row is the most expensive |
| `fig6_codecourt_case.png` | CodeCourt before/after + % savings chart |

---

## Algorithms Implemented

| Algorithm | Type | Time Complexity | Purpose |
|---|---|---|---|
| Greedy | Baseline | O(N×P) | Cheapest compute per component, ignores egress |
| Single-Provider | Baseline | O(P) | Best all-on-one-cloud option |
| Exhaustive | Exact | O(P^N) | Ground truth for N ≤ 6 |
| ILP (PuLP/CBC) | Exact | Exponential (practical for N≤15) | Exact optimum |
| Simulated Annealing | Heuristic | O(iterations) | Near-optimal with annealing schedule |
| **TEAP** | **Novel Hybrid** | **O(K log K + P^K)** | **Our contribution — best of all worlds** |

---

## Research Context

**Problem statement:** Cloud workload placement is currently done greedily (minimize compute cost per component). Egress costs — which can exceed compute costs at high traffic — are ignored.

**Research question:** Can a placement algorithm that explicitly models egress costs reduce total cloud spend by >15% compared to the greedy baseline?

**Result:** Yes. TEAP reduces cost by up to 43.9%, crossing the 15% threshold at 2.5x baseline traffic for a 3-tier web application.

---

*Capstone Project | B.Tech CSE | Review 2 Submission*
