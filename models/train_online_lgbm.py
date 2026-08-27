#!/usr/bin/env python3
"""
VYUH 2.0 — Train Online LightGBM Micro-Classifier
=================================================
Trains a compact, ultra-low-latency online-computable LightGBM model:
Features:
  1. TransactionAmt (Amount in INR)
  2. TransactionAmt_log (log1p amount)
  3. hour_sin (Cyclical time)
  4. hour_cos (Cyclical time)
  5. is_night (Binary night flag)
  6. card1_amt_mean (Rolling mean amount on card)
  7. card1_amt_std (Rolling std amount on card)
  8. card1_amt_zscore (Rolling z-score of amount on card)
  9. card1_txn_count (Rolling transaction count on card)
  10. card1_unique_devices (Rolling unique devices on card)
  11. graph_device_shared_deg (Real-time device degree in dynamic graph)
  12. graph_card_shared_deg (Real-time card degree in dynamic graph)
  13. graph_burst_score (10-minute event velocity)
  14. graph_ring_size (Connected component cluster size)

Saves:
  models/checkpoints/online_lgbm.pkl
"""

import os
import sys
import pickle
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.metrics import average_precision_score, roc_auc_score, f1_score

warnings.filterwarnings("ignore")

PROJECT_ROOT = Path(__file__).parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
CHECKPOINT_DIR = PROJECT_ROOT / "models" / "checkpoints"
CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)


def build_online_dataset():
    print("📂 Loading datasets for Online LightGBM training...")
    train_df = pd.read_pickle(PROCESSED_DIR / "train.pkl")
    test_df = pd.read_pickle(PROCESSED_DIR / "test.pkl")
    train_graph = pd.read_pickle(PROCESSED_DIR / "train_graph_feats.pkl")
    test_graph = pd.read_pickle(PROCESSED_DIR / "test_graph_feats.pkl")

    def extract_features(df, graph_df):
        amt_series = df["TransactionAmt"].fillna(499.0)
        amt = amt_series.values
        amt_log = np.log1p(amt)
        h_sin = df["hour_sin"].fillna(0.0).values if "hour_sin" in df.columns else np.zeros(len(df))
        h_cos = df["hour_cos"].fillna(1.0).values if "hour_cos" in df.columns else np.ones(len(df))
        is_night = df["is_night"].fillna(0).values if "is_night" in df.columns else np.zeros(len(df))
        
        amt_mean = df["card1_amt_mean"].fillna(amt_series).values if "card1_amt_mean" in df.columns else amt
        amt_std = df["card1_amt_std"].fillna(100.0).values if "card1_amt_std" in df.columns else np.ones(len(df))*100.0
        zscore = df["card1_amt_zscore"].fillna(0.0).clip(-5.0, 10.0).values if "card1_amt_zscore" in df.columns else np.zeros(len(df))
        card_cnt = df["card1_txn_count"].fillna(1).clip(1, 500).values if "card1_txn_count" in df.columns else np.ones(len(df))
        uniq_dev = df["card1_unique_devices"].fillna(1).clip(1, 50).values if "card1_unique_devices" in df.columns else np.ones(len(df))

        dev_deg = graph_df["graph_device_shared_deg"].fillna(1).values
        card_deg = graph_df["graph_card_shared_deg"].fillna(1).values
        burst_vel = graph_df["graph_burst_score"].fillna(1.0).values
        ring_sz = graph_df["graph_ring_size"].fillna(1).values

        X = pd.DataFrame({
            "TransactionAmt": amt,
            "TransactionAmt_log": amt_log,
            "hour_sin": h_sin,
            "hour_cos": h_cos,
            "is_night": is_night,
            "card1_amt_mean": amt_mean,
            "card1_amt_std": amt_std,
            "card1_amt_zscore": zscore,
            "card1_txn_count": card_cnt,
            "card1_unique_devices": uniq_dev,
            "graph_device_shared_deg": dev_deg,
            "graph_card_shared_deg": card_deg,
            "graph_burst_score": burst_vel,
            "graph_ring_size": ring_sz
        })
        return X

    X_train = extract_features(train_df, train_graph)
    y_train = train_df["isFraud"].astype(int).values

    X_test = extract_features(test_df, test_graph)
    y_test = test_df["isFraud"].astype(int).values

    return X_train, y_train, X_test, y_test


def train_and_save():
    X_train, y_train, X_test, y_test = build_online_dataset()
    print(f"   Online Train Matrix: {X_train.shape} | Test Matrix: {X_test.shape}")

    val_idx = int(len(X_train) * 0.85)
    X_tr, y_tr = X_train.iloc[:val_idx], y_train[:val_idx]
    X_val, y_val = X_train.iloc[val_idx:], y_train[val_idx:]

    scale_pos_weight = (y_tr == 0).sum() / max(1, (y_tr == 1).sum())

    params = {
        "objective": "binary",
        "metric": "average_precision",
        "boosting_type": "gbdt",
        "n_estimators": 600,
        "learning_rate": 0.04,
        "num_leaves": 63,
        "max_depth": 7,
        "scale_pos_weight": scale_pos_weight,
        "random_state": 42,
        "n_jobs": -1,
        "verbose": -1
    }

    callbacks = [lgb.early_stopping(stopping_rounds=40, verbose=False)]
    model = lgb.LGBMClassifier(**params)
    model.fit(X_tr, y_tr, eval_set=[(X_val, y_val)], callbacks=callbacks)

    # Evaluate on held out test
    y_pred = model.predict_proba(X_test)[:, 1]
    pr_auc = average_precision_score(y_test, y_pred)
    roc_auc = roc_auc_score(y_test, y_pred)

    print(f"✅ Online LightGBM Model Trained ({X_train.shape[1]} Features)")
    print(f"   Held-out Test PR-AUC: {pr_auc:.4f} | ROC-AUC: {roc_auc:.4f}")

    out_path = CHECKPOINT_DIR / "online_lgbm.pkl"
    with open(out_path, "wb") as f:
        pickle.dump(model, f)
    print(f"💾 Saved Online GBDT to: {out_path}")


if __name__ == "__main__":
    train_and_save()
