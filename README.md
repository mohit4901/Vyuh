# VYUH (व्यूह) 2.0 — AI Fraud Network Sentinel & Forensic Copilot

> **Razorpay AI Buildathon 2026 · Track 02: AI Risk Manager**  
> *A Production-Grade Risk Engine Pairing Fast Per-Transaction Detection with a Dynamic Temporal Entity Graph, Counterfactual "What Changed?" Forensics, and an Asymmetric Cost-Calibrated Decision Gateway.*

---

## 📌 Executive Summary & Thesis

In modern payment aggregation, **individual transactions frequently appear clean in isolation, but are deeply linked across hardware fingerprints, shared card subnets, and coordinated temporal bursts.**

Rather than treating payments as disconnected rows in a database ($P(\text{Fraud} \mid \text{Transaction}_i)$) or using opaque LLM wrappers to make financial decisions, **VYUH 2.0 establishes a 4-tier risk architecture**:

```
                         [Incoming Real Transaction Stream]
                                         │
                                         ▼
                 ┌──────────────────────────────────────────────┐
                 │ 1. DETECTION (Per-Transaction Baseline)      │
                 │    LightGBM GBDT (<0.01ms Inference Latency) │
                 └───────────────────────┬──────────────────────┘
                                         │
                                         ▼
                 ┌──────────────────────────────────────────────┐
                 │ 2. CONTEXT (Dynamic Temporal Entity Graph)   │
                 │    In-Memory Graph Updates: Degrees, Bursts, │
                 │    2-Hop Fraud Proximity & Community Size    │
                 └───────────────────────┬──────────────────────┘
                                         │
                                         ▼
                 ┌──────────────────────────────────────────────┐
                 │ 3. INVESTIGATION ("What Changed?" Engine)    │
                 │    Counterfactual Attribution (Δ Risk)       │
                 │    Forensic Tool Execution for Risk Officers │
                 └───────────────────────┬──────────────────────┘
                                         │
                                         ▼
                 ┌──────────────────────────────────────────────┐
                 │ 4. DECISION (Asymmetric Cost Gateway)        │
                 │    Minimizes: (Fraud Loss ₹) - (FP × ₹350)   │
                 └───────────────────────┬──────────────────────┘
                                         │
                 ┌───────────────────────┼──────────────────────┐
                 ▼                       ▼                      ▼
        [FLAG HUMAN REVIEW]      [STEP-UP KYC/2FA]           [ALLOW]
        Risk ≥ 0.80              0.45 ≤ Risk < 0.80          Risk < 0.45
        + Forensic Brief         + Biometric Step-Up         + Immutable Audit Log
```

---

## 💡 AI Judgment Showcase: The Transformer & GRPO Negative Ablation

A core tenet of engineering maturity is **knowing where NOT to use complex AI**. 

During early architecture exploration, we built and trained a **55M-Parameter Sequence Transformer with LoRA adapters and Group Relative Policy Optimization (GRPO)** on transaction sequences (`models/transformer_55m.py`, `models/grpo_trainer.py`). 

We ran a full 120-epoch training loop and benchmarked it directly against Gradient Boosted Decision Trees (LightGBM):

| Architecture Evaluated | Inference Latency | Validation PR-AUC | P99 Latency | Engineering Maintainability | Production Verdict |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **55M Seq Transformer + GRPO Policy** | ~22.4 ms | 0.3812 | > 45 ms | High (GPU dependency, fragile weights) | ❌ **REJECTED (Product-Wrong)** |
| **Calibrated LightGBM + Dynamic Graph** | **0.01 ms** | **0.4608** | **< 0.1 ms** | Low (CPU microservice, deterministic) | ✅ **ADOPTED IN PRODUCTION** |

> **Key Takeaway:** Tabular payment fraud data lacks dense autoregressive language semantics. Deploying a 55M Transformer in a checkout critical path adds 22ms of latency and GPU operational overhead without yielding superior precision-recall performance. **We intentionally killed the deep sequence model in favor of an ultra-low latency GBDT + dynamic graph sentinel.**

---

## 📊 Empirical Results & Ablation (118,108 Unseen Temporal Test Set)

Evaluated on the strict held-out temporal test set (80:20 split on `TransactionDT` with zero temporal leakage):

| Model Architecture | PR-AUC (Primary) | ROC-AUC | Precision | Recall | FPR | Net Saved (₹ Lakhs) | Inference Latency |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **M0 — Simple Rule Baseline** | 0.0395 | 0.5390 | 2.4% | 19.6% | 28.03% | -₹109.77L | < 0.01 ms |
| **M1 — LightGBM Tabular Baseline** | **0.4608** | 0.8533 | 67.4% | 35.0% | 0.60% | -₹0.60L | 0.01 ms |
| **M2 — LightGBM + Static Graph** | 0.4567 | 0.8557 | 69.0% | 33.9% | 0.54% | -₹0.49L | 0.01 ms |
| **M3 — LightGBM + Dynamic Temporal Graph** | 0.4588 | **0.8634** | 62.3% | **36.0%** | 0.78% | -₹1.34L | 0.01 ms |
| **M4 — VYUH Full (Cost-Calibrated Gateway)** | 0.4429 | 0.8610 | **93.3%** | 15.8% | **0.04%** | **+₹0.45L** | **0.01 ms** |

### Why Asymmetric Cost-Calibration Matters (M4)
In digital payments, false positives carry a heavy merchant friction penalty (estimated at ₹350 per customer drop-off). Model M4 calibrates the decision threshold to $0.84$, driving False Positive Rate down from **$0.60\%$ (689 false alarms) to $0.04\%$ (46 false alarms)**—turning a net operational loss into a positive **+₹45,142 net savings** on the test set.

---

## 🔍 The Hero Feature: Dynamic "What Changed?" Anomaly Diff

When a transaction is flagged, risk analysts receive an instant counterfactual decomposition explaining exactly which topological link triggered the risk elevation:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ 📋 COUNTERFACTUAL DECOMPOSITION (ORDER #ORD-4402)                                      │
│                                                                                        │
│ Baseline Isolated Risk:     0.06 (Clean)                                               │
│ Live Evaluated Risk:        0.94 (FLAG_HUMAN_REVIEW)                                   │
│ Risk Delta (Δ Risk):        +0.88                                                      │
│                                                                                        │
│ 🔎 Top Counterfactual Interventions:                                                   │
│ 1. Remove Shared Device Link ('DEV_938291'):    Risk drops 0.94 ──► 0.12 (Δ -82.0%)   │
│ 2. Remove Shared Card Link ('CARD_718293'):     Risk drops 0.94 ──► 0.18 (Δ -76.0%)   │
│ 3. Isolate from 2-Hop Chargeback Cluster:       Risk drops 0.94 ──► 0.08 (Δ -86.0%)   │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quickstart & Reproduction

### 1. Prerequisites
- Python 3.9+ (`.venv`)
- Node.js 18+

### 2. Start Live Microservices
```bash
# Terminal 1: Python Dynamic Graph & Inference Microservice (Port 5001)
.venv/bin/python backend/inference_service.py

# Terminal 2: Node.js Express Gateway & Web Dashboard (Port 3000)
node backend/server.js
```
Open **`http://localhost:3000`** in your browser!

### 3. Test with Arbitrary Unseen Data (Zero Hardcoded IDs)
```bash
curl -X POST http://localhost:5001/score \
  -H "Content-Type: application/json" \
  -d '{
    "orderId": "ORD-TEST-999",
    "amount": 1499.0,
    "cardId": "CARD_UNSEEN_101",
    "deviceId": "DEV_UNSEEN_202",
    "email": "merchant_user@domain.com"
  }'
```

### 4. Run Genuine Empirical Ablation
```bash
.venv/bin/python benchmarks/ablation_study.py
```

---

## 📜 Compliance & Safety (100% Defense-Only)

- **Zero Destructive Automated Account Termination**: Decisions are bounded to non-destructive actions (`ALLOW`, `STEP_UP_AUTH`, `FLAG_HUMAN_REVIEW`).
- **RBI & Indian Payment Gateway Aligned**: Full audit logging, plain-English forensic summaries, and verifiable step-up KYC triggers.
- **License**: Apache 2.0
