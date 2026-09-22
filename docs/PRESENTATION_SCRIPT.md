# 10-Minute Presentation Script — Review 2

> Read this before your review. Follow the timing exactly.
> You will have two screens: the Streamlit dashboard in your browser, and a backup of this script in case you need talking points.

---

## Before the Review

1. Open PowerShell and run:
   ```
   cd "C:\Users\sinha\Desktop\cloud a1\p5-egress-optimizer"
   python -m streamlit run streamlit_app.py
   ```
2. Open browser to `http://localhost:8501`
3. Keep `p5_review2.html` open as a backup (right-click → Open with → Chrome)
4. Have this script open on your phone or a second screen

---

## MINUTE 0-1 — Opening (The Problem)

**Navigate to:** Streamlit → Egress Rate Matrix (sidebar option 6)

**Say:**

> "Our project solves a real problem that every cloud cost calculator ignores — data transfer costs."

**Show the 3×3 egress rate table and explain:**

> "When you put your web server on GCP and your database on Azure, every single byte of data flowing between them costs money. GCP charges 12 cents per GB. Azure charges 8.7 cents. And the standard approach — greedy deployment — completely ignores this."

**Drag the traffic slider to 1000 GB:**

> "At 1000 GB/month of traffic, just by choosing the wrong sender cloud, you waste 33 dollars every month — that's 400 dollars a year from one bad placement decision."

---

## MINUTE 1-3 — Our Solution (TEAP Algorithm)

**Navigate to:** Streamlit → Overview & Figures (sidebar option 1)

**Point to the 4 metric cards:**

> "We built TEAP — Traffic-aware Egress-Aware Placement. A novel 5-phase algorithm that finds the cheapest placement by accounting for both compute AND egress costs."

**Scroll down to the Review 1 baseline table:**

> "In Review 1, we proved the problem is real. The greedy approach costs $304 per month. The optimal is $285. That's a $19 gap — just from ignoring egress on a tiny 3-component app."

**Now explain TEAP phases (keep it simple):**

> "TEAP works in 5 phases:
> 1. Build a traffic graph — heavier edges = more expensive to split
> 2. Use Louvain community detection to find which services talk the most
> 3. Exploit egress rate asymmetry — put heavy senders on cheaper providers
> 4. Run ILP on the reduced search space — only clusters, not individual components
> 5. Local search to polish the result
>
> The key innovation is Phase 4: instead of solving 3^15 = 14 million combinations, we solve 3^4 = 81. That's what makes it fast AND optimal."

---

## MINUTE 3-5 — Live Demo (Parameter Sweep)

**Navigate to:** Streamlit → Live Parameter Sweep (sidebar option 4)

**Select "3-Tier Web App", max 10.0x, click "Run Live Sweep"**

**While it runs, say:**

> "Watch what happens as traffic increases. The red line is greedy — it keeps going up. The green line is TEAP — it stays almost flat."

**When the 15% threshold is crossed (at 2.5x):**

> "There — at 2.5x traffic, the gap crosses 15%. That's our research hypothesis confirmed. At 10x traffic, greedy wastes 43.9% — nearly half the budget."

**Point to the bar chart on the right:**

> "Each bar shows the percentage gap. At 10x, the greedy approach wastes $231 per month compared to TEAP. That's $2,700 per year. For one application."

---

## MINUTE 5-7 — CodeCourt Case Study (Your Real Project)

**Navigate to:** Streamlit → CodeCourt Case Study (sidebar option 7)

**Click "Run Greedy vs TEAP Comparison"**

**Point to the two columns:**

> "This is our actual CodeCourt online judge. 5 components — Nginx, API, Redis, Judge Workers, PostgreSQL."

**Point to the Greedy column:**

> "Greedy puts PostgreSQL on Azure because Azure DB is $4.96 cheaper in compute. But this creates $18.60 of cross-cloud egress. Net loss."

**Point to the TEAP column:**

> "TEAP moves PostgreSQL to GCP. Pays $4.96 more in compute, saves $16.80 in egress. Net win: $11.84 per month."

**Point to the table at the bottom:**

> "At 5x traffic — which is realistic for a production system — TEAP saves $79 per month. That's $948 per year. And the hypothesis threshold of 15% is crossed."

---

## MINUTE 7-8 — Algorithm Comparison (Proof)

**Navigate to:** Streamlit → Algorithm Comparison (sidebar option 2)

**Select "3-Tier Web App", slider to 3.5x, click "Run All Algorithms"**

> "Here's the proof that TEAP actually works. All 6 algorithms ran on the same topology, same traffic."

**Point to the table:**

> "Greedy: $366. Every other algorithm: $288. TEAP matches the true optimal — verified by exhaustive brute-force. It's not an approximation. On every topology we tested, TEAP finds the exact same cost as the ILP and the exhaustive solver."

**Point to the green/red row highlighting:**

> "Green rows = optimal. Red = wasteful. Greedy is always red."

---

## MINUTE 8-9 — Ablation Study (Proof of Novelty)

**Navigate to:** Streamlit → Ablation Study (sidebar option 5)

**Select "Microservice Mesh", 3.5x traffic, click Run:**

> "This answers the question: which part of our algorithm actually matters?"

**Point to the table:**

> "When we disable ILP refinement — Phase 4 — the cost jumps by 31.9%. Clustering alone isn't enough. Asymmetry alone isn't enough. The ILP refinement on the reduced search space is what makes TEAP work."

> "This validates our core contribution: decompose the problem first using Louvain, then solve the smaller problem exactly using ILP."

---

## MINUTE 9-10 — Summary & What's Next

**Navigate to:** Streamlit → Overview page (scroll to top)

**Point to the 4 metric cards and summarize:**

> "To summarize:
> - We proved that ignoring egress costs wastes up to 43.9% of cloud budget
> - Our TEAP algorithm finds the optimal placement on every topology tested
> - On our real CodeCourt project, it saves $948/year at 5x traffic
> - The 15% hypothesis is confirmed at 2.5x traffic for 3-Tier and 5x for CodeCourt"

**If asked "What's next for Review 3?":**

> "Three things:
> 1. IaC parser — paste Terraform or Docker Compose, auto-generate topology
> 2. Real-time pricing — live AWS/Azure API integration
> 3. Web input form — a frontend where anyone can analyze their architecture"

---

## Common Questions & Answers

### Q: "Why not just put everything on one cloud?"

> "Sometimes that IS the best answer — and our algorithm finds that automatically. For 3-Tier Web App, all-GCP wins. But for complex topologies with mixed resource requirements — like GPU for ML but cheap storage on Azure — mixing providers can be cheaper. Our algorithm figures out which case applies."

### Q: "What is ILP?"

> "Integer Linear Programming — a mathematical optimization technique that finds the globally optimal solution by modeling the problem as linear constraints with integer variables. We use the PuLP library with the CBC solver. The key challenge was linearizing the quadratic egress cost term using McCormick envelopes."

### Q: "Why did you choose Louvain for community detection?"

> "Louvain is designed for weighted graphs — it respects edge weights, which is exactly what we need for traffic-weighted component graphs. K-means works on vectors, not graphs. Spectral clustering works but is O(N^3). Louvain is O(N log N) and gives better communities on our traffic graphs."

### Q: "Is this original research?"

> "Yes. No prior paper combines community detection + egress asymmetry exploitation + reduced-space ILP decomposition in a single pipeline for cloud placement. Each technique exists individually — our contribution is the novel combination and the proof that it matches the exact optimal."

### Q: "How did you verify correctness?"

> "Three ways:
> 1. Exhaustive brute-force on small topologies (3-5 components) — TEAP matches every time
> 2. ILP solver gives guaranteed optimal — TEAP matches ILP on all 5 topologies
> 3. Regression test: Review 1 numbers ($304.41 greedy, $285.70 optimal) must pass on every run"

### Q: "What happens with more than 3 providers?"

> "TEAP scales naturally. Adding a 4th provider (e.g., Oracle Cloud) just adds one more column to the pricing model. The Louvain phase is provider-agnostic. The ILP phase would solve 4^K instead of 3^K — still fast because K (number of clusters) is small."

### Q: "Can this work with latency or SLA constraints?"

> "Not yet — that's Review 3 scope. But the ILP formulation can easily add constraints like 'database must stay in region X' or 'latency between frontend and API must be < 50ms'. The framework supports it; we just need to add the constraint data."

---

## Backup Demo (If Streamlit Fails)

If Streamlit doesn't start, fall back to the CLI dashboard:

```
cd "C:\Users\sinha\Desktop\cloud a1\p5-egress-optimizer"
python dashboard.py
```

Show options in this order:
1. `[5]` Egress rates
2. `[6]` CodeCourt case study
3. `[3]` Live sweep → pick 3-Tier Web App
4. `[1]` Algorithm comparison → pick CodeCourt, 3.5x traffic
5. `[4]` Ablation → pick Microservice Mesh, 3.5x traffic

Or simply open `C:\Users\sinha\Desktop\cloud a1\p5_review2.html` in Chrome — it has all results, tables, and figures embedded.

---

## Files to Show If Asked

| What they want to see | Where it is |
|---|---|
| Full project report | `C:\Users\sinha\Desktop\cloud a1\p5_review2.html` |
| Source code | `C:\Users\sinha\Desktop\cloud a1\p5-egress-optimizer\src\` |
| TEAP algorithm | `src\algorithms\teap.py` |
| ILP solver | `src\algorithms\ilp_solver.py` |
| Generated charts | `results\figures\fig1-fig6.png` |
| Raw benchmark data | `results\tables\benchmark_results.csv` |
| GitHub repo | https://github.com/AtharvSinha26052005/multicloud_egress_optimizer |
| Algorithm docs | `docs\ALGORITHMS.md` |
| Architecture docs | `docs\Architecture.md` |
| Decision log | `docs\Decisions.md` |
