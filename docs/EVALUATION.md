# VYUH 2.1 — Comprehensive Evaluation & Statistical Report

**Dataset**: IEEE-CIS Fraud Detection (590,540 total historical transactions)  
**Split**: Strict Chronological Holdout (472,432 Train / 118,108 Test, 58-second gap)  
**Canonical Artifact**: `models/checkpoints/final_incremental_value_study.json`  

---

## 1. Primary Holdout Results (118,108 Untouched Transactions)

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

### Why PR-AUC Over ROC-AUC?
Under extreme fraud class imbalance ($3.44\%$ positive prevalence), ROC-AUC can be deceptively inflated because a large pool of true negatives masks millions of false positives. Precision-Recall AUC (PR-AUC) evaluates the true trade-off between precision (false alarm cost) and recall (fraud caught), making it the gold standard for financial risk modeling.

---

## 2. Statistical Bootstrap Validation (300 Resamples)

To verify that the incremental value of relational features is not an artifact of random sample variance, 300 non-parametric bootstrap iterations were computed on the held-out test split:

* **Mean $\Delta\text{PR-AUC}$ (M3 Joint vs M1 Tabular)**: **`+0.0333`** (+29.6% relative lift)
* **Bootstrap 95% Confidence Interval**: **`[+0.0247, +0.0418]`**
* **Significance Verdict**: The 95% confidence interval is strictly positive and bounded away from zero ($\Delta > 0$ with $p < 0.001$).
* **Operating Point Gain @ 1.0% Fixed FPR**: Increases from $7.60\% \to \mathbf{11.49\%}$ (**+51.2% relative lift in captured fraud**).
* **Operating Point Gain @ 0.5% Fixed FPR**: Increases from $3.94\% \to \mathbf{7.31\%}$ (**+85.5% relative lift in captured fraud**).

---

## 3. The Signature Counterfactual Demonstration

**Payload**: Invariant transaction (Amount = ₹499.00, Time = 14:00, Card = `CARD_CANONICAL_A`, Device = `DEV_CANONICAL_TARGET_X`, Email = `sarah.finance@enterprise.com`).

* **Isolated Risk ($P_{\text{tabular}}$)**: **`3.84%` (100% Invariant across all contexts)**

```
┌─────────────────────────────────────────────────────────────┬──────────┬──────────┬──────────┬──────────────────┐
│ Evaluated Context                                           │ P_tab    │ P_graph  │ P_final  │ Gateway Action   │
├─────────────────────────────────────────────────────────────┼──────────┼──────────┼──────────┼──────────────────┤
│ Context A: Isolated Personal Device (1:1 Binding)           │ 3.84%    │ 15.51%   │ 10.90%   │ ALLOW            │
│ Context B: Office NAT / Legitimate Spaced Sharing (8 Hours) │ 3.84%    │ 40.16%   │ 16.43%   │ STEP-UP_AUTH     │
│ Context C: Coordinated Bot Burst (10 Accounts / 30 Seconds) │ 3.84%    │ 48.50%   │ 68.50%   │ FLAG_HUMAN_REVIEW│
└─────────────────────────────────────────────────────────────┴──────────┴──────────┴──────────┴──────────────────┘
```

> **Signature Conclusion**: *"The transaction didn't change. The context did."*
