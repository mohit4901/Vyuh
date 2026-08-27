#!/usr/bin/env python3
"""
VYUH 2.1 — End-to-End Public HTTP REST API Test
===============================================
Spawns both:
  1. Python Live Inference Microservice (Port 5001)
  2. Node.js Express REST Gateway (Port 3000)

Sends real HTTP POST requests to `http://127.0.0.1:3000/api/score`
and `http://127.0.0.1:3000/api/investigate` to verify complete
multi-process end-to-end integration without mock boundaries.
"""

import sys
import time
import json
import urllib.request
import subprocess
import signal
import os
import tempfile
os.environ.setdefault("MPLCONFIGDIR", tempfile.gettempdir())
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

def run_http_e2e():
    print("=" * 85)
    print("🌐 VYUH 2.1 — END-TO-END HTTP REST API INTEGRATION AUDIT")
    print("=" * 85)

    python_proc = None
    node_proc = None

    try:
        # 1. Start Python Inference Microservice
        print("\n[1/4] Starting Python Inference Microservice on port 5001...")
        python_proc = subprocess.Popen(
            [str(PROJECT_ROOT / ".venv" / "bin" / "python"), str(PROJECT_ROOT / "backend" / "inference_service.py")],
            cwd=str(PROJECT_ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        time.sleep(2.0)

        # Verify Python /health
        req = urllib.request.urlopen("http://127.0.0.1:5001/health", timeout=3)
        py_health = json.loads(req.read().decode("utf-8"))
        print(f"      ✅ Python Service Health: status='{py_health.get('status', 'ok')}', nodes={py_health.get('graphNodes', 0)}")

        # 2. Start Node.js Express Server
        print("\n[2/4] Starting Node.js REST Gateway on port 3000...")
        env = os.environ.copy()
        env["PORT"] = "3000"
        env["PYTHON_SERVICE_HOST"] = "127.0.0.1"
        env["PYTHON_SERVICE_PORT"] = "5001"
        node_proc = subprocess.Popen(
            ["node", str(PROJECT_ROOT / "backend" / "server.js")],
            cwd=str(PROJECT_ROOT),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        time.sleep(2.0)

        # Verify Node /api/health
        req = urllib.request.urlopen("http://127.0.0.1:3000/api/health", timeout=3)
        node_health = json.loads(req.read().decode("utf-8"))
        print(f"      ✅ Node.js Gateway Health: status='{node_health['status']}', version='{node_health['version']}'")

        # 3. Test Public POST /api/score
        print("\n[3/4] Testing Public HTTP POST /api/score (Razorpay-style payload)...")
        payload = {
            "orderId": "HTTP_E2E_001",
            "amount": 1499.0,
            "cardId": "CARD_HTTP_TEST",
            "deviceId": "DEV_HTTP_TEST",
            "email": "customer_e2e@domain.in"
        }
        data_bytes = json.dumps(payload).encode("utf-8")
        score_req = urllib.request.Request(
            "http://127.0.0.1:3000/api/score",
            data=data_bytes,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(score_req, timeout=5) as res:
            assert res.status == 200
            score_body = json.loads(res.read().decode("utf-8"))
            print(f"      ✅ HTTP 200 Received!")
            print(f"      • Decision ID:     {score_body['decisionId']}")
            print(f"      • Risk Score:      {score_body['scores']['finalCalibratedRisk']}")
            print(f"      • Model Backed:    {score_body['provenance']['model_backed_prediction']}")
            print(f"      • Action:          {score_body['decision']['action']}")
            print(f"      • Latency:         {score_body['inferenceLatencyMs']} ms")

        # 4. Test Public POST /api/investigate
        print("\n[4/4] Testing Public HTTP POST /api/investigate...")
        inv_payload = {
            "query": "Why was this order flagged?",
            "transactionContext": score_body
        }
        inv_bytes = json.dumps(inv_payload).encode("utf-8")
        inv_req = urllib.request.Request(
            "http://127.0.0.1:3000/api/investigate",
            data=inv_bytes,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(inv_req, timeout=5) as res:
            assert res.status == 200
            inv_body = json.loads(res.read().decode("utf-8"))
            print(f"      ✅ HTTP 200 Received!")
            print(f"      • Forensic Brief:  {inv_body['forensic_brief'].splitlines()[0]}")
            print(f"      • Tools Executed:  {len(inv_body['tool_call_trace'])} tools")

        print("\n" + "=" * 85)
        print("🎉 COMPLETE DUAL-RUNTIME HTTP STACK VERIFIED END-TO-END WITH ZERO CRASHES!")
        print("=" * 85)

    finally:
        if node_proc:
            node_proc.terminate()
            node_proc.kill()
        if python_proc:
            python_proc.terminate()
            python_proc.kill()

if __name__ == "__main__":
    run_http_e2e()
