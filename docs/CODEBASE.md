# Codebase — Files and Folders Explained

> A high-level map of every important file in the project.
> What it does, why it exists, and what you'd change it for.

---

## Root Level Files

### `run_experiments.py`
**What:** Main CLI entry point for running benchmarks.
**When to use:** `python run_experiments.py --quick` for a sanity check, `python run_experiments.py` for full 120-experiment suite.
**Key logic:**
- Loads pricing data via `PricingModel()`
- Calls `BenchmarkRunner.run_all()` with all topologies and traffic multipliers
- Prints tabular results to terminal
- Saves CSV + JSON to `results/tables/`
- Has `--quick` flag that runs only 1 topology × 1 traffic level × 6 algorithms (6 experiments total, <5 seconds)

**Change it when:** You want to add a new topology to the benchmark or change which traffic multipliers to test.

---

### `generate_figures.py`
**What:** One-shot script that runs everything and generates all 6 charts.
**When to use:** Before creating the report or presentation. Run once, get all output.
**Key logic:**
- Full benchmark (120 experiments)
- Ablation study (5 TEAP variants × 5 topologies)
- Parameter sweep (14 traffic levels × 2 topologies)
- All 6 PNG charts via `visualizer.py`

**Takes:** ~90 seconds to complete.

---

### `dashboard.py`
**What:** Interactive CLI dashboard with 8 menu options.
**When to use:** During live demo or review presentation.
**Key logic:** Uses `input()` loops with a menu. Each option calls a standalone function (`option1_compare_algorithms`, `option6_codecourt`, etc.). Each function prints results using `tabulate` in `grid` format.
**See:** `docs/DASHBOARDS.md` for full walkthrough of each option.

---

### `streamlit_app.py`
**What:** Web dashboard equivalent of the CLI dashboard.
**When to use:** For a polished demo in a browser. Run with `python -m streamlit run streamlit_app.py`.
**Key logic:** Each CLI option = one Streamlit page (selected via sidebar radio buttons). Uses `@st.cache_resource` to cache the PricingModel and topologies so they don't reload on every interaction.
**See:** `docs/DASHBOARDS.md` for full walkthrough of each page.

---

### `requirements.txt`
```
pulp>=2.7           # ILP solver (CBC backend)
numpy>=1.24         # Arrays for cost matrices
matplotlib>=3.7     # Chart generation
networkx>=3.1       # Traffic graph + Louvain
python-louvain>=0.16 # Community detection
requests>=2.28      # Live pricing API calls
tabulate>=0.9       # CLI table formatting
streamlit>=1.32     # Web dashboard
pandas>=1.4         # DataFrames for Streamlit tables
```

---

## `src/` — Source Code

### `src/__init__.py`
Empty — just marks `src/` as a Python package so imports work.

---

## `src/pricing/` — Cost Model

This module provides two things: compute prices (how much does a VM cost?) and egress rates (how much does sending data cost?).

### `src/pricing/fallback_data.py`
**What:** Hardcoded price table — the single source of truth for reproducibility.
**Structure:**
```python
PROVIDERS = ['AWS', 'GCP', 'Azure']

COMPUTE_CATALOG = {
    'web_tier': {
        'AWS': {'instance': 't3.medium', 'vcpu': 2, 'ram_gb': 4, 'price_monthly': 30.37},
        'GCP': {'instance': 'e2-medium', 'vcpu': 2, 'ram_gb': 4, 'price_monthly': 24.46},
        'Azure': {'instance': 'B2s',     'vcpu': 2, 'ram_gb': 4, 'price_monthly': 34.82},
    },
    # ... 9 more component types
}

EGRESS_RATES = {
    ('AWS', 'GCP'):   0.090,  # $/GB
    ('AWS', 'Azure'): 0.090,
    ('GCP', 'AWS'):   0.120,  # GCP is most expensive
    ('GCP', 'Azure'): 0.120,
    ('Azure', 'AWS'): 0.087,  # Azure is cheapest
    ('Azure', 'GCP'): 0.087,
    # Same-provider = 0 (free)
}
```

**Change it when:** Prices change and you want to update the baseline. Always update the regression test values in `run_experiments.py` too.

---

### `src/pricing/unified_model.py`
**What:** The `PricingModel` class — the single interface all algorithms use.
**Key methods:**

| Method | What it returns |
|---|---|
| `get_compute_cost(component_type, provider)` | $/month for that VM |
| `get_egress_rate(src_provider, dst_provider)` | $/GB for cross-provider transfer |
| `get_total_cost(placement, topology)` | Total compute + egress for a full placement |
| `get_instance_name(component_type, provider)` | e.g., "e2-medium" |
| `get_cheapest_provider(component_type)` | Provider with lowest compute for that type |

**Initialization:**
1. Try to fetch live prices from AWS Bulk API → GCP → Azure Retail API
2. If any fetch fails, fall back to `fallback_data.py`
3. Merge: use live prices where available, fallback where not

**Change it when:** Adding a new provider (e.g., OCI), adding a new component type, or changing the fallback logic.

---

### `src/pricing/aws_pricing.py`
**What:** Fetches current EC2 prices from AWS Bulk Pricing API (public, no auth).
**Key detail:** The AWS Bulk API returns JSON with thousands of SKUs. We filter by:
- `location` = "US East (N. Virginia)"
- `instanceType` in our catalog
- `operatingSystem` = "Linux"
- `tenancy` = "Shared"
- `capacityStatus` = "Used"

---

### `src/pricing/azure_pricing.py`
**What:** Fetches current VM prices from Azure Retail Prices API (public, no auth).
**Endpoint:** `https://prices.azure.com/api/retail/prices`
**Key detail:** Filters by `serviceName = 'Virtual Machines'`, `armRegionName = 'eastus'`, `type = 'Consumption'`.

---

### `src/pricing/gcp_pricing.py`
**What:** GCP pricing data (cached — GCP's API requires auth).
**Key detail:** GCP doesn't have a fully public pricing API like AWS/Azure. We use manually-scraped pricing for the specific instance types in our catalog. These match GCP Cloud Console prices as of August 2026.

---

## `src/topology/` — Application Architectures

### `src/topology/base.py`
**What:** Base classes for all topologies.

```python
@dataclass
class Component:
    name: str               # e.g., "web_tier"
    description: str        # e.g., "Nginx load balancer"
    component_type: str     # Key into COMPUTE_CATALOG
    vcpu: int
    ram_gb: float

@dataclass
class Topology:
    name: str
    components: List[Component]
    traffic_matrix: Dict[Tuple[str, str], float]  # (src_name, dst_name) -> GB/month
    num_components: int

    def scale_traffic(self, multiplier: float) -> Topology:
        # Returns a new Topology with all traffic values multiplied
```

**Change it when:** Adding a new field to components (e.g., GPU count, latency SLA).

---

### `src/topology/three_tier.py`
**What:** The 3-component baseline used in Review 1.
**Components:** Web (Nginx) → App (Node.js) → DB (PostgreSQL)
**Traffic:** Web→App: 200 GB/mo, App→DB: 150 GB/mo, DB→App: 100 GB/mo, App→Web: 80 GB/mo
**Why it matters:** This is the regression baseline. Review 1 numbers ($304.41 greedy, $285.70 optimal) must match exactly.

---

### `src/topology/codecourt.py`
**What:** The CodeCourt online judge architecture (5 components).
**Components:** Nginx → API Server → Redis (cache) → Judge Workers → PostgreSQL
**Why it matters:** Real-world case study — this is the actual CodeCourt system architecture. Shows that the optimizer works on a real project, not just toy examples.

---

### `src/topology/microservice_mesh.py`
**What:** 5-service e-commerce system (high interconnect).
**Why it matters:** Tests the algorithm's ability to handle dense traffic graphs (many edges, many interactions). Most relevant for TEAP's Louvain phase.

---

### `src/topology/data_pipeline.py`
**What:** 4-stage ETL pipeline (linear flow: ingest → transform → load → serve).
**Why it matters:** Linear topology (chain graph). Tests whether the algorithm exploits the directional nature of data pipelines.

---

### `src/topology/ml_training.py`
**What:** ML training workflow (3 stages: prep → GPU training → serving).
**Why it matters:** Tests large GPU instances which have very different pricing profiles. AWS P3 instances vs GCP A2 instances have dramatically different costs.

---

## `src/algorithms/` — Placement Solvers

### `src/algorithms/base.py`
**What:** Abstract base class all solvers inherit from.
```python
class PlacementSolver(ABC):
    name: str

    @abstractmethod
    def _solve_impl(self, topology: Topology, pricing: PricingModel) -> Dict[str, str]:
        # Returns placement: {component_name: provider}

    def solve(self, topology, pricing) -> PlacementResult:
        # Wraps _solve_impl with timing + cost calculation
```

**Why this matters:** Every algorithm just implements `_solve_impl`. The `solve` wrapper handles timing, cost calculation, and result packaging. Adding a new algorithm = add one file, no other changes.

---

### `src/algorithms/teap.py`
**What:** The TEAP algorithm — all 5 phases.
**Constructor args:**
```python
TEAPSolver(
    use_clustering=True,      # Phase 2 toggle (for ablation study)
    use_asymmetry=True,       # Phase 3 toggle
    use_ilp_refinement=True,  # Phase 4 toggle
)
```

The toggle flags exist specifically for the ablation study. When `use_ilp_refinement=False`, Phase 4 skips ILP and uses the Phase 3 greedy assignment directly.

**See:** `docs/ALGORITHMS.md` for the detailed per-phase explanation.

---

### `src/algorithms/ilp_solver.py`
**What:** Full ILP solver using PuLP/CBC.
**Key function:** `_add_egress_constraints()` implements the McCormick envelope linearization.
**Timeout:** Set to 60 seconds. If CBC doesn't solve in 60s, returns the best incumbent solution found.

---

## `src/evaluation/` — Measurement Framework

### `src/evaluation/benchmark.py`
**What:** `BenchmarkRunner` class that runs all experiments systematically.
**Key method:** `run_all(topologies, traffic_multipliers, solvers)`
**Output format:**
```python
{
    "topology": "3-Tier Web App",
    "traffic_multiplier": 1.0,
    "algorithm": "TEAP",
    "compute_cost": 284.50,
    "egress_cost": 1.20,
    "total_cost": 285.70,
    "runtime_seconds": 0.161,
    "placement": {"web_tier": "GCP", "app_tier": "GCP", "db_tier": "GCP"}
}
```

**Change it when:** Adding a new metric to track (e.g., CO2 emissions per provider).

---

### `src/evaluation/ablation.py`
**What:** `AblationRunner` — runs 5 TEAP variants across all topologies.
**The 5 variants:** Greedy baseline, TEAP-full, TEAP-no-clustering, TEAP-no-asymmetry, TEAP-no-ILP
**Output:** Same format as benchmark, plus `variant` field instead of `algorithm`.

---

### `src/evaluation/parameter_sweep.py`
**What:** `ParameterSweeper` — sweeps traffic from 0.5× to 10× and records the gap between Greedy and TEAP.
**Key output:** The crossover point where gap > 15% (our hypothesis threshold).

---

### `src/evaluation/visualizer.py`
**What:** Generates all 6 PNG charts.
**Function per chart:**

| Function | Output file |
|---|---|
| `fig1_cost_by_algorithm()` | `fig1_cost_by_algorithm.png` |
| `fig2_cost_vs_traffic()` | `fig2_cost_vs_traffic.png` |
| `fig3_runtime_comparison()` | `fig3_runtime_comparison.png` |
| `fig4_ablation()` | `fig4_ablation.png` |
| `fig5_egress_heatmap()` | `fig5_egress_heatmap.png` |
| `fig6_codecourt_case_study()` | `fig6_codecourt_case.png` |

Uses `matplotlib.use('Agg')` — headless backend, saves directly to file.

---

## `results/` — Output Directory

### `results/figures/`
All 6 generated PNG charts. Generated by `python generate_figures.py`.

| File | Description |
|---|---|
| `fig1_cost_by_algorithm.png` | Bar chart: 6 algorithms × 5 topologies |
| `fig2_cost_vs_traffic.png` | Line chart: cost divergence as traffic grows |
| `fig3_runtime_comparison.png` | Runtime bar chart |
| `fig4_ablation.png` | TEAP phase ablation |
| `fig5_egress_heatmap.png` | 3×3 egress rate matrix (heatmap) |
| `fig6_codecourt_case.png` | CodeCourt before/after + savings % |

### `results/tables/`
- `benchmark_results.csv` — All 120 experiment results in spreadsheet format
- `benchmark_results.json` — Same data in JSON (for programmatic use)

### `results/logs/`
- `experiment.log` — Full log of every experiment run with timestamps

---

## `docs/` — Documentation

| File | Contents |
|---|---|
| `Architecture.md` | System design, module boundaries, data flow |
| `Decisions.md` | WHY each design choice was made (not just what) |
| `Flow.md` | Step-by-step execution trace through the code |
| `Bug.md` | Bug tracker (known issues, fixes applied) |
| `Feature.md` | Feature ideas for Review 3 |
| `TestChecklist.md` | Manual test cases and regression checks |
| `ALGORITHMS.md` | In-depth algorithm explanations (this doc series) |
| `PROJECT_JOURNEY.md` | How the project was built step by step |
| `CODEBASE.md` | This file — file-by-file explanation |
| `DASHBOARDS.md` | CLI and Streamlit dashboard walkthroughs |
