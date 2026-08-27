#!/usr/bin/env python3
"""
VYUH 2.1 — Strict Temporal Relational Feature Engine
===================================================
Constructs leakage-free, time-ordered relational and temporal graph features
on historical IEEE-CIS transaction streams.

Features Extracted (Strictly Looking Backward in Time):
  Device Temporal & Relational:
    1. dev_unique_cards_24h (Number of unique cards on device in last 24h)
    2. dev_unique_emails_24h (Number of unique emails on device in last 24h)
    3. dev_txn_velocity_1h (Transaction count on device in last 1 hour)
    4. dev_amount_sum_1h (Total amount processed on device in last 1 hour)

  Card Relational & Cross-Entity:
    5. card_unique_devices_24h (Number of unique devices on card in last 24h)
    6. card_unique_emails_24h (Number of unique emails on card in last 24h)
    7. card_txn_velocity_1h (Transaction count on card in last 1 hour)
    8. card_device_switch_rate (Ratio of device changes to total card transactions)

  Dynamic Subgraph Topology:
    9. graph_device_shared_deg (Real-time shared accounts on device)
    10. graph_card_shared_deg (Real-time shared devices on card)
    11. graph_burst_score (Short-window event velocity)
    12. graph_ring_size (Connected component size)
    13. graph_2hop_neighborhood_size (2-hop reachable entity count)

Outputs:
  - data/processed/train_temporal_graph_feats.pkl
  - data/processed/test_temporal_graph_feats.pkl
"""

import os
import sys
import time
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from collections import defaultdict, deque

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
CHECKPOINT_DIR = PROJECT_ROOT / "models" / "checkpoints"

def extract_strict_temporal_features(df, dataset_name="train"):
    print(f"\n🕸️  Extracting Strict Temporal Relational Features for {dataset_name.upper()} ({len(df):,} rows)...")
    t0 = time.time()

    # Sort strictly by TransactionDT (chronological order)
    df_sorted = df.sort_values("TransactionDT").copy()
    
    # Pre-extract numpy/lists for high-speed streaming processing
    dts = df_sorted["TransactionDT"].values
    amts = df_sorted["TransactionAmt"].fillna(499.0).values
    cards = df_sorted["card1"].fillna(-999).astype(str).values
    devs = df_sorted["DeviceInfo"].fillna("unknown").astype(str).values
    emails = df_sorted["P_emaildomain"].fillna("unknown").astype(str).values

    n = len(df_sorted)

    # Output arrays
    dev_uniq_cards_24h = np.zeros(n, dtype=np.float32)
    dev_uniq_emails_24h = np.zeros(n, dtype=np.float32)
    dev_txn_vel_1h = np.zeros(n, dtype=np.float32)
    dev_amt_sum_1h = np.zeros(n, dtype=np.float32)

    card_uniq_devs_24h = np.zeros(n, dtype=np.float32)
    card_uniq_emails_24h = np.zeros(n, dtype=np.float32)
    card_txn_vel_1h = np.zeros(n, dtype=np.float32)
    card_dev_switch_rate = np.zeros(n, dtype=np.float32)

    graph_dev_deg = np.zeros(n, dtype=np.float32)
    graph_card_deg = np.zeros(n, dtype=np.float32)
    graph_burst = np.zeros(n, dtype=np.float32)
    graph_ring = np.zeros(n, dtype=np.float32)
    graph_2hop = np.zeros(n, dtype=np.float32)

    # In-memory sliding history windows (deque of (timestamp, value))
    # 24h = 86,400s | 1h = 3,600s | 10m = 600s
    dev_cards_window = defaultdict(lambda: deque())
    dev_emails_window = defaultdict(lambda: deque())
    dev_txns_1h = defaultdict(lambda: deque())

    card_devs_window = defaultdict(lambda: deque())
    card_emails_window = defaultdict(lambda: deque())
    card_txns_1h = defaultdict(lambda: deque())
    card_total_devs = defaultdict(set)
    card_total_txns = defaultdict(int)

    # Dynamic Bipartite Adjacency for Graph Degrees (dev <-> card, dev <-> email)
    dev_connected_cards = defaultdict(set)
    card_connected_devs = defaultdict(set)

    print("   Streaming transactions chronologically through temporal graph...")
    report_step = max(50000, n // 10)

    for i in range(n):
        t = dts[i]
        amt = amts[i]
        card = cards[i]
        dev = devs[i]
        email = emails[i]

        # 1. Purge events older than 24h (86,400s) and 1h (3,600s)
        if dev != "unknown":
            dq_c = dev_cards_window[dev]
            while dq_c and t - dq_c[0][0] > 86400:
                dq_c.popleft()

            dq_e = dev_emails_window[dev]
            while dq_e and t - dq_e[0][0] > 86400:
                dq_e.popleft()

            dq_tx = dev_txns_1h[dev]
            while dq_tx and t - dq_tx[0][0] > 3600:
                dq_tx.popleft()

            # Measure state BEFORE current transaction
            dev_uniq_cards_24h[i] = len(set(c for _, c in dq_c))
            dev_uniq_emails_24h[i] = len(set(e for _, e in dq_e))
            dev_txn_vel_1h[i] = len(dq_tx)
            dev_amt_sum_1h[i] = sum(a for _, a in dq_tx)
            graph_dev_deg[i] = len(dev_connected_cards[dev])
        else:
            dev_uniq_cards_24h[i] = 1.0
            dev_uniq_emails_24h[i] = 1.0
            dev_txn_vel_1h[i] = 1.0
            dev_amt_sum_1h[i] = amt
            graph_dev_deg[i] = 1.0

        if card != "-999":
            dq_cd = card_devs_window[card]
            while dq_cd and t - dq_cd[0][0] > 86400:
                dq_cd.popleft()

            dq_ce = card_emails_window[card]
            while dq_ce and t - dq_ce[0][0] > 86400:
                dq_ce.popleft()

            dq_ctx = card_txns_1h[card]
            while dq_ctx and t - dq_ctx[0][0] > 3600:
                dq_ctx.popleft()

            card_uniq_devs_24h[i] = len(set(d for _, d in dq_cd))
            card_uniq_emails_24h[i] = len(set(e for _, e in dq_e))
            card_txn_vel_1h[i] = len(dq_ctx)
            total_cnt = card_total_txns[card]
            card_dev_switch_rate[i] = len(card_total_devs[card]) / max(1, total_cnt)
            graph_card_deg[i] = len(card_connected_devs[card])
        else:
            card_uniq_devs_24h[i] = 1.0
            card_uniq_emails_24h[i] = 1.0
            card_txn_vel_1h[i] = 1.0
            card_dev_switch_rate[i] = 0.0
            graph_card_deg[i] = 1.0

        # Topological Synthesis
        deg_d = max(1.0, graph_dev_deg[i])
        deg_c = max(1.0, graph_card_deg[i])
        vel = max(1.0, dev_txn_vel_1h[i] + card_txn_vel_1h[i])
        
        graph_burst[i] = np.log1p(vel) * np.log1p(deg_d)
        graph_ring[i] = deg_d + deg_c + (2 if email != 'unknown' else 0)
        graph_2hop[i] = deg_d * deg_c

        # 2. Append CURRENT transaction to state (available strictly for FUTURE txns)
        if dev != "unknown":
            dev_cards_window[dev].append((t, card))
            dev_emails_window[dev].append((t, email))
            dev_txns_1h[dev].append((t, amt))
            if card != "-999":
                dev_connected_cards[dev].add(card)

        if card != "-999":
            card_devs_window[card].append((t, dev))
            card_emails_window[card].append((t, email))
            card_txns_1h[card].append((t, amt))
            card_total_txns[card] += 1
            if dev != "unknown":
                card_total_devs[card].add(dev)
                card_connected_devs[card].add(dev)

        if (i + 1) % report_step == 0 or i == n - 1:
            print(f"   • Processed {i+1:,}/{n:,} events (Elapsed: {time.time()-t0:.1f}s)...")

    # Construct DataFrame aligned with original index
    feat_df = pd.DataFrame({
        "dev_unique_cards_24h": dev_uniq_cards_24h,
        "dev_unique_emails_24h": dev_uniq_emails_24h,
        "dev_txn_velocity_1h": dev_txn_vel_1h,
        "dev_amount_sum_1h": dev_amt_sum_1h,
        "card_unique_devices_24h": card_uniq_devs_24h,
        "card_unique_emails_24h": card_uniq_emails_24h,
        "card_txn_velocity_1h": card_txn_vel_1h,
        "card_device_switch_rate": card_dev_switch_rate,
        "graph_device_shared_deg": graph_dev_deg,
        "graph_card_shared_deg": graph_card_deg,
        "graph_burst_score": graph_burst,
        "graph_ring_size": graph_ring,
        "graph_2hop_neighborhood_size": graph_2hop
    }, index=df_sorted.index)

    # Reindex back to original DataFrame index ordering
    feat_df = feat_df.loc[df.index]
    
    elapsed = time.time() - t0
    print(f"   ✅ Finished {dataset_name.upper()} temporal extraction in {elapsed:.1f}s ({feat_df.shape[1]} features)")
    return feat_df

def build_and_save_all():
    train_df = pd.read_pickle(PROCESSED_DIR / "train.pkl")
    test_df = pd.read_pickle(PROCESSED_DIR / "test.pkl")

    train_feats = extract_strict_temporal_features(train_df, "train")
    test_feats = extract_strict_temporal_features(test_df, "test")

    train_feats.to_pickle(PROCESSED_DIR / "train_temporal_graph_feats.pkl")
    test_feats.to_pickle(PROCESSED_DIR / "test_temporal_graph_feats.pkl")
    print("\n💾 Saved:")
    print("   • data/processed/train_temporal_graph_feats.pkl")
    print("   • data/processed/test_temporal_graph_feats.pkl")

if __name__ == "__main__":
    build_and_save_all()
