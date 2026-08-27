# VYUH Research & Negative Ablations

This directory contains historical research prototypes, exploratory training architectures, and negative ablations evaluated during the development of VYUH.

---

## 1. Directory Structure

```
research/
├── README.md                          # Research overview and ablation findings
└── ablations/
    ├── transformer_55m.py             # 55M-parameter sequence payment transformer
    ├── grpo_trainer.py                # Group Relative Policy Optimization (RL) trainer
    ├── stage1_lgbm.py                 # 481-feature high-capacity offline batch model
    ├── train_learned_multimodal.py    # Multimodal tabular+graph probability stacking
    ├── train_online_lgbm.py           # Online streaming micro-classifier
    ├── temporal_diff_engine.py        # Temporal "what changed" attribution prototype
    └── graph_engine.py                # Static Louvain graph baseline
```

---

## 2. Key Negative Ablation Findings

1. **55M Sequence Transformer (`transformer_55m.py`)**:
   - *Hypothesis*: Multi-head attention over customer event sequences would learn complex temporal interactions.
   - *Result*: Incurred prohibitive CPU latency (~85ms) and struggled with tabular continuous feature discretization compared to tree-based partitioning.
2. **GRPO Policy Optimization (`grpo_trainer.py`)**:
   - *Hypothesis*: RL policy optimization could learn dynamic action thresholds directly from reward signals.
   - *Result*: Unstable multi-objective reward balancing; deterministic asymmetric cost calibration ($M4$) proved more stable, explainable, and compliant with payment gateway SLAs.
3. **Stage-1 High-Capacity Batch Baseline (`stage1_lgbm.py`, 481 features)**:
   - *Hypothesis*: Offline historical aggregations ($V1-V339, C1-C14$) provide a strong retrospective upper bound ($0.4608$ PR-AUC).
   - *Result*: Feature store latency ($>120\text{ms}$) violated sub-10ms checkout constraints. The 23-feature streaming pipeline ($M3$) was selected for sub-millisecond extraction ($0.514\text{ms}$) with $+29.6\%$ holdout lift.
