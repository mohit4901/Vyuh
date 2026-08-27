#!/usr/bin/env python3
"""
VYUH 2.1 — Operating Regime Characterization Study (Multi-Trial Monte Carlo)
===========================================================================
Characterizes the exact operating regimes in which relational intelligence adds value:
  Regime 1: Individual Benign (Isolated Hardware, Normal Behavior)
  Regime 2: Individual Fraud (Tabular Anomaly, Single Hardware)
  Regime 3: 2-Account Hardware Sharing (Low Coordination / Family)
  Regime 4: 3-Account Hardware Sharing (Moderate Coordination)
  Regime 5: 5-Account Syndicate Cluster (High Coordination)
  Regime 6: 10-Account Hardware Ring (Dense Coordinated Syndicate)

Runs 50 randomized Monte Carlo trials per regime with randomized amounts,
timestamps, and noise to measure:
  - Mean P_tabular ± Std
  - Mean P_graph ± Std
  - Mean P_final (Calibrated Fusion) ± Std
  - Step-Up / Review Escalation Rate (%)
"""

import sys
import os
import json
import pickle
import time
import numpy as np
import pandas as pd
import networkx as nx
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

CHECKPOINT_DIR = PROJECT_ROOT / "models" / "checkpoints"
from backend.inference_service import ModelManager

def run_regime_study(n_trials=50, random_seed=42):
    np.random.seed(random_seed)
    print("=" * 115)
    print(f"🔬 OPERATING REGIME CHARACTERIZATION STUDY ({n_trials} RANDOMIZED MONTE CARLO TRIALS / REGIME)")
    print("=" * 115)

    regimes = [
        ("Regime 1: Individual Benign (Isolated 1:1)", 1, False),
        ("Regime 2: Individual Fraud (Tabular Anomaly)", 1, True),
        ("Regime 3: 2-Account Coordination (Low)", 2, False),
        ("Regime 4: 3-Account Coordination (Moderate)", 3, False),
        ("Regime 5: 5-Account Syndicate (High)", 5, False),
        ("Regime 6: 10-Account Hardware Ring (Dense)", 10, False)
    ]

    report = []

    for name, k_accs, is_tabular_fraud in regimes:
        p_tab_trials = []
        p_graph_trials = []
        p_final_trials = []
        stepup_or_review_count = 0

        for trial in range(n_trials):
            mgr = ModelManager()
            mgr.live_graph.G = nx.Graph()
            mgr.live_graph.confirmed_fraud_nodes = set()

            device_id = f"DEV_EXP_{k_accs}_{trial}"

            # Seed k-1 background accounts on the same device
            for b in range(k_accs - 1):
                mgr.score_transaction({
                    "orderId": f"BG_{trial}_{b}",
                    "amount": float(np.random.uniform(200, 600)),
                    "cardId": f"CARD_BG_{trial}_{b}",
                    "deviceId": device_id,
                    "email": f"bg_{trial}_{b}@dom.in"
                })

            # Target transaction
            if is_tabular_fraud:
                target_amount = float(np.random.uniform(45000, 95000))  # High-ticket anomaly
            else:
                target_amount = float(np.random.uniform(299, 599))      # Normal micro-checkout

            res = mgr.score_transaction({
                "orderId": f"TGT_{trial}",
                "amount": target_amount,
                "cardId": f"CARD_TGT_{trial}",
                "deviceId": device_id,
                "email": f"tgt_{trial}@dom.in"
            })

            p_tab_trials.append(res["scores"]["pTabular"])
            p_graph_trials.append(res["scores"]["pGraph"])
            p_final_trials.append(res["scores"]["finalCalibratedRisk"])

            if res["decision"]["action"] in ["STEP_UP_AUTH", "FLAG_HUMAN_REVIEW"]:
                stepup_or_review_count += 1

        mean_tab = float(np.mean(p_tab_trials))
        std_tab = float(np.std(p_tab_trials))
        mean_graph = float(np.mean(p_graph_trials))
        std_graph = float(np.std(p_graph_trials))
        mean_final = float(np.mean(p_final_trials))
        std_final = float(np.std(p_final_trials))
        escalation_pct = (stepup_or_review_count / n_trials) * 100.0

        report.append({
            "regime": name,
            "k_accounts": k_accs,
            "mean_p_tabular": round(mean_tab, 4),
            "std_p_tabular": round(std_tab, 4),
            "mean_p_graph": round(mean_graph, 4),
            "std_p_graph": round(std_graph, 4),
            "mean_p_final": round(mean_final, 4),
            "std_p_final": round(std_final, 4),
            "escalation_rate_pct": round(escalation_pct, 1)
        })

    print(f"{'Operating Regime':<46} | {'P_tabular (Mean±Std)':<22} | {'P_graph (Mean±Std)':<20} | {'P_final (Mean±Std)':<20} | {'Escalation %'}")
    print("-" * 125)
    for r in report:
        tab_str = f"{r['mean_p_tabular']:.4f} ± {r['std_p_tabular']:.4f}"
        graph_str = f"{r['mean_p_graph']:.4f} ± {r['std_p_graph']:.4f}"
        final_str = f"{r['mean_p_final']:.4f} ± {r['std_p_final']:.4f}"
        print(f"{r['regime']:<46} | {tab_str:<22} | {graph_str:<20} | {final_str:<20} | {r['escalation_rate_pct']:>9.1f}%")

    print("=" * 125)

    out_file = CHECKPOINT_DIR / "regime_characterization_results.json"
    with open(out_file, "w") as f:
        json.dump(report, f, indent=2)
    print(f"💾 Saved regime characterization report to: {out_file}")

if __name__ == "__main__":
    run_regime_study()
