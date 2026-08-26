#!/usr/bin/env python3
"""
VYUH — Feature Engineering & Temporal Split Pipeline
=====================================================
Loads raw IEEE-CIS data, merges transaction + identity tables,
engineers 60+ fraud-detection features, and creates a strict
temporal train/test split (80:20 by time) with zero data leakage.

Output:
  data/processed/train.pkl   — Training set (first 80% by TransactionDT)
  data/processed/test.pkl    — Held-out test set (last 20% by TransactionDT)
  data/processed/split_report.txt — Split verification report
"""

import os
import sys
import warnings
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder

warnings.filterwarnings("ignore")

PROJECT_ROOT = Path(__file__).parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "ieee-cis"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def load_and_merge():
    """Load and merge transaction + identity tables."""
    print("📂 Loading raw data...")
    
    txn = pd.read_csv(RAW_DIR / "train_transaction.csv")
    print(f"   Transactions: {len(txn):,} rows × {len(txn.columns)} cols")
    
    ident = pd.read_csv(RAW_DIR / "train_identity.csv")
    print(f"   Identity: {len(ident):,} rows × {len(ident.columns)} cols")
    
    # Left join on TransactionID (not all transactions have identity info)
    df = txn.merge(ident, on="TransactionID", how="left")
    print(f"   Merged: {len(df):,} rows × {len(df.columns)} cols")
    print(f"   Identity coverage: {ident['TransactionID'].isin(txn['TransactionID']).sum() / len(txn) * 100:.1f}%")
    
    return df


def temporal_split(df, train_ratio=0.80):
    """
    Strict temporal split based on TransactionDT.
    NO random splitting — this prevents future data leaking into training.
    """
    print(f"\n⏱️  Creating strict temporal split ({int(train_ratio*100)}:{int((1-train_ratio)*100)})...")
    
    # Sort by time
    df = df.sort_values("TransactionDT").reset_index(drop=True)
    
    split_idx = int(len(df) * train_ratio)
    split_time = df.iloc[split_idx]["TransactionDT"]
    
    train = df.iloc[:split_idx].copy()
    test = df.iloc[split_idx:].copy()
    
    # Verify zero leakage: max train time < min test time
    assert train["TransactionDT"].max() <= test["TransactionDT"].min(), \
        "DATA LEAKAGE DETECTED! Train data overlaps with test data in time!"
    
    print(f"   Train: {len(train):,} rows (time: {train['TransactionDT'].min()} → {train['TransactionDT'].max()})")
    print(f"   Test:  {len(test):,} rows (time: {test['TransactionDT'].min()} → {test['TransactionDT'].max()})")
    print(f"   Split point: TransactionDT = {split_time}")
    print(f"   Train fraud rate: {train['isFraud'].mean()*100:.2f}%")
    print(f"   Test fraud rate:  {test['isFraud'].mean()*100:.2f}%")
    print(f"   ✅ Zero temporal leakage verified!")
    
    return train, test


def engineer_features(df, is_train=True, encoders=None):
    """
    Engineer 60+ features for fraud detection.
    Features are designed to capture:
    1. Transaction-level anomalies (amount, time patterns)
    2. Entity-level aggregates (per card, device, email behavior)
    3. Velocity features (transaction frequency in time windows)
    4. Graph-ready link features (shared entity counts)
    """
    print(f"\n🔧 Engineering features ({'train' if is_train else 'test'})...")
    
    if encoders is None:
        encoders = {}
    
    # ==========================================
    # 1. TIME-BASED FEATURES
    # ==========================================
    print("   [1/6] Time-based features...")
    
    # Convert TransactionDT to interpretable time features
    # TransactionDT is seconds from a reference point
    START_DATE = pd.Timestamp("2017-11-30")  # Known reference for IEEE-CIS
    df["datetime"] = START_DATE + pd.to_timedelta(df["TransactionDT"], unit="s")
    df["hour"] = df["datetime"].dt.hour
    df["dayofweek"] = df["datetime"].dt.dayofweek
    df["dayofmonth"] = df["datetime"].dt.day
    df["month"] = df["datetime"].dt.month
    
    # Cyclical time encoding (prevents 23:00 being "far" from 00:00)
    df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
    df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)
    df["dow_sin"] = np.sin(2 * np.pi * df["dayofweek"] / 7)
    df["dow_cos"] = np.cos(2 * np.pi * df["dayofweek"] / 7)
    
    # Is weekend / night
    df["is_weekend"] = (df["dayofweek"] >= 5).astype(int)
    df["is_night"] = ((df["hour"] >= 22) | (df["hour"] <= 5)).astype(int)
    
    # ==========================================
    # 2. AMOUNT-BASED FEATURES
    # ==========================================
    print("   [2/6] Amount-based features...")
    
    df["TransactionAmt_log"] = np.log1p(df["TransactionAmt"])
    df["TransactionAmt_decimal"] = df["TransactionAmt"] - df["TransactionAmt"].astype(int)
    df["TransactionAmt_is_round"] = (df["TransactionAmt_decimal"] == 0).astype(int)
    
    # Amount bins
    df["amt_bin"] = pd.cut(df["TransactionAmt"], 
                           bins=[0, 10, 50, 100, 500, 1000, 5000, 50000],
                           labels=False)
    
    # ==========================================
    # 3. CARD-LEVEL AGGREGATE FEATURES
    # ==========================================
    print("   [3/6] Card-level aggregate features...")
    
    # Per-card statistics (critical for ring detection)
    for col in ["card1", "card2", "card3", "card5"]:
        if col in df.columns:
            card_stats = df.groupby(col)["TransactionAmt"].agg(["mean", "std", "count"])
            card_stats.columns = [f"{col}_amt_mean", f"{col}_amt_std", f"{col}_txn_count"]
            df = df.merge(card_stats, left_on=col, right_index=True, how="left")
            
            # Amount deviation from card's mean (anomaly signal)
            df[f"{col}_amt_zscore"] = (
                (df["TransactionAmt"] - df[f"{col}_amt_mean"]) / 
                df[f"{col}_amt_std"].clip(lower=0.01)
            )
    
    # ==========================================
    # 4. EMAIL DOMAIN FEATURES
    # ==========================================
    print("   [4/6] Email domain features...")
    
    for col in ["P_emaildomain", "R_emaildomain"]:
        if col in df.columns:
            # Extract top-level domain
            df[f"{col}_tld"] = df[col].fillna("missing").apply(
                lambda x: x.split(".")[-1] if isinstance(x, str) else "missing"
            )
            # Email provider (gmail, yahoo, hotmail, etc.)
            df[f"{col}_provider"] = df[col].fillna("missing").apply(
                lambda x: x.split(".")[0] if isinstance(x, str) else "missing"
            )
            # Is free email provider
            free_providers = ["gmail", "yahoo", "hotmail", "outlook", "aol", "mail", "protonmail"]
            df[f"{col}_is_free"] = df[f"{col}_provider"].isin(free_providers).astype(int)
            
            # Email domain frequency (rare domains are suspicious)
            domain_freq = df[col].value_counts(normalize=True).to_dict()
            df[f"{col}_freq"] = df[col].map(domain_freq).fillna(0)
    
    # Email domain mismatch (P != R → suspicious)
    if "P_emaildomain" in df.columns and "R_emaildomain" in df.columns:
        df["email_domain_mismatch"] = (
            df["P_emaildomain"].fillna("") != df["R_emaildomain"].fillna("")
        ).astype(int)
    
    # ==========================================
    # 5. DEVICE & IDENTITY FEATURES
    # ==========================================
    print("   [5/6] Device & identity features...")
    
    if "DeviceType" in df.columns:
        df["DeviceType_filled"] = df["DeviceType"].fillna("unknown")
        df["has_device_info"] = df["DeviceInfo"].notna().astype(int)
    
    if "DeviceInfo" in df.columns:
        # Device brand extraction
        df["device_brand"] = df["DeviceInfo"].fillna("unknown").apply(
            lambda x: x.split("/")[0].split("-")[0].strip().lower() if isinstance(x, str) else "unknown"
        )
        # Device frequency (rare devices are suspicious)
        device_freq = df["DeviceInfo"].value_counts(normalize=True).to_dict()
        df["device_freq"] = df["DeviceInfo"].map(device_freq).fillna(0)
    
    # ID columns — count of non-null identity fields per transaction
    id_cols = [c for c in df.columns if c.startswith("id_")]
    if id_cols:
        df["id_fields_filled"] = df[id_cols].notna().sum(axis=1)
        df["id_fill_ratio"] = df["id_fields_filled"] / len(id_cols)
    
    # ==========================================
    # 6. INTERACTION & GRAPH-READY FEATURES
    # ==========================================
    print("   [6/6] Interaction & graph-ready features...")
    
    # Unique devices per card (ring signal: many devices = suspicious)
    if "DeviceInfo" in df.columns and "card1" in df.columns:
        card_device_count = df.groupby("card1")["DeviceInfo"].nunique().rename("card1_unique_devices")
        df = df.merge(card_device_count, left_on="card1", right_index=True, how="left")
        df["card1_unique_devices"] = df["card1_unique_devices"].fillna(0)
    
    # Unique cards per device (reverse ring signal)
    if "DeviceInfo" in df.columns and "card1" in df.columns:
        device_card_count = df.groupby("DeviceInfo")["card1"].nunique().rename("device_unique_cards")
        df = df.merge(device_card_count, left_on="DeviceInfo", right_index=True, how="left")
        df["device_unique_cards"] = df["device_unique_cards"].fillna(0)
    
    # Unique emails per card
    if "P_emaildomain" in df.columns and "card1" in df.columns:
        card_email_count = df.groupby("card1")["P_emaildomain"].nunique().rename("card1_unique_emails")
        df = df.merge(card_email_count, left_on="card1", right_index=True, how="left")
    
    # Unique addresses per card
    if "addr1" in df.columns and "card1" in df.columns:
        card_addr_count = df.groupby("card1")["addr1"].nunique().rename("card1_unique_addrs")
        df = df.merge(card_addr_count, left_on="card1", right_index=True, how="left")
    
    # ==========================================
    # LABEL ENCODING FOR CATEGORICAL COLUMNS
    # ==========================================
    print("   Encoding categoricals...")
    
    cat_cols = df.select_dtypes(include=["object"]).columns.tolist()
    # Remove datetime column
    cat_cols = [c for c in cat_cols if c != "datetime"]
    
    for col in cat_cols:
        if is_train:
            le = LabelEncoder()
            df[col] = le.fit_transform(df[col].astype(str))
            encoders[col] = le
        else:
            if col in encoders:
                le = encoders[col]
                # Handle unseen labels
                df[col] = df[col].astype(str)
                known_labels = set(le.classes_)
                df[col] = df[col].apply(lambda x: x if x in known_labels else "unknown")
                if "unknown" not in le.classes_:
                    le.classes_ = np.append(le.classes_, "unknown")
                df[col] = le.transform(df[col])
            else:
                df[col] = 0  # Fallback
    
    # Drop non-feature columns
    drop_cols = ["TransactionID", "datetime"]
    df = df.drop(columns=[c for c in drop_cols if c in df.columns], errors="ignore")
    
    # Fill remaining NaN with -999 (LightGBM handles this natively)
    df = df.fillna(-999)
    
    total_features = len([c for c in df.columns if c != "isFraud"])
    print(f"   ✅ Total features engineered: {total_features}")
    
    return df, encoders


def save_split_report(train, test):
    """Save a verification report for the temporal split."""
    report = []
    report.append("VYUH — Temporal Split Verification Report")
    report.append("=" * 50)
    report.append(f"Train rows: {len(train):,}")
    report.append(f"Test rows:  {len(test):,}")
    report.append(f"Train fraud rate: {train['isFraud'].mean()*100:.2f}%")
    report.append(f"Test fraud rate:  {test['isFraud'].mean()*100:.2f}%")
    report.append(f"Train time range: {train['TransactionDT'].min()} → {train['TransactionDT'].max()}")
    report.append(f"Test time range:  {test['TransactionDT'].min()} → {test['TransactionDT'].max()}")
    report.append(f"Temporal gap: {test['TransactionDT'].min() - train['TransactionDT'].max()} seconds")
    report.append(f"Total features: {len([c for c in train.columns if c not in ['isFraud']])}")
    report.append("")
    report.append("LEAKAGE CHECK: PASSED ✅" if train["TransactionDT"].max() <= test["TransactionDT"].min() else "LEAKAGE CHECK: FAILED ❌")
    
    report_text = "\n".join(report)
    (PROCESSED_DIR / "split_report.txt").write_text(report_text)
    print(f"\n📄 Split report saved to: data/processed/split_report.txt")
    return report_text


def main():
    print()
    print("╔══════════════════════════════════════════════════════╗")
    print("║   VYUH — Feature Engineering & Temporal Split       ║")
    print("║   IEEE-CIS → 60+ Features → 80:20 Temporal Split   ║")
    print("╚══════════════════════════════════════════════════════╝")
    
    # 1. Load and merge
    df = load_and_merge()
    
    # 2. Temporal split BEFORE feature engineering
    #    (prevents any aggregate statistics from leaking future info)
    train_raw, test_raw = temporal_split(df)
    
    # 3. Feature engineering on train
    train_fe, encoders = engineer_features(train_raw, is_train=True)
    
    # 4. Feature engineering on test (using train's encoders)
    test_fe, _ = engineer_features(test_raw, is_train=False, encoders=encoders)
    
    # 5. Align columns (ensure both have the same features)
    common_cols = list(set(train_fe.columns) & set(test_fe.columns))
    # Make sure isFraud is included
    if "isFraud" not in common_cols:
        common_cols.append("isFraud")
    common_cols = sorted(common_cols)
    
    train_final = train_fe[common_cols]
    test_final = test_fe[common_cols]
    
    print(f"\n📊 Final aligned columns: {len(common_cols)}")
    
    # 6. Save
    print("\n💾 Saving processed data...")
    train_final.to_pickle(PROCESSED_DIR / "train.pkl")
    test_final.to_pickle(PROCESSED_DIR / "test.pkl")
    
    # Save encoders for inference
    with open(PROCESSED_DIR / "encoders.pkl", "wb") as f:
        pickle.dump(encoders, f)
    
    train_mb = (PROCESSED_DIR / "train.pkl").stat().st_size / 1024 / 1024
    test_mb = (PROCESSED_DIR / "test.pkl").stat().st_size / 1024 / 1024
    print(f"   train.pkl: {train_mb:.0f} MB ({len(train_final):,} rows)")
    print(f"   test.pkl:  {test_mb:.0f} MB ({len(test_final):,} rows)")
    
    # 7. Save split report
    report = save_split_report(train_final, test_final)
    print()
    print(report)
    
    print()
    print("🎉 Feature engineering complete — ready for Stage-1 LightGBM training!")


if __name__ == "__main__":
    main()
