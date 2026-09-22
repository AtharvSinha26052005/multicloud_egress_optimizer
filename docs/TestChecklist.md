# Test Checklist

Proof it works, not just a claim that it does.

---

## Unit Tests

### Pricing Module
- [ ] `test_fallback_prices_match_review1` — Hardcoded prices return $30.37 for AWS Web, $24.27 for GCP Web, etc.
- [ ] `test_egress_rates_correct` — AWS=$0.09, GCP=$0.12, Azure=$0.087
- [ ] `test_intra_provider_egress_is_free` — get_egress_rate("AWS", "AWS") == 0.0
- [ ] `test_compute_cost_returns_float` — No None, no negative values
- [ ] `test_total_cost_greedy_matches_review1` — Greedy 3-tier = $304.41
- [ ] `test_total_cost_optimal_matches_review1` — Optimal 3-tier = $285.70

### Topology Module
- [ ] `test_three_tier_has_3_components` — Exactly 3 components
- [ ] `test_three_tier_traffic_matrix_valid` — All traffic values > 0
- [ ] `test_microservice_mesh_has_5_components` — Exactly 5 components
- [ ] `test_codecourt_has_5_components` — Exactly 5 components
- [ ] `test_topology_to_graph_returns_networkx` — .to_graph() returns nx.DiGraph
- [ ] `test_all_topologies_have_providers_list` — 3 providers: AWS, GCP, Azure

### Algorithm Module
- [ ] `test_greedy_picks_cheapest_compute` — Each component on its cheapest provider
- [ ] `test_single_provider_returns_one_provider` — All components on same cloud
- [ ] `test_exhaustive_finds_global_minimum` — Matches manual calculation for 3-tier
- [ ] `test_ilp_matches_exhaustive` — Same cost as brute-force for N≤5
- [ ] `test_sa_within_5pct_of_optimal` — SA result ≤ 1.05 × optimal
- [ ] `test_teap_matches_ilp_for_small_n` — TEAP cost == ILP cost for N≤5
- [ ] `test_teap_faster_than_ilp_for_large_n` — TEAP runtime < ILP runtime for N≥10
- [ ] `test_all_solvers_return_valid_placement` — Every component assigned exactly one provider

### Evaluation Module
- [ ] `test_benchmark_runs_without_error` — 100 experiments complete
- [ ] `test_ablation_produces_4_variants` — Full, no-clustering, no-asymmetry, no-ILP
- [ ] `test_parameter_sweep_produces_20_datapoints` — 100-2000 in steps of 100
- [ ] `test_visualizer_saves_6_pngs` — All 6 figure files exist in results/figures/

---

## Integration Tests

- [ ] `test_full_pipeline_three_tier` — run_experiments.py on 3-tier topology produces correct CSV + PNGs
- [ ] `test_full_pipeline_codecourt` — run_experiments.py on CodeCourt topology completes without error
- [ ] `test_api_fetch_aws_returns_data` — Live AWS API returns parseable JSON (network required)
- [ ] `test_api_fetch_azure_returns_data` — Live Azure API returns parseable JSON (network required)

---

## Regression Tests (Review 1 Numbers Must Not Change)

| Placement | Expected Compute | Expected Egress | Expected Total |
|---|---|---|---|
| Greedy (GCP, GCP, Azure) | $279.54 | $24.87 | $304.41 |
| Optimal (GCP, GCP, GCP) | $284.50 | $1.20 | $285.70 |
| All-AWS | $335.80 | $0.90 | $336.70 |
| All-Azure | $302.88 | $0.87 | $303.75 |
| Worst (GCP, Azure, AWS) | $318.63 | $78.30 | $396.93 |

---

## Visual Verification (Manual)

- [ ] Graph 1 (bar chart): All 5 algorithms visible, TEAP ≤ ILP ≤ Greedy
- [ ] Graph 2 (line chart): Greedy/ILP/TEAP on same axes, crossover point visible
- [ ] Graph 3 (runtime): ILP curve grows faster than TEAP curve
- [ ] Graph 4 (ablation): Full TEAP is best; removing phases degrades performance
- [ ] Graph 5 (heatmap): GCP→* row has highest egress rates
- [ ] Graph 6 (CodeCourt): Clear cost difference between greedy and TEAP
