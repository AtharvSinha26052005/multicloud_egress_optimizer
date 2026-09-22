# Execution Flow

Traces exactly how execution moves between files and functions.

---

## Entry Point: `python run_experiments.py`

```
run_experiments.py
│
├─ 1. LOAD PRICING
│  └─ pricing.unified_model.PricingModel()
│     ├─ Try: pricing.aws_pricing.fetch_aws_prices()
│     │   └─ GET https://pricing.us-east-1.amazonaws.com/...
│     │   └─ Parse JSON → extract EC2 on-demand + data transfer rates
│     │   └─ Cache to results/cache/aws_prices.json
│     │
│     ├─ Try: pricing.azure_pricing.fetch_azure_prices()
│     │   └─ GET https://prices.azure.com/api/retail/prices?$filter=...
│     │   └─ Paginate through results
│     │   └─ Cache to results/cache/azure_prices.json
│     │
│     ├─ Try: pricing.gcp_pricing.fetch_gcp_prices()
│     │   └─ Load from cached Infracost data or hardcoded fallback
│     │   └─ Cache to results/cache/gcp_prices.json
│     │
│     └─ Fallback: pricing.fallback_data.get_fallback_prices()
│        └─ Returns hardcoded Aug 2026 verified prices
│
├─ 2. LOAD TOPOLOGIES
│  └─ topology.__init__.get_all_topologies()
│     ├─ three_tier.ThreeTierTopology()
│     │   └─ Creates 3 Components + traffic_matrix {(web,app):500, (app,db):200, (db,internet):10}
│     ├─ microservice_mesh.MicroserviceMeshTopology()
│     ├─ data_pipeline.DataPipelineTopology()
│     ├─ ml_training.MLTrainingTopology()
│     └─ codecourt.CodeCourtTopology()
│
├─ 3. RUN BENCHMARKS
│  └─ evaluation.benchmark.BenchmarkRunner(pricing_model, topologies, traffic_levels)
│     │
│     └─ For each topology × traffic_level:
│        │
│        ├─ algorithms.greedy.GreedySolver.solve(topology, pricing)
│        │   └─ For each component: pick min compute_cost provider
│        │   └─ Return PlacementResult{placement, cost, runtime}
│        │
│        ├─ algorithms.single_provider.SingleProviderSolver.solve(...)
│        │   └─ Try all-AWS, all-GCP, all-Azure → return cheapest
│        │
│        ├─ algorithms.exhaustive.ExhaustiveSolver.solve(...)
│        │   └─ Enumerate all P^N placements → find minimum total cost
│        │   └─ (Only runs if N ≤ 6, else skipped)
│        │
│        ├─ algorithms.ilp_solver.ILPSolver.solve(...)
│        │   └─ Create PuLP problem
│        │   └─ Add binary vars x[i,j] for each component×provider
│        │   └─ Add constraint: sum(x[i,:]) == 1 for each i
│        │   └─ Add objective: min(compute_terms + linearised_egress_terms)
│        │   └─ Solve with CBC → extract placement from x values
│        │
│        ├─ algorithms.simulated_annealing.SASolver.solve(...)
│        │   └─ Start from greedy solution
│        │   └─ For 1000 iterations:
│        │   │   └─ Pick random component, swap to random provider
│        │   │   └─ If cheaper: accept. Else: accept with prob e^(-ΔC/T)
│        │   │   └─ Cool temperature: T *= 0.995
│        │   └─ Return best solution found
│        │
│        └─ algorithms.teap.TEAPSolver.solve(...)
│           ├─ Phase 1: Build NetworkX DiGraph from traffic_matrix
│           ├─ Phase 2: Run community_louvain.best_partition(graph)
│           │   └─ Returns {component: cluster_id}
│           ├─ Phase 3: For each cluster, score providers by
│           │   └─ cluster_compute_cost + inter_cluster_egress
│           │   └─ Prefer cheaper-egress provider for high-traffic senders
│           ├─ Phase 4: Run ILP on cluster-to-provider (small problem)
│           │   └─ Variables: y[cluster, provider]
│           │   └─ Objective: min(cluster_compute + inter_cluster_egress)
│           └─ Phase 5: Local search — try swapping each component
│               └─ If any swap reduces total cost, apply it
│               └─ Repeat until no improvement
│
├─ 4. RUN ABLATION
│  └─ evaluation.ablation.AblationRunner(pricing_model, topologies)
│     ├─ TEAP-full (all phases)
│     ├─ TEAP-no-clustering (skip Phase 2, assign components directly)
│     ├─ TEAP-no-asymmetry (skip Phase 3, ignore rate differences)
│     └─ TEAP-no-ILP (skip Phase 4, use greedy cluster assignment)
│
├─ 5. RUN PARAMETER SWEEP
│  └─ evaluation.parameter_sweep.ParameterSweeper(pricing_model)
│     └─ For traffic_volume in range(100, 2100, 100):
│        └─ Run greedy vs TEAP on three_tier topology
│        └─ Record cost difference → find crossover point
│
└─ 6. GENERATE FIGURES
   └─ evaluation.visualizer.Visualizer(results)
      ├─ fig1_cost_by_algorithm.png      ← bar chart
      ├─ fig2_cost_vs_traffic.png        ← line chart (same axes)
      ├─ fig3_runtime_vs_components.png  ← scalability
      ├─ fig4_ablation.png              ← TEAP variants
      ├─ fig5_egress_heatmap.png        ← provider-pair costs
      └─ fig6_codecourt_case.png        ← before/after
```

## Key Function Signatures

```python
# pricing/unified_model.py
class PricingModel:
    def get_compute_cost(component: Component, provider: str) -> float
    def get_egress_rate(src_provider: str, dst_provider: str) -> float
    def get_total_cost(placement: dict, topology: Topology) -> CostBreakdown

# algorithms/base.py
class PlacementSolver(ABC):
    @abstractmethod
    def solve(topology: Topology, pricing: PricingModel) -> PlacementResult

@dataclass
class PlacementResult:
    placement: Dict[str, str]       # {component_name: provider}
    cost: CostBreakdown             # compute, egress, total
    runtime_seconds: float
    solver_name: str

@dataclass
class CostBreakdown:
    compute: float
    egress: float
    total: float
    details: Dict                   # per-component and per-edge breakdown
```
