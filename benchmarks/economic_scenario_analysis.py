#!/usr/bin/env python3
"""
VYUH 2.1 — Economic Scenario & Merchant Value Analysis
======================================================
Translates real-world holdout operating point lifts (Recall @ 1.0% FPR)
into economic financial impact for a representative payment aggregation merchant:
  - Monthly Volume: ₹100.00 Crore (2,000,000 Transactions @ ₹500 Avg Ticket)
  - Gross Fraud Rate: 1.50% (30,000 Fraudulent Transactions = ₹1.50 Crore at Risk)
  - Fixed False Positive Rate: 1.00% (Strictly Capped Customer Friction)
"""

import sys
import os
import tempfile
os.environ.setdefault("MPLCONFIGDIR", tempfile.gettempdir())
import json
from pathlib import Path

CHECKPOINT_DIR = Path(__file__).resolve().parents[1] / "models" / "checkpoints"

def run_economic_analysis():
    print("=" * 95)
    print("💰 ECONOMIC SCENARIO & MERCHANT VALUE MODELING")
    print("=" * 95)

    monthly_gmv_inr = 100_000_000_0  # ₹100 Crore
    avg_ticket_inr = 500.0
    total_txns = int(monthly_gmv_inr / avg_ticket_inr)  # 2,000,000 txns
    base_fraud_rate = 0.015  # 1.50%
    gross_fraud_txns = int(total_txns * base_fraud_rate)  # 30,000 txns
    gross_fraud_inr = gross_fraud_txns * avg_ticket_inr  # ₹1.50 Crore

    # Operating Points from Canonical IEEE-CIS Benchmark (models/checkpoints/final_incremental_value_study.json)
    rec_tab_1pct = 0.0760   # 7.60% recall
    rec_vyuh_1pct = 0.1149  # 11.49% recall

    fraud_caught_tab_inr = gross_fraud_inr * rec_tab_1pct
    fraud_caught_vyuh_inr = gross_fraud_inr * rec_vyuh_1pct
    incremental_savings_monthly_inr = fraud_caught_vyuh_inr - fraud_caught_tab_inr
    incremental_savings_annual_inr = incremental_savings_monthly_inr * 12.0

    print(f"📊 Merchant Portfolio Profile:")
    print(f"   • Monthly GMV: ₹{monthly_gmv_inr / 1e7:.2f} Crore ({total_txns:,} checkouts)")
    print(f"   • Gross Fraud at Risk: ₹{gross_fraud_inr / 1e5:.2f} Lakhs / month ({gross_fraud_txns:,} fraud attempts)")
    print(f"   • False-Positive Friction Cap: Strictly Fixed at 1.0% FPR")
    print("-" * 95)
    print(f"💵 Fraud Loss Prevention Comparison:")
    print(f"   • Tabular Baseline (M1): ₹{fraud_caught_tab_inr / 1e5:.2f} Lakhs caught / month (7.60% Recall)")
    print(f"   • VYUH Joint GBDT (M3):  ₹{fraud_caught_vyuh_inr / 1e5:.2f} Lakhs caught / month (11.49% Recall)")
    print(f"   • Incremental Fraud Saved: +₹{incremental_savings_monthly_inr / 1e5:.2f} Lakhs / month (+₹{incremental_savings_annual_inr / 1e5:.2f} Lakhs / year)")
    print(f"   • Relative Fraud Capture Increase: +{(rec_vyuh_1pct - rec_tab_1pct)/rec_tab_1pct * 100:.1f}%")
    print("=" * 95)

    payload = {
        "scenario_parameters": {
            "monthly_gmv_inr": monthly_gmv_inr,
            "avg_ticket_inr": avg_ticket_inr,
            "monthly_txns": total_txns,
            "gross_fraud_rate_pct": base_fraud_rate * 100,
            "gross_fraud_loss_at_risk_inr": gross_fraud_inr,
            "fixed_operating_fpr_pct": 1.0
        },
        "comparative_economics": {
            "tabular_baseline": {
                "recall_pct": round(rec_tab_1pct * 100, 2),
                "monthly_fraud_caught_inr": round(fraud_caught_tab_inr, 2),
                "annual_fraud_caught_inr": round(fraud_caught_tab_inr * 12, 2)
            },
            "vyuh_joint_model": {
                "recall_pct": round(rec_vyuh_1pct * 100, 2),
                "monthly_fraud_caught_inr": round(fraud_caught_vyuh_inr, 2),
                "annual_fraud_caught_inr": round(fraud_caught_vyuh_inr * 12, 2)
            },
            "incremental_merchant_lift": {
                "monthly_net_savings_inr": round(incremental_savings_monthly_inr, 2),
                "annual_net_savings_inr": round(incremental_savings_annual_inr, 2),
                "relative_fraud_capture_gain_pct": round((rec_vyuh_1pct - rec_tab_1pct)/rec_tab_1pct * 100, 1)
            }
        },
        "disclaimer": "Scenario analysis based on real IEEE-CIS holdout operating points applied to a representative merchant volume model."
    }

    out_file = CHECKPOINT_DIR / "economic_impact_scenario.json"
    with open(out_file, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"💾 Saved economic scenario artifact: {out_file}")

if __name__ == "__main__":
    run_economic_analysis()
