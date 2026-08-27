#!/usr/bin/env python3
"""
VYUH 2.1 — Benign Friction & Temporal Sharing Calibration Study
==============================================================
Evaluates false friction under legitimate sharing vs coordinated abuse
by explicitly modeling temporal dispersion:

  1. Normal Single User (1 Account / Device, Isolated)
  2. Family Shared Device (2 Accounts / Device, 4 Hours Apart)
  3. Office / Coworking NAT (4 Accounts / Device, Spaced over 8 Hours)
  4. Public Retail POS Kiosk (8 Cards / Device, Spaced over 12 Hours)
  5. Bot Syndicate Attack (5 Accounts / Device, Rapid 30-Second Burst)
  6. Dense Carding Ring (10 Accounts / Device, Rapid 45-Second Burst)

Measures:
  - P50, P95 Risk Score
  - Step-Up Challenge Rate (%)
  - Human Review Rate (%)
  - Conversion Preservation Rate (%)
"""

import sys
import os
import json
import time
import numpy as np
import pandas as pd
import networkx as nx
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

CHECKPOINT_DIR = PROJECT_ROOT / "models" / "checkpoints"
from backend.inference_service import ModelManager

def run_friction_study(n_trials=100, random_seed=42):
    np.random.seed(random_seed)
    print("=" * 115)
    print(f"🛡️  BENIGN FRICTION & TEMPORAL SHARING CALIBRATION STUDY ({n_trials} TRIALS / SCENARIO)")
    print("=" * 115)

    # (Name, k_entities, spacing_seconds, is_fraud)
    scenarios = [
        ("1. Normal Single User (1 Acc/Dev, Isolated)", 1, 0, False),
        ("2. Family Shared Device (2 Accs/Dev, 4h Spaced)", 2, 14400, False),
        ("3. Office / Coworking NAT (4 Accs/Dev, 8h Spaced)", 4, 7200, False),
        ("4. Public Retail Kiosk (8 Cards, 12h Spaced)", 8, 5400, False),
        ("5. Bot Syndicate (5 Accs, 30s Rapid Burst)", 5, 5, True),
        ("6. Dense Carding Ring (10 Accs, 45s Rapid Burst)", 10, 4, True)
    ]

    report = []

    for name, k_entities, spacing_sec, is_fraud in scenarios:
        scores = []
        allow_count = 0
        stepup_count = 0
        review_count = 0

        for trial in range(n_trials):
            mgr = ModelManager()
            mgr.live_graph.G = nx.Graph()
            mgr.live_graph.events_stream.clear()
            mgr.live_graph.confirmed_fraud_nodes = set()

            device_id = f"DEV_SCENARIO_{k_entities}_{trial}"
            now = time.time()

            # Pre-populate background entities with exact temporal offsets
            for b in range(k_entities - 1):
                offset_sec = (k_entities - 1 - b) * spacing_sec
                txn_time = now - offset_sec
                mgr.score_transaction({
                    "orderId": f"BG_{trial}_{b}",
                    "amount": float(np.random.uniform(250, 1250)),
                    "cardId": f"CARD_BG_{trial}_{b}",
                    "deviceId": device_id,
                    "email": f"user_bg_{trial}_{b}@domain.in"
                }, timestamp=txn_time)

            # Target transaction arriving right NOW
            target_amount = 499.0 if is_fraud else float(np.random.uniform(299, 899))
            res = mgr.score_transaction({
                "orderId": f"TARGET_{trial}",
                "amount": target_amount,
                "cardId": f"CARD_TARGET_{trial}",
                "deviceId": device_id,
                "email": f"target_user_{trial}@domain.in"
            }, timestamp=now)

            risk = res["scores"]["finalCalibratedRisk"]
            scores.append(risk)
            action = res["decision"]["action"]

            if action == "ALLOW":
                allow_count += 1
            elif action == "STEP_UP_AUTH":
                stepup_count += 1
            elif action == "FLAG_HUMAN_REVIEW":
                review_count += 1

        p50 = float(np.percentile(scores, 50))
        p95 = float(np.percentile(scores, 95))
        stepup_pct = (stepup_count / n_trials) * 100.0
        review_pct = (review_count / n_trials) * 100.0
        conversion_pct = (allow_count / n_trials) * 100.0

        report.append({
            "scenario": name,
            "entities": k_entities,
            "p50_risk": round(p50, 4),
            "p95_risk": round(p95, 4),
            "stepup_rate_pct": round(stepup_pct, 1),
            "review_rate_pct": round(review_pct, 1),
            "clean_conversion_pct": round(conversion_pct, 1)
        })

    print(f"{'Sharing Scenario':<48} | {'P50 Risk':<9} | {'P95 Risk':<9} | {'Step-Up %':<10} | {'Review %':<9} | {'Clean Conversion %'}")
    print("-" * 120)
    for r in report:
        print(f"{r['scenario']:<48} | {r['p50_risk']:<9.4f} | {r['p95_risk']:<9.4f} | {r['stepup_rate_pct']:>8.1f}%  | {r['review_rate_pct']:>7.1f}% | {r['clean_conversion_pct']:>16.1f}%")

    print("=" * 120)

    out_file = CHECKPOINT_DIR / "benign_friction_study_results.json"
    with open(out_file, "w") as f:
        json.dump(report, f, indent=2)
    print(f"💾 Saved results to: {out_file}")

if __name__ == "__main__":
    run_friction_study()
