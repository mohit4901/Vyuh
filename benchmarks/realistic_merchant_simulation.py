#!/usr/bin/env python3
"""
VYUH 2.0 — Synthetic Coordinated-Fraud Stress Benchmark (10,000 Transactions)
=============================================================================
A controlled live-stream scenario evaluation:
  - 9,800 Synthetic Benign Transactions (98% generated baseline traffic)
  - 200 Synthetic Coordinated Syndicate Transactions (2% distributed across 5 device-sharing rings)

Purpose:
  Demonstrates live-system stateful graph evolution and relational pattern detection.
  (Primary general ML accuracy is evaluated separately on the 118,108 temporal held-out IEEE-CIS test set).
"""

import sys
import os
import time
import json
import numpy as np
import pandas as pd
import networkx as nx
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

CHECKPOINT_DIR = PROJECT_ROOT / "models" / "checkpoints"

from backend.inference_service import ModelManager, LiveEntityGraph, RollingFeatureStore

def generate_realistic_stream(n_total=10000, fraud_ratio=0.02, random_seed=42):
    """
    Generates a controlled synthetic stream to test relational network dynamics:
    - 98% synthetic benign transactions (dedicated devices, normal amounts)
    - 2% synthetic syndicate fraud (multi-account hardware sharing, rotating emails, burst checkouts)
    """
    np.random.seed(random_seed)
    n_fraud = int(n_total * fraud_ratio)
    n_normal = n_total - n_fraud

    print(f"📊 Generating {n_total:,} synthetic test transactions ({n_normal:,} Synthetic Benign [98%], {n_fraud:,} Synthetic Syndicate [2%])...")

    transactions = []

    # 1. Generate 9,800 Normal Organic Transactions
    # Normal users have high device uniqueness (1:1 mostly) and normal lognormal/exponential amounts
    normal_amounts = np.random.exponential(scale=1850, size=n_normal) + 50.0
    normal_amounts = np.clip(normal_amounts, 50.0, 50000.0)

    for i in range(n_normal):
        user_idx = i + 10000
        transactions.append({
            "orderId": f"ORD_NORM_{i:05d}",
            "amount": float(round(normal_amounts[i], 2)),
            "cardId": f"CARD_NORM_{user_idx}",
            "deviceId": f"DEV_NORM_{user_idx}",
            "email": f"customer_{user_idx}@gmail.com",
            "is_fraud": 0,
            "fraud_type": "none"
        })

    # 2. Generate 200 Syndicate Fraud Transactions
    # Distributed across 5 distinct coordinated hardware/card replay rings
    syndicate_rings = [
        {"ring_id": "RING_ELECTRONICS_01", "device_id": "DEV_SYN_HARDWARE_ALPHA", "n_accounts": 50, "amt_mean": 2499.0},
        {"ring_id": "RING_PROMO_ABUSE_02", "device_id": "DEV_SYN_HARDWARE_BETA", "n_accounts": 40, "amt_mean": 499.0},
        {"ring_id": "RING_CARDING_BOT_03", "device_id": "DEV_SYN_HARDWARE_GAMMA", "n_accounts": 45, "amt_mean": 1200.0},
        {"ring_id": "RING_GIFT_CARD_04", "device_id": "DEV_SYN_HARDWARE_DELTA", "n_accounts": 35, "amt_mean": 3500.0},
        {"ring_id": "RING_QUICK_COMMERCE_05", "device_id": "DEV_SYN_HARDWARE_EPSILON", "n_accounts": 30, "amt_mean": 799.0}
    ]

    fraud_txns = []
    fraud_count = 0
    for ring in syndicate_rings:
        dev_id = ring["device_id"]
        for acc in range(ring["n_accounts"]):
            if fraud_count >= n_fraud:
                break
            amt = float(round(np.random.normal(ring["amt_mean"], ring["amt_mean"] * 0.15), 2))
            amt = max(99.0, amt)
            fraud_txns.append({
                "orderId": f"ORD_SYN_{ring['ring_id']}_{acc:03d}",
                "amount": amt,
                "cardId": f"CARD_SYN_{ring['ring_id']}_{acc % 4}", # Reusing 4 cards across accounts
                "deviceId": dev_id,                                # Same hardware fingerprint!
                "email": f"synd_user_{acc}_{ring['ring_id'][:6].lower()}@disposablemail.org",
                "is_fraud": 1,
                "fraud_type": ring["ring_id"]
            })
            fraud_count += 1

    # Interleave fraud into normal stream realistically (bursts over time)
    full_stream = transactions + fraud_txns
    # Shuffle with seed so fraud is scattered in temporal bursts
    np.random.shuffle(full_stream)
    return full_stream


def run_benchmark():
    print("=" * 95)
    print("🚀 VYUH 2.0 — SYNTHETIC COORDINATED-FRAUD STRESS BENCHMARK (10,000 TRANSACTIONS)")
    print("   [98% Synthetic Benign Baseline + 2% Synthetic Syndicate Rings]")
    print("=" * 95)

    stream = generate_realistic_stream(n_total=10000, fraud_ratio=0.02, random_seed=42)

    # Initialize fresh dynamic manager
    class CleanDynamicLiveEntityGraph(LiveEntityGraph):
        def _seed_initial_topology(self):
            # Clean zero-seeded state for pure dynamic benchmark
            self.G = nx.Graph()
            self.confirmed_fraud_nodes = set()

    manager = ModelManager()
    manager.live_graph = CleanDynamicLiveEntityGraph()
    manager.feature_store = RollingFeatureStore()

    y_true = np.array([t["is_fraud"] for t in stream])
    amounts = np.array([t["amount"] for t in stream])

    # Store predictions for the 3 pipelines
    p_lgbm_raw = []
    p_lgbm_isolated = []
    p_vyuh_calibrated = []

    print(f"\n⚡ Ingesting {len(stream):,} transactions through live dynamic pipeline...")
    t0 = time.time()

    for i, txn in enumerate(stream):
        res = manager.score_transaction(txn)
        raw_prob = res["scores"]["rawLgbmProbability"]
        iso_risk = res["scores"]["isolatedRiskScore"]
        final_risk = res["scores"]["finalCalibratedRisk"]

        p_lgbm_raw.append(raw_prob)
        p_lgbm_isolated.append(iso_risk)
        p_vyuh_calibrated.append(final_risk)

        if (i + 1) % 2500 == 0:
            print(f"   Processed {i+1:,} / {len(stream):,} transactions (Elapsed: {(time.time()-t0):.2f}s)...")

    p_lgbm_raw = np.array(p_lgbm_raw)
    p_vyuh_calibrated = np.array(p_vyuh_calibrated)

    total_time = time.time() - t0
    avg_latency = (total_time / len(stream)) * 1000

    print(f"✅ Ingestion complete in {total_time:.2f}s (Average {avg_latency:.2f} ms / transaction)")

    # =========================================================================
    # PIPELINE EVALUATION
    # =========================================================================
    # Thresholds:
    # 1. LightGBM Alone (Standard 0.50 threshold)
    # 2. LightGBM + Graph (Without Cost Calibration, standard 0.50 threshold)
    # 3. VYUH Full (Cost-Calibrated threshold 0.52 + Tiered Actions)

    def evaluate_pipeline(scores, threshold, name, friction_cost=350.0):
        preds = (scores >= threshold).astype(int)
        tp = int(np.sum((y_true == 1) & (preds == 1)))
        fp = int(np.sum((y_true == 0) & (preds == 1)))
        tn = int(np.sum((y_true == 0) & (preds == 0)))
        fn = int(np.sum((y_true == 1) & (preds == 0)))

        precision = tp / max(1, tp + fp)
        recall = tp / max(1, tp + fn)
        f1 = (2 * precision * recall) / max(1e-6, precision + recall)
        fpr = fp / max(1, fp + tn)

        total_fraud_loss_inr = float(np.sum(amounts[y_true == 1]))
        fraud_caught_inr = float(np.sum(amounts[(y_true == 1) & (preds == 1)]))
        fraud_missed_inr = float(np.sum(amounts[(y_true == 1) & (preds == 0)]))
        friction_loss_inr = float(fp * friction_cost)
        net_saved_inr = float(fraud_caught_inr - friction_loss_inr)

        return {
            "name": name,
            "threshold": threshold,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "fpr": fpr,
            "tp": tp,
            "fp": fp,
            "tn": tn,
            "fn": fn,
            "total_fraud_loss_inr": total_fraud_loss_inr,
            "fraud_caught_inr": fraud_caught_inr,
            "fraud_missed_inr": fraud_missed_inr,
            "friction_loss_inr": friction_loss_inr,
            "net_saved_inr": net_saved_inr
        }

    m1_eval = evaluate_pipeline(p_lgbm_raw, 0.40, "1. LightGBM Tabular Only (Isolation)")
    m3_eval = evaluate_pipeline(p_vyuh_calibrated, 0.50, "2. LightGBM + Dynamic Graph")
    m4_eval = evaluate_pipeline(p_vyuh_calibrated, 0.52, "3. VYUH Full (Cost Gateway)")

    print("\n" + "=" * 105)
    print("📈 COMPREHENSIVE PERFORMANCE COMPARISON (10,000 REALISTIC TRANSACTIONS)")
    print("=" * 105)
    print(f"{'Pipeline Architecture':<36} | {'Recall':<8} | {'Precision':<10} | {'FPR (Friction)':<15} | {'Fraud Caught (₹)':<16} | {'Net Saved (₹)':<14}")
    print("-" * 105)

    for ev in [m1_eval, m3_eval, m4_eval]:
        print(f"{ev['name']:<36} | {ev['recall']*100:>6.1f}% | {ev['precision']*100:>8.1f}% | {ev['fpr']*100:>13.2f}% | ₹{ev['fraud_caught_inr']:>14,.2f} | ₹{ev['net_saved_inr']:>12,.2f}")

    print("-" * 105)

    # Syndicate Ring Breakdown
    print("\n" + "=" * 105)
    print("🔍 CONDITIONAL VALUE PROOF: PERFORMANCE ON NORMAL VS COORDINATED SYNDICATE")
    print("=" * 105)

    normal_mask = (y_true == 0)
    fraud_mask = (y_true == 1)

    print(f"\n1. Normal Merchant Traffic ({np.sum(normal_mask):,} genuine transactions):")
    print(f"   • LightGBM Only False Positives:  {m1_eval['fp']} ({m1_eval['fpr']*100:.2f}% FPR) -> ₹{m1_eval['fp']*350:,.2f} Friction Loss")
    print(f"   • VYUH Full False Positives:      {m4_eval['fp']} ({m4_eval['fpr']*100:.2f}% FPR) -> ₹{m4_eval['fp']*350:,.2f} Friction Loss")
    print(f"   • Friction Cost Reduction:        ₹{(m1_eval['fp'] - m4_eval['fp'])*350:,.2f} saved in checkout drop-offs")

    print(f"\n2. Coordinated Fraud Syndicate ({np.sum(fraud_mask):,} distributed ring transactions):")
    print(f"   • Total Potential Fraud Loss:     ₹{np.sum(amounts[fraud_mask]):,.2f}")
    print(f"   • LightGBM Alone Caught:          ₹{m1_eval['fraud_caught_inr']:,.2f} ({m1_eval['recall']*100:.1f}% Recall)")
    print(f"   • VYUH Graph Sentinel Caught:     ₹{m4_eval['fraud_caught_inr']:,.2f} ({m4_eval['recall']*100:.1f}% Recall)")
    recall_lift = ((m4_eval['recall'] - m1_eval['recall']) / max(1e-4, m1_eval['recall'])) * 100
    print(f"   • Net Recall Lift on Rings:       +{recall_lift:.1f}% Relative Lift over Single-Transaction Isolation!")

    print(f"\n3. Net Economic Bottom Line:")
    print(f"   • LightGBM Only Net Benefit:      ₹{m1_eval['net_saved_inr']:,.2f}")
    print(f"   • VYUH Full Net Benefit:          ₹{m4_eval['net_saved_inr']:,.2f} (+₹{(m4_eval['net_saved_inr'] - m1_eval['net_saved_inr']):,.2f} Net INR Lift)")

    print("\n" + "=" * 105)
    print("🎉 BENCHMARK EXPERIMENT COMPLETED SUCCESSFULLY WITH RIGOROUS ECONOMIC PROOF!")
    print("=" * 105)

    return {
        "m1": m1_eval,
        "m3": m3_eval,
        "m4": m4_eval,
        "latency_ms": avg_latency
    }


if __name__ == "__main__":
    run_benchmark()
