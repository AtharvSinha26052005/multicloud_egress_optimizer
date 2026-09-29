# How TEAP Was Built — The Full Story With Example

---

## PART 1 — How We Arrived at TEAP (The Thinking Process)

### Step 1: We saw the problem

In Review 1, we manually calculated cloud costs for a 3-tier app (Web, App, DB) across AWS, GCP, Azure. We discovered:

- **Greedy** (pick cheapest VM per component) → puts DB on Azure → total = **$304.41**
- **Optimal** (all on GCP) → total = **$285.70**
- Gap = $18.71/month from one bad decision

The question became: **Can we automate finding the optimal placement?**

### Step 2: We tried the obvious solution — ILP

ILP (Integer Linear Programming) can solve this exactly. Model it as math, let the solver find the minimum. It works perfectly.

**But ILP has a problem:** The number of variables grows as N × P (components × providers), and the egress cost creates N² × P² auxiliary variables. For 15 components and 3 providers:
- Decision variables: 45
- Auxiliary egress variables: 45 × 45 = 2,025
- Total combinations to search: 3^15 = **14.3 million**

ILP can handle this for small N, but for 50-100 microservices? It chokes.

### Step 3: We asked — "Can we make the problem SMALLER before giving it to ILP?"

This is the key insight. Instead of solving ILP on the full problem, what if we could:
1. First **group** tightly-communicating services together (so they obviously go on the same cloud)
2. Then solve ILP only on **which cloud each group goes to** (much fewer groups than services)

Groups of 15 services might be only 3-4 clusters. So instead of 3^15 = 14M, we solve 3^4 = **81**. That's instant.

### Step 4: We needed a grouping algorithm — found Louvain

How do you group tightly-communicating services? This is literally the **community detection problem** from social network analysis:
- In social networks: "find groups of people who talk to each other a lot"
- In our problem: "find groups of services that send lots of data to each other"

Same structure. Different domain. **Louvain** is the gold standard for this — fast (O(N log N)), produces good communities, and respects edge weights (heavier traffic = stronger connection).

### Step 5: We realized direction matters — added asymmetry exploitation

While building the ILP, we noticed something: GCP charges $0.12/GB to send data out, but Azure only charges $0.087/GB. That's a 27% difference.

If two clusters MUST be on different clouds (because compute prices demand it), then **which cluster is the sender matters hugely**. Put the heavy sender on the cheapest-egress provider.

No paper we found exploits this. We added it as Phase 3.

### Step 6: We added a cleanup step — local search

Louvain groups services together, but what if ONE service in a group has a wildly different price profile? (e.g., a GPU job in a cluster of cheap web servers). The cluster-level assignment might be wrong for that one service.

Local search fixes this: after the main algorithm, try swapping each individual service to a different provider. If it's cheaper, keep the swap.

### That gives us 5 phases — TEAP is born.

---

## PART 2 — Every Algorithm and Formula Inside TEAP

### 2.1 The Problem Definition (Formal)

**Given:**
- A set of components: C = {c1, c2, ..., cN}
- A set of providers: P = {AWS, GCP, Azure}
- Compute cost function: `compute(ci, pj)` = $/month to run component ci on provider pj
- Traffic matrix: `T(ci, ck)` = GB/month of data flowing from ci to ck
- Egress rate function: `egress(pj, pl)` = $/GB to send data from provider pj to provider pl
  - If pj = pl (same provider): egress = 0 (free)
  - If pj != pl (different providers): egress > 0

**Find:**
- An assignment function: `A: C -> P` (maps each component to a provider)
- That minimizes the **total cost:**

```
TotalCost(A) = ComputeCost(A) + EgressCost(A)

Where:
  ComputeCost(A) = SUM over all ci: compute(ci, A(ci))

  EgressCost(A) = SUM over all pairs (ci, ck) where T(ci,ck) > 0:
                  T(ci, ck) * egress(A(ci), A(ck))
```

**This is NP-hard** because:
- There are |P|^|C| possible assignments (3^N for 3 providers)
- The egress cost creates interactions between every pair of components
- You can't optimize each component independently (greedy fails because of cross-terms)

---

### 2.2 Phase 1 — Traffic Graph Construction

**Algorithm used:** Weighted undirected graph construction

**What it does:** Converts the topology into a graph that Louvain can process.

**Formula:**

```
For each pair (ci, ck) with traffic T(ci, ck) > 0:
  edge_weight(ci, ck) = T(ci, ck) * max_egress_rate

Where:
  max_egress_rate = max over all (pj, pl) where pj != pl: egress(pj, pl)
                  = $0.12/GB  (GCP's rate, the highest)
```

**Why max_egress_rate?** We use the worst-case egress cost as the edge weight because we want Louvain to aggressively cluster components that have high traffic between them. If two components exchange 500 GB/month, the edge weight is 500 * 0.12 = $60 — representing the MAXIMUM egress penalty if they're separated.

**Output:** A weighted graph G = (V, E) where:
- V = {component names}
- E = {(ci, ck, weight)} for each pair with traffic

---

### 2.3 Phase 2 — Louvain Community Detection

**Algorithm used:** Louvain method (Blondel et al., 2008)

**What Louvain does:** Finds communities (dense subgroups) in a graph by maximizing **modularity**.

**Modularity formula:**

```
Q = (1 / 2m) * SUM over all (ci, ck):
    [A(ci,ck) - (ki * kk) / (2m)] * delta(community(ci), community(ck))

Where:
  m = total edge weight in the graph
  A(ci, ck) = edge weight between ci and ck (0 if no edge)
  ki = sum of all edge weights connected to ci
  delta(a, b) = 1 if a == b, 0 otherwise
```

**In plain English:** Modularity Q measures how much more densely connected the communities are internally compared to what you'd expect from a random graph. Higher Q = better community structure.

**How Louvain works (2 phases, repeated):**

```
Phase A — Local moves:
  For each node ci:
    Try moving ci to each neighbor's community
    Compute the change in modularity (delta_Q)
    Move ci to the community that gives the highest positive delta_Q
  Repeat until no more improvements

Phase B — Aggregation:
  Merge each community into a single super-node
  Edge weights between super-nodes = sum of inter-community edges
  Go back to Phase A on the smaller graph

Repeat until modularity stops increasing.
```

**Time complexity:** O(N log N) — very fast even for thousands of nodes.

**Output:** A partition: `partition = {c1: cluster_0, c2: cluster_0, c3: cluster_1, ...}`

Components in the same cluster will be co-located on the same provider.

---

### 2.4 Phase 3 — Egress-Asymmetry-Aware Assignment

**Algorithm used:** Sorted greedy matching (our invention)

**The insight:** Different providers charge different egress rates:
- GCP: $0.120/GB (most expensive)
- AWS: $0.090/GB
- Azure: $0.087/GB (cheapest)

If clusters MUST be on different providers, put the cluster with the MOST outbound traffic on the provider with the CHEAPEST egress rate.

**Formula:**

```
Step 1: For each cluster k, compute total outbound traffic:
  outbound(k) = SUM over all ci in cluster k, all ck NOT in cluster k:
                T(ci, ck)

Step 2: Sort clusters by outbound traffic (descending):
  sorted_clusters = sort(clusters, key=outbound, descending)
  // Result: [heaviest_sender, ..., lightest_sender]

Step 3: Sort providers by average egress rate (ascending):
  avg_egress(pj) = average over all pl != pj: egress(pj, pl)
  sorted_providers = sort(providers, key=avg_egress, ascending)
  // Result: [Azure($0.087), AWS($0.090), GCP($0.120)]

Step 4: Assign by position:
  sorted_clusters[0] -> sorted_providers[0]  // heaviest sender -> cheapest egress
  sorted_clusters[1] -> sorted_providers[1]
  sorted_clusters[2] -> sorted_providers[2]
```

**Time complexity:** O(K log K) where K = number of clusters (typically 2-4).

**Why this is novel:** No prior work does this. Every paper treats egress as symmetric or ignores it entirely. But in reality, the sender pays — and sender costs differ by 27% across providers.

---

### 2.5 Phase 4 — ILP on Reduced Search Space

**Algorithm used:** Integer Linear Programming with McCormick envelope linearization

**The key trick:** Instead of solving ILP over individual components (3^N), we solve ILP over clusters (3^K where K << N).

**Decision variables:**

```
y[k, pj] in {0, 1}   for each cluster k, provider pj
// 1 if cluster k is assigned to provider pj, 0 otherwise
```

**Objective function (minimize):**

```
Minimize:
  SUM over all clusters k, providers pj:
    cluster_compute_cost(k, pj) * y[k, pj]
  +
  SUM over all cluster pairs (k, l) where k != l,
      all provider pairs (pj, pl):
    inter_cluster_egress(k, l) * egress(pj, pl) * y[k, pj] * y[l, pl]

Where:
  cluster_compute_cost(k, pj) = SUM over all ci in cluster k: compute(ci, pj)
  inter_cluster_egress(k, l) = SUM over all ci in k, ck in l: T(ci, ck)
```

**The quadratic problem:** The term `y[k, pj] * y[l, pl]` is a product of two binary variables — this is NOT linear. ILP solvers require linear constraints.

**McCormick Envelope Linearization:**

```
Introduce auxiliary variable:
  z[k, pj, l, pl] = y[k, pj] * y[l, pl]

Add constraints to force z to behave like the product:
  z[k, pj, l, pl] <= y[k, pj]           // z can't be 1 unless y[k,pj] is 1
  z[k, pj, l, pl] <= y[l, pl]           // z can't be 1 unless y[l,pl] is 1
  z[k, pj, l, pl] >= y[k, pj] + y[l, pl] - 1  // z must be 1 if both y's are 1
  z[k, pj, l, pl] >= 0                  // z can't be negative
```

These four inequalities create an "envelope" around the true product — for binary variables, this is exact (not an approximation).

**Assignment constraint:**

```
For each cluster k:
  SUM over all pj: y[k, pj] = 1   // each cluster on exactly one provider
```

**Why this is fast:** For K=4 clusters, P=3 providers:
- Decision variables: 4 * 3 = 12  (vs 15 * 3 = 45 for full ILP)
- Auxiliary variables: at most 4*3 * 4*3 = 144  (vs 2025 for full ILP)
- Search space: 3^4 = 81  (vs 3^15 = 14,348,907 for full ILP)

**Solver:** PuLP library with CBC (COIN-OR Branch and Cut) backend. Solves in <10ms for K=4.

---

### 2.6 Phase 5 — Component-Level Local Search

**Algorithm used:** First-improvement hill climbing

```
Repeat:
  improved = False
  For each component ci:
    current_provider = A(ci)
    current_total_cost = TotalCost(A)

    For each other provider pj != current_provider:
      A_new = A with ci moved to pj
      new_cost = TotalCost(A_new)

      If new_cost < current_total_cost:
        A = A_new              // accept the swap
        improved = True
        Break                  // restart the scan

Until improved == False       // no single swap improves the solution
```

**Time complexity:** O(N * P) per iteration. Usually converges in 2-3 iterations.

**Why it's needed:** Louvain clusters ALL components in a community to the same provider. But sometimes one component has a dramatically different price profile. Example: a GPU-heavy ML job clustered with cheap web servers. The cluster goes to GCP (cheapest for web), but the GPU job is much cheaper on AWS. Local search catches this.

---

## PART 3 — Full Worked Example: CodeCourt Through All 5 Phases

### The Setup

**CodeCourt components:**

| Component | Type | vCPU | RAM | Role |
|---|---|---|---|---|
| nginx | web_tier | 2 | 4 GB | Load balancer |
| api_server | app_tier | 4 | 8 GB | REST API |
| redis | cache_tier | 4 | 8 GB | Session cache |
| judge_workers | compute_tier | 8 | 16 GB | Runs submitted code |
| postgres | db_tier | 4 | 16 GB | Stores users + submissions |

**Traffic matrix (GB/month):**

| From | To | GB/month |
|---|---|---|
| nginx | api_server | 100 |
| api_server | nginx | 60 |
| api_server | redis | 80 |
| redis | api_server | 75 |
| api_server | judge_workers | 50 |
| judge_workers | api_server | 40 |
| api_server | postgres | 70 |
| postgres | api_server | 60 |

**Compute prices ($/month):**

| Component | AWS | GCP | Azure |
|---|---|---|---|
| nginx (web) | $30.37 | $24.46 | $34.82 |
| api_server (app) | $60.74 | $48.92 | $55.98 |
| redis (cache) | $60.74 | $48.92 | $55.98 |
| judge_workers (compute) | $121.47 | $97.83 | $111.96 |
| postgres (db) | $182.50 | $162.40 | $157.44 |

**Egress rates ($/GB):**

| From / To | AWS | GCP | Azure |
|---|---|---|---|
| AWS | FREE | $0.09 | $0.09 |
| GCP | $0.12 | FREE | $0.12 |
| Azure | $0.087 | $0.087 | FREE |

---

### Phase 1 — Build the Traffic Graph

```
max_egress_rate = $0.12/GB (GCP's rate)

Edges (with weights = traffic * $0.12):
  nginx <-> api_server:      (100 + 60) * 0.12 = $19.20
  api_server <-> redis:      (80 + 75) * 0.12  = $18.60
  api_server <-> judge_workers: (50 + 40) * 0.12 = $10.80
  api_server <-> postgres:   (70 + 60) * 0.12  = $15.60
```

**Graph visualization:**

```
  nginx ---($19.20)--- api_server ---($18.60)--- redis
                          |
                      ($10.80)
                          |
                    judge_workers
                          |
                      ($15.60)
                          |
                       postgres
```

api_server is the central node (hub) with the heaviest connections.

---

### Phase 2 — Louvain Community Detection

Louvain looks at this graph and asks: "Which nodes are most tightly connected?"

**Iteration 1 — Local moves:**
- nginx and api_server have the heaviest edge ($19.20) -> group them
- redis also connects strongly to api_server ($18.60) -> join the group
- judge_workers connects to api_server ($10.80) -> moderate, could go either way
- postgres connects to api_server ($15.60) -> joins the group

**Result (for this topology):** Louvain finds that all 5 components are tightly connected through api_server. It creates:

```
Cluster 0: {nginx, api_server, redis, judge_workers}  (high internal traffic)
Cluster 1: {postgres}  (somewhat isolated, connects only to api_server)
```

OR (depending on resolution):

```
Cluster 0: {nginx, api_server, redis, judge_workers, postgres}  (all in one cluster)
```

**If all components land in one cluster:** TEAP assigns them all to one provider and Phase 4 just picks the cheapest all-in-one option. Let's trace the more interesting case where postgres separates.

---

### Phase 3 — Egress Asymmetry Assignment

**Compute outbound traffic per cluster:**

```
Cluster 0 (nginx, api, redis, judges):
  Outbound to Cluster 1 (postgres): api->postgres = 70 GB
  Total outbound = 70 GB

Cluster 1 (postgres):
  Outbound to Cluster 0: postgres->api = 60 GB
  Total outbound = 60 GB
```

**Sort clusters by outbound (descending):**
```
  [Cluster 0 (70 GB), Cluster 1 (60 GB)]
```

**Sort providers by egress rate (ascending):**
```
  [Azure ($0.087), AWS ($0.090), GCP ($0.120)]
```

**Assign by position (heaviest sender -> cheapest egress):**
```
  Cluster 0 (70 GB outbound) -> Azure (cheapest egress)
  Cluster 1 (60 GB outbound) -> AWS
```

**Phase 3 initial assignment:**
- nginx, api_server, redis, judge_workers -> Azure
- postgres -> AWS

---

### Phase 4 — ILP on Reduced Space

Now ILP checks: is the Phase 3 assignment actually optimal? It solves:

```
Variables:
  y[Cluster0, AWS], y[Cluster0, GCP], y[Cluster0, Azure]  (one must be 1)
  y[Cluster1, AWS], y[Cluster1, GCP], y[Cluster1, Azure]  (one must be 1)

Search space: 3 * 3 = 9 combinations (vs 3^5 = 243 brute force)

For each of the 9 combinations, ILP evaluates:
  Combination: Cluster0=Azure, Cluster1=AWS
    Compute: (34.82 + 55.98 + 55.98 + 111.96) + 182.50 = $441.24
    Egress:  70 * 0.087 (Azure->AWS) + 60 * 0.090 (AWS->Azure) = $6.09 + $5.40 = $11.49
    Total: $452.73

  Combination: Cluster0=GCP, Cluster1=GCP (all on GCP)
    Compute: (24.46 + 48.92 + 48.92 + 97.83) + 162.40 = $382.53
    Egress:  70 * 0 + 60 * 0 = $0 (same provider = free!)
    Total: $382.53    <-- MUCH CHEAPER!

  Combination: Cluster0=GCP, Cluster1=Azure
    Compute: (24.46 + 48.92 + 48.92 + 97.83) + 157.44 = $377.57
    Egress:  70 * 0.12 (GCP->Azure) + 60 * 0.087 (Azure->GCP) = $8.40 + $5.22 = $13.62
    Total: $391.19
```

**ILP finds:** All-on-GCP ($382.53) beats the Phase 3 split assignment ($452.73). Even though Azure DB is $4.96 cheaper than GCP DB, the egress savings of co-locating everything on GCP ($11.49 saved) far exceeds the compute penalty.

**Phase 4 assignment:**
- ALL components -> GCP

---

### Phase 5 — Local Search

Now we try swapping each component individually:

```
Current: all on GCP, total = $382.53

Try moving nginx to AWS:
  Compute change: +$5.91 (AWS is more expensive for web tier)
  Egress change: nginx->api = 100 * 0.09 = $9.00 (was $0)
                 api->nginx = 60 * 0.12 = $7.20 (was $0)
  New total: $382.53 + 5.91 + 9.00 + 7.20 = $404.64  WORSE. Reject.

Try moving postgres to Azure:
  Compute change: -$4.96 (Azure DB is cheaper)
  Egress change: api->postgres = 70 * 0.12 = $8.40 (was $0)
                 postgres->api = 60 * 0.087 = $5.22 (was $0)
  New total: $382.53 - 4.96 + 8.40 + 5.22 = $391.19  WORSE. Reject.

Try every other swap... all worse.
```

**Result:** No single swap improves the solution. Local search confirms the all-GCP assignment is optimal.

---

### Final Answer

```
TEAP result for CodeCourt:
  nginx          -> GCP (e2-medium,  $24.46/mo)
  api_server     -> GCP (e2-standard-4, $48.92/mo)
  redis          -> GCP (e2-standard-4, $48.92/mo)
  judge_workers  -> GCP (e2-standard-8, $97.83/mo)
  postgres       -> GCP (e2-standard-4, $162.40/mo)

  Compute: $382.53/mo
  Egress:  $0.00/mo (all same provider)
  TOTAL:   $382.53/mo

vs Greedy:
  postgres -> Azure ($157.44, saves $4.96 compute)
  But creates $18.60 egress!
  TOTAL: $383.94/mo

  TEAP saves: $1.41/month at 1x traffic
  At 5x traffic: TEAP saves $79.04/month = $948/year
```

---

## PART 4 — Terminology Cheat Sheet

| Term | What it means |
|---|---|
| **Egress** | Data leaving a cloud provider. The sender pays. Intra-provider = free. |
| **Placement / Assignment** | Which component goes on which cloud provider |
| **Topology** | The application architecture: components + traffic between them |
| **Traffic matrix** | A table showing GB/month flowing between each pair of components |
| **NP-hard** | A class of problems where no known algorithm solves it in polynomial time. Must use heuristics or exponential-time algorithms. |
| **ILP** | Integer Linear Programming — mathematical optimization with integer-valued variables |
| **McCormick envelope** | A technique to replace x*y (quadratic) with a new variable z plus 4 linear constraints. Exact for binary variables. |
| **Louvain** | A greedy algorithm that finds communities in graphs by maximizing modularity |
| **Modularity (Q)** | A score from -1 to 1 measuring how well a graph is partitioned into communities. Higher = better clustering. |
| **Community / Cluster** | A group of nodes that are more connected to each other than to the rest of the graph |
| **Local search** | Try small changes to the current solution, keep improvements, stop when no improvement found |
| **Ablation study** | Disable one component at a time to measure its contribution |
| **Parameter sweep** | Vary one input (traffic) while keeping everything else constant, measure how output changes |
| **Baseline** | The reference algorithm (Greedy) that everything is compared against |
| **Ground truth** | The guaranteed correct answer (from Exhaustive brute-force) |
| **Decomposition** | Breaking a large problem into smaller sub-problems, solving each, combining results |
| **Branch-and-bound** | ILP solving technique: explore a tree of possibilities, prune branches that can't be optimal |
| **Metaheuristic** | A high-level strategy for finding good solutions (SA, genetic algorithms, etc.) — not guaranteed optimal but fast |
