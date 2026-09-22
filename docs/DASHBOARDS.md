# Dashboards — CLI and Streamlit Explained In Depth

> This document explains both dashboards: the CLI (`dashboard.py`) and the Streamlit web app (`streamlit_app.py`).
> Covers: how to run, each option/page, what it shows, and how to use it for the review presentation.

---

## Quick Start

```bash
# CLI Dashboard (terminal-based, no browser needed)
cd "C:\Users\sinha\Desktop\cloud a1\p5-egress-optimizer"
python dashboard.py

# Streamlit Web Dashboard (browser-based)
python -m streamlit run streamlit_app.py
# Then open: http://localhost:8501
```

---

# Part 1 — CLI Dashboard (`dashboard.py`)

The CLI dashboard is a terminal menu system. It runs directly in your PowerShell/Command Prompt window. No browser, no dependencies beyond what's already installed.

```
================================================================
  P5 - Egress-Aware Cost-Optimal Multi-Cloud Placement
  Interactive Dashboard | Review 2 Demo
================================================================

  [1] Run all algorithms on a topology (side-by-side)
  [2] Show placement decisions (which component -> which cloud)
  [3] Live parameter sweep (watch cost grow with traffic)
  [4] Ablation study (which TEAP phase matters most)
  [5] Egress rate comparison (why direction matters)
  [6] CodeCourt case study (your real project)
  [7] Run full benchmark (120 experiments)
  [8] Pricing data explorer
  [0] Exit
```

After each option, press Enter to return to the menu.

---

## CLI Option [1] — Run All Algorithms on a Topology

**What it does:** Runs all 6 algorithms on a topology you choose, then prints a comparison table.

**Flow:**
1. Shows list of 5 topologies with component count and edge count
2. You type a number (1-5) to select one
3. You type a traffic multiplier (e.g., 3.5) or press Enter for 1.0
4. All 6 algorithms run sequentially
5. Results printed in a grid table
6. Gap analysis printed below: which algorithms are optimal, which overpay by how much %

**Example output:**
```
--- 3-Tier Web App (traffic x3.5) ---
+---------------------+-----------+----------+---------+-----------+
| Algorithm           | Compute   | Egress   | Total   | Runtime   |
+=====================+===========+==========+=========+===========+
| Greedy              | $279.54   | $87.05   | $366.58 | 0.0ms     |
| Single-Provider     | $284.50   | $4.20    | $288.70 | 0.0ms     |
| Exhaustive          | $284.50   | $4.20    | $288.70 | 0.2ms     |
| ILP                 | $284.50   | $4.20    | $288.70 | 47.3ms    |
| Simulated Annealing | $284.50   | $4.20    | $288.70 | 10.0ms    |
| TEAP                | $284.50   | $4.20    | $288.70 | 161.8ms   |
+---------------------+-----------+----------+---------+-----------+

Optimal: $288.70
Greedy: +$77.88/mo (+21.2%) WASTED
```

**When to use in your review:** When the teacher asks "Show me that your algorithm works" — run this, pick CodeCourt, pick 3.5x traffic. Point out TEAP matches optimal and Greedy wastes 21%.

---

## CLI Option [2] — Show Placement Decisions

**What it does:** Shows exactly which component goes to which cloud, for Greedy vs TEAP vs ILP side by side.

**Flow:**
1. Select topology
2. Greedy, TEAP, and ILP all run on the baseline topology
3. For each algorithm: print a table of (component name, description, assigned provider, compute cost)
4. Show total compute and egress for each

**Example output (CodeCourt):**
```
--- Greedy (Total: $383.94) ---
+------------------+------------------+--------+------------+
| Component        | Role             | Prov   | Compute    |
+==================+==================+========+============+
| nginx            | Load balancer    | GCP    | $12.23     |
| api_server       | REST API         | GCP    | $48.92     |
| redis            | Cache layer      | GCP    | $48.92     |
| judge_workers    | Code execution   | GCP    | $97.83     |
| postgres         | Database         | Azure  | $157.44    |
+------------------+------------------+--------+------------+
Compute: $365.34 | Egress: $18.60

--- TEAP (Total: $372.10) ---
| postgres         | Database         | GCP    | $162.40    |  <- TEAP moved this!
Compute: $370.30 | Egress: $1.80
```

**The insight:** Greedy puts PostgreSQL on Azure because Azure DB is slightly cheaper ($157.44 vs GCP $162.40 = $4.96 savings). But this creates $18.60/month of egress from GCP→Azure. TEAP moves it to GCP: pays $4.96 more in compute but saves $16.80 in egress. Net gain: $11.84/month.

**When to use:** When teacher asks "How does your algorithm actually work? What decision does it make differently?"

---

## CLI Option [3] — Live Parameter Sweep

**What it does:** Slowly increases traffic from 0.5x to 10x and prints results in real-time with an ASCII bar chart showing the gap growing.

**Flow:**
1. Select topology (3-Tier Web App recommended)
2. Algorithm runs Greedy and TEAP at each traffic level
3. Prints one row every ~300ms — looks "live"
4. Each row has an ASCII `#` bar proportional to the gap %
5. Marks rows where the gap crosses 15% with `<-- 15% threshold`

**Example output:**
```
Live Sweep: 3-Tier Web App
  Traffic      Greedy      TEAP    Savings    Gap%  Bar
  -------------------------------------------------------
       0.5x $  291.97 $  285.10 $    6.87     2.4%  ####
       1.0x $  304.41 $  285.70 $   18.71     6.1%  ############
       1.5x $  316.84 $  286.30 $   30.54     9.6%  ###################
       2.0x $  329.28 $  286.90 $   42.38    12.9%  #########################
       2.5x $  341.71 $  287.50 $   54.21    15.9%  ################# <-- 15% threshold
       3.0x $  354.15 $  288.10 $   66.05    18.7%  #####################################
       ...
      10.0x $  528.24 $  296.50 $  231.74    43.9%  ###########################################
```

**When to use:** This is the best option for a live demo. Run this during the presentation and let it play out while explaining. The real-time updating makes it visually engaging. The 15% threshold crossing is your research hypothesis being proven live.

---

## CLI Option [4] — Ablation Study

**What it does:** Tests TEAP with each phase disabled, showing which phase causes the savings.

**Flow:**
1. Select topology and traffic multiplier (3.5x recommended)
2. Runs 5 variants: Greedy baseline, TEAP-full, TEAP-no-clustering, TEAP-no-asymmetry, TEAP-no-ILP
3. Prints a comparison table
4. Identifies which phase has the biggest impact

**Example output (Microservice Mesh at 3.5x):**
```
--- Microservice Mesh ---
  Greedy (baseline)          -> $326.17 (compute=$317.77, egress=$8.40)
  TEAP-full                  -> $326.17 (compute=$317.77, egress=$8.40)
  TEAP (no clustering)       -> $326.17 (same)
  TEAP (no asymmetry)        -> $326.17 (same)
  TEAP (no ILP refine)       -> $430.08 (compute=$330.33, egress=$99.75)   <- BIG JUMP
  >> Same cost (topology favors single-provider)
```

**The key finding:** Removing ILP refinement causes a 31.9% cost jump on Microservice Mesh. This proves Phase 4 (ILP refinement) is the critical phase, not just Phases 2 or 3.

**When to use:** When teacher asks "Which part of your algorithm actually matters? Prove it." This is your proof.

---

## CLI Option [5] — Egress Rate Comparison

**What it does:** Prints the 3×3 egress rate matrix and a worked example with actual dollar amounts.

**Output:**
```
Egress Rates ($/GB) - Why Direction Matters

+-------------+--------+--------+---------+
| From \ To   | AWS    | GCP    | Azure   |
+=============+========+========+=========+
| AWS         | FREE   | $0.090 | $0.090  |
| GCP         | $0.120 | FREE   | $0.120  |  <- Most expensive row
| Azure       | $0.087 | $0.087 | FREE    |  <- Cheapest row

KEY INSIGHT (TEAP Phase 3):
  For 500 GB/month of traffic:
  - If sender is on GCP:   $60.00/mo in egress
  - If sender is on Azure: $43.50/mo in egress
  - Savings by swapping direction: $16.50/mo (27% less egress!)
```

**When to use:** At the START of your presentation, before showing results. This explains why the problem exists and why direction matters.

---

## CLI Option [6] — CodeCourt Case Study

**What it does:** Runs the optimizer on the exact CodeCourt architecture and shows savings at baseline and 5x traffic.

**Output:**
```
CodeCourt Online Judge - Real-World Case Study
Components: nginx, api_server, redis, judge_workers, postgres

--- GREEDY Placement ---
    nginx                -> GCP    ($12.23/mo)
    api_server           -> GCP    ($48.92/mo)
    redis                -> GCP    ($48.92/mo)
    judge_workers        -> GCP    ($97.83/mo)
    postgres             -> Azure  ($157.44/mo)   <- causes egress!
    TOTAL  Compute=$365.34 + Egress=$18.60 = $383.94/mo

--- TEAP Placement ---
    postgres             -> GCP    ($162.40/mo)   <- moved here!
    TOTAL  Compute=$370.30 + Egress=$1.80 = $372.10/mo

SAVINGS: $11.84/mo (3.1%) = $142.08/year

--- At Higher Traffic (5x) ---
    Greedy: $458.34 | TEAP: $379.30 | Savings: $79.04/mo (17.2%)
    Annual savings at 5x traffic: $948.48/year
```

**When to use:** The most impactful option. Shows your research solving a real problem — YOUR project. Memorize the numbers: $948/year at 5x traffic, 17.2% savings.

---

## CLI Option [7] — Full Benchmark (120 Experiments)

**What it does:** Runs all 120 experiments and shows all results.
**Takes:** ~60 seconds.
**When to use:** Not during a live demo (too slow). Run beforehand to generate fresh results.

---

## CLI Option [8] — Pricing Data Explorer

**What it does:** Browse compute prices for any component type across all providers.
1. Shows all available component types
2. You select one
3. Prints a table: provider, instance name, vCPU, RAM, price/month
4. Highlights the cheapest provider

**When to use:** When explaining Review 1's pricing data or showing that the optimizer knows the actual instance types.

---

# Part 2 — Streamlit Web Dashboard (`streamlit_app.py`)

The Streamlit dashboard is a browser-based interface that mirrors all CLI options but adds:
- Real-time animated charts (not ASCII bars)
- Interactive sliders and dropdowns
- Embedded PNG figures from `results/figures/`
- Colored highlighted tables (green = optimal, red = wasteful)
- Side-by-side layout using Streamlit columns

**Run:** `python -m streamlit run streamlit_app.py`
**URL:** http://localhost:8501

Navigation is via the left sidebar. Click any option to switch pages.

---

## Streamlit Page 1 — Overview & Figures

**URL:** http://localhost:8501 (default landing page)
**Mirrors:** CLI startup screen + README

**Contents:**
1. **Hero section** — Title, tagline, description
2. **4 metric cards** — Key numbers (43.9% savings, 120 experiments, 6 algorithms, $948/year)
3. **Review 1 Baseline Table** — The exact numbers from Review 1 in a styled dataframe
4. **All 6 PNG Charts** — Embedded in a 2-column grid with captions

**Why the figures are shown here:** The overview page is what you show first in a presentation. The reviewer can see all results at a glance without running any code.

---

## Streamlit Page 2 — Algorithm Comparison

**Mirrors:** CLI Option [1]

**Interactive elements:**
- Dropdown: select topology (5 options)
- Slider: traffic multiplier (0.5 to 10.0, step 0.5)
- Button: "▶ Run All Algorithms"

**On click:**
- Progress bar shows which algorithm is running
- Results table with color highlighting (green rows = optimal, red = >10% gap)
- 2-panel bar chart: compute costs and total costs side by side
- Expandable section: full placement decisions for every algorithm

---

## Streamlit Page 3 — Placement Decisions

**Mirrors:** CLI Option [2]

**Layout:** 3 equal columns showing Greedy, TEAP, ILP side by side.

For each algorithm:
- `st.metric` showing total cost with egress as delta
- DataFrame showing component → provider → instance → cost
- Color difference makes it immediately obvious where TEAP differs from Greedy

Also shows the **Traffic Matrix** in an expandable section.

---

## Streamlit Page 4 — Live Parameter Sweep

**Mirrors:** CLI Option [3] — but animated in the browser!

**Flow:**
1. Select topology and max traffic multiplier
2. Click "▶ Run Live Sweep"
3. Progress bar ticks through each multiplier
4. TWO charts update live:
   - Left chart: Greedy vs ILP vs TEAP cost lines (with filled area showing penalty)
   - Right chart: Gap % bar chart (red bars for >15%, orange for >10%, blue for <10%)
5. Table below also updates incrementally showing all results so far
6. After completion: success message showing where 15% threshold was crossed

**Why this is the best demo page:** The animation shows the gap growing in real-time. It's visually compelling and makes the research hypothesis intuitive without any explanation.

---

## Streamlit Page 5 — Ablation Study

**Mirrors:** CLI Option [4]

**Interactive elements:**
- Dropdown: topology
- Slider: traffic multiplier (recommended: 3.5x)
- Button: "▶ Run Ablation Study"

**Output:**
- Results table
- Bar chart: each TEAP variant as a colored bar
- Dashed line showing the TEAP-Full cost as reference
- Success/info message explaining the key finding

---

## Streamlit Page 6 — Egress Rate Matrix

**Mirrors:** CLI Option [5]

**Contents:**
1. Interactive dataframe showing the 3×3 egress rate table with a red gradient (darker = more expensive)
2. The pre-generated heatmap PNG embedded (fig5_egress_heatmap.png)
3. 3 metric cards: GCP=$0.120/GB, AWS=$0.090/GB, Azure=$0.087/GB
4. **Interactive slider:** Set traffic volume (100-2000 GB/month)
5. Dynamic calculation: shows cost for that volume from each provider
6. Success message showing savings of switching from GCP to Azure for that volume

**The slider is the key feature:** Students can drag the slider and immediately see how much money changes. At 1000 GB/month:
- GCP sends: $120/month
- Azure sends: $87/month
- Savings: $33/month (27%)

This makes the insight tangible and interactive.

---

## Streamlit Page 7 — CodeCourt Case Study

**Mirrors:** CLI Option [6]

**Contents:**
1. Architecture table: all 5 CodeCourt components with specs
2. Expandable traffic matrix
3. Button: "▶ Run Greedy vs TEAP Comparison"

**On click:**
- 2-column layout: Greedy placement (left) vs TEAP placement (right)
- st.metric for compute, egress, total (with deltas showing egress penalty/savings)
- Traffic level comparison table (1x, 2x, 3.5x, 5x)
- Embedded fig6_codecourt_case.png
- Success message: $948/year savings highlighted

---

## Streamlit Page 8 — Pricing Explorer

**Mirrors:** CLI Option [8]

**Contents:**
1. Dropdown: select component type (10 options)
2. 3 metric cards: cheapest and most expensive provider highlighted
3. Styled dataframe with all provider prices for that type
4. Bar chart comparing ALL component types across all providers

The bar chart is the unique addition vs the CLI version — you can see at a glance which component types have the largest price differences between providers (those are the ones worth optimizing).

---

## Presentation Order (Recommended)

For a 10-minute review presentation:

| Time | Page/Option | What to say |
|---|---|---|
| 0-1 min | CLI Option [5] or Streamlit Page 6 | "The problem: egress is invisible but expensive. GCP charges $0.12/GB to send data." |
| 1-3 min | Streamlit Page 1 (Overview) | "Here's the full dashboard. Four key numbers. Here are our pre-generated results." |
| 3-5 min | Streamlit Page 7 (CodeCourt) | "This is our actual CodeCourt project. Greedy wastes $79/month at 5x traffic = $948/year." |
| 5-7 min | Streamlit Page 4 (Live Sweep) | "Watch the gap grow as traffic increases. Crosses 15% at 2.5x." |
| 7-9 min | Streamlit Page 2 (Algorithm Comparison) | "All 6 algorithms. TEAP matches the true optimal. Greedy overpays." |
| 9-10 min | Streamlit Page 5 (Ablation) | "Proof that ILP refinement is the critical phase. Removing it causes +31.9% cost." |
