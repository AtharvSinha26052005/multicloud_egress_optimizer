# P5 Egress-Aware Cost-Optimal Multi-Cloud Placement

## Architecture Overview

This document maps the entire system so nothing gets touched blind.

```
p5-egress-optimizer/
│
├── run_experiments.py          ← ENTRY POINT: one command runs everything
├── requirements.txt            ← All dependencies
│
├── src/
│   ├── __init__.py
│   │
│   ├── pricing/                ← O1: Unified Cost Model
│   │   ├── __init__.py
│   │   ├── fallback_data.py    ← Hardcoded Aug 2026 prices (always works)
│   │   ├── aws_pricing.py      ← Fetches from AWS Bulk API (no auth)
│   │   ├── azure_pricing.py    ← Fetches from Azure Retail API (no auth)
│   │   ├── gcp_pricing.py      ← GCP cached data + optional API
│   │   └── unified_model.py    ← Merges all 3 into PricingModel class
│   │
│   ├── topology/               ← Application topology definitions
│   │   ├── __init__.py
│   │   ├── base.py             ← Component, Topology, TrafficEdge classes
│   │   ├── three_tier.py       ← Review 1 topology (3 components)
│   │   ├── microservice_mesh.py← 5-service mesh
│   │   ├── data_pipeline.py    ← 4-stage ETL pipeline
│   │   ├── ml_training.py      ← 3-component ML workflow
│   │   └── codecourt.py        ← 5-component CodeCourt (real-world)
│   │
│   ├── algorithms/             ← O2+O3: Placement solvers
│   │   ├── __init__.py
│   │   ├── base.py             ← PlacementSolver ABC + PlacementResult
│   │   ├── greedy.py           ← Baseline: cheapest compute per component
│   │   ├── single_provider.py  ← Baseline: best single cloud
│   │   ├── exhaustive.py       ← Brute-force: P^N enumeration (verify)
│   │   ├── ilp_solver.py       ← PuLP/CBC exact ILP
│   │   ├── simulated_annealing.py ← SA heuristic (1000 iterations)
│   │   └── teap.py             ← NOVEL: Traffic-aware Egress-Aware Placement
│   │
│   └── evaluation/             ← O4: Benchmarking + visualization
│       ├── __init__.py
│       ├── benchmark.py        ← Run all algo × topology × traffic combos
│       ├── ablation.py         ← TEAP variant comparison
│       ├── parameter_sweep.py  ← Traffic volume 100-2000 GB sweep
│       └── visualizer.py       ← Matplotlib figure generation (6 charts)
│
├── tests/
│   ├── test_pricing.py
│   ├── test_algorithms.py
│   └── test_topologies.py
│
├── results/                    ← Generated outputs (gitignored)
│   ├── figures/                ← PNG charts
│   ├── tables/                 ← CSV results
│   └── logs/                   ← Experiment logs
│
└── docs/
    ├── Architecture.md         ← This file
    ├── Decisions.md            ← Why behind every decision
    ├── Flow.md                 ← How execution moves between files
    ├── Bug.md                  ← Bug tracking
    ├── Feature.md              ← Feature tracking
    └── TestChecklist.md        ← Proof it works
```

## Data Flow

```
                    ┌─────────────────────┐
                    │  run_experiments.py  │ ← User runs this
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                 ▼
     ┌────────────┐   ┌──────────────┐   ┌───────────┐
     │  pricing/  │   │  topology/   │   │  results/ │
     │  module    │   │  definitions │   │  output   │
     └─────┬──────┘   └──────┬───────┘   └───────────┘
           │                 │                   ▲
           ▼                 ▼                   │
     ┌─────────────────────────────┐             │
     │      algorithms/ solvers    │             │
     │  greedy | ilp | sa | teap   │─────────────┘
     └─────────────┬───────────────┘
                   │
                   ▼
     ┌─────────────────────────────┐
     │    evaluation/ framework    │──→ figures/*.png
     │  benchmark | ablation | viz │──→ tables/*.csv
     └─────────────────────────────┘
```

## Key Classes

| Class | File | Purpose |
|---|---|---|
| `Component` | topology/base.py | Represents one app component (name, vCPU, RAM) |
| `Topology` | topology/base.py | Collection of Components + traffic matrix |
| `PricingModel` | pricing/unified_model.py | Get compute/egress costs for any provider |
| `PlacementSolver` | algorithms/base.py | Abstract base — all algorithms implement this |
| `PlacementResult` | algorithms/base.py | Placement dict + cost breakdown + runtime |
| `BenchmarkRunner` | evaluation/benchmark.py | Orchestrates all experiments |

## Dependencies

| Package | Version | Purpose |
|---|---|---|
| pulp | ≥2.7 | ILP solver (CBC backend) |
| numpy | ≥1.24 | Array operations |
| matplotlib | ≥3.7 | Chart generation |
| networkx | ≥3.1 | Graph operations for TEAP |
| python-louvain | ≥0.16 | Community detection for TEAP Phase 2 |
| requests | ≥2.28 | HTTP calls to pricing APIs |
| tabulate | ≥0.9 | Pretty terminal tables |
