#!/usr/bin/env python3
"""
VYUH — Stage 1 LightGBM Baseline Classifier (Model M1)
======================================================
Trains a high-capacity LightGBM ensemble on the strict temporal train set (472k rows)
and evaluates on the unseen held-out temporal test set (118k rows).

Reports honest metrics:
  - PR-AUC (Average Precision) — primary metric for imbalanced fraud detection
  - ROC-AUC
  - Precision, Recall, F1 across decision thresholds
  - Confusion Matrix
  - Top 20 Most Important Features
"""

import os
import sys
import pickle
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.metrics import (
    average_precision_score,
    roc_auc_score,
    precision_recall_curve,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score
)

warnings.filterwarnings("ignore")

PROJECT_ROOT = Path(__file__).parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
CHECKPOINT_DIR = PROJECT_ROOT / "models" / "checkpoints"
CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)


def load_data():
    """Load preprocessed temporal train and test sets."""
    print("📂 Loading preprocessed datasets...")
    train_df = pd.read_pickle(PROCESSED_DIR / "train.pkl")
    test_df = pd.read_pickle(PROCESSED_DIR / "test.pkl")

    feature_cols = [c for c in train_df.columns if c not in ["isFraud", "TransactionID"]]
    
    X_train = train_df[feature_cols]
    y_train = train_df["isFraud"].astype(int)
    
    X_test = test_df[feature_cols]
    y_test = test_df["isFraud"].astype(int)
    
    print(f"   Train features shape: {X_train.shape} | Positive (Fraud) cases: {y_train.sum():,} ({y_train.mean()*100:.2f}%)")
    print(f"   Test features shape:  {X_test.shape} | Positive (Fraud) cases: {y_test.sum():,} ({y_test.mean()*100:.2f}%)")
    
    return X_train, y_train, X_test, y_test, feature_cols


def train_lgbm(X_train, y_train, X_test, y_test, feature_cols):
    """Train high-capacity LightGBM model with early stopping."""
    print("\n🚀 Training Stage-1 LightGBM Classifier (Model M1)...")
    
    # Calculate scale_pos_weight for class imbalance (~3.5% fraud)
    neg_count = (y_train == 0).sum()
    pos_count = (y_train == 1).sum()
    scale_pos_weight = neg_count / max(1, pos_count)
    print(f"   Calculated scale_pos_weight: {scale_pos_weight:.2f}")

    # Create LightGBM datasets
    # Split train further into train (85%) and validation (15%) temporally for early stopping
    val_split_idx = int(len(X_train) * 0.85)
    X_tr, y_tr = X_train.iloc[:val_split_idx], y_train.iloc[:val_split_idx]
    X_val, y_val = X_train.iloc[val_split_idx:], y_train.iloc[val_split_idx:]
    
    dtrain = lgb.Dataset(X_tr, label=y_tr)
    dval = lgb.Dataset(X_val, label=y_val, reference=dtrain)
    
    params = {
        "objective": "binary",
        "metric": "average_precision",  # PR-AUC
        "boosting_type": "gbdt",
        "n_estimators": 2000,
        "learning_rate": 0.03,
        "num_leaves": 127,
        "max_depth": 10,
        "min_child_samples": 50,
        "subsample": 0.8,
        "colsample_bytree": 0.7,
        "reg_alpha": 0.1,
        "reg_lambda": 1.0,
        "scale_pos_weight": scale_pos_weight,
        "random_state": 42,
        "n_jobs": -1,
        "verbose": -1
    }
    
    callbacks = [
        lgb.early_stopping(stopping_rounds=50, verbose=False),
        lgb.log_evaluation(period=200)
    ]
    
    model = lgb.LGBMClassifier(**params)
    model.fit(
        X_tr, y_tr,
        eval_set=[(X_val, y_val)],
        eval_metric="average_precision",
        callbacks=callbacks
    )
    
    print(f"   ✅ Best iteration: {model.best_iteration_}")
    
    # Save model artifact
    model_path = CHECKPOINT_DIR / "stage1_lgbm.pkl"
    with open(model_path, "wb") as f:
        pickle.dump(model, f)
    print(f"   💾 Saved model checkpoint to: {model_path}")
    
    return model


def evaluate_model(model, X_test, y_test, feature_cols):
    """Honest evaluation on held-out temporal test set."""
    print("\n" + "=" * 60)
    print("📊 STAGE 1 (MODEL M1) — HELD-OUT TEST EVALUATION")
    print("=" * 60)
    
    # Predict probabilities
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    
    # Metrics
    pr_auc = average_precision_score(y_test, y_pred_proba)
    roc_auc = roc_auc_score(y_test, y_pred_proba)
    
    print(f"\n🌟 Primary Metric: PR-AUC (Average Precision) = {pr_auc:.4f}")
    print(f"🌟 Secondary Metric: ROC-AUC = {roc_auc:.4f}")
    
    # Threshold sweep to analyze precision vs recall tradeoff
    print("\n📈 Threshold Performance Tradeoff:")
    print(f"{'Threshold':>10} | {'Precision':>10} | {'Recall':>10} | {'F1-Score':>10} | {'FP Count':>10} | {'FN Count':>10}")
    print("-" * 72)
    
    thresholds = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    best_f1 = 0
    best_thresh = 0.5
    
    for th in thresholds:
        y_pred = (y_pred_proba >= th).astype(int)
        p = precision_score(y_test, y_pred, zero_division=0)
        r = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        cm = confusion_matrix(y_test, y_pred)
        fp = cm[0, 1]
        fn = cm[1, 0]
        
        if f1 > best_f1:
            best_f1 = f1
            best_thresh = th
            
        print(f"{th:>10.2f} | {p*100:>9.2f}% | {r*100:>9.2f}% | {f1:>10.4f} | {fp:>10,d} | {fn:>10,d}")
    
    print(f"\n⭐ Best F1-Score: {best_f1:.4f} at Threshold = {best_thresh:.2f}")
    
    # Feature Importance
    importances = model.feature_importances_
    feat_imp = pd.DataFrame({
        "feature": feature_cols,
        "importance": importances
    }).sort_values("importance", ascending=False)
    
    print("\n🔝 Top 15 Most Important Features:")
    for idx, row in feat_imp.head(15).iterrows():
        print(f"   {row['feature']:<30} : {row['importance']:.0f}")
        
    # Save evaluation summary to JSON
    results = {
        "model": "M1_LightGBM_Baseline",
        "pr_auc": float(pr_auc),
        "roc_auc": float(roc_auc),
        "best_threshold": float(best_thresh),
        "best_f1": float(best_f1),
        "top_features": feat_imp.head(20).to_dict(orient="records")
    }
    
    with open(CHECKPOINT_DIR / "m1_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n📄 Saved evaluation report to: {CHECKPOINT_DIR / 'm1_results.json'}")
    
    return results


def main():
    X_train, y_train, X_test, y_test, feature_cols = load_data()
    model = train_lgbm(X_train, y_train, X_test, y_test, feature_cols)
    evaluate_model(model, X_test, y_test, feature_cols)


if __name__ == "__main__":
    main()
