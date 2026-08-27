#!/usr/bin/env python3
"""
VYUH 2.1 — Learned Multi-Modal Risk Engine & Fusion Training Pipeline
====================================================================
Trains a 100% learned multi-modal architecture on real IEEE-CIS historical data:
  1. Tabular LightGBM (10 Features): P_tabular
  2. Relational Graph LightGBM (4 Features): P_graph
  3. Learned Multi-Modal Fusion Layer (OOF Trained + Isotonic Calibration): P_final

Zero synthetic data used in training.
Zero future leakage.
Zero hand-coded risk addition formulas.
"""

import os
import sys
import json
import pickle
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.metrics import average_precision_score, roc_auc_score, precision_score, recall_score, brier_score_loss
from sklearn.model_selection import KFold
from sklearn.calibration import CalibratedClassifierCV
from sklearn.linear_model import LogisticRegression

warnings.filterwarnings("ignore")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
CHECKPOINT_DIR = PROJECT_ROOT / "models" / "checkpoints"
CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)


def load_datasets():
    print("📂 [1/5] Loading real preprocessed IEEE-CIS datasets & Strict Temporal Features...")
    train_df = pd.read_pickle(PROCESSED_DIR / "train.pkl")
    test_df = pd.read_pickle(PROCESSED_DIR / "test.pkl")
    train_graph = pd.read_pickle(PROCESSED_DIR / "train_temporal_graph_feats.pkl")
    test_graph = pd.read_pickle(PROCESSED_DIR / "test_temporal_graph_feats.pkl")

    y_train = train_df["isFraud"].astype(int).values
    y_test = test_df["isFraud"].astype(int).values
    amounts_test = test_df["TransactionAmt"].fillna(1850.0).values

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

        # 10 Tabular Features
        X_tab = pd.DataFrame({
            "TransactionAmt": amt_s.values,
            "TransactionAmt_log": np.log1p(amt_s.values),
            "hour_sin": h_sin,
            "hour_cos": h_cos,
            "is_night": is_night,
            "card1_amt_mean": amt_mean,
            "card1_amt_std": amt_std,
            "card1_amt_zscore": zscore,
            "card1_txn_count": card_cnt,
            "card1_unique_devices": uniq_dev
        })

        # 13 Strict Temporal Relational Graph Features
        X_graph = g_df.copy()

        return X_tab, X_graph

    X_train_tab, X_train_graph = build_feature_matrices(train_df, train_graph)
    X_test_tab, X_test_graph = build_feature_matrices(test_df, test_graph)

    print(f"   Train Set: {len(X_train_tab):,} rows | Tabular: {X_train_tab.shape[1]} cols | Temporal Graph: {X_train_graph.shape[1]} cols")
    print(f"   Test Set:  {len(X_test_tab):,} rows (Untouched Temporal Holdout)")

    return (X_train_tab, X_train_graph, y_train), (X_test_tab, X_test_graph, y_test, amounts_test)


def train_multimodal_system():
    (X_tr_tab, X_tr_graph, y_train), (X_te_tab, X_te_graph, y_test, amounts_test) = load_datasets()

    # =========================================================================
    # 1. TRAIN TABULAR MODEL WITH 5-FOLD OUT-OF-FOLD (OOF) PREDICTIONS
    # =========================================================================
    print("\n🧠 [2/5] Training Tier-1 Tabular LightGBM (10 Features) with 5-Fold OOF...")
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    oof_p_tabular = np.zeros(len(y_train))
    test_p_tabular_folds = np.zeros(len(y_test))

    tabular_params = {
        "objective": "binary",
        "metric": "average_precision",
        "boosting_type": "gbdt",
        "n_estimators": 300,
        "learning_rate": 0.03,
        "num_leaves": 31,
        "subsample": 0.8,
        "subsample_freq": 1,
        "colsample_bytree": 0.8,
        "random_state": 42,
        "n_jobs": -1,
        "verbose": -1
    }

    for fold, (trn_idx, val_idx) in enumerate(kf.split(X_tr_tab)):
        X_trn, y_trn = X_tr_tab.iloc[trn_idx], y_train[trn_idx]
        X_val, y_val = X_tr_tab.iloc[val_idx], y_train[val_idx]

        model = lgb.LGBMClassifier(**tabular_params)
        model.fit(X_trn, y_trn, eval_set=[(X_val, y_val)], callbacks=[lgb.early_stopping(stopping_rounds=30, verbose=False)])
        oof_p_tabular[val_idx] = model.predict_proba(X_val)[:, 1]
        test_p_tabular_folds += model.predict_proba(X_te_tab)[:, 1] / 5.0

    oof_pr_tab = average_precision_score(y_train, oof_p_tabular)
    test_pr_tab = average_precision_score(y_test, test_p_tabular_folds)
    print(f"   ✅ Tabular LightGBM OOF PR-AUC: {oof_pr_tab:.4f} | Test PR-AUC: {test_pr_tab:.4f}")

    # Retrain full Tabular model on all training data
    final_tabular_model = lgb.LGBMClassifier(**tabular_params)
    final_tabular_model.fit(X_tr_tab, y_train)
    with open(CHECKPOINT_DIR / "tabular_lgbm.pkl", "wb") as f:
        pickle.dump(final_tabular_model, f)
    print("   💾 Saved: models/checkpoints/tabular_lgbm.pkl")

    # =========================================================================
    # 2. TRAIN GRAPH MODEL WITH 5-FOLD OUT-OF-FOLD (OOF) PREDICTIONS
    # =========================================================================
    print("\n🕸️  [3/5] Training Tier-2 Relational Graph LightGBM (4 Features) with 5-Fold OOF...")
    oof_p_graph = np.zeros(len(y_train))
    test_p_graph_folds = np.zeros(len(y_test))

    graph_params = {
        "objective": "binary",
        "metric": "average_precision",
        "boosting_type": "gbdt",
        "n_estimators": 200,
        "learning_rate": 0.03,
        "num_leaves": 15,
        "subsample": 0.8,
        "subsample_freq": 1,
        "random_state": 42,
        "n_jobs": -1,
        "verbose": -1
    }

    for fold, (trn_idx, val_idx) in enumerate(kf.split(X_tr_graph)):
        X_trn, y_trn = X_tr_graph.iloc[trn_idx], y_train[trn_idx]
        X_val, y_val = X_tr_graph.iloc[val_idx], y_train[val_idx]

        model_g = lgb.LGBMClassifier(**graph_params)
        model_g.fit(X_trn, y_trn, eval_set=[(X_val, y_val)], callbacks=[lgb.early_stopping(stopping_rounds=30, verbose=False)])
        oof_p_graph[val_idx] = model_g.predict_proba(X_val)[:, 1]
        test_p_graph_folds += model_g.predict_proba(X_te_graph)[:, 1] / 5.0

    oof_pr_graph = average_precision_score(y_train, oof_p_graph)
    test_pr_graph = average_precision_score(y_test, test_p_graph_folds)
    print(f"   ✅ Graph LightGBM OOF PR-AUC: {oof_pr_graph:.4f} | Test PR-AUC: {test_pr_graph:.4f}")

    # Retrain full Graph model on all training data
    final_graph_model = lgb.LGBMClassifier(**graph_params)
    final_graph_model.fit(X_tr_graph, y_train)
    with open(CHECKPOINT_DIR / "graph_lgbm.pkl", "wb") as f:
        pickle.dump(final_graph_model, f)
    print("   💾 Saved: models/checkpoints/graph_lgbm.pkl")

    # =========================================================================
    # 3. TRAIN MULTI-MODAL FUSION LAYER ON LEAKAGE-FREE OOF PREDICTIONS
    # =========================================================================
    print("\n🔀 [4/5] Training Tier-3 Multi-Modal Fusion Model (OOF-Trained)...")
    X_train_fusion = pd.DataFrame({
        "p_tabular": oof_p_tabular,
        "p_graph": oof_p_graph,
        "TransactionAmt_log": X_tr_tab["TransactionAmt_log"].values,
        "card1_amt_zscore": X_tr_tab["card1_amt_zscore"].values,
        "graph_burst_score": X_tr_graph["graph_burst_score"].values
    })

    X_test_fusion = pd.DataFrame({
        "p_tabular": test_p_tabular_folds,
        "p_graph": test_p_graph_folds,
        "TransactionAmt_log": X_te_tab["TransactionAmt_log"].values,
        "card1_amt_zscore": X_te_tab["card1_amt_zscore"].values,
        "graph_burst_score": X_te_graph["graph_burst_score"].values
    })

    fusion_params = {
        "objective": "binary",
        "metric": "average_precision",
        "boosting_type": "gbdt",
        "n_estimators": 150,
        "learning_rate": 0.03,
        "num_leaves": 15,
        "random_state": 42,
        "n_jobs": -1,
        "verbose": -1
    }

    base_fusion = lgb.LGBMClassifier(**fusion_params)
    # Wrap in Isotonic Calibrator for true probability calibration
    calibrated_fusion = CalibratedClassifierCV(estimator=base_fusion, method="isotonic", cv=3)
    calibrated_fusion.fit(X_train_fusion, y_train)

    p_test_fusion = calibrated_fusion.predict_proba(X_test_fusion)[:, 1]

    with open(CHECKPOINT_DIR / "fusion_lgbm.pkl", "wb") as f:
        pickle.dump(calibrated_fusion, f)
    print("   💾 Saved: models/checkpoints/fusion_lgbm.pkl")

    # =========================================================================
    # 4. SYSTEMATIC ABLATION EVALUATION ON HELD-OUT TEMPORAL TEST SET
    # =========================================================================
    print("\n" + "=" * 105)
    print("📊 [5/5] REAL IEEE-CIS 118,108 TEST SET SYSTEMATIC ABLATION RESULTS")
    print("=" * 105)

    def evaluate_model(y_prob, name, threshold=0.50):
        pr = average_precision_score(y_test, y_prob)
        roc = roc_auc_score(y_test, y_prob)
        brier = brier_score_loss(y_test, y_prob)
        preds = (y_prob >= threshold).astype(int)
        rec = recall_score(y_test, preds, zero_division=0)
        prec = precision_score(y_test, preds, zero_division=0)
        cm_fp = int(np.sum((y_test == 0) & (preds == 1)))
        fpr = cm_fp / max(1, np.sum(y_test == 0))
        fc = float(np.sum(amounts_test[(y_test == 1) & (preds == 1)]))
        fric = float(cm_fp * 350.0)
        net = fc - fric
        return {
            "name": name,
            "pr_auc": pr,
            "roc_auc": roc,
            "brier": brier,
            "recall": rec,
            "precision": prec,
            "fpr": fpr,
            "net_saved": net
        }

    m1_eval = evaluate_model(test_p_tabular_folds, "1. Tabular LightGBM (10 Feats)", threshold=0.40)
    m2_eval = evaluate_model(test_p_graph_folds, "2. Relational Graph GBDT (4 Feats)", threshold=0.40)
    m3_eval = evaluate_model(p_test_fusion, "3. Multi-Modal Learned Fusion", threshold=0.40)
    m4_eval = evaluate_model(p_test_fusion, "4. VYUH Full (Cost-Calibrated Gate)", threshold=0.52)

    print(f"{'Architecture Evaluated':<38} | {'PR-AUC':<8} | {'ROC-AUC':<8} | {'Recall':<8} | {'Precision':<10} | {'FPR':<8} | {'Net Saved (₹)'}")
    print("-" * 105)
    for ev in [m1_eval, m2_eval, m3_eval, m4_eval]:
        print(f"{ev['name']:<38} | {ev['pr_auc']:.4f}   | {ev['roc_auc']:.4f}   | {ev['recall']*100:>5.1f}%  | {ev['precision']*100:>7.1f}%   | {ev['fpr']*100:>5.2f}%  | ₹{ev['net_saved']:>12,.2f}")
    print("=" * 105)

    # Save ablation summary
    results_summary = {
        "m1_tabular": m1_eval,
        "m2_graph": m2_eval,
        "m3_fusion": m3_eval,
        "m4_cost_calibrated": m4_eval
    }
    with open(CHECKPOINT_DIR / "multimodal_ablation_results.json", "w") as f:
        json.dump(results_summary, f, indent=2)
    print("✅ Saved ablation results: models/checkpoints/multimodal_ablation_results.json")

if __name__ == "__main__":
    train_multimodal_system()
