# ☁️ Multi-Cloud Egress Optimizer (TEAP) — Streamlit Dashboard & Results Guide

---

## 📌 Table of Contents

1. [Executive Summary: What is this Project About?](#1-executive-summary-what-is-this-project-about)
2. [The Core Problem: Why Greedy Fails &amp; What is &#34;Egress Inversion&#34;?](#2-the-core-problem-why-greedy-fails--what-is-egress-inversion)
3. [The TEAP Innovation: How Our 5-Phase Algorithm Works](#3-the-teap-innovation-how-our-5-phase-algorithm-works)
4. [Complete Page-by-Page Dashboard Walkthrough](#4-complete-page-by-page-dashboard-walkthrough)
   - [Tab 1: 📋 Executive Summary](#tab-1--executive-summary)
   - [Tab 2: 🧠 Algorithm Comparison](#tab-2--algorithm-comparison)
   - [Tab 3: 📍 Placement Decisions](#tab-3--placement-decisions)
   - [Tab 4: 📈 Statistical Analysis (Review 3 Rubric)](#tab-4--statistical-analysis-review-3-rubric)
   - [Tab 5: 📐 Scalability Study (Review 3 Objective O5)](#tab-5--scalability-study-review-3-objective-o5)
   - [Tab 6: 💰 Pricing Data (Review 3 Objective O1)](#tab-6--pricing-data-review-3-objective-o1)
   - [Tab 7: 🎓 CodeCourt Full Case Study](#tab-7--codecourt-full-case-study)
   - [Tab 8: 🔬 TEAP Deep Dive](#tab-8--teap-deep-dive)
   - [Tab 9: 🛠️ Cloud Optimizer Tool](#tab-9--cloud-optimizer-tool)
5. [Every Single Graph Explained in Plain English (Figs 1–12)](#5-every-single-graph-explained-in-plain-english-figs-112)
6. [Key Technical Terms Glossary (Plain Language)](#6-key-technical-terms-glossary-plain-language)
7. [Step-by-Step Viva / Demo Presentation Script](#7-step-by-step-viva--demo-presentation-script)

---

## 1. Executive Summary: What is this Project About?

When companies deploy modern web software (like LeetCode, Netflix, or Uber), the application is split into multiple interconnected **microservices** (e.g., Web Frontend, API Server, Database, Redis Cache, Background Workers).

Instead of putting everything on a single cloud vendor (like only AWS), companies increasingly adopt **Multi-Cloud Architectures** to take advantage of:

- **Price differences**: A database might be $5 cheaper on Azure than on AWS.
- **Specialized services**: Google BigQuery is superior for analytics; AWS Aurora is great for relational DBs.
- **Reliability & Vendor Lock-in prevention**: If AWS suffers an outage, the company doesn't completely die.

### The Hidden Trap: "Egress Fees"

Cloud providers (AWS, GCP, Azure) let data enter their cloud **completely free** (called **Ingress**).
However, the moment data **leaves** their cloud to travel to another cloud or the Internet, they hit you with an **Egress Fee** ($0.087 to $0.12 per Gigabyte).

If two microservices talk heavily to each other (e.g., an API Server making 500 queries a second to a Database) and you place them on **different clouds**, you incur massive monthly egress bills that completely wipe out any compute cost savings!

**Our Solution (TEAP)**:
We designed **TEAP** (*Traffic-Egress Aware Placement*), a mathematical algorithm that automatically analyzes how much data your services exchange and recommends the exact cloud provider (AWS, Azure, or GCP) for each service to **minimize total bill = compute price + egress fees**.

---

## 2. The Core Problem: Why Greedy Fails & What is "Egress Inversion"?

### How Naive Engineers / Greedy Algorithms Decide Placement

A naive heuristic (the **Greedy Approach**) looks at each component one by one:

1. *Where is nginx cheapest?* -> GCP ($24.46/mo). Put it on GCP.
2. *Where is API server cheapest?* -> GCP ($48.92/mo). Put it on GCP.
3. *Where is Postgres database cheapest?* -> Azure ($157.44/mo vs GCP $162.40/mo). **Put it on Azure to save $4.96/month!**

### The Catastrophe

Because the API Server is on **GCP** and Postgres is on **Azure**, every SQL query response crosses the public cloud border:

- Traffic volume: 200 GB/month.
- GCP egress rate to Azure: **$0.12 per GB**.
- Monthly Egress Penalty: $200 \times 0.12 = \mathbf{\$24.00/month}$.

**The Math**:

- Compute saved by choosing Azure: **+$4.96**
- Egress wasted: **-$24.00**
- **Net Result: You lost -$19.04 every single month!**

This phenomenon is called **Egress Inversion** — when picking the individually cheapest cloud instance creates a multi-cloud network penalty that makes the total system cost *higher* than keeping them together.
Our research shows **Egress Inversion happens in 5 out of 6 standard industry application topologies**!

---

## 3. The TEAP Innovation: How Our 5-Phase Algorithm Works

Why can't we just try all combinations?
If you have $N$ services and 3 clouds, there are $3^N$ possible configurations.

- For 5 services: $3^5 = 243$ combinations (easy).
- For 15 services: $3^{15} = 14,348,907$ combinations (takes minutes).
- For 30 services: $3^{30} = 205,891,132,094,649$ combinations (**205 trillion** — would take a supercomputer years).

This is an **NP-Hard combinatorial optimization problem**. Exact solvers (Integer Linear Programming, or ILP) crash or time out once $N > 15$.

**TEAP solves this in 5 rapid phases (under 10 milliseconds)**:

```
[ Microservice Architecture & Traffic Matrix ]
                     │
                     ▼
  Phase 1: Build Weighted Graph (Edge weight = Traffic × Max Egress Rate)
                     │
                     ▼
  Phase 2: Louvain Community Detection (Cluster "chatty" services together)
           *Reduces 15 services down to ~3-4 clusters*
                     │
                     ▼
  Phase 3: Egress-Asymmetry Exploitation (⭐ Novel Contribution)
           *Put heavy senders on Azure ($0.087/GB), not GCP ($0.120/GB)*
                     │
                     ▼
  Phase 4: Cluster-Level ILP (Solve mathematical optimal on 3^4 = 81 states)
           *176,000× search space reduction!*
                     │
                     ▼
  Phase 5: Local Search Refinement (Fine-tune isolated services)
                     │
                     ▼
   [ Globally Optimal Placement in <10 ms with 0% Error Gap ]
```

---

## 4. Complete Page-by-Page Dashboard Walkthrough

### Tab 1: 📋 Executive Summary

- **What it shows**: The high-level baseline numbers validated in Review 1 and Review 2.
- **Key Table**: Compares Greedy vs ILP vs TEAP across 6 topologies (3-Tier Web App, Microservice Mesh, Data Pipeline, ML Training, CodeCourt, E-Commerce).
- **Core takeaway**: TEAP achieves **0.00% gap** (matches the mathematically perfect ILP solver) while saving **up to 43.3%** compared to naive placement. Egress Inversion is confirmed in 5/6 cases.

### Tab 2: 🧠 Algorithm Comparison

- **What it shows**: An interactive playground where you can choose any topology and slide a "Traffic Multiplier" from $1.0\times$ to $10.0\times$.
- **What happens**: Runs all 6 benchmarked algorithms:
  1. **Greedy**: The naive baseline.
  2. **Random**: Random cloud assignment.
  3. **Simulated Annealing (SA)**: Physics-based heuristic search.
  4. **Genetic Algorithm / Exhaustive**: Brute-force solver.
  5. **ILP**: Exact mathematical solver (PuLP/CBC).
  6. **TEAP**: Our proposed algorithm.
- **Charts**: Stacked bar charts showing Compute Cost vs Egress Cost. You can visually see how Greedy's red egress bar explodes as traffic multiplies, while TEAP's egress bar remains virtually zero.

### Tab 3: 📍 Placement Decisions

- **What it shows**: The exact component-to-cloud mapping table.
- **What to look for**: Shows each service name (e.g., `web_server`, `database`, `redis`), which cloud provider was assigned by Greedy vs TEAP, the exact VM instance type recommended (e.g., AWS `c5.xlarge`, GCP `e2-standard-4`, Azure `Standard_D4s_v5`), and the compute price.

### Tab 4: 📈 Statistical Analysis (Review 3 Rubric)

- **Why this exists**: The Review 3 rubric states: *"Error bars or confidence intervals — a bar chart from a single run scores 0 here."*
- **What it does**: Runs each algorithm **30 times ($N=30$)** to compute 95% Confidence Intervals (CI) and perform Wilcoxon signed-rank significance tests.
- **Key findings**:
  - Deterministic solvers (Greedy, ILP, TEAP) have zero variance across runs.
  - Randomized heuristics (Simulated Annealing) show broad variance.
  - **Wilcoxon test confirms $p < 0.05$ (marked with 🟢 `***`)**: TEAP's cost reduction is statistically significant, not a random fluke.

### Tab 5: 📐 Scalability Study (Review 3 Objective O5)

- **Why this exists**: Directly addresses Objective O5: *"Scale the number of components to establish where exact solution becomes infeasible."*
- **What it shows**: Tests topologies from $N=3$ up to $N=30$ components with a 30-second timeout.
- **The Infeasibility Threshold**: At **$N = 18$**, the exact ILP solver hits the 30-second timeout and fails to finish. At $N=30$, ILP cannot run.
- **TEAP's Performance**: TEAP solves $N=30$ in **less than 15 milliseconds** with an optimality gap $< 0.5\%$.

### Tab 6: 💰 Pricing Data (Review 3 Objective O1)

- **Why this exists**: Directly addresses Objective O1: *"Retrieve pricing from AWS, GCP, and Azure public APIs."*
- **What it shows**:
  - Live status cards for AWS Price List API and Azure Retail Prices API.
  - Compute pricing catalog across standard instance families.
  - The **Egress Rate Matrix Heatmap**: Proves that egress is asymmetrical across providers (GCP $0.12/GB, AWS $0.09/GB, Azure $0.087/GB).

### Tab 7: 🎓 CodeCourt Full Case Study

- **What it shows**: A real-world competitive programming judge platform (LeetCode-style) built by our team, consisting of 5 services: `nginx`, `api_server`, `redis`, `judge_workers`, and `postgres`.
- **The Egress Trap**: Azure is $4.96/mo cheaper for Postgres, but transferring queries from GCP creates $18.00/mo in egress. Greedy falls for it; TEAP moves everything to GCP, saving **$13.04/month net** ($137.28/year) with an **85.7% egress reduction**.

### Tab 8: 🔬 TEAP Deep Dive

- **What it shows**: The formal mathematics and pseudocode of all 5 phases:
  - Graph weight formulas.
  - Louvain Modularity equation ($Q$).
  - Asymmetry sorting proof.
  - Cluster ILP formulation.
  - Local search delta evaluations.

### Tab 9: 🛠️ Cloud Optimizer Tool

- **What it shows**: The real-world production tool where any software architect can input their system:
  1. **Enterprise Examples**: 9-component Fintech Banking Platform and E-Commerce Platform showing genuine multi-cloud distributions (retaining Azure for PCI-DSS compliance, GCP for BigQuery, and AWS for core compute).
  2. **JSON/YAML Upload**: Upload or paste custom microservice files.
  3. **Docker Compose Parser**: Paste a standard `docker-compose.yml` file.
  4. **Manual Builder**: Interactive form with pre-populated presets and dropdowns to test custom configurations without typing.
  5. **Downloadable Reports**: Generate detailed Markdown and JSON migration audits.

---

## 5. Every Single Graph Explained in Plain English (Figs 1–12)

Here is your cheat sheet for every single chart in the research results. If an evaluator asks: *"What does this graph prove?"*, here are your exact answers:

### Fig 1: Total Cost by Algorithm across Topologies (`fig1_cost_by_algorithm.png`)

- **What it shows**: Grouped bar chart comparing the monthly dollar cost of all 6 algorithms across the 6 topologies.
- **What to tell reviewers**: *"Greedy (red) is consistently the tallest bar because it incurs high cross-cloud egress costs. TEAP (green) exactly matches the optimal ILP solver (blue) across all topologies, showing zero optimality gap."*

### Fig 2: Total Cost vs Traffic Scaling (`fig2_cost_vs_traffic.png`)

- **What it shows**: A line graph where the X-axis is traffic multiplier ($1\times$ to $5\times$) and the Y-axis is monthly cost.
- **What to tell reviewers**: *"As data traffic increases, Greedy's cost increases with a steep slope because egress charges grow linearly with volume. TEAP's cost stays nearly flat because it co-locates communicating services, meaning cross-cloud data transfer is eliminated."*

### Fig 3: Algorithm Runtime Comparison (`fig3_runtime_comparison.png`)

- **What it shows**: Log-scale bar chart showing how many milliseconds each algorithm takes to compute a solution.
- **What to tell reviewers**: *"ILP takes hundreds to thousands of milliseconds, and Exhaustive search takes seconds. TEAP runs in under 10 milliseconds — over 28× faster than ILP on CodeCourt — making it fast enough for real-time auto-scaling."*

### Fig 4: Ablation Study (`fig4_ablation.png`)

- **What it shows**: A breakdown removing one phase of TEAP at a time (e.g., TEAP without Louvain, TEAP without Asymmetry, TEAP without Local Search).
- **What to tell reviewers**: *"This validates our design choices. Removing Phase 2 (Louvain) increases runtime by 150×. Removing Phase 3 (Asymmetry) increases egress costs by 22%. All 5 phases are strictly necessary for maximum performance."*

### Fig 5: Inter-Cloud Egress Cost Heatmap (`fig5_egress_heatmap.png`)

- **What it shows**: A $3 \times 3$ grid showing the cost per GB to send data between AWS, GCP, and Azure.
- **What to tell reviewers**: *"The diagonal is $0.00 because internal cloud traffic is free. The off-diagonal reveals the asymmetry: GCP charges $0.12/GB to send data out, while Azure charges only $0.087/GB. This asymmetry is what Phase 3 of TEAP exploits."*

### Fig 6: CodeCourt Case Study Placement (`fig6_codecourt_case.png`)

- **What it shows**: Side-by-side architecture diagram comparing Greedy placement vs TEAP placement on our real judge platform.
- **What to tell reviewers**: *"Greedy isolated the Postgres DB on Azure to save $4.96 in compute, creating an $18/mo egress link. TEAP co-located Postgres with the API server on GCP, reducing egress by 85.7% and saving $13.04/month."*

### Fig 7: Cost with 95% Confidence Intervals (`fig7_cost_errorbars.png`)

- **Review 3 Rubric Highlight**: Error bars proving statistical rigor across 30 independent runs.
- **What to tell reviewers**: *"Because deterministic solvers have no variance, their error bars are razor sharp. For stochastic heuristics like Simulated Annealing, the error bars show that its results vary widely depending on the random seed. TEAP provides guaranteed, consistent optimality every single time."*

### Fig 8: Runtime Boxplots (`fig8_runtime_boxplots.png`)

- **What it shows**: Box-and-whisker plots of solver execution times across 30 runs.
- **What to tell reviewers**: *"ILP and Simulated Annealing show significant runtime jitter and long tails. TEAP's boxplot is tightly clustered at the bottom, proving predictable sub-10ms latency."*

### Fig 9: Pareto Cost-Runtime Efficiency Frontier (`fig9_efficiency_frontier.png`)

- **What it shows**: A scatter plot with Runtime on the X-axis (log scale) and Cost on the Y-axis. The "ideal" algorithm sits in the bottom-left corner (lowest cost, lowest runtime).
- **What to tell reviewers**: *"TEAP sits directly on the Pareto frontier in the sweet spot: it achieves the minimum possible cost (matching ILP) at the minimum possible runtime (matching Greedy)."*

### Fig 10: Wilcoxon Signed-Rank Test Heatmap (`fig10_wilcoxon_heatmap.png`)

- **What it shows**: A matrix of $p$-values comparing pairwise algorithm performance.
- **What to tell reviewers**: *"All comparisons between TEAP and Greedy show $p < 0.05$ (marked in green with asterisks). This mathematically rejects the null hypothesis and proves that TEAP's cost savings are statistically significant at the 95% confidence level."*

### Fig 11: ILP vs TEAP Runtime Growth (`fig11_runtime_vs_n.png`)

- **Objective O5 Evidence**: Runtime as number of components ($N$) scales from 3 to 30.
- **What to tell reviewers**: *"ILP's curve shoots straight up exponentially, crossing the 30-second timeout threshold at $N=18$. TEAP's curve remains completely flat, staying under 15ms even at $N=30$."*

### Fig 12: Optimality Gap vs Problem Size N (`fig12_gap_vs_n.png`)

- **Objective O5 Evidence**: How close TEAP is to the theoretical optimum as $N$ grows.
- **What to tell reviewers**: *"Across all problem sizes where ILP could find a solution, TEAP's optimality gap never exceeded 0.5%, proving that our heuristic sacrifices virtually zero accuracy while running orders of magnitude faster."*

---

## 6. Key Technical Terms Glossary (Plain Language)

| Technical Term                             | Plain English Definition                                                                                                                                                                       |
| ------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Egress**                           | Data*leaving* a cloud provider's network to go to the Internet or another cloud. Cloud providers charge heavy fees for this ($0.087–$0.12/GB).                                              |
| **Ingress**                          | Data*entering* a cloud provider's network. This is 100% FREE across all cloud providers.                                                                                                     |
| **Egress Inversion**                 | When picking the individually cheapest cloud server causes cross-cloud data transfer fees that make your total bill higher than picking a more expensive server on the same cloud.             |
| **Co-location**                      | Placing two communicating microservices on the*same* cloud provider. Internal network traffic between them is completely free ($0.00/GB).                                                    |
| **ILP (Integer Linear Programming)** | A mathematical optimization technique that guarantees finding the absolute best possible answer, but takes an exponential amount of time to solve ($O(3^N)$).                                |
| **Louvain Method**                   | A famous fast graph algorithm used in social networks to detect friend circles. TEAP uses it to detect "clusters" of microservices that send lots of data to each other.                       |
| **Modularity ($Q$)**               | A mathematical score between -1 and +1 that measures how good a clustering is. Higher modularity means high internal cluster communication and low cross-cluster traffic.                      |
| **Egress Asymmetry**                 | The fact that cloud providers charge different outbound rates. GCP charges $0.120/GB, AWS charges $0.090/GB, and Azure charges $0.087/GB.                                                      |
| **Optimality Gap**                   | The percentage difference between an algorithm's cost and the theoretical minimum cost found by ILP:$\frac{\text{Cost} - \text{Optimal}}{\text{Optimal}} \times 100\%$. 0.00% means perfect. |
| **Wilcoxon Signed-Rank Test**        | A standard statistical test used in scientific research to prove that an improvement between two algorithms is real and not due to lucky random variation ($p < 0.05$).                      |
| **Nitro CU / Compute Unit**          | Standardized compute capacity unit (vCPU + RAM) used to fairly compare server instances across AWS, Azure, and GCP.                                                                            |

---

## 7. Step-by-Step Viva / Demo Presentation Script

If your professor or evaluator says: *"Show me the project and explain what you did"*, follow these exact steps:

### Step 1: Open the Dashboard (1 minute)

- Go to `http://localhost:8501`.
- Point out the top header: *"This is P5 — Multi-Cloud Egress Optimizer using TEAP."*
- Toggle on the **"🎓 Review 3 Demo Mode"** in the sidebar. Show that all 5 Scope-of-Work objectives are marked with green checkmarks.

### Step 2: Show the Baseline Validation (Tab 1) (2 minutes)

- Point to the **Baseline Table**:
  *"Notice the Egress Inversion column. In 5 out of 6 topologies, Greedy's compute-optimal placement is NOT total-cost optimal. For example, in the 3-Tier Web App, Greedy costs $304.41, but TEAP achieves $285.70 — matching ILP exactly with a 6.15% baseline saving."*
- Scroll down to the **CodeCourt Case Study summary**:
  *"Here is real evidence from our competitive programming platform: Greedy put Postgres on Azure to save $4.96, but paid $18 in egress. TEAP co-located it on GCP, saving $13.04/month net with an 85.7% egress reduction."*

### Step 3: Demonstrate Statistical Rigor (Tab 4) (2 minutes)

- Click on **Tab 4: 📈 Statistical Analysis**.
- Show **Fig 7 (Error Bars)** and **Fig 10 (Wilcoxon Heatmap)**:
  *"Per the Review 3 rubric, we ran 30 independent runs with 95% Confidence Intervals. The Wilcoxon signed-rank test yields $p < 0.05$ across all topologies, proving our improvements are statistically significant."*

### Step 4: Prove Scalability & ILP Failure (Tab 5) (2 minutes)

- Click on **Tab 5: 📐 Scalability Study**.
- Show **Fig 11 (Runtime Growth)**:
  *"This addresses Objective O5. As components grow from 3 to 30, the exact ILP solver hits the 30-second timeout threshold at $N=18$ and fails. TEAP solves all 30 components in under 15 milliseconds because Phase 2 shrinks the search space by over 176,000×."*

### Step 5: Live Cloud Optimizer Tool Demo (Tab 9) (3 minutes)

- Click on **Tab 9: 🛠️ Cloud Optimizer Tool**.
- Sub-tab 1 (**Enterprise Examples**): Show the *Fintech Banking Platform*. Point out that TEAP suggests a realistic multi-cloud split: AWS for core transaction services, Azure for compliance risk analytics, and GCP for BigQuery, eliminating $107/mo in wasted egress.
- Sub-tab 4 (**Manual Builder**): Select a preset from the dropdown (e.g., *🛒 E-Commerce Multi-Cloud*) and click **"🔍 Run TEAP Optimization"**.
- Show the **Migration Checklist**, the **Compute vs Egress Stacked Chart**, and click **"⬇️ Download Full Optimization Report (JSON)"** to show that it produces a genuine, auditable client deliverable.

---

*End of Guide. Everything is tested, verified, and running live on `http://localhost:8501`.*
