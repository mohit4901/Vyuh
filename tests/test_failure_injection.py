#!/usr/bin/env python3
"""
VYUH 2.0 — Failure Injection & Bounded Recovery Kill Test
=========================================================
Injects actual failures across 5 system boundaries:
  1. Corrupt / Malformed Type Injection (e.g. non-numeric string amount)
  2. Missing Entity Payload ({})
  3. Model Checkpoint Failure (simulates model unpickling failure / None)
  4. Extreme Outlier Values (e.g. ₹100,000,000 transaction)
  5. Investigation Agent on Unknown Entity
"""

import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

from backend.inference_service import ModelManager

def run_failure_tests():
    print("=" * 80)
    print("🧪 VYUH 2.0 — FAILURE INJECTION & BOUNDED RECOVERY KILL TEST")
    print("=" * 80)

    manager = ModelManager()

    # 1. Malformed Type Injection
    print("\n[Test 1] Malformed Type Injection (amount='invalid_str', cardId=None)")
    malformed_txn = {"orderId": "FAIL-01", "amount": "invalid_str", "cardId": None, "deviceId": None}
    r1 = manager.score_transaction(malformed_txn)
    print(f"   Safe Recovery -> Action: {r1['decision']['action']} | Risk: {r1['scores']['finalCalibratedRisk']} | Safe INR: ₹{r1['amountINR']}")
    assert r1['amountINR'] == 499.0, "Should default safely to 499.0"

    # 2. Empty Payload
    print("\n[Test 2] Empty Payload ({})")
    r2 = manager.score_transaction({})
    print(f"   Safe Recovery -> Action: {r2['decision']['action']} | Risk: {r2['scores']['finalCalibratedRisk']}")
    assert r2['decision']['action'] in ['ALLOW', 'STEP_UP_AUTH'], "Should safely evaluate empty payload"

    # 3. Model Failure Simulation
    print("\n[Test 3] Model Failure Simulation (online_model = None)")
    saved_model = manager.online_model
    manager.online_model = None
    r3 = manager.score_transaction({"orderId": "FAIL-03", "amount": 1200.0})
    print(f"   Safe Recovery -> Action: {r3['decision']['action']} | Fallback Risk: {r3['scores']['finalCalibratedRisk']}")
    manager.online_model = saved_model
    assert r3['scores']['finalCalibratedRisk'] > 0, "Fallback heuristic should produce positive risk"

    # 4. Extreme Amount Outlier
    print("\n[Test 4] Extreme Amount Outlier (₹100,000,000.0)")
    r4 = manager.score_transaction({"orderId": "FAIL-04", "amount": 100000000.0, "cardId": "CARD_WHALE"})
    print(f"   Bounded Recovery -> Action: {r4['decision']['action']} | Risk: {r4['scores']['finalCalibratedRisk']} | Expected Fraud Loss: ₹{r4['economics']['expectedFraudLossINR']:,.2f}")
    assert r4['scores']['finalCalibratedRisk'] <= 1.0, "Risk score must remain bounded in [0, 1]"

    # 5. Investigation on Unknown Entity
    print("\n[Test 5] Forensic Agent Investigation on Cold-Start Entity")
    inv = manager.agent.investigate("Why flagged?", {"order_id": "FAIL-05", "device_id": "UNKNOWN_DEV_999"})
    print(f"   Tool Execution Trace: {len(inv['tool_call_trace'])} tools executed successfully")
    assert len(inv['tool_call_trace']) == 6, "All 6 forensic tools must complete execution"

    print("\n" + "=" * 80)
    print("🎉 ALL 5 FAILURE RECOVERY TESTS PASSED — 100% BOUNDED & SAFE!")
    print("=" * 80)

if __name__ == "__main__":
    run_failure_tests()
