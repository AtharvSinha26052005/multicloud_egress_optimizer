# Decisions Log

Every AI-assisted and manual design decision, with the "why" not just the "what".

---

## D001 — Algorithm Choice: TEAP over pure ILP
**Date:** 2026-09-19
**Decision:** Create a 5-phase hybrid (TEAP) instead of relying solely on ILP.
**Why:** ILP is exact but has exponential worst-case complexity. For 20+ components it becomes infeasible. Maam explicitly asked for "better than ILP or combination of algos." TEAP decomposes the problem via graph clustering first, making ILP tractable at any scale.
**Alternative considered:** Pure Genetic Algorithm — rejected because GA doesn't guarantee optimality even for small instances, and we need exact verification.

## D002 — Louvain for Community Detection (TEAP Phase 2)
**Date:** 2026-09-19
**Decision:** Use the Louvain algorithm for clustering communicating components.
**Why:** Louvain is fast (O(n log n)), well-studied (Blondel et al. 2008, 40k+ citations), and produces hierarchical communities that map naturally to provider assignment. Alternatives like spectral clustering or label propagation were considered but Louvain has the best balance of speed and quality for our graph sizes (3-20 nodes).
**Alternative considered:** K-means on traffic matrix — rejected because it doesn't respect graph topology.

## D003 — Egress Asymmetry Exploitation (TEAP Phase 3)
**Date:** 2026-09-19
**Decision:** When two clusters must be on different providers, prefer putting the high-traffic sender on the cheaper-egress provider.
**Why:** Azure egress ($0.087/GB) is 28% cheaper than GCP ($0.12/GB). No existing paper exploits this. For a 500 GB/month flow, the direction saves 500 × ($0.12 - $0.087) = $16.50/month. This is free money from a simple provider assignment swap.
**Alternative considered:** Ignore direction, just minimize total egress — this leaves up to $16.50/month on the table.

## D004 — Hardcoded Fallback Pricing
**Date:** 2026-09-19
**Decision:** Include hardcoded Aug 2026 prices as fallback even though we fetch from live APIs.
**Why:** Demo reliability. If AWS API is slow or Azure is down during the review presentation, the tool still runs with verified prices. The fallback also serves as the ground truth for regression testing (ensuring live API results are in the right ballpark).
**Alternative considered:** API-only with error handling — rejected because a demo that fails on network issues is worse than a demo with cached data.

## D005 — Python + PuLP over OR-Tools or Gurobi
**Date:** 2026-09-19
**Decision:** Use PuLP with CBC solver instead of Google OR-Tools or Gurobi.
**Why:** PuLP is pure Python (`pip install pulp`), CBC is bundled with it (no separate install), and it's used in multiple cited papers (Kochhar et al. 2024). Gurobi requires a commercial license. OR-Tools is more complex to set up. For our problem sizes (3-20 components), CBC is fast enough.
**Alternative considered:** Gurobi — rejected because it requires a license and would make the project non-reproducible for others.

## D006 — 5 Topologies Instead of 3
**Date:** 2026-09-19
**Decision:** Test on 5 different application topologies including CodeCourt.
**Why:** The rubric asks for "comparative results." More topologies = stronger evidence that TEAP generalises. CodeCourt adds a real-world case study that isn't synthetic. 5 topologies × 4 traffic levels × 5 algorithms = 100 experiments — enough for statistical credibility but runnable in minutes.

## D007 — CLI Output First, No Frontend for Review 2
**Date:** 2026-09-19
**Decision:** Review 2 deliverable is a Python CLI tool with terminal tables and PNG graphs. No web dashboard.
**Why:** The rubric says "working code in a version-controlled repository" and "at least one graph." A CLI tool satisfies both. Building a frontend would take 1-2 days that should be spent on algorithm quality and graph generation. Frontend is deferred to Review 3.

## D008 — Review 2 vs Review 3 Scope Split
**Date:** 2026-09-19
**Decision:** Review 2 = algorithms + experiments + graphs. Review 3 = web dashboard + IaC parser + CodeCourt integration + IEEE paper.
**Why:** The rubric for Review 2 rewards algorithm quality (O1+O2: 4 marks) and comparative evidence (graphs: 3 marks). The rubric for Review 3 rewards demo and paper. Building the right thing at the right time.
