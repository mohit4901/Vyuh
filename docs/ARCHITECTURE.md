# VYUH (व्यूह) — System & Machine Learning Architecture

**Track**: Razorpay AI Buildathon 2026 · Track 02: AI Risk Manager  
**Repository**: `mohit4901/Vyuh`  
**License**: Apache License 2.0  

---

## 1. Executive Summary

Traditional transaction-level fraud detection systems evaluate transactions in isolation. A payment of ₹499 at 2:00 PM with a standard email and card typically exhibits low isolated risk ($P_{\text{tabular}} \approx 3.8\%$). However, modern coordinated fraud syndicates distribute attacks across multiple synthetic accounts, rotating cards, and shared hardware emulators.

**VYUH (व्यूह)** is a **Temporal Relational Fraud Intelligence Gateway** that resolves this limitation by evaluating incoming transactions within their live bipartite graph context. It combines 10 tabular transaction features with 13 strictly backward-looking ($t < T_i$) temporal relational features into a **23-Feature Joint GBDT** ($M3$, Canonical Winner) calibrated via Isotonic Regression ($M4$) and governed by an asymmetric economic cost gateway.

---

## 2. The 15-Second System Flow

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

---

## 3. Feature Schema & Leakage Safety

### A. Tabular Features (10 Features — Transaction Domain)
1. `TransactionAmt`: Raw checkout amount in INR / USD.
2. `TransactionAmt_log`: Natural logarithm $\ln(1 + \text{Amt})$.
3. `hour_sin`: Cyclical diurnal component $\sin(2\pi \cdot \text{hour} / 24)$.
4. `hour_cos`: Cyclical diurnal component $\cos(2\pi \cdot \text{hour} / 24)$.
5. `is_night`: High-risk nighttime indicator ($22:00 \le \text{hour} \le 05:00$).
6. `card1_amt_mean`: Historical mean transaction amount on card subnet.
7. `card1_amt_std`: Historical standard deviation of amounts on card subnet.
8. `card1_amt_zscore`: Standardized amount deviation $\frac{\text{Amt} - \mu}{\sigma}$.
9. `card1_txn_count`: Lifetime transaction count on card subnet.
10. `card1_unique_devices`: Number of distinct physical hardware devices mapped to card.

### B. Temporal Relational Features (13 Features — Graph Domain, Strictly Backward-Looking $t < T_i$)
1. `dev_unique_cards_24h`: Distinct payment cards observed on device in 24-hour sliding window.
2. `dev_unique_emails_24h`: Distinct customer emails associated with device in 24 hours.
3. `dev_txn_velocity_1h`: Transaction velocity on device in 1-hour sliding window.
4. `dev_amount_sum_1h`: Total currency processed on device across all cards in 1 hour.
5. `card_unique_devices_24h`: Distinct physical devices observed for card in 24 hours.
6. `card_unique_emails_24h`: Distinct customer emails associated with card in 24 hours.
7. `card_txn_velocity_1h`: Transaction velocity on card in 1 hour.
8. `card_device_switch_rate`: Lifetime hardware volatility ratio $\frac{\text{Unique Devices}}{\text{Total Txns}}$.
9. `graph_device_shared_deg`: Live bipartite degree between device node and transaction nodes.
10. `graph_card_shared_deg`: Live bipartite degree between card node and transaction nodes.
11. `graph_burst_score`: Multiplicative burst index $\ln(1 + \text{Velocity}) \times \ln(1 + \text{Degree})$.
12. `graph_ring_size`: Real-time connected component size in bipartite multigraph.
13. `graph_2hop_neighborhood_size`: 2-Hop entity count reachable from transaction node.

> **Zero Future Leakage Principle**: For every transaction $i$ occurring at timestamp $T_i$, graph topology and rolling metrics are computed strictly from events with timestamp $t < T_i$. No future events or downstream chargeback labels enter feature matrices.

---

## 4. Model Architecture & Information Bottleneck Discovery

VYUH evaluates 4 distinct architectures:
* **M1 (Tabular Baseline)**: 10-feature LightGBM GBDT trained solely on tabular features ($P_{\text{tabular}}$).
* **M2 (Relational GBDT)**: 13-feature LightGBM GBDT trained solely on temporal graph features ($P_{\text{graph}}$).
* **M3 (Joint 23-Feature Concat GBDT — Canonical Winner)**: 23-feature concatenated GBDT jointly optimized over both tabular and relational feature spaces.
* **M4 (Calibrated Joint GBDT)**: 23-feature joint GBDT mapped through 5-fold out-of-fold Isotonic Probability Calibration.

### The Fusion Bottleneck Finding
In earlier development, a 2-stage hierarchical stacking architecture was tested where tabular and graph models were trained separately and their scalar probabilities fused via a meta-learner. Empirical evaluation revealed an **information bottleneck**: compressing the 13-dimensional relational space into a 1D scalar probability discarded critical feature interactions (e.g., interaction between high amount $Z$-score and device burst velocity). The **23-feature Joint GBDT (M3)** restored these cross-domain split interactions, achieving superior PR-AUC (0.1456 vs 0.1251).

---

## 5. Decision Policy & Cost Calibration

The decision gateway optimizes expected business loss:
$$\mathcal{L}(\text{Action}) = \begin{cases} P_{\text{final}} \times \text{Amount} & \text{if ALLOW} \\ \text{Cost}_{\text{stepup}} \approx ₹22 & \text{if STEP-UP} \\ \text{Cost}_{\text{review}} \approx ₹132.50 & \text{if REVIEW} \end{cases}$$

* **ALLOW** ($P_{\text{final}} < 0.15$): Frictionless 1-click checkout committed to immutable audit trail.
* **STEP-UP AUTH** ($0.15 \le P_{\text{final}} < 0.25$): Non-destructive challenge (biometric/OTP) for moderate sharing.
* **FLAG HUMAN REVIEW** ($P_{\text{final}} \ge 0.25$): High-risk escalation with automated forensic brief.

---

## 6. Negative Ablations & Research Evolution

To maintain rigorous scientific transparency, several candidate architectures were evaluated during development:

1. **55M-Parameter Sequence Transformer (`research/ablations/transformer_55m.py`)**:
   * *Hypothesis*: Multi-head self-attention over sequential payment history could learn complex temporal dependencies.
   * *Finding (Negative Ablation)*: Incurred prohibitive inference latency (~85ms CPU) and suffered from feature discretization loss compared to tree-based partitioning on continuous tabular features.
2. **GRPO Policy Optimization (`research/ablations/grpo_trainer.py`)**:
   * *Hypothesis*: Group Relative Policy Optimization could learn dynamic threshold actions directly from reward signals.
   * *Finding (Negative Ablation)*: Required unstable multi-reward balancing; deterministic asymmetric cost-calibration on calibrated GBDT probabilities ($M4$) proved more stable, explainable, and compliant with payment gateway SLAs.
3. **Stage-1 High-Capacity Batch Baseline (`research/ablations/stage1_lgbm.py`, 481 Features, PR-AUC 0.4608)**:
   * *Role*: Evaluated 481 historical engineered batch features ($V1-V339, C1-C14, D1-D15$) as an offline research upper bound.
   * *Trade-off*: Extracting 481 complex multi-table aggregations requires $>120\text{ms}$ feature store lookups, violating real-time sub-10ms checkout constraints. The 23-feature streaming pipeline ($M3$) was specifically engineered for sub-millisecond extraction ($0.514\text{ms}$) while capturing temporal coordination.

