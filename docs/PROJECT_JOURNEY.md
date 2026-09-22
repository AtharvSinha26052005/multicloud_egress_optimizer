# Project Journey — How P5 Was Built (Step by Step)

> A high-level walkthrough of how this project went from a research question to working code.
> Written for future reference and handover.

---

## The Starting Point — Review 1

**Question asked:** "Can we quantify the cost of ignoring egress in cloud deployment?"

We started with a simple 3-component topology (Web → App → DB) and manually calculated costs for every possible placement across AWS, GCP, and Azure. The result was shocking:

- The **greedy** placement (cheapest VM per component) chose GCP+GCP+Azure
- Total cost: **$304.41/month**
- The optimal placement (all-GCP) cost only **$285.70/month**
- The difference: **$18.71/month ($224/year)** from doing nothing except moving the database

This proved the problem is real and worth solving programmatically.

---

## Step 1 — Define the Research Objective

After Review 1, we formalized the research question:

> *Can a placement algorithm that explicitly models egress costs reduce total cloud spend by >15% compared to the greedy baseline?*

**Hypothesis:** Yes — and the savings grow linearly with traffic volume, meaning the algorithm becomes more valuable as the application scales.

**Key constraint:** The algorithm must be:
1. Faster than full exhaustive search (can't try all 3^N combinations)
2. Better than greedy (must account for egress)
3. Competitive with ILP on solution quality
4. Novel (not just re-implementing existing work)

---

## Step 2 — Literature Survey and Algorithm Choice

We reviewed:
- **ILP for cloud placement** (Meng et al., 2010; Breitgand & Epstein, 2012) — exact but doesn't exploit graph structure
- **Louvain community detection** (Blondel et al., 2008) — fast graph partitioning
- **Simulated Annealing for VM placement** (Xu & Fortes, 2010) — good heuristic, but ignores egress structure
- **Egress-aware networking** (Laoutaris et al., 2011) — models egress but not placement

**Gap identified:** No paper combines community detection + egress asymmetry exploitation + reduced ILP in a single pipeline.

**Decision:** Build TEAP — a 5-phase algorithm that chains these techniques.

---

## Step 3 — Project Structure Design

We designed the folder structure before writing any code:

```
p5-egress-optimizer/
├── src/pricing/        ← Cost data (compute + egress rates)
├── src/topology/       ← What the applications look like
├── src/algorithms/     ← The placement solvers
├── src/evaluation/     ← How we measure results
├── results/            ← Output (CSV, JSON, PNG charts)
└── docs/               ← All documentation
```

**Key design principle:** Separation of concerns.
- Pricing doesn't know about topologies
- Algorithms don't fetch prices directly — they go through PricingModel
- Evaluation doesn't know about algorithm internals

This meant adding a new algorithm = create one file in `src/algorithms/`, no changes elsewhere.

---

## Step 4 — Pricing Module (src/pricing/)

**First thing built.** Everything else depends on cost data.

**Challenge:** Live cloud APIs require authentication and rate-limit. We needed reproducible results.

**Solution:** Two-layer approach:
1. `fallback_data.py` — hardcoded, manually verified prices from August 2026. Used as regression baseline (Review 1 numbers must match exactly).
2. `aws_pricing.py` / `azure_pricing.py` — live API fetchers for when real-world prices are needed.
3. `unified_model.py` — `PricingModel` class that tries live APIs first, falls back to hardcoded data.

**Regression test built in:** Every run checks that `Greedy = $304.41` and `Optimal = $285.70` match Review 1 exactly.

---

## Step 5 — Topology Definitions (src/topology/)

**Second thing built.** Algorithms need a topology to operate on.

Each topology is a Python dataclass with:
- `components: List[Component]` — what services exist (name, type, vCPU, RAM)
- `traffic_matrix: Dict[(src, dst), float]` — GB/month between each pair
- `scale_traffic(mult)` — returns a new topology with traffic multiplied by `mult`

**Why `scale_traffic`?** This is how we do the parameter sweep. Instead of changing the topology definition, we just multiply all traffic values. The algorithm sees the same component structure but different egress costs.

**Topologies created:**
1. `three_tier.py` — Review 1 baseline (3 components)
2. `microservice_mesh.py` — 5-component e-commerce microservices
3. `data_pipeline.py` — 4-stage ETL (ingest → transform → load → serve)
4. `ml_training.py` — 3-component ML (data prep → GPU training → model serving)
5. `codecourt.py` — The real CodeCourt project (5 components)

---

## Step 6 — Algorithm Implementations (src/algorithms/)

**Built in this order (simple → complex):**

### 6a. Abstract Base Class (`base.py`)

Defined the interface:
```python
class PlacementSolver:
    def solve(topology, pricing) -> PlacementResult
```

Every algorithm returns a `PlacementResult` with:
- `placement: Dict[str, str]` (component → provider)
- `cost.compute`, `cost.egress`, `cost.total`
- `runtime_seconds`

This meant evaluation code worked without knowing which algorithm was running.

### 6b. Greedy — 1 hour to implement

Trivial: for each component, pick the cheapest provider for that component type. Done.

### 6c. Single-Provider — 30 minutes

Try each provider for all components, return the cheapest total.

### 6d. Exhaustive — 2 hours (including linearization test)

Used `itertools.product` to enumerate all P^N combinations. Added a limit: if N > 8, raise an error to prevent hanging.

### 6e. ILP — 2 days

This was the hardest algorithm to implement. Key challenges:
- The egress cost term `x[src,j] × x[dst,l]` is quadratic → had to implement McCormick envelope linearization
- PuLP API for adding auxiliary variables z[src,j,dst,l] for each edge × provider-pair combination
- Debugging: ILP was giving wrong results initially because we forgot the constraint `z ≥ x[src,j] + x[dst,l] - 1`

### 6f. Simulated Annealing — 1 day

Implemented standard SA with geometric cooling. The tricky part was choosing the temperature schedule — too fast and it gets stuck in local optima, too slow and it's as slow as exhaustive. Used `T_initial = 1000, cooling = 0.995`.

### 6g. TEAP — 3 days (the main contribution)

Built phase by phase, testing each phase independently:
- Phase 1: networkx graph — straightforward
- Phase 2: Louvain — needed `python-louvain` library (community module)
- Phase 3: Sorting by traffic and egress rate — logical but took time to verify
- Phase 4: Running ILP on cluster variables — had to carefully map cluster assignments back to component assignments
- Phase 5: Local search — simple but important for correctness

---

## Step 7 — Evaluation Framework (src/evaluation/)

Once all algorithms worked, we needed to measure them systematically.

### `benchmark.py` — Main experiment runner

Runs every combination:
```
5 topologies × 4 traffic levels × 6 algorithms = 120 experiments
```

For each combination, records:
- compute cost, egress cost, total cost
- runtime in milliseconds
- placement decisions

Outputs: `benchmark_results.csv` and `benchmark_results.json`

### `ablation.py` — Which TEAP phase matters?

Runs 5 TEAP variants (full + disable one phase each) on all topologies at 3.5× traffic.

Discovered: Removing ILP refinement (Phase 4) on Microservice Mesh causes cost to jump 31.9%. This proved Phase 4 is the critical phase, not just Phase 2 or Phase 3.

### `parameter_sweep.py` — When does TEAP beat Greedy by >15%?

Sweeps traffic from 0.5× to 10× in 0.5× increments. Records the "crossover point" where TEAP's advantage exceeds 15%.

Results:
- 3-Tier Web App: crossover at **2.5×** traffic
- CodeCourt: crossover at **5.0×** traffic

### `visualizer.py` — 6 matplotlib charts

Generated all 6 figures as PNG files for the report. Used `matplotlib.use('Agg')` (non-interactive backend) so charts save to disk without needing a display.

---

## Step 8 — Entry Points

Three scripts for different use cases:

| Script | Use case |
|---|---|
| `run_experiments.py` | Quick test or full benchmark from CLI |
| `generate_figures.py` | Full benchmark + ablation + sweep + 6 charts in one shot |
| `dashboard.py` | Interactive CLI demo (8 menu options) |
| `streamlit_app.py` | Web dashboard (8 pages, live charts) |

---

## Step 9 — Fixing Windows Encoding Issues

**Unexpected problem:** Windows console uses `cp1252` encoding by default. Our print statements had Unicode box-drawing characters (╔, ║, ╠) that caused `UnicodeEncodeError` when running on Windows.

**Fix applied to every entry point:**
```python
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
```

Also replaced all Unicode table formats (`simple_outline` in tabulate) with ASCII-safe alternatives (`grid`).

---

## Step 10 — Documentation and Git

**Documentation files created:**
- `docs/Architecture.md` — system design
- `docs/Decisions.md` — WHY each decision was made
- `docs/Flow.md` — execution trace
- `docs/Bug.md` — bug tracker
- `docs/Feature.md` — future feature ideas
- `docs/TestChecklist.md` — manual test cases
- `docs/ALGORITHMS.md` — this algorithm deep-dive (new)
- `docs/CODEBASE.md` — file-by-file explanation (new)
- `docs/DASHBOARDS.md` — dashboard walkthroughs (new)

**Git:**
- Repo: `github.com/AtharvSinha26052005/multicloud_egress_optimizer`
- Initial commit: 47 files, 5670 lines
- Second commit: Streamlit dashboard (688 lines)
- Third commit: this documentation

---

## Key Decisions and Why

| Decision | Why |
|---|---|
| Use PuLP over CPLEX/Gurobi | Free, open source, no license needed for research |
| Use fallback prices instead of always fetching live | Reproducibility — live prices change daily |
| Louvain over K-means clustering | Louvain is designed for graphs (respects edge weights), K-means is for vectors |
| McCormick linearization over binary quadratic programming | PuLP only supports linear constraints |
| Streamlit over React/Next.js | Python-native — no JS needed, all algorithms run in the same process |
| Windows ASCII output instead of Unicode | `cp1252` console limitation on Windows |

---

## What's Next (Review 3)

- [ ] IaC parser: parse Terraform/YAML to auto-generate topology
- [ ] Real-time pricing: always fetch live API data
- [ ] Web input form: paste Terraform, get optimal placement
- [ ] Multi-region support: e.g., GCP us-east1 vs GCP asia-south1 have different prices
- [ ] SLA constraints: some components must stay on-premise
