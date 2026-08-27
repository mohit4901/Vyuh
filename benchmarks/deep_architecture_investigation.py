#!/usr/bin/env python3
"""
VYUH 2.1 — Model Architecture Ablation & Deep Investigation (M1 vs M2 vs M3 vs M4)
===================================================================================
Investigates:
  M1: Tabular LightGBM (10 Features)
  M2: Relational Graph GBDT (13 Strict Temporal Features)
  M3: Joint Concatenation GBDT (23 Features)
  M4: Calibrated Joint Stacking / Multi-Modal GBDT (OOF-Trained + Isotonic)

Measures:
  - PR-AUC, ROC-AUC, Brier Score
  - Recall @ 1.0% FPR, Recall @ 0.5% FPR, Recall @ 0.1% FPR
  - FPR @ 10% Recall, FPR @ 20% Recall
  - Bootstrap 95% Confidence Intervals (300 resamples)
"""

import sys
import os
import json
import pickle
import time
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.metrics import average_precision_score, roc_auc_score, precision_recall_curve, roc_curve, brier_score_loss
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import StratifiedKFold
import lightgbm as lgb

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
CHECKPOINT_DIR = PROJECT_ROOT / "models" / "checkpoints"

def run_deep_architecture_study():
    print("=" * 115)
    print("🔬 DEEP ARCHITECTURE INVESTIGATION: M1 (Tabular) vs M2 (Graph) vs M3 (Concat) vs M4 (Calibrated)")
    print("=" * 115)

    train_df = pd.read_pickle(PROCESSED_DIR / "train.pkl")
    test_df = pd.read_pickle(PROCESSED_DIR / "test.pkl")
    train_graph = pd.read_pickle(PROCESSED_DIR / "train_temporal_graph_feats.pkl")
    test_graph = pd.read_pickle(PROCESSED_DIR / "test_temporal_graph_feats.pkl")

    y_train = train_df["isFraud"].astype(int).values
    y_test = test_df["isFraud"].astype(int).values

    def build_feature_matrices(df, g_df):
        amt_s = df["TransactionAmt"].fillna(499.0)
        h_sin = df["hour_sin"].fillna(0.0).values if "hour_sin" in df.columns else np.zeros(len(df))
        h_cos = df["hour_cos"].fillna(1.0).values if "hour_cos" in df.columns else np.ones(len(df))
        is_night = df["is_night"].fillna(0).values if "is_night" in df.columns else np.zeros(len(df))
        amt_mean = df["card1_amt_mean"].fillna(amt_s).values if "card1_amt_mean" in df.columns else amt_s.values
        amt_std = df["card1_amt_std"].fillna(100.0).values if "card1_amt_std" in df.columns else np.ones(len(df))*100.0
        zscore = df["card1_amt_zscore"].fillna(0.0).clip(-5.0, 10.0).values if "card1_amt_zscore" in df.columns else np.zeros(len(df))
        card_cnt = df["card1_txn_count"].fillna(1).clip(1, 500).values if "card1_txn_count" in df.columns else np.ones(len(df))
        uniq_dev = df["card1_unique_devices"].fillna(1).clip(1, 50).values if "card1_unique_devices" in df.columns else np.ones(len(df))

        X_tab = pd.DataFrame({
            "TransactionAmt": amt_s.values, "TransactionAmt_log": np.log1p(amt_s.values), "hour_sin": h_sin, "hour_cos": h_cos, "is_night": is_night,
            "card1_amt_mean": amt_mean, "card1_amt_std": amt_std, "card1_amt_zscore": zscore, "card1_txn_count": card_cnt, "card1_unique_devices": uniq_dev
        }).reset_index(drop=True)
        X_graph = g_df.reset_index(drop=True).copy()
        return X_tab, X_graph

    X_train_tab, X_train_graph = build_feature_matrices(train_df, train_graph)
    X_test_tab, X_test_graph = build_feature_matrices(test_df, test_graph)

    X_train_23 = pd.concat([X_train_tab, X_train_graph], axis=1)
    X_test_23 = pd.concat([X_test_tab, X_test_graph], axis=1)

    # 1. Load or Train M1, M2
    with open(CHECKPOINT_DIR / "tabular_lgbm.pkl", "rb") as f:
        m1 = pickle.load(f)
    with open(CHECKPOINT_DIR / "graph_lgbm.pkl", "rb") as f:
        m2 = pickle.load(f)

    # 2. Train Joint Concat (23 Features) with 5-Fold Stratified CV
    print("🔨 Training M3: Joint 23-Feature GBDT with 5-Fold Cross-Validation...")
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    oof_p3 = np.zeros(len(y_train))
    test_p3_folds = np.zeros(len(y_test))

    lgb_params = {
        "objective": "binary", "metric": "average_precision", "boosting_type": "gbdt",
        "n_estimators": 250, "learning_rate": 0.03, "num_leaves": 31, "min_child_samples": 50,
        "subsample": 0.8, "colsample_bytree": 0.8, "random_state": 42, "n_jobs": -1, "verbose": -1
    }

    for fold, (train_idx, val_idx) in enumerate(skf.split(X_train_23, y_train)):
        model_f = lgb.LGBMClassifier(**lgb_params)
        model_f.fit(X_train_23.iloc[train_idx], y_train[train_idx])
        oof_p3[val_idx] = model_f.predict_proba(X_train_23.iloc[val_idx])[:, 1]
        test_p3_folds += model_f.predict_proba(X_test_23)[:, 1] / 5.0

    print(f"   ✅ M3 5-Fold OOF PR-AUC: {average_precision_score(y_train, oof_p3):.4f} | Test PR-AUC: {average_precision_score(y_test, test_p3_folds):.4f}")

    # Train final M3 model on full training data
    m3_final = lgb.LGBMClassifier(**lgb_params)
    m3_final.fit(X_train_23, y_train)
    with open(CHECKPOINT_DIR / "joint_23feat_lgbm.pkl", "wb") as f:
        pickle.dump(m3_final, f)

    # 3. Train M4: Calibrated Multi-Modal Model (Full 23 Features + Isotonic Calibration)
    print("🔨 Training M4: Calibrated 23-Feature Joint Model (Isotonic Calibration on OOF)...")
    m4_calibrated = CalibratedClassifierCV(estimator=lgb.LGBMClassifier(**lgb_params), method="isotonic", cv=5)
    m4_calibrated.fit(X_train_23, y_train)
    with open(CHECKPOINT_DIR / "calibrated_23feat_lgbm.pkl", "wb") as f:
        pickle.dump(m4_calibrated, f)

    # Predictions
    p1 = m1.predict_proba(X_test_tab)[:, 1]
    p2 = m2.predict_proba(X_test_graph)[:, 1]
    p3 = m3_final.predict_proba(X_test_23)[:, 1]
    p4 = m4_calibrated.predict_proba(X_test_23)[:, 1]

    def eval_model(y_true, scores):
        pr = float(average_precision_score(y_true, scores))
        roc = float(roc_auc_score(y_true, scores))
        brier = float(brier_score_loss(y_true, scores))
        fpr_arr, tpr_arr, _ = roc_curve(y_true, scores)

        def rec_at_fpr(target_fpr):
            idx = np.where(fpr_arr <= target_fpr)[0]
            return float(tpr_arr[idx[-1]]) if len(idx) > 0 else 0.0

        def fpr_at_rec(target_rec):
            idx = np.where(tpr_arr >= target_rec)[0]
            return float(fpr_arr[idx[0]]) if len(idx) > 0 else 1.0

        return {
            "pr_auc": pr, "roc_auc": roc, "brier_score": brier,
            "rec_at_1pct_fpr": rec_at_fpr(0.010),
            "rec_at_05pct_fpr": rec_at_fpr(0.005),
            "rec_at_01pct_fpr": rec_at_fpr(0.001),
            "fpr_at_10pct_rec": fpr_at_rec(0.10),
            "fpr_at_20pct_rec": fpr_at_rec(0.20)
        }

    m_list = [
        ("M1: Tabular LightGBM (10 Feats)", "m1_tabular", p1),
        ("M2: Relational Graph GBDT (13 Feats)", "m2_graph", p2),
        ("M3: Joint Concat GBDT (23 Feats)", "m3_concat", p3),
        ("M4: Calibrated Joint GBDT (23 Feats + Isotonic)", "m4_calibrated", p4)
    ]

    print("\n" + "=" * 125)
    print(f"{'Model Architecture':<42} | {'PR-AUC':<8} | {'ROC-AUC':<8} | {'Rec@1.0% FPR':<12} | {'Rec@0.5% FPR':<12} | {'FPR@20% Rec'}")
    print("-" * 125)

    stats = {}
    for name, key, sc in m_list:
        res = eval_model(y_test, sc)
        stats[key] = res
        print(f"{name:<42} | {res['pr_auc']:.4f}   | {res['roc_auc']:.4f}   | {res['rec_at_1pct_fpr']*100:>10.2f}%  | {res['rec_at_05pct_fpr']*100:>10.2f}%  | {res['fpr_at_20pct_rec']*100:>9.2f}%")

    print("=" * 125)

    # Bootstrap 95% CI (300 resamples for M3 vs M1 and M4 vs M1)
    print("\n🎲 Computing Bootstrap 95% Confidence Intervals (300 resamples)...")
    np.random.seed(42)
    n_samples = len(y_test)
    deltas_pr_m3 = []
    deltas_pr_m4 = []

    for b in range(300):
        idx = np.random.choice(n_samples, size=n_samples, replace=True)
        y_b = y_test[idx]
        if len(np.unique(y_b)) < 2:
            continue
        pr_1 = average_precision_score(y_b, p1[idx])
        pr_3 = average_precision_score(y_b, p3[idx])
        pr_4 = average_precision_score(y_b, p4[idx])
        deltas_pr_m3.append(pr_3 - pr_1)
        deltas_pr_m4.append(pr_4 - pr_1)

    ci_m3_low, ci_m3_high = np.percentile(deltas_pr_m3, [2.5, 97.5])
    ci_m4_low, ci_m4_high = np.percentile(deltas_pr_m4, [2.5, 97.5])

    print(f"   • M3 (Joint Concat) vs M1 (Tabular): Mean ΔPR-AUC = {np.mean(deltas_pr_m3):+.4f} (95% CI: [{ci_m3_low:+.4f}, {ci_m3_high:+.4f}])")
    print(f"   • M4 (Calibrated Joint) vs M1 (Tabular): Mean ΔPR-AUC = {np.mean(deltas_pr_m4):+.4f} (95% CI: [{ci_m4_low:+.4f}, {ci_m4_high:+.4f}])")

if __name__ == "__main__":
    run_deep_architecture_study()
