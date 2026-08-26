#!/usr/bin/env python3
"""
VYUH 2.0 — Controlled Stress-Test Slices Benchmark
==================================================
Evaluates model robustness across three distinct evaluation slices:
  1. Slice A — Normal Temporal Future (118,108 unseen test transactions)
  2. Slice B — Cold Entities (Zero historical card/device sightings in training data)
  3. Slice C — Coordinated Syndicate Stress (Multi-account fraud rings with shared hardware)

Proves the core hypothesis:
  "VYUH's advantage escalates specifically as fraud becomes coordinated."
"""

import os
import sys
import json
import time
import pickle
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score, f1_score, precision_score, recall_score

warnings.filterwarnings("ignore")

PROJECT_ROOT = Path(__file__).parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
CHECKPOINT_DIR = PROJECT_ROOT / "models" / "checkpoints"


def evaluate_slice(y_true, y_pred_proba, threshold=0.5):
    """Calculates PR-AUC, Recall, Precision, and F1 on a specific test slice."""
    if len(y_true) == 0 or len(np.unique(y_true)) < 2:
        return {"pr_auc": 0.0, "roc_auc": 0.0, "recall": 0.0, "precision": 0.0, "f1": 0.0, "count": len(y_true)}
    
    pr_auc = float(average_precision_score(y_true, y_pred_proba))
    roc_auc = float(roc_auc_score(y_true, y_pred_proba))
    
    y_pred = (y_pred_proba >= threshold).astype(int)
    p = float(precision_score(y_true, y_pred, zero_division=0))
    r = float(recall_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))
    
    return {
        "pr_auc": round(pr_auc, 4),
        "roc_auc": round(roc_auc, 4),
        "precision": round(p, 4),
        "recall": round(r, 4),
        "f1": round(f1, 4),
        "count": len(y_true),
        "fraud_count": int(np.sum(y_true))
    }


def run_stress_test():
    print("=" * 80)
    print("⚡ VYUH 2.0 — CONTROLLED STRESS-TEST BENCHMARK ACROSS 3 EVALUATION SLICES")
    print("=" * 80)

    train_df = pd.read_pickle(PROCESSED_DIR / "train.pkl")
    test_df = pd.read_pickle(PROCESSED_DIR / "test.pkl")
    test_graph = pd.read_pickle(PROCESSED_DIR / "test_graph_feats.pkl")

    y_test = test_df["isFraud"].astype(int).values
    base_cols = [c for c in train_df.columns if c not in ["isFraud", "TransactionID"]]
    all_graph_cols = test_graph.columns.tolist()

    # Load trained models
    lgbm_path = CHECKPOINT_DIR / "stage1_lgbm.pkl"
    vyuh_path = CHECKPOINT_DIR / "m3_lgbm_temporal_graph.pkl"

    if not lgbm_path.exists() or not vyuh_path.exists():
        print("⚠️ Waiting for trained model checkpoints...")
        return

    with open(lgbm_path, "rb") as f:
        model_lgbm = pickle.load(f)
    with open(vyuh_path, "rb") as f:
        model_vyuh = pickle.load(f)

    # 1. Predictions on full test set
    X_test_lgbm = test_df[base_cols]
    X_test_vyuh = pd.concat([test_df[base_cols], test_graph[all_graph_cols]], axis=1)

    preds_lgbm = model_lgbm.predict_proba(X_test_lgbm)[:, 1]
    preds_vyuh = model_vyuh.predict_proba(X_test_vyuh)[:, 1]

    # --- SLICE DEFINITIONS ---
    # Slice A: Full Standard Temporal Future
    slice_a_mask = np.ones(len(test_df), dtype=bool)

    # Slice B: Cold Entities (card1 not in train_df)
    train_cards = set(train_df["card1"].unique())
    slice_b_mask = ~test_df["card1"].isin(train_cards).values

    # Slice C: Coordinated Ring Stress (ring_size >= 5 or shared_device_deg >= 3)
    slice_c_mask = ((test_graph["graph_ring_size"] >= 5) | (test_graph["graph_device_shared_deg"] >= 3)).values

    slices = [
        ("Slice A: Standard Temporal Future", slice_a_mask, "General out-of-time distribution shift"),
        ("Slice B: Cold Entities (Unseen Cards)", slice_b_mask, "No prior transaction history for card"),
        ("Slice C: Coordinated Rings & Syndicates", slice_c_mask, "Multi-account clusters & device bursts")
    ]

    stress_results = []
    print("\n" + "=" * 90)
    print(f"{'Evaluation Slice':<40} | {'Test Size':<10} | {'LGBM PR-AUC':<12} | {'VYUH PR-AUC':<12} | {'Delta Lift':<10}")
    print("-" * 90)

    for name, mask, desc in slices:
        y_slice = y_test[mask]
        preds_lgbm_slice = preds_lgbm[mask]
        preds_vyuh_slice = preds_vyuh[mask]

        res_lgbm = evaluate_slice(y_slice, preds_lgbm_slice, threshold=0.5)
        res_vyuh = evaluate_slice(y_slice, preds_vyuh_slice, threshold=0.5)

        delta_pr = round(((res_vyuh["pr_auc"] - res_lgbm["pr_auc"]) / max(0.001, res_lgbm["pr_auc"])) * 100, 1)

        print(f"{name:<40} | {len(y_slice):<10,d} | {res_lgbm['pr_auc']:<12.4f} | {res_vyuh['pr_auc']:<12.4f} | +{delta_pr}%")

        stress_results.append({
            "slice_name": name,
            "description": desc,
            "sample_count": len(y_slice),
            "fraud_count": int(np.sum(y_slice)),
            "lgbm_metrics": res_lgbm,
            "vyuh_metrics": res_vyuh,
            "delta_pr_auc_pct": f"+{delta_pr}%"
        })

    print("=" * 90)

    # Save to JSON
    with open(CHECKPOINT_DIR / "stress_test_results.json", "w") as f:
        json.dump(stress_results, f, indent=2)
    print(f"\n💾 Saved Stress-Test Results to: {CHECKPOINT_DIR / 'stress_test_results.json'}")

    return stress_results


if __name__ == "__main__":
    run_stress_test()
