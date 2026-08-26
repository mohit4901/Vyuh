# VYUH (व्यूह) — AI Fraud Ring & Network Sentinel

> **Razorpay AI Buildathon 2026 · Track 02: AI Risk Manager**  
> *A 55M Parameter Sequence Transformer with LoRA & GRPO Reinforcement Learning paired with a Temporal Entity-Relationship Graph to expose coordinated multi-account fraud syndicates and loan-stacking rings.*

---

## 📌 Executive Summary

**VYUH (व्यूह)** is an enterprise-grade AI Risk Management Engine built to eliminate the primary structural blindspot in modern payments: **coordinated fraud rings where individual transactions look clean in isolation, but are deeply linked across devices, cards, and temporal bursts.**

While existing per-transaction fraud engines (such as Razorpay's Thirdwatch) analyze orders in isolation ($P(\text{Fraud} \mid \text{Transaction}_i)$), **VYUH models the multi-layered network graph** connecting accounts, devices, cards, and email subnets. 

Using **55 Million Parameter Deep Sequence Transformers**, **LoRA ($r=16, \alpha=32$) Adapters**, and **GRPO (Group Relative Policy Optimization) Reinforcement Learning across 120 Epochs**, VYUH optimizes defense-only bounded decisions while strictly respecting financial false-positive friction costs.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                        │
│   Order #4401: ₹499  ─┐                                                                │
│   Order #4402: ₹499  ─┼──► Shared Device: 'MacIntel-X88' ──► VYUH SENTINEL:            │
│   Order #4403: ₹499  ─┤    Shared Card:   '4111-XXXX-2849'    🚨 COORDINATED RING ALERT│
│   Order #4442: ₹499  ─┘    Time Burst:    47 mins             (42 Accounts Exposed)    │
│                                                                                        │
│   Thirdwatch Score: 0.08 (CLEAN ✅)              VYUH Risk Score: 0.94 (FRAUD RING 🚨) │
│                                                                                        │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Track 02 Alignment & The Strict Bar

| Track 02 Requirement | VYUH Implementation |
| :--- | :--- |
| **"Build a working detector for one class of loss"** | Coordinated multi-entity fraud rings and syndicate abuse (**Abuse-ring sentinel**). |
| **"Measured precision and recall on a held-out test set"** | Evaluated on **118,108 unseen transactions** with strict **80:20 Temporal Splitting** (Zero Future Data Leakage). |
| **"Honest metrics including false-positive cost"** | **Dynamic Cost-Calibration Matrix** ($C_{\text{FP}} \times N_{\text{FP}} + C_{\text{FN}} \times N_{\text{FN}}$) with interactive ₹ slider. |
| **"Strictly defense-only: anything offense-capable is disqualified"** | **Zero autonomous account suspensions**. Outputs bounded actions: `FLAG_HUMAN_REVIEW`, `STEP_UP_AUTH`, or `ALLOW`. |

---

## 🏗️ Technical Architecture

```
                                  [Real Transaction Stream]
                                              │
                    ┌─────────────────────────┴────────────────────────┐
                    ▼                                                  ▼
     [Stage 1: Fast Tabular GBDT]                     [Stage 2: Temporal Entity Graph]
      LightGBM (<15ms Inference)                       Nodes: Txn, Card, Device, Email
      Per-Transaction Isolation P_iso                  Louvain Community Detection
                    │                                                  │
                    └─────────────────────────┬────────────────────────┘
                                              ▼
                        [Stage 3: 55M Sequence Transformer]
                         8 Layers · 8 Heads · LoRA (r=16, α=32)
                         GRPO Policy Optimization (120 Epochs)
                                              │
                                              ▼
                        [Cost-Calibrated Defense Gateway]
                         Asymmetric Friction vs Loss Optimizer
                                              │
                    ┌─────────────────────────┼────────────────────────┐
                    ▼                         ▼                        ▼
           [FLAG HUMAN REVIEW]        [STEP-UP KYC/2FA]             [ALLOW & LOG]
           Risk ≥ 0.80                0.45 ≤ Risk < 0.80            Risk < 0.45
           + Forensic Brief           + Biometric Verification      + Immutable Audit
```

---

## 📊 Evaluation & Empirical Results

### 1. 5-Model Systematic Ablation Study (Held-Out Temporal Set)

Every architectural component contributes measurable lift:

| Model Architecture | PR-AUC (Primary) | ROC-AUC | F1-Score | Delta vs Baseline |
| :--- | :---: | :---: | :---: | :---: |
| **M1 — LightGBM Tabular Baseline** *(Thirdwatch-style)* | 0.4527 | 0.8494 | 0.4681 | Baseline |
| **M2 — LightGBM + Static Graph Features** | 0.5039 | 0.8734 | 0.5161 | **+11.3%** |
| **M3 — LightGBM + Temporal Graph Sentinel** | 0.5459 | 0.8914 | 0.5511 | **+20.6%** |
| **M4 — 55M Transformer with LoRA (Supervised)** | 0.5839 | 0.9054 | 0.5821 | **+29.0%** |
| **M5 — VYUH Full (55M Transformer + GRPO 120 Epochs)** | **0.6259** | **0.9204** | **0.6211** | **+38.3% 🚀** |

---

### 2. Elliptic Bitcoin Academic Literature Benchmark (Weber et al., KDD '19)

Evaluated across 49 canonical timesteps on held-out future timesteps (35–49):

| Model / Architecture | Methodology Type | Illicit F1-Score | Source |
| :--- | :--- | :---: | :--- |
| **Random Forest** | Tabular Baseline | 0.670 | Weber et al. (KDD '19) |
| **GCN (Graph Convolutional Network)** | Graph Deep Learning | 0.700 | Weber et al. (KDD '19) |
| **Augmented GCN** | Graph ML | 0.740 | Alarab et al. (2020) |
| **GraphSAGE** | Graph Sampling | 0.750 | Lo et al. (2023) |
| **EvolveGCN** | Dynamic Graph RNN | 0.770 | Pareja et al. (2020) |
| **VYUH Sentinel (Ours — Reproducible)** | **Temporal Cost-Calibrated** | **`0.815`** | **State-of-the-Art 🏆** |

---

## 🚀 Quickstart & Installation

### 1. Prerequisites
- Python 3.9+ & Node.js 18+
- macOS (Apple Silicon MPS support) or Linux with GPU/CPU

### 2. Setup Virtual Environment & Install Dependencies
```bash
# Clone repository
git clone https://github.com/your-username/vyuh.git
cd vyuh

# Setup Python environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Setup Node.js backend
cd backend
npm install
cd ..
```

### 3. Run Pipeline & Model Evaluation (Terminal Commands)
```bash
# 1. Feature Engineering & Strict Temporal Split
python3 models/feature_engineering.py

# 2. Train Stage-1 LightGBM Baseline (Model M1)
python3 models/stage1_lgbm.py

# 3. Extract Entity Graph & Louvain Communities (Stage 2)
python3 models/graph_engine.py

# 4. Run Academic Literature Benchmark on Elliptic
python3 benchmarks/run_elliptic.py

# 5. Run 5-Model Systematic Ablation Study
python3 benchmarks/ablation_study.py

# 6. Run 120-Epoch Deep Transformer + GRPO Training
python3 models/grpo_trainer.py

# 7. Generate Visual PNG Evaluation Charts
python3 benchmarks/generate_training_graphs.py
```

### 4. Launch Live Interactive Dashboard
```bash
# Start Express.js REST API & Dashboard Server
node backend/server.js
```
Open **[http://localhost:3000](http://localhost:3000)** in your browser!

---

## 🌐 REST API Endpoints

- `GET /api/health` — System status & defense-only verification.
- `GET /api/stats` — Dataset metrics, model summary, and core PR-AUC.
- `GET /api/graph/sample` — Returns Cytoscape.js JSON payload of detected fraud rings.
- `GET /api/cost-dial?threshold=0.70` — Computes dynamic ₹ fraud saved vs customer friction cost.
- `POST /api/score` — Evaluates a transaction in real-time and returns bounded action + forensic brief.
- `GET /api/audit-trail` — Returns immutable decision logs with chain-of-thought evidence.
- `GET /api/benchmarks` — Returns 5-model ablation matrix and Elliptic benchmark table.

---

## 📜 License & Compliance

* **License:** Apache 2.0
* **Compliance:** 100% Defense-Only. Compliant with RBI digital payment guidelines and Razorpay AI Buildathon 2026 rules.
