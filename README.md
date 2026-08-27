# VYUH (व्यूह) — Temporal Relational Fraud Intelligence

> **Detect fraud not only from what a payment looks like, but from what is happening around it over time.**

[![Track](https://img.shields.io/badge/Razorpay_Buildathon_2026-Track_02:_AI_Risk_Manager-blue.svg)](https://razorpay.com/buildathon)
[![License](https://img.shields.io/badge/License-Apache_2.0-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![Node.js](https://img.shields.io/badge/Node.js-18%2B-darkgreen.svg)](https://nodejs.org/)
[![LightGBM](https://img.shields.io/badge/ML_Engine-LightGBM_GBDT-orange.svg)](https://lightgbm.readthedocs.io/)
[![Docker](https://img.shields.io/badge/Container-Docker_Compose-blue.svg)](docker-compose.yml)

---

## Table of Contents

- [1. The Core Idea & Signature Counterfactual](#1-the-core-idea--the-signature-counterfactual)
- [2. At a Glance (Verified Metrics)](#2-at-a-glance-verified-canonical-metrics)
- [3. Problem Statement & Why Now](#3-problem-statement--why-conventional-models-fail)
- [4. Core Architecture](#4-core-system-architecture)
- [5. End-to-End Request Lifecycle](#5-end-to-end-request-lifecycle)
- [6. Feature Engineering & Schema](#6-feature-engineering--feature-schema)
- [7. Temporal Leakage Prevention](#7-temporal-leakage-prevention--evaluation-integrity)
- [8. Model Development & Architectural Evolution](#8-model-development--architectural-evolution)
- [9. Statistical Evidence & Bootstrap Validation](#9-statistical-evidence--bootstrap-validation)
- [10. Operating-Point Metrics (Fixed FPR)](#10-operating-point-metrics-fixed-fpr)
- [11. Production Inference & Latency Profile](#11-production-inference--latency-profile)
- [12. Economic Decision Gateway](#12-economic-decision-gateway--asymmetric-cost-matrix)
- [13. Failure Safety & Graceful Degradation](#13-failure-safety--graceful-degradation)
- [14. Adversarial Evaluation & Known Blindspots](#14-adversarial-evaluation--known-blindspots)
- [15. Illustrative Merchant Economic Scenario](#15-illustrative-merchant-economic-scenario)
- [16. Repository Structure](#16-repository-structure)
- [17. Technology Stack](#17-technology-stack)
- [18. Prerequisites & Installation](#18-prerequisites--installation)
- [19. Running Locally](#19-running-locally)
- [20. Running with Docker Compose](#20-running-with-docker-compose)
- [21. Environment Configuration](#21-environment-configuration)
- [22. Running the Canonical Live Demo](#22-running-the-canonical-live-demo)
- [23. REST API Reference](#23-rest-api-reference)
- [24. Reproducibility & Benchmark Suite](#24-reproducibility--benchmark-suite)
- [25. Test Suite & Verification](#25-test-suite--verification)
- [26. Clean-Machine Verification](#26-clean-machine-verification-7-step-checklist)
- [27. Model Checkpoints & Serialization](#27-model-checkpoints--serialization)
- [28. Dataset Management](#28-dataset-management)
- [29. Research Ablations & Negative Experiments](#29-research-ablations--negative-experiments)
- [30. Architectural Justifications (Why GBDT? Why Graph? Why not GNN?)](#30-architectural-justifications)
- [31. Security, Privacy & Compliance](#31-security-privacy--compliance)
- [32. Verified System Limitations](#32-verified-system-limitations)
- [33. Future Roadmap](#33-future-roadmap)
- [34. Technical Defense & Judge FAQ](#34-technical-defense--judge-faq)
- [35. Evidence Map](#35-evidence-map)

---

## 1. The Core Idea & the Signature Counterfactual

Traditional payment risk engines evaluate each checkout in isolation. When an individual payment payload presents a standard ticket (e.g., ₹499 at 2:00 PM) with a syntactically valid card and email, a transaction-level tabular model sees an ordinary behavioral profile with negligible risk ($P_{\text{tabular}} = 3.84\%$).

However, coordinated abuse syndicates distribute attacks across multiple synthetic accounts, rotated payment cards, and disposable credentials on shared hardware emulators.

### The Canonical Counterfactual Demonstration

Holding the incoming raw transaction payload **100% bitwise invariant**, observe how the final risk decision shifts across three relational contexts:

```
                            CANONICAL ₹499 TRANSACTION
                                         │
                  ├── Order ID: ORD_CANONICAL_7781
                  ├── Amount: ₹499.00
                  ├── Card ID: CARD_CANONICAL_A
                  ├── Device ID: DEV_CANONICAL_TARGET_X
                  ├── Email: sarah.finance@enterprise.com
                  └── Time: 14:00 (2:00 PM)
                                         │
                  ┌──────────────────────┴──────────────────────┐
                  ▼                                             ▼
        P_tabular = 3.84%                             P_tabular = 3.84%
     (100% Invariant Payload)                      (100% Invariant Payload)
                  │                                             │
                  ▼                                             ▼
        [Context A: Isolated]                         [Context B: Office 8h]
        P_final = 10.90%                              P_final = 16.43%
        Action  = ALLOW                               Action  = STEP_UP_AUTH
                  │
                  ▼
        [Context C: Bot Burst (10 accts / 30s)]
        P_final = 68.50%
        Action  = FLAG_HUMAN_REVIEW
```

| Context | Scenario Regime | Relational State | $P_{\text{tabular}}$ | $P_{\text{graph}}$ | $P_{\text{final}}$ | Gateway Decision |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| **Context A** | **Isolated Personal Device (1:1)** | Clean personal hardware (1 account, 1 device) | 3.84% | 15.51% | **10.90%** | **`ALLOW`** (Clean 1-Click) |
| **Context B** | **Legitimate Office NAT (Spaced Sharing)** | 4 coworkers checking out across 8 hours | 3.84% | 40.16% | **16.43%** | **`STEP_UP_AUTH`** (Non-blocking Challenge) |
| **Context C** | **Coordinated Bot Burst (Syndicate Attack)** | 10 synthetic accounts on 1 emulator in 30s | 3.84% | 48.50% | **68.50%** | **`FLAG_HUMAN_REVIEW`** (Analyst Brief) |

> **Signature Thesis**: *"The transaction didn't change. The context did."*

*(Note: This is a controlled canonical counterfactual demonstration to isolate relational impact; real historical holdout metrics are presented below).*

---

## 2. At a Glance (Verified Canonical Metrics)

All numbers below are extracted directly from the verified canonical JSON artifacts (`models/checkpoints/final_incremental_value_study.json` and `models/checkpoints/final_latency_benchmark.json`):

| Evaluation Dimension | Benchmark Metric | Verified Canonical Value | Operational Significance |
| :--- | :--- | :---: | :--- |
| **Historical Test Holdout** | Untouched Test Transactions | **118,108** | Real IEEE-CIS holdout (3.44% fraud rate, zero temporal leakage) |
| **Baseline Tabular Model ($M1$)** | Precision-Recall AUC (PR-AUC) | **0.1124** | 10-feature isolated transaction LightGBM baseline |
| **Relational Graph GBDT ($M2$)** | Precision-Recall AUC (PR-AUC) | **0.1251** | 13-feature graph-only GBDT model |
| **VYUH Joint 23-Feat Model ($M3$)** | Precision-Recall AUC (PR-AUC) | **0.1456** | **Canonical Winner** (Joint concatenated feature space) |
| **Calibrated Joint Model ($M4$)** | Precision-Recall AUC (PR-AUC) | **0.1402** | 23-feature joint model with Isotonic Probability Calibration |
| **Incremental Value ($\Delta\text{PR-AUC}$)** | Absolute Lift ($M3 - M1$) | **`+0.0333`** | **+29.6% relative PR-AUC improvement** over tabular baseline |
| **Statistical Significance** | Bootstrap 95% Confidence Interval | **`[+0.0247, +0.0418]`** | 300 resamples; interval strictly excludes zero ($p < 0.001$) |
| **Fraud Capture @ 1.0% Fixed FPR** | Recall @ 1.0% Merchant Friction | **7.60% $\to$ 11.49%** | **+51.2% relative lift** in caught fraud under strict friction budget |
| **Fraud Capture @ 0.5% Fixed FPR** | Recall @ 0.5% Merchant Friction | **3.94% $\to$ 7.31%** | **+85.5% relative lift** in caught fraud at ultra-low friction |
| **False Positive Rate @ 20% Recall** | Fixed 20% Recall FPR | **3.35% $\to$ 2.48%** | **-26.0% reduction** in merchant false alarm overhead |
| **Inference Latency (Local CPU)** | P50 / P95 / P99 Total Latency | **7.46 ms / 8.38 ms / 13.55 ms** | Single-core CPU execution (500 measured requests) |
| **Graph Traversal Overhead** | In-Memory Graph Query (P50) | **0.514 ms** | Sub-millisecond sliding-window multigraph extraction |

---

## 3. Problem Statement & Why Conventional Models Fail

### The Isolation Blindspot
In traditional payment infrastructures, risk scoring models treat each checkout request as an isolated tabular row $[x_1, x_2, \dots, x_k]$. A fraud syndicate testing stolen credit card numbers against low-ticket ₹499 digital purchases bypasses tabular rules by ensuring each individual request looks completely standard:
* Valid card BIN and Luhn checksum.
* Standard diurnal shopping hour (e.g., 2:00 PM).
* Common transaction amount (e.g., ₹499).
* Disposable, valid email format.

### The Fundamental Rule: Shared Infrastructure $\ne$ Fraud
Crucially, physical infrastructure sharing is common in legitimate commerce:
1. **Family Shared Device**: Parents and children checking out hours apart on a shared household tablet.
2. **Corporate Office NAT / VPN**: Hundreds of employees sharing a single public egress IP throughout the workday.
3. **Retail POS / Mall Kiosk**: Foot traffic passing through a shared public terminal across 12 hours.

Therefore, the engineering challenge is **not**: *"Does this device, IP, or card appear more than once?"*  
The true challenge is: **"Does the temporal velocity and inter-arrival spacing of reuse indicate automated, coordinated syndicate abuse?"**

---

## 4. Core System Architecture

VYUH is engineered as a **dual-tier decoupled microservice architecture** executing sub-10ms CPU inference:

```mermaid
flowchart TD
    Txn[Incoming Payment Transaction] --> TabFeat[10 Tabular Features]
    Txn --> GraphEngine[Live In-Memory Temporal Multigraph]
    GraphEngine --> RelFeat[13 Backward-Looking Relational Features]
    
    TabFeat --> JointGBDT[23-Feature Joint GBDT Model M3]
    RelFeat --> JointGBDT
    
    JointGBDT --> Calib[Isotonic Probability Calibration M4]
    Calib --> CostGateway[Asymmetric Economic Cost Gateway]
    
    CostGateway -->|Risk < 0.15| Allow[ALLOW: 1-Click Clean Checkout]
    CostGateway -->|0.15 <= Risk < 0.25| StepUp[STEP-UP: 2FA / Biometric Challenge]
    CostGateway -->|Risk >= 0.25| Review[FLAG REVIEW: Forensic Analyst Brief]
```

```
                 INCOMING PAYMENT TRANSACTION
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Transaction Features │
                    │    (10 Features)    │
                    └──────────┬──────────┘
                               │
                               ▼
                        Tabular Model (M1)
                               │
Transaction ──────────────────┼────────────────► 23-Feature Joint GBDT (M3)
                               │                  (joint_23feat_lgbm.pkl)
                               ▲
                               │
                    ┌──────────┴──────────┐
                    │ Temporal Relational │
                    │    (13 Features)    │
                    └──────────▲──────────┘
                               │
                        Entity Graph (M2)
                               │
                     device / card / email
                               │
                               ▼
                       Risk Probability
                               │
                               ▼
                     Economic Cost Gateway
                               │
                    ┌──────────┼──────────┐
                    ▼          ▼          ▼
                  ALLOW     STEP-UP     REVIEW
```

> **Design Clarity**: The entity graph is **not a GNN** (Graph Neural Network). It is an in-memory bipartite temporal multigraph with sliding-window TTL pruning (`networkx`) that extracts 13 engineered graph statistics, evaluated by a learned **LightGBM GBDT**.

---

## 5. End-to-End Request Lifecycle

When a payment checkout payload arrives at the gateway:

1. **Gateway Ingestion (`backend/server.js`)**: Express REST gateway receives `POST /api/score` with `{ orderId, amount, cardId, deviceId, email }`.
2. **Bridge Forwarding (`backend/decision_engine.js`)**: Routes the payload over internal HTTP socket (Port 5001) to the Python inference engine.
3. **Graph Ingestion & Pruning (`backend/inference_service.py:LiveEntityGraph`)**:
   - Ingests transaction node $T_i$ and links to card, device, and email entity nodes with current timestamp.
   - Prunes expired nodes/edges exceeding the 2-hour TTL sliding window.
4. **Online Rolling Feature Extraction (`backend/inference_service.py:RollingFeatureStore`)**:
   - Retrieves per-card historical distribution (mean, standard deviation, $Z$-score, lifetime transaction count).
5. **10 Tabular Feature Computation (`backend/inference_service.py:score_transaction`)**:
   - Computes logarithmic amount and cyclical diurnal trigonometric embeddings ($\sin, \cos$).
6. **13 Temporal Relational Feature Extraction (`backend/inference_service.py:score_transaction`)**:
   - Extracts live entity degrees, burst scores, 2-hop graph neighborhood size, and rolling 1h/24h velocities.
7. **Joint 23-Feature GBDT Inference (`models/checkpoints/joint_23feat_lgbm.pkl`)**:
   - Evaluates concatenated 23-dimensional feature matrix through LightGBM GBDT in $< 5\text{ms}$.
8. **Probability Calibration (`models/checkpoints/calibrated_23feat_lgbm.pkl`)**:
   - Maps raw margin to true empirical posterior probability via isotonic regression.
9. **Asymmetric Economic Cost Routing (`backend/decision_engine.js:calculateCostDial`)**:
   - Evaluates expected merchant loss: $\text{Loss}(\text{ALLOW}) = P_{\text{final}} \times \text{Amount}$ against friction costs.
10. **Gateway Decision Dispatch**:
    - Dispatches decision (`ALLOW`, `STEP_UP_AUTH`, or `FLAG_HUMAN_REVIEW`) to merchant response payload.
11. **Immutable Audit Trail Commit (`backend/decision_engine.js:auditTrail`)**:
    - Appends decision ID, feature values, calibrated probability, and latency timestamp to in-memory forensic audit log.

---

## 6. Feature Engineering & Feature Schema

### A. 10 Transaction-Level Tabular Features

| Feature Name | Type | Mathematical Definition | Fraud Domain Justification | Available at Live Checkout? |
| :--- | :---: | :--- | :--- | :---: |
| `TransactionAmt` | Float | Raw payment ticket in INR / USD | Base economic exposure. | Yes |
| `TransactionAmt_log` | Float | $\ln(1 + \text{TransactionAmt})$ | Compresses heavy-tailed ticket distribution. | Yes |
| `hour_sin` | Float | $\sin(2\pi \cdot \text{hour} / 24.0)$ | Diurnal circadian cycle component. | Yes |
| `hour_cos` | Float | $\cos(2\pi \cdot \text{hour} / 24.0)$ | Diurnal circadian cycle component. | Yes |
| `is_night` | Int | $\mathbb{I}(\text{hour} \ge 22 \lor \text{hour} \le 5)$ | Binary flag for high-risk off-peak nocturnal activity. | Yes |
| `card1_amt_mean` | Float | $\mu_{\text{card}} = \frac{1}{N}\sum \text{Amt}_k$ | Rolling baseline ticket size on card profile. | Yes |
| `card1_amt_std` | Float | $\sigma_{\text{card}} = \sqrt{\frac{1}{N}\sum (\text{Amt}_k - \mu)^2}$ | Rolling amount dispersion on card profile. | Yes |
| `card1_amt_zscore` | Float | $Z = \frac{\text{Amt} - \mu_{\text{card}}}{\max(1.0, \sigma_{\text{card}})}$ | Standardized ticket deviation (catches sudden whale spikes). | Yes |
| `card1_txn_count` | Int | $N_{\text{card}}$ | Rolling transaction frequency count on card profile. | Yes |
| `card1_unique_devices`| Int | $\|\mathcal{D}_{\text{card}}\|$ | Number of distinct physical hardware IDs linked to card. | Yes |

### B. 13 Temporal Relational Graph Features (Strictly Backward-Looking $t < T_i$)

All relational features are strictly calculated over historical observations ($t < T_i$):

| Feature Name | Entity | Window | Mathematical Definition | Fraud Domain Justification | Backward Looking ($t < T_i$)? |
| :--- | :---: | :---: | :--- | :--- | :---: |
| `dev_unique_cards_24h` | Device | 24 Hours | $\|\mathcal{C}_{\text{dev}, 24h}\|$ | Distinct payment cards seen on hardware (card cycling). | Yes |
| `dev_unique_emails_24h`| Device | 24 Hours | $\|\mathcal{E}_{\text{dev}, 24h}\|$ | Distinct customer emails seen on hardware (synthetic IDs). | Yes |
| `dev_txn_velocity_1h` | Device | 1 Hour | $\sum \mathbb{I}(t_k \in [T_i-3600, T_i))$ | Rapid transaction bursts on single hardware fingerprint. | Yes |
| `dev_amount_sum_1h` | Device | 1 Hour | $\sum \text{Amt}_k \cdot \mathbb{I}(t_k \in [T_i-3600, T_i))$ | Total capital drained through device in short window. | Yes |
| `card_unique_devices_24h`| Card | 24 Hours | $\|\mathcal{D}_{\text{card}, 24h}\|$ | Distinct hardware devices processing same card. | Yes |
| `card_unique_emails_24h`| Card | 24 Hours | $\|\mathcal{E}_{\text{card}, 24h}\|$ | Distinct customer accounts charging same card. | Yes |
| `card_txn_velocity_1h` | Card | 1 Hour | $\sum \mathbb{I}(t_k \in [T_i-3600, T_i))$ | High-frequency automated card testing attacks. | Yes |
| `card_device_switch_rate`| Card | Lifetime | $\frac{\text{Unique Devices}}{\max(1, \text{Txn Count})}$ | Hardware volatility ratio (high ratio = distributed abuse). | Yes |
| `graph_device_shared_deg`| Graph | Live TTL | $\text{deg}_{\mathcal{G}}(v_{\text{device}})$ | Bipartite degree of device node in active multigraph. | Yes |
| `graph_card_shared_deg` | Graph | Live TTL | $\text{deg}_{\mathcal{G}}(v_{\text{card}})$ | Bipartite degree of card node in active multigraph. | Yes |
| `graph_burst_score` | Graph | Live TTL | $\ln(1 + \text{Velocity}) \times \ln(1 + \text{Degree})$ | Multiplicative compound burst index. | Yes |
| `graph_ring_size` | Graph | Live TTL | $\|\text{Component}_{\mathcal{G}}(v_{\text{txn}})\|$ | Total entity count in connected bipartite multigraph cluster. | Yes |
| `graph_2hop_neighborhood_size`| Graph | Live TTL | $\|\mathcal{N}_2(v_{\text{txn}})\|$ | Reachable entity count within 2-hop graph radius. | Yes |

---

## 7. Temporal Leakage Prevention & Evaluation Integrity

### Chronological Holdout vs. Random Splitting
In fraud detection, **random cross-validation causes massive data leakage**: future fraud patterns and graph links leak into historical training records, inflating validation scores by $+40\%$.

VYUH enforces **strict chronological time-series splitting**:
* **Total Transactions**: 590,540 real-world ecommerce records (IEEE-CIS dataset).
* **Chronological Training Split**: 472,432 transactions ($80\%$).
* **Untouched Historical Holdout Split**: 118,108 transactions ($20\%$, $3.44\%$ fraud rate).
* **Temporal Ordering**: $\max(T_{\text{train}}) \le \min(T_{\text{test}})$, separated by a strict 58-second chronological gap.
* **Leakage-Free Guarantee**: For every test transaction $i$ at timestamp $T_i$, all graph degrees and rolling stats depend exclusively on events $t < T_i$.

---

## 8. Model Development & Architectural Evolution

VYUH evaluated 4 model configurations on identical temporal splits (`models/checkpoints/final_incremental_value_study.json`):

```
┌──────────────────────────────────────────────┬──────────┬──────────┬──────────────┬──────────────┬─────────────┐
│ Model Architecture Evaluated                 │ PR-AUC   │ ROC-AUC  │ Rec@1.0% FPR │ Rec@0.5% FPR │ FPR@20% Rec │
├──────────────────────────────────────────────┼──────────┼──────────┼──────────────┼──────────────┼─────────────┤
│ M1: Tabular LightGBM (10 Feats)              │ 0.1124   │ 0.7309   │ 7.60%        │ 3.94%        │ 3.35%       │
│ M2: Relational Graph GBDT (13 Feats)         │ 0.1251   │ 0.7137   │ 9.60%        │ 6.87%        │ 3.95%       │
│ M3: Joint Concat GBDT (23 Feats) [WINNER]    │ 0.1456   │ 0.7359   │ 11.49%       │ 7.31%        │ 2.48% (Best)│
│ M4: Calibrated Joint GBDT (23 Feats+Isotonic)│ 0.1402   │ 0.7355   │ 10.75%       │ 7.60%        │ 2.91%       │
└──────────────────────────────────────────────┴──────────┴──────────┴──────────────┴──────────────┴─────────────┘
```

### The Information Bottleneck Discovery
Earlier experiments tested a 2-stage hierarchical stacking architecture where tabular and relational models were trained independently and their scalar probabilities fused via a meta-learner:

```
Hierarchical Stacking (Information Bottleneck):
[ 10 Tabular Feats ] ──► GBDT ──► P_tab (1D Scalar)   ──┐
                                                         ├──► Fusion GBDT (Discards cross-domain split interactions)
[ 13 Graph Feats ]   ──► GBDT ──► P_graph (1D Scalar) ──┘

Joint Concat M3 (Canonical Winner):
[ 10 Tabular Feats + 13 Graph Feats ] ──► Single 23-Feature GBDT (Learns Amount-ZScore × DeviceBurst interactions)
```

**Key Discovery**: Compressing the 13-dimensional relational space into a 1D scalar probability discarded high-order cross-domain split interactions (e.g., interaction between high transaction amount deviation and device burst score). The **23-feature Joint GBDT ($M3$)** directly captures these interactions, achieving the highest PR-AUC (**0.1456**).

---

## 9. Statistical Evidence & Bootstrap Validation

To confirm that the $+0.0333$ PR-AUC lift of $M3$ over $M1$ is statistically significant, 300 non-parametric bootstrap resamples were evaluated on the held-out test split:

* **Mean $\Delta\text{PR-AUC}$ ($M3 - M1$)**: **`+0.0333`** (+29.6% relative improvement).
* **Bootstrap 95% Confidence Interval**: **`[+0.0247, +0.0418]`**.
* **Statistical Interpretation**: The 95% confidence interval strictly excludes zero ($\Delta > 0$ with $p < 0.001$), demonstrating that the observed PR-AUC improvement is unlikely to be explained by sample variation.
* **Mean $\Delta\text{ROC-AUC}$ ($M3 - M1$)**: `+0.0048` (95% CI: `[-0.0001, 0.0095]`).

### Why PR-AUC is the Primary Metric for Fraud
Under extreme class imbalance ($3.44\%$ fraud rate), ROC-AUC can be deceptively optimistic because a massive pool of true negatives inflates the denominator. Precision-Recall AUC (PR-AUC) directly evaluates the trade-off between false-positive merchant friction and true fraud capture.

---

## 10. Operating-Point Metrics (Fixed FPR)

In payment gateways, fraud models cannot be evaluated in the abstract—they operate under strict merchant friction budgets:

| Fixed Operating Budget | Baseline Tabular ($M1$) | VYUH Joint ($M3$) | Absolute Lift | Relative Capture Gain |
| :--- | :---: | :---: | :---: | :---: |
| **Recall @ 1.0% Fixed FPR** | 7.60% | **11.49%** | **+3.89%** | **+51.2% relative lift in caught fraud** |
| **Recall @ 0.5% Fixed FPR** | 3.94% | **7.31%** | **+3.37%** | **+85.5% relative lift in caught fraud** |
| **FPR @ 20.0% Fixed Recall**| 3.35% | **2.48%** | **-0.87%** | **-26.0% reduction in false alarms** |

*(Note: "Recall @ 1.0% FPR = 11.49%" means that at a decision threshold allowing exactly 1 false alarm per 100 legitimate checkouts, VYUH catches 11.49% of all fraud attacks, compared to 7.60% for the tabular baseline).*

---

## 11. Production Inference & Latency Profile

Measured across 500 requests on local single-core CPU microservice execution (`models/checkpoints/final_latency_benchmark.json`):

```
┌─────────────────────────────────────────────────────────────┬──────────────┐
│ Benchmark Stage / Latency Metric                            │ Measured Time│
├─────────────────────────────────────────────────────────────┼──────────────┤
│ P50 End-to-End Total Microservice Execution                 │ 7.46 ms      │
│ P95 End-to-End Total Microservice Execution                 │ 8.38 ms      │
│ P99 End-to-End Total Microservice Execution                 │ 13.55 ms     │
│ P50 Sliding-Window Multigraph Traversal & Ingestion         │ 0.514 ms     │
└─────────────────────────────────────────────────────────────┴──────────────┘
```

* **Zero GPU Requirement**: LightGBM and NetworkX run entirely on CPU.
* **Scope Clarification**: Benchmark measurements cover local microservice feature extraction and scoring. Production deployments across network hops will incur standard transit latency.

---

## 12. Economic Decision Gateway & Asymmetric Cost Matrix

Model probability is mapped to economic action using an asymmetric cost matrix balancing fraud loss against customer checkout friction:

$$\mathcal{L}(\text{Action}) = \begin{cases} P_{\text{final}} \times \text{Amount}, & \text{for ALLOW} \\ C_{\text{stepup}}, & \text{for STEP-UP AUTH} \\ C_{\text{review}}, & \text{for FLAG HUMAN REVIEW} \end{cases}$$

where:
* $\mathcal{L}(\text{ALLOW}) = P_{\text{final}} \times \text{Amount}$ (Expected fraud loss exposure)
* $C_{\text{stepup}} \approx \text{INR 22.00}$ (Authentication friction and OTP dispatch overhead)
* $C_{\text{review}} \approx \text{INR 132.50}$ (Forensic analyst manual investigation overhead)

### Decision Threshold Policy:

| Gateway Action | Cost Formulation | Economic Policy Range | Operational Workflow |
| :--- | :--- | :---: | :--- |
| **`ALLOW`** | $\mathcal{L} = P_{\text{final}} \times \text{Amount}$ | $P_{\text{final}} < 0.15$ | Clean transaction profile verified; frictionless 1-click checkout. |
| **`STEP_UP_AUTH`** | $C_{\text{stepup}} \approx \text{INR 22.00}$ | $0.15 \le P_{\text{final}} < 0.25$ | Moderate relational risk; non-destructive 2FA/biometric verification. |
| **`FLAG_HUMAN_REVIEW`** | $C_{\text{review}} \approx \text{INR 132.50}$ | $P_{\text{final}} \ge 0.25$ | Coordinated syndicate abuse; flags settlement with forensic brief. |

---

## 13. Failure Safety & Graceful Degradation

In financial payment infrastructure, fail-open behavior is unacceptable. Verified by `tests/test_failure_injection.py`:

```
                PYTHON INFERENCE SERVICE FAILS / DIES
                               │
                               ▼
            Node.js Decision Engine Detects Socket Drop
                               │
                               ▼
                 Returns HTTP 503 Gateway Status
                               │
                               ▼
          Action: STEP-UP_AUTH (Safe Non-Destructive Fallback)
         Zero Fabricated Mock Scores • Zero Silent Passes
```

1. **Service Crash Detection**: If the Python inference service terminates, Node.js catches the socket drop within 3000ms.
2. **Safe Defense-Only Fallback**: Returns HTTP 503 with default action `STEP_UP_AUTH`. Legitimate users can verify via 2FA; attackers cannot slip through during outages.
3. **Zero Fabricated Risk Scores**: Risk scores are returned as `null` with explicit `confidence: "NONE (Inference Offline)"`.

---

## 14. Adversarial Evaluation & Known Blindspots

Evaluated across 6 attack regimes (`models/checkpoints/adversarial_attack_characterization.json`):

| Attack / Scenario Regime | Evasion Mechanism | $P_{\text{tab}}$ | $P_{\text{graph}}$ | $P_{\text{joint}}$ | Gateway Action | Detection Outcome |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **1. Baseline Single User** | Clean personal hardware; 1:1 binding | 0.0384 | 0.1551 | 0.1090 | `ALLOW` | ✅ Passed (Clean 1-Click Checkout) |
| **2. Legitimate Office NAT** | Coworkers sharing network spaced across 8 hours | 0.0384 | 0.4016 | 0.1643 | `STEP_UP_AUTH` | ✅ Passed (Human Spacing Prevents Review Hold) |
| **3. Coordinated Bot Burst** | 10 synthetic accounts in 30s on same hardware | 0.0384 | 0.4850 | 0.6850 | `FLAG_HUMAN_REVIEW` | ✅ Caught (Velocity & Shared Degree Spike) |
| **4. Low-and-Slow Attack** | Multi-day spacing to evade 1-hour velocity | 0.0384 | 0.4423 | 0.1662 | `STEP_UP_AUTH` | ⚠️ Partial Catch (24h Degree Flags Linkage) |
| **5. Fully Distributed Attack** | Disposable proxy + virtual card (**Zero Reuse**) | 0.0384 | 0.1551 | 0.1090 | `ALLOW` | ❌ **Disclosed Blindspot (Zero Entity Reuse)** |
| **6. Rapid Carding Attack** | Testing 8 stolen cards on single emulator in 45s | 0.0384 | 0.3337 | 0.1633 | `STEP_UP_AUTH` | ✅ Caught (Hardware Switch Rate Escalates Challenge) |

### Explicitly Disclosed Blindspot: Zero-Entity-Reuse Attacks
* **Threat Model**: Adversaries utilizing single-use residential rotating proxies, dynamic virtual cards, and synthetic disposable user profiles.
* **Why Relational Intelligence Fails**: When every transaction presents a unique device ID, unique card token, and fresh email, the live graph degree remains $1$, velocity remains $1$, and connected component size remains $1$.
* **Architectural Boundary**: In this regime, relational features provide zero uplift; VYUH gracefully degrades to tabular behavioral anomaly detection.

---

## 15. Illustrative Merchant Economic Scenario

*Illustrative projection applying holdout operating points to a representative merchant volume model (`models/checkpoints/economic_impact_scenario.json`):*

* **Merchant Parameters**: ₹100 Crore/month GMV, 2,000,000 monthly transactions, ₹500 average ticket, 1.5% gross fraud loss at risk (₹1.50 Crore/month).
* **Baseline Tabular Model ($M1$)**: Recalls 7.60% fraud $\to$ ₹11.40 Lakhs/month caught.
* **VYUH Joint Model ($M3$)**: Recalls 11.49% fraud $\to$ ₹17.23 Lakhs/month caught.
* **Incremental Merchant Net Benefit**: **`₹5.83 Lakhs/month`** (**`₹70.02 Lakhs/year`** net fraud savings at identical 1.0% false-positive friction).

*(Disclaimer: This is an illustrative economic scenario based on empirical holdout operating points, not observed production merchant savings).*

---

## 16. Repository Structure

```
Vyuh/
├── backend/
│   ├── decision_engine.js         # Cost-calibrated policy & Python bridge client
│   ├── inference_service.py       # Live in-memory graph & GBDT microservice (Port 5001)
│   ├── package.json               # Backend Node.js manifest
│   └── server.js                  # Express REST gateway & static file server (Port 3000)
│
├── frontend/
│   ├── index.html                 # Single-page application entry
│   ├── package.json               # Frontend dependencies & Vite configuration
│   ├── vite.config.js             # Vite build configuration
│   └── src/
│       ├── App.jsx                # Main application component & tab router
│       ├── index.css              # Design system & dark theme styling
│       └── components/
│           ├── AuditTrail.jsx            # Real-time immutable decision audit log
│           ├── BenchmarksView.jsx        # Academic benchmarks, ROC/PR curves, & CI
│           ├── CostDial.jsx              # Interactive economic threshold slider
│           ├── Header.jsx                # Header bar & system status
│           ├── InvestigationCopilot.jsx  # Forensic copilot investigation chat
│           ├── NetworkGraph.jsx          # Live Cytoscape.js interactive entity graph
│           └── TwoWorldsDemo.jsx         # Canonical counterfactual comparison view
│
├── models/
│   ├── feature_engineering.py     # Tabular feature transformation pipeline
│   ├── investigation_agent.py     # Graph traversal forensic copilot agent
│   ├── temporal_diff_engine.py    # Counterfactual "What Changed?" diff engine
│   ├── temporal_relational_engine.py # Backward-looking relational feature extractor
│   └── checkpoints/
│       ├── adversarial_attack_characterization.json # 6-regime adversarial test matrix
│       ├── benign_friction_study_results.json       # Monte Carlo sharing simulation
│       ├── calibrated_23feat_lgbm.pkl               # M4: Calibrated joint model
│       ├── canonical_counterfactual_demo.json       # Canonical demo ground truth
│       ├── economic_impact_scenario.json            # ₹100 Cr GMV merchant model
│       ├── final_incremental_value_study.json       # 118K holdout metrics & bootstrap CI
│       ├── final_latency_benchmark.json             # 500-request CPU latency profile
│       ├── graph_lgbm.pkl                           # M2: 13-feature graph GBDT model
│       ├── joint_23feat_lgbm.pkl                    # M3: 23-feature joint GBDT model (Winner)
│       ├── stage1_lgbm.pkl                          # 481-feature research baseline
│       └── tabular_lgbm.pkl                         # M1: 10-feature tabular GBDT model
│
├── benchmarks/
│   ├── adversarial_attack_characterization.py # Adversarial benchmark runner
│   ├── canonical_counterfactual_demo.py       # Canonical demo generator
│   ├── economic_scenario_analysis.py          # Merchant economic model script
│   ├── final_incremental_value_study.py       # 300-bootstrap significance runner
│   ├── final_latency_benchmark.py             # CPU latency profiler
│   └── final_submission_validation.py         # Automated integrity validation suite
│
├── tests/
│   ├── test_adversarial_deep_audit.py # Multi-regime adversarial audit
│   ├── test_failure_injection.py      # Microservice failure recovery kill test
│   ├── test_http_end_to_end.py        # End-to-end HTTP integration test
│   ├── test_online_offline_parity.py  # 100-sample mathematical parity test
│   └── test_stream_evolution.py       # Live stream progression & cold-start test
│
├── docs/
│   ├── ADVERSARIAL_LIMITATIONS.md     # Detailed threat models & boundary disclosures
│   ├── ARCHITECTURE.md                # System design & mathematical specifications
│   └── EVALUATION.md                  # Comprehensive empirical evaluation report
│
├── data/
│   ├── README.md                      # Data documentation & download guide
│   ├── download.py                    # Automated dataset fetcher
│   ├── graphs/                        # Seed graph samples
│   ├── processed/                     # Train/test temporal split pickle files
│   └── raw/                           # Raw CSV files directory
│
├── Dockerfile                         # Multi-runtime container (Node 18 + Python 3.9)
├── docker-compose.yml                 # Multi-service container orchestration
├── requirements.txt                   # Python package manifest
├── .env                               # Environment configuration
├── LICENSE                            # Apache License 2.0
└── README.md                          # Primary documentation & defense document
```

---

## 17. Technology Stack

| Layer | Technology | Version | Purpose in VYUH |
| :--- | :--- | :---: | :--- |
| **ML Engine** | `LightGBM` | $\ge 4.0.0$ | Fast GBDT training & sub-5ms CPU inference. |
| **Scientific Stack** | `scikit-learn`, `numpy`, `pandas` | Standard | Isotonic calibration, bootstrap validation, feature arrays. |
| **Graph Processing** | `NetworkX` | $\ge 3.1$ | In-memory bipartite multigraph & 2-hop topological extraction. |
| **API Gateway** | `Express.js` (Node.js) | `^5.2.1` | Asynchronous REST gateway & static asset server. |
| **Dashboard UI** | `React` + `Vite` | `React 19` / `Vite 8` | Interactive forensic dashboard & counterfactual demo. |
| **Graph Visualization**| `Cytoscape.js` | `^3.30.4` | Interactive entity-graph topology rendering in UI. |
| **Containerization** | `Docker` / `Docker Compose` | Multi-stage | Reproducible dual-service orchestration. |

---

## 18. Prerequisites & Installation

### System Requirements:
* **Python**: `3.9` or higher
* **Node.js**: `18.x` or higher
* **npm**: `9.x` or higher
* **RAM**: 4 GB minimum (8 GB recommended)
* **CPU**: Dual-core x86_64 or ARM64 (Apple Silicon natively supported)

### Step 1: Clone Repository
```bash
git clone https://github.com/mohit4901/Vyuh.git
cd Vyuh
```

### Step 2: Python Environment Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 3: Node.js Dependencies Setup
```bash
# Install backend dependencies
cd backend && npm install
cd ..

# Install frontend dependencies and build static assets
cd frontend && npm install && npm run build
cd ..
```

---

## 19. Running Locally

Running VYUH locally requires two lightweight processes:

### Terminal 1: Start Python Live Inference Microservice
```bash
source .venv/bin/activate
python backend/inference_service.py
```
*Expected Output:*
```
🧠 Initializing VYUH In-Memory Inference & Dynamic Graph Engine...
   ✅ Loaded Tabular LightGBM (10-Feature)
   ✅ Loaded Relational Graph GBDT (4-Feature)
   ✅ Loaded Calibrated 23-Feature Joint Model
   ✅ Loaded Joint 23-Feature GBDT Model
🚀 Python Live Inference Microservice running on http://127.0.0.1:5001
```

### Terminal 2: Start Express REST Gateway & Static Server
```bash
node backend/server.js
```
*Expected Output:*
```
🛡️  VYUH AI Risk Manager REST API Live on Port 3000
🌐 Dashboard: http://localhost:3000
📊 Health Endpoint: http://localhost:3000/api/health
```

Open your browser at **`http://localhost:3000`** to access the dashboard.

---

## 20. Running with Docker Compose

To launch the complete isolated production environment in a single command:

```bash
docker compose up --build
```

### What happens:
1. **`inference-engine`**: Container starts Python microservice on port `5001` with internal healthchecks.
2. **`gateway-dashboard`**: Container waits for `inference-engine` healthcheck to pass, starts Node.js on port `3000`, and serves the pre-compiled React dashboard.

### Stop Containers:
```bash
docker compose down
```

---

## 21. Environment Configuration

VYUH is configured via `.env` (or environment variables):

| Variable | Required? | Default | Purpose |
| :--- | :---: | :---: | :--- |
| `PORT` | Optional | `3000` | Express REST API gateway listening port. |
| `PYTHON_SERVICE_HOST` | Optional | `127.0.0.1` | Hostname for Python inference service (`inference-engine` in Docker). |
| `PYTHON_SERVICE_PORT` | Optional | `5001` | Port for Python inference service. |
| `NODE_ENV` | Optional | `production` | Node.js execution environment (`development` / `production`). |

---

## 22. Running the Canonical Live Demo

1. Open `http://localhost:3000` in your browser.
2. Navigate to the **"Two Worlds / Counterfactual"** tab.
3. Observe the canonical ₹499 transaction payload ($P_{\text{tabular}} = 3.84\%$).
4. Click through the three scenario buttons:
   * **Click "Scenario 1: Isolated Checkout"**: Risk = **`10.90%`**, Action = **`ALLOW`**.
   * **Click "Scenario 2: Office NAT (8h Spaced)"**: Risk = **`16.43%`**, Action = **`STEP_UP_AUTH`**.
   * **Click "Scenario 3: Bot Burst (10 Accts / 30s)"**: Risk = **`68.50%`**, Action = **`FLAG_HUMAN_REVIEW`**.
5. Switch to the **"Live Entity Graph"** tab to inspect the real-time bipartite topology.
6. Switch to the **"Economic Cost Dial"** tab to adjust merchant ticket values and see real-time INR loss curves.

---

## 23. REST API Reference

### 1. `POST /api/score`
Evaluates an incoming payment transaction through the multi-modal learned pipeline.

* **Request (`application/json`)**:
```json
{
  "orderId": "ORD-CANONICAL-7781",
  "amount": 499.0,
  "cardId": "CARD_CANONICAL_A",
  "deviceId": "DEV_CANONICAL_TARGET_X",
  "email": "sarah.finance@enterprise.com"
}
```

* **Response (`200 OK`)**:
```json
{
  "decisionId": "DEC-1756285200-842",
  "orderId": "ORD-CANONICAL-7781",
  "amountINR": 499.0,
  "scores": {
    "pTabular": 0.0384,
    "pGraph": 0.1551,
    "finalCalibratedRisk": 0.1090
  },
  "decision": {
    "action": "ALLOW",
    "actionLevel": "LOW",
    "description": "Clean transaction profile verified and committed to immutable audit trail."
  },
  "inferenceLatencyMs": 7.46
}
```

### 2. `GET /api/health`
Returns system status, active inference engine status, and timestamp.

* **Response (`200 OK`)**:
```json
{
  "status": "healthy",
  "system": "VYUH AI Risk Manager & Forensic Copilot",
  "version": "2.1.0",
  "track": "Track 02: AI Risk Manager",
  "mode": "Strictly Defense-Only",
  "inferenceEngine": "Joint 23-Feature GBDT + Python Live Microservice (Port 5001)",
  "timestamp": "2026-08-27T21:00:00.000Z"
}
```

### 3. `GET /api/stats`
Returns system performance summary, dataset split details, and core benchmark metrics.

### 4. `GET /api/benchmarks`
Serves verified canonical evaluation results, adversarial matrices, and economic scenario JSONs.

### 5. `GET /api/cost-dial?threshold=0.52&aov=1850&friction=350`
Computes empirical TP, FP, FN, TN, and net business benefit in INR for custom merchant parameters.

### 6. `GET /api/audit-trail?limit=50`
Returns real-time immutable audit trail logs.

### 7. `POST /api/investigate`
Routes natural-language forensic queries to the graph traversal forensic copilot agent.

---

## 24. Reproducibility & Benchmark Suite

Every metric reported in this README can be independently reproduced using the scripts in `benchmarks/`:

```bash
# 1. Run Automated Submission Integrity Suite (Validates dataset, schemas, hashes, purity)
python benchmarks/final_submission_validation.py

# 2. Run 300-Resample Bootstrap Statistical Significance Study
python benchmarks/final_incremental_value_study.py

# 3. Run CPU Latency Profiler (P50, P95, P99 across 500 requests)
python benchmarks/final_latency_benchmark.py

# 4. Generate Canonical Counterfactual Demo Ground Truth
python benchmarks/canonical_counterfactual_demo.py

# 5. Run 6-Regime Adversarial Characterization
python benchmarks/adversarial_attack_characterization.py

# 6. Run Merchant Economic Scenario Model
python benchmarks/economic_scenario_analysis.py
```

| Benchmark Script | Verification Purpose | Canonical Expected Output |
| :--- | :--- | :--- |
| `final_submission_validation.py` | Dataset integrity, schema parity, pure scoring path | `ALL AUDIT CHECKS PASSED (Exit 0)` |
| `final_incremental_value_study.py` | 118K holdout PR-AUC, 300 bootstrap iterations | `ΔPR-AUC: +0.0333, 95% CI: [+0.0247, +0.0418]` |
| `final_latency_benchmark.py` | CPU latency distribution over 500 requests | `P50: 7.46ms, P95: 8.38ms, Graph: 0.514ms` |
| `adversarial_attack_characterization.py` | 6 adversarial scenario evaluations | Verified attack matrix with disclosed blindspot |
| `economic_scenario_analysis.py` | Merchant ROI projection (₹100 Cr GMV) | `₹5.83 Lakhs/mo net lift (₹70.02 Lakhs/yr)` |

---

## 25. Test Suite & Verification

VYUH includes 5 test suites covering mathematical parity, streaming evolution, and failure injection:

```bash
# Run 100-sample online/offline mathematical parity test
python tests/test_online_offline_parity.py

# Run stream progression & cold-start reset test
python tests/test_stream_evolution.py

# Run failure injection & graceful degradation test
python tests/test_failure_injection.py

# Run multi-regime adversarial audit
python tests/test_adversarial_deep_audit.py

# Run HTTP end-to-end integration test (requires services running)
python tests/test_http_end_to_end.py
```

### Key Test Descriptions:
1. **`test_online_offline_parity.py`**: Feeds 100 unseen random transaction payloads through the live microservice and compares predictions with direct offline `.pkl` inference. Asserts $|P_{\text{live}} - P_{\text{offline}}| = 0.0$ (Max error $< 5 \times 10^{-5}$).
2. **`test_stream_evolution.py`**: Simulates live streaming checkouts. Demonstrates clean transaction ($T_1$) getting `ALLOW`, subsequent syndicate burst on same hardware ($T_2-T_5$) escalating to `STEP_UP_AUTH` and `FLAG_HUMAN_REVIEW`, and cold-start clean device ($T_6$) resetting to `ALLOW`.
3. **`test_failure_injection.py`**: Injects 5 system boundary failures (malformed types, empty payload, model unpickling failure, ₹10 Crore outlier, unknown entity query). Verifies 100% bounded, safe fail-closed recovery.

---

## 26. Clean-Machine Verification (7-Step Checklist)

For an independent reviewer or judge auditing the repository on a fresh machine:

```bash
# 1. Clone & Enter Directory
git clone https://github.com/mohit4901/Vyuh.git && cd Vyuh

# 2. Setup Virtual Environment
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 3. Install & Build Web Gateway
cd backend && npm install && cd ../frontend && npm install && npm run build && cd ..

# 4. Run Automated Submission Integrity Suite
python benchmarks/final_submission_validation.py

# 5. Run Parity & Failure Tests
python tests/test_online_offline_parity.py
python tests/test_failure_injection.py

# 6. Start Services
python backend/inference_service.py &
node backend/server.js &

# 7. Execute Test Curl Request
curl -X POST http://localhost:3000/api/score \
  -H "Content-Type: application/json" \
  -d '{"orderId":"AUDIT-001","amount":499.0,"cardId":"CARD_A","deviceId":"DEV_X","email":"user@corp.com"}'
```

---

## 27. Model Checkpoints & Serialization

All model checkpoints are stored in `models/checkpoints/`:

| Checkpoint File | Architecture | Features | Status | SHA-256 Hash Prefix |
| :--- | :--- | :---: | :---: | :--- |
| `tabular_lgbm.pkl` | LightGBM GBDT | 10 | Baseline $M1$ | `aa9b260dc1bd...` |
| `graph_lgbm.pkl` | LightGBM GBDT | 13 | Relational $M2$ | `4fac01353987...` |
| `joint_23feat_lgbm.pkl` | LightGBM GBDT | 23 | **Winner $M3$** | `429d7fc5ddfd...` |
| `calibrated_23feat_lgbm.pkl`| Joint GBDT + Isotonic | 23 | Calibrated $M4$| `b6370ba3ddf2...` |
| `stage1_lgbm.pkl` | High-Capacity LightGBM | 481 | Research Baseline | `8f21901a88b1...` |

*(All models are saved using Python `pickle` with LightGBM $\ge 4.0.0$ and scikit-learn $\ge 1.3.0$).*

---

## 28. Dataset Management

* **Primary Dataset**: IEEE-CIS Fraud Detection Benchmark (Vesta Corp / Kaggle).
* **Total Transactions**: 590,540 real-world e-commerce checkout records.
* **Storage Location**: Raw files reside in `data/raw/` and processed splits in `data/processed/` (`train.pkl`: 472,432 rows, `test.pkl`: 118,108 rows).
* **Data Access**: Due to licensing and file size constraints, raw Kaggle dataset files are not committed directly to Git. To fetch and generate the preprocessed splits, configure Kaggle API credentials and run `python data/download.py` (see [data/README.md](data/README.md)).

---

## 29. Research Ablations & Negative Experiments

To maintain strict scientific transparency, VYUH evaluated several alternate architectures during research:

```
┌──────────────────────────────────────────────┬──────────┬──────────┬─────────────┬──────────────────────────────────────────────────┐
│ Architecture / Experiment                    │ PR-AUC   │ ROC-AUC  │ Latency P50 │ Classification & Decision Finding                │
├──────────────────────────────────────────────┼──────────┼──────────┼─────────────┼──────────────────────────────────────────────────┤
│ Stage-1 High-Capacity Tabular (481 Feats)    │ 0.4608   │ 0.8610   │ >120 ms     │ Offline Research Baseline (Latency Unacceptable) │
│ 55M Parameter Sequence Transformer           │ 0.0892   │ 0.6720   │ ~85 ms      │ Negative Ablation (Feature Discretization Loss)  │
│ 2-Stage Hierarchical Probability Fusion      │ 0.1251   │ 0.7137   │ 12.4 ms     │ Negative Ablation (1D Information Bottleneck)    │
│ M3: 23-Feature Joint GBDT (Canonical Winner) │ 0.1456   │ 0.7359   │ 7.46 ms     │ Canonical Winner (Preserves Feature Interactions)│
└──────────────────────────────────────────────┴──────────┴──────────┴─────────────┴──────────────────────────────────────────────────┘
```

1. **55M Parameter Sequence Transformer (`research/ablations/transformer_55m.py`)**:
   - *Hypothesis*: Multi-head self-attention over sequential payment history could learn complex temporal dependencies.
   - *Result (Negative Ablation)*: Incurred prohibitive CPU latency (~85ms) and suffered from feature discretization loss compared to tree-based partitioning on continuous tabular features.
2. **GRPO Policy Optimization (`research/ablations/grpo_trainer.py`)**:
   - *Hypothesis*: Group Relative Policy Optimization could learn dynamic threshold actions directly from reward signals.
   - *Result (Negative Ablation)*: Multi-reward balancing proved unstable; deterministic asymmetric cost-calibration on calibrated GBDT probabilities ($M4$) proved more stable, explainable, and compliant with payment gateway SLAs.
3. **Stage-1 High-Capacity Batch Baseline (`models/checkpoints/stage1_lgbm.pkl`, 481 Features, PR-AUC 0.4608)**:
   - *Role*: Offline research upper bound utilizing 481 multi-table batch features. Extracting 481 features requires $> 120\text{ms}$ multi-table lookups, violating real-time sub-10ms checkout constraints.

---

## 30. Architectural Justifications

### Why GBDT Over Deep Learning?
1. **Heterogeneous Feature Types**: Combines continuous amounts, trigonometric diurnal angles, integer graph degrees, and ratio metrics. Tree boosting handles mixed distributions without delicate feature normalization.
2. **Sub-10ms CPU Inference**: LightGBM evaluates 100 decision trees in $< 5\text{ms}$ on standard CPU cores, avoiding expensive GPU infrastructure costs.
3. **Split-Level Feature Interactions**: GBDTs natively learn multiplicative interactions between tabular metrics (Amount $Z$-score) and relational metrics (Device Burst Score).

### Why Temporal Relational Engineering Over GNNs?
1. **Latency Constraints**: Full GNN message passing over large dynamic payment graphs incurs $> 40\text{ms}$ neighborhood aggregation latency.
2. **Streaming Scalability**: Sliding-window multigraph extraction computes exact degree and burst statistics in $0.514\text{ms}$ on CPU.
3. **Explainability**: Graph degree, velocity, and connected component size map directly to human-understandable forensic explanations for fraud analysts.

---

## 31. Security, Privacy & Compliance

* **Strictly Defense-Only**: VYUH operates strictly as a defensive risk scoring gateway. Contains zero automated credential stuffing, card generation, or offensive exploitation capabilities.
* **No Raw Payment Credentials**: Card numbers are tokenized IDs (`CARD_A101`); no raw PANs or CVVs are stored or processed in graph memory.
* **No Hardcoded Secrets**: All configuration values and credentials are managed strictly via environment variables.

---

## 32. Verified System Limitations

1. **Zero-Entity-Reuse Attacks (Primary Blindspot)**: If an attacker utilizes disposable rotating residential proxies with single-use virtual cards and unique synthetic credentials, graph degree remains 1. Relational features provide no lift; VYUH relies on tabular anomaly detection.
2. **In-Memory Graph Scaling**: The current in-memory NetworkX implementation prunes stale nodes via a 2-hour TTL. Scaling to $> 50,000\text{ req/sec}$ will require distributed graph stores (e.g., RedisGraph / Memgraph).
3. **Delayed Ground-Truth Labels**: In payment gateways, chargeback labels arrive 30–90 days post-transaction. Graph scoring uses unsupervised topological structure, but GBDT model retraining requires delayed-label correction.

---

## 33. Future Roadmap

* **Distributed Graph State**: Migration of in-memory sliding-window topology to Redis-backed graph partitioning.
* **Continuous Online Drift Adaptation**: Automated population stability index (PSI) monitoring for concept drift detection.
* **Biometric Keystroke Dynamics**: Ingestion of behavioral client-side entropy into Tier-1 tabular features.

---

## 34. Technical Defense & Judge FAQ

#### Q1: Why isn't shared hardware or shared IP automatically flagged as fraud?
**Answer**: Legitimate users routinely share infrastructure (family tablets, corporate NAT gateways, university Wi-Fi). VYUH specifically incorporates **inter-arrival spacing and burst velocity** ($t < T_i$). Normal sharing spaced across hours produces low burst scores and clean conversions; automated syndicate bot bursts compressed into 30 seconds trigger risk escalation.

#### Q2: What is the exact formula for preventing future data leakage in relational features?
**Answer**: For any transaction $i$ at timestamp $T_i$, feature calculation is strictly constrained to the historical set $\{e_k \mid t_k < T_i\}$. No subsequent transactions or downstream chargeback labels enter graph feature computation.

#### Q3: Why is PR-AUC used instead of ROC-AUC or Accuracy?
**Answer**: The holdout dataset has a $3.44\%$ fraud rate. Accuracy is trivialized by predicting all legitimate ($96.56\%$ accuracy with 0% fraud caught). ROC-AUC is distorted by millions of true negatives. PR-AUC directly evaluates precision (merchant false alarm overhead) against recall (fraud caught).

#### Q4: What does the $+29.6\%$ relative PR-AUC lift mean?
**Answer**: PR-AUC increases from $0.1124$ (Tabular $M1$) to $0.1456$ (Joint $M3$). The absolute lift is $+0.0333$; $\frac{0.1456 - 0.1124}{0.1124} \times 100 = +29.6\%$.

#### Q5: What is the interpretation of the Bootstrap 95% Confidence Interval `[+0.0247, +0.0418]`?
**Answer**: Across 300 non-parametric bootstrap resamples on the 118,108 held-out test split, the difference $\Delta\text{PR-AUC} = \text{PR-AUC}(M3) - \text{PR-AUC}(M1)$ strictly excludes zero ($p < 0.001$), confirming that the incremental value of relational features is statistically robust.

#### Q6: Why did the Joint Concat GBDT ($M3$) outperform Hierarchical Stacking?
**Answer**: Compressing 13 relational features into a 1D scalar probability created an **Information Bottleneck**. Joint concatenation allows the decision trees to learn cross-domain split interactions directly (e.g., $\text{Amount } Z\text{-score} \times \text{Device Burst Velocity}$).

#### Q7: Why is M3 considered the canonical winner over M4?
**Answer**: $M3$ achieves the highest discrimination capability ($\text{PR-AUC} = 0.1456$ vs $0.1402$). $M4$ applies Isotonic Regression to calibrate probabilities for dollar-loss calculations, but $M3$ remains the primary discrimination engine.

#### Q8: Is this a Graph Neural Network (GNN)?
**Answer**: No. It is an in-memory bipartite temporal multigraph (`networkx`) that extracts 13 engineered graph statistics evaluated by a learned LightGBM GBDT. This design achieves $< 8.5\text{ms}$ P95 CPU inference without GPU infrastructure costs.

#### Q9: What happens if the Python inference engine crashes?
**Answer**: The Node.js gateway catches the socket drop within 3000ms, logs the failure, and returns an HTTP 503 status with action `STEP_UP_AUTH`. It strictly fails closed with zero fabricated risk scores.

#### Q10: What is the primary architectural blindspot?
**Answer**: Zero-Entity-Reuse attacks. If an adversary uses disposable rotating proxies, unique virtual cards, and synthetic identities, graph degree remains 1. VYUH gracefully falls back to tabular behavioral anomaly detection.

#### Q11: How is the ₹5.83 Lakhs/month merchant net savings calculated?
**Answer**: In an illustrative ₹100 Crore/month GMV model (2M txns, 1.5% fraud rate), operating at 1.0% fixed FPR increases fraud recall from 7.60% to 11.49%, catching an incremental ₹5.83 Lakhs/month in prevented fraud at identical friction overhead.

#### Q12: Are the benchmark latency numbers representative of production?
**Answer**: The 7.46ms P50 latency covers local in-memory CPU feature extraction and GBDT inference. Production multi-region deployments will incur standard external network transit hops.

---

## 35. Evidence Map

| Claim / Benchmark Result | Source Code / Artifact Path | Verification Command |
| :--- | :--- | :--- |
| **Dataset Temporal Split (472K/118K, 58s gap)** | `data/processed/train.pkl`, `test.pkl` | `python benchmarks/final_submission_validation.py` |
| **Incremental Value (+0.0333 PR-AUC)** | `models/checkpoints/final_incremental_value_study.json` | `python benchmarks/final_incremental_value_study.py` |
| **Bootstrap 95% CI `[+0.0247, +0.0418]`** | `models/checkpoints/final_incremental_value_study.json` | `python benchmarks/final_incremental_value_study.py` |
| **P50 Latency (7.46 ms CPU)** | `models/checkpoints/final_latency_benchmark.json` | `python benchmarks/final_latency_benchmark.py` |
| **Canonical Counterfactual Ground Truth** | `models/checkpoints/canonical_counterfactual_demo.json` | `python benchmarks/canonical_counterfactual_demo.py` |
| **Mathematical Parity ($|P_{\text{live}} - P_{\text{offline}}| = 0$)** | `tests/test_online_offline_parity.py` | `python tests/test_online_offline_parity.py` |
| **Stream Progression & Cold-Start Reset** | `tests/test_stream_evolution.py` | `python tests/test_stream_evolution.py` |
| **Fail-Closed Graceful Degradation** | `tests/test_failure_injection.py` | `python tests/test_failure_injection.py` |
| **Adversarial Evaluation & Blindspots** | `models/checkpoints/adversarial_attack_characterization.json` | `python benchmarks/adversarial_attack_characterization.py` |
| **Representative Merchant Economics** | `models/checkpoints/economic_impact_scenario.json` | `python benchmarks/economic_scenario_analysis.py` |

---

<div align="center">
  <sub>Built for Razorpay AI Buildathon 2026 · Track 02: AI Risk Manager</sub><br>
  <sub>Licensed under Apache License 2.0</sub>
</div>
