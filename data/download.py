#!/usr/bin/env python3
"""
VYUH — Dataset Download Script (kagglehub + KGAT Token)
Downloads IEEE-CIS Fraud Detection + Elliptic Bitcoin datasets.
"""

import os
import sys
import shutil
import zipfile
from pathlib import Path

# Set KGAT token before any kaggle imports
os.environ["KAGGLE_API_TOKEN"] = "KGAT_206c7f9cf69143743f169dad80e8d56a"

import kagglehub

PROJECT_ROOT = Path(__file__).parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)


def download_ieee_cis():
    """Download IEEE-CIS Fraud Detection dataset using kagglehub."""
    ieee_dir = RAW_DIR / "ieee-cis"
    ieee_dir.mkdir(parents=True, exist_ok=True)

    # Check if already downloaded
    if (ieee_dir / "train_transaction.csv").exists():
        size_mb = (ieee_dir / "train_transaction.csv").stat().st_size / (1024 * 1024)
        print(f"✅ IEEE-CIS train_transaction.csv already exists ({size_mb:.0f} MB)")
        return True

    print()
    print("=" * 60)
    print("📦 Downloading IEEE-CIS Fraud Detection Dataset")
    print("   Source: Kaggle Competition (Vesta Corp)")
    print("   590,540 real transactions · 394 features")
    print("=" * 60)

    try:
        # kagglehub downloads competition data to a cache dir
        print("⬇️  Downloading via kagglehub (this may take a few minutes)...")
        cached_path = kagglehub.competition_download("ieee-fraud-detection")
        cached_path = Path(cached_path)
        print(f"📂 Downloaded to cache: {cached_path}")

        # Copy train files to our data directory
        for pattern in ["*train_transaction*", "*train_identity*"]:
            for src in cached_path.rglob(pattern):
                if src.is_file():
                    dest = ieee_dir / src.name
                    # Handle .csv.zip or .csv
                    if src.suffix == ".zip":
                        print(f"   Extracting: {src.name}")
                        with zipfile.ZipFile(src, 'r') as zf:
                            zf.extractall(ieee_dir)
                    else:
                        print(f"   Copying: {src.name} → {dest}")
                        shutil.copy2(str(src), str(dest))

        # If no individual train files found, copy everything
        if not (ieee_dir / "train_transaction.csv").exists():
            print("   Copying all CSV files from cache...")
            for src in cached_path.rglob("*.csv"):
                if "train" in src.name.lower():
                    dest = ieee_dir / src.name
                    print(f"   Copying: {src.name}")
                    shutil.copy2(str(src), str(dest))

        # Verify
        txn = ieee_dir / "train_transaction.csv"
        if txn.exists():
            size_mb = txn.stat().st_size / (1024 * 1024)
            print(f"✅ train_transaction.csv: {size_mb:.0f} MB")
            return True
        else:
            # List what's in cache to debug
            print("⚠️  train_transaction.csv not found. Cache contents:")
            for f in cached_path.rglob("*"):
                if f.is_file():
                    print(f"   {f.relative_to(cached_path)} ({f.stat().st_size / 1024 / 1024:.1f} MB)")
            return False

    except Exception as e:
        print(f"❌ Download failed: {e}")
        print()
        if "403" in str(e) or "accept" in str(e).lower():
            print("🔧 You need to accept competition rules first:")
            print("   https://www.kaggle.com/c/ieee-fraud-detection/rules")
        return False


def download_elliptic():
    """Download Elliptic Bitcoin dataset using kagglehub."""
    elliptic_dir = RAW_DIR / "elliptic"
    elliptic_dir.mkdir(parents=True, exist_ok=True)

    # Check if already downloaded
    feat_files = list(elliptic_dir.glob("*features*"))
    if feat_files:
        print(f"✅ Elliptic dataset already exists ({len(list(elliptic_dir.glob('*.csv')))} CSV files)")
        return True

    print()
    print("=" * 60)
    print("📦 Downloading Elliptic Bitcoin Dataset")
    print("   Source: Weber et al. (KDD '19)")
    print("   203,769 transactions · 49 timesteps")
    print("=" * 60)

    try:
        print("⬇️  Downloading via kagglehub...")
        cached_path = kagglehub.dataset_download("ellipticco/elliptic-data-set")
        cached_path = Path(cached_path)
        print(f"📂 Downloaded to cache: {cached_path}")

        # Copy CSV files to our data directory
        csv_count = 0
        for src in cached_path.rglob("*.csv"):
            dest = elliptic_dir / src.name
            print(f"   Copying: {src.name}")
            shutil.copy2(str(src), str(dest))
            csv_count += 1

        if csv_count == 0:
            # Maybe it's in zip format
            for src in cached_path.rglob("*.zip"):
                print(f"   Extracting: {src.name}")
                with zipfile.ZipFile(src, 'r') as zf:
                    zf.extractall(elliptic_dir)
                csv_count += 1

        # Flatten any nested directories
        for sub in list(elliptic_dir.iterdir()):
            if sub.is_dir():
                for f in sub.rglob("*.csv"):
                    shutil.move(str(f), str(elliptic_dir / f.name))
                shutil.rmtree(sub, ignore_errors=True)

        # Verify
        csv_files = list(elliptic_dir.glob("*.csv"))
        print(f"✅ Elliptic: {len(csv_files)} CSV files")
        for f in sorted(csv_files):
            size_mb = f.stat().st_size / (1024 * 1024)
            print(f"   {f.name}: {size_mb:.1f} MB")

        return len(csv_files) >= 2

    except Exception as e:
        print(f"❌ Download failed: {e}")
        return False


def verify_all():
    """Final verification with data quality checks."""
    print()
    print("=" * 60)
    print("🔍 FINAL VERIFICATION & DATA QUALITY CHECK")
    print("=" * 60)

    import pandas as pd
    all_good = True

    # === IEEE-CIS ===
    ieee_txn = RAW_DIR / "ieee-cis" / "train_transaction.csv"
    ieee_id = RAW_DIR / "ieee-cis" / "train_identity.csv"

    if ieee_txn.exists():
        df = pd.read_csv(ieee_txn, nrows=10)
        # Count total rows efficiently
        with open(ieee_txn, 'r') as f:
            total_rows = sum(1 for _ in f) - 1
        fraud_rate = None
        if "isFraud" in df.columns:
            # Sample fraud rate from first 100k rows
            sample = pd.read_csv(ieee_txn, usecols=["isFraud"], nrows=100000)
            fraud_rate = sample["isFraud"].mean() * 100
        print(f"✅ IEEE-CIS Transactions:")
        print(f"   Rows: {total_rows:,}")
        print(f"   Columns: {len(df.columns)}")
        if fraud_rate:
            print(f"   Fraud Rate (sample): {fraud_rate:.1f}%")
        print(f"   Key columns: TransactionDT, TransactionAmt, card1-6, addr1-2")
        print(f"   Label: isFraud ({'found ✅' if 'isFraud' in df.columns else 'MISSING ❌'})")
    else:
        print("❌ IEEE-CIS train_transaction.csv MISSING")
        all_good = False

    if ieee_id.exists():
        df_id = pd.read_csv(ieee_id, nrows=5)
        print(f"✅ IEEE-CIS Identity: {len(df_id.columns)} columns")
        device_cols = [c for c in df_id.columns if 'device' in c.lower() or c.startswith('id_')]
        print(f"   Device/ID columns: {len(device_cols)}")
    else:
        print("⚠️  IEEE-CIS Identity file missing (graph features will be limited)")

    # === Elliptic ===
    elliptic_dir = RAW_DIR / "elliptic"
    feat_files = list(elliptic_dir.glob("*features*"))
    class_files = list(elliptic_dir.glob("*classes*"))
    edge_files = list(elliptic_dir.glob("*edgelist*"))

    if feat_files:
        df_feat = pd.read_csv(feat_files[0], header=None, nrows=5)
        print(f"✅ Elliptic Features: {len(df_feat.columns)} columns")
    else:
        print("❌ Elliptic features MISSING")
        all_good = False

    if class_files:
        df_cls = pd.read_csv(class_files[0])
        print(f"✅ Elliptic Classes: {len(df_cls)} rows")
    if edge_files:
        df_edge = pd.read_csv(edge_files[0])
        print(f"✅ Elliptic Edges: {len(df_edge):,} edges")

    # Total disk
    total_bytes = 0
    for d in [RAW_DIR / "ieee-cis", RAW_DIR / "elliptic"]:
        if d.exists():
            for f in d.rglob("*"):
                if f.is_file():
                    total_bytes += f.stat().st_size

    print()
    print(f"💾 Total disk usage: {total_bytes / (1024**2):.0f} MB")
    print()
    if all_good:
        print("🎉 ══════════════════════════════════════════════════")
        print("🎉  ALL DATASETS VERIFIED — VYUH TRAINING CAN BEGIN!")
        print("🎉 ══════════════════════════════════════════════════")
    else:
        print("⚠️  Some datasets missing. Check errors above.")

    return all_good


if __name__ == "__main__":
    print()
    print("╔══════════════════════════════════════════════════════╗")
    print("║   VYUH (व्यूह) — Dataset Download & Setup           ║")
    print("║   Razorpay AI Buildathon 2026 · Track 02            ║")
    print("╠══════════════════════════════════════════════════════╣")
    print("║   Dataset 1: IEEE-CIS Fraud Detection (~150 MB)     ║")
    print("║   Dataset 2: Elliptic Bitcoin Dataset (~35 MB)      ║")
    print("║   Total Internet: ~185 MB                           ║")
    print("╚══════════════════════════════════════════════════════╝")

    ieee_ok = download_ieee_cis()
    elliptic_ok = download_elliptic()
    verify_all()
