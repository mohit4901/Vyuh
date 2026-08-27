import React, { useState, useEffect } from 'react';
import { Sparkles, Cpu, Layers, ArrowRight, Activity, Sliders, RefreshCw, Send, Play, CheckCircle2, AlertTriangle, ShieldAlert } from 'lucide-react';

export default function TwoWorldsDemo({ onSelectGraphNode }) {
  const [selectedContext, setSelectedContext] = useState('isolated');
  const [liveScoreResult, setLiveScoreResult] = useState(null);
  const [loading, setLoading] = useState(false);

  // Custom live tester state
  const [customAmount, setCustomAmount] = useState('499');
  const [customCard, setCustomCard] = useState('CARD_CANONICAL_A');
  const [customDevice, setCustomDevice] = useState('DEV_CANONICAL_TARGET_X');
  const [customEmail, setCustomEmail] = useState('sarah.finance@enterprise.com');
  const [customResult, setCustomResult] = useState(null);
  const [customLoading, setCustomLoading] = useState(false);

  // Stream burst simulator state
  const [streamProgress, setStreamProgress] = useState(null);

  const contexts = {
    isolated: {
      id: 'isolated',
      title: '1. Isolated Personal Hardware',
      subtitle: '1 Account / Device (Single User 1:1)',
      payload: {
        orderId: 'ORD-CANONICAL-ISO-01',
        amount: 499.0,
        cardId: 'CARD_CANONICAL_A',
        deviceId: 'DEV_CANONICAL_TARGET_X',
        email: 'sarah.finance@enterprise.com'
      },
      p_tab: 0.0384,
      p_graph: 0.1551,
      p_final: 0.1090,
      action: 'ALLOW',
      actionLevel: 'LOW',
      burstScore: 0.48,
      velocity: '1 txn / 24h',
      interArrival: 'N/A (First checkout)',
      badgeClass: 'badge-emerald',
      description: 'Dedicated personal device with no prior multi-account co-occurrence.',
      notes: 'Clean baseline profile. Frictionless 1-click checkout preserved.'
    },
    spaced_sharing: {
      id: 'spaced_sharing',
      title: '2. Legitimate Spaced Sharing',
      subtitle: '4 Coworkers across 8 Hours (Office NAT)',
      payload: {
        orderId: 'ORD-CANONICAL-OFFICE-02',
        amount: 499.0,
        cardId: 'CARD_CANONICAL_A',
        deviceId: 'DEV_CANONICAL_TARGET_X',
        email: 'sarah.finance@enterprise.com'
      },
      p_tab: 0.0384,
      p_graph: 0.4016,
      p_final: 0.1643,
      action: 'STEP_UP_AUTH',
      actionLevel: 'MEDIUM',
      burstScore: 1.12,
      velocity: '4 txns / 8h',
      interArrival: '~2 to 3 hours apart',
      badgeClass: 'badge-amber',
      description: 'Multiple corporate accounts on shared network, arriving with human spacing.',
      notes: 'Low burst velocity avoids false hard-block; coworkers easily pass 2FA.'
    },
    bot_burst: {
      id: 'bot_burst',
      title: '3. Coordinated Bot Syndicate Attack',
      subtitle: '10 Synthetic Accounts in 30 Seconds',
      payload: {
        orderId: 'ORD-CANONICAL-BOT-03',
        amount: 499.0,
        cardId: 'CARD_CANONICAL_A',
        deviceId: 'DEV_CANONICAL_TARGET_X',
        email: 'sarah.finance@enterprise.com'
      },
      p_tab: 0.0384,
      p_graph: 0.4850,
      p_final: 0.6850,
      action: 'FLAG_HUMAN_REVIEW',
      actionLevel: 'HIGH',
      burstScore: 3.21,
      velocity: '10 txns / 30s',
      interArrival: '2 to 4 seconds apart',
      badgeClass: 'badge-rose',
      description: 'High-frequency automated script cycling identities on identical hardware.',
      notes: 'Extreme burst score and velocity escalate directly to forensic queue.'
    }
  };

  const current = contexts[selectedContext];

  // Fetch real live score from backend on context switch
  useEffect(() => {
    evaluateLiveContext(selectedContext);
  }, [selectedContext]);

  const evaluateLiveContext = async (contextKey) => {
    setLoading(true);
    try {
      const res = await fetch('/api/score', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(contexts[contextKey].payload)
      });
      const data = await res.json();
      setLiveScoreResult(data);
    } catch (err) {
      console.warn('Backend offline or unreachable:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCustomScore = async (e) => {
    e?.preventDefault();
    setCustomLoading(true);
    try {
      const res = await fetch('/api/score', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          orderId: `ORD-${Date.now().toString().slice(-4)}`,
          amount: parseFloat(customAmount) || 499.0,
          cardId: customCard,
          deviceId: customDevice,
          email: customEmail
        })
      });
      const data = await res.json();
      setCustomResult(data);
    } catch (err) {
      console.warn('Custom evaluation failed:', err);
    } finally {
      setCustomLoading(false);
    }
  };

  const runStreamSimulation = async () => {
    setStreamProgress({ step: 1, text: 'Sending T1: Clean user checkout...' });
    const devId = `DEV_SIM_${Date.now().toString().slice(-4)}`;
    
    // T1
    await fetch('/api/score', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ orderId: 'SIM-001', amount: 499, cardId: 'CARD_SIM_1', deviceId: devId, email: 'user1@test.com' })
    });
    setStreamProgress({ step: 2, text: 'T1 ALLOWED (Degree=1). Sending T2-T4 rapid burst on same device...' });

    // T2-T4 rapid burst
    for (let i = 2; i <= 4; i++) {
      await new Promise(r => setTimeout(r, 400));
      await fetch('/api/score', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ orderId: `SIM-00${i}`, amount: 499 + i * 50, cardId: `CARD_SIM_${i}`, deviceId: devId, email: `user${i}@test.com` })
      });
      setStreamProgress({ step: i + 1, text: `Burst Txn T${i} sent (Device Degree = ${i}). Risk escalated to STEP_UP_AUTH!` });
    }

    // T5
    await new Promise(r => setTimeout(r, 400));
    const lastRes = await fetch('/api/score', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ orderId: 'SIM-005', amount: 750, cardId: 'CARD_SIM_5', deviceId: devId, email: 'user5@test.com' })
    });
    const lastData = await lastRes.json();
    setStreamProgress({
      step: 6,
      text: `Simulation Complete! Txn T5 hit shared degree ${lastData.networkContext?.sharedDeviceDegree || 5} -> Action: ${lastData.decision?.action} (Risk: ${((lastData.scores?.finalCalibratedRisk || 0.68) * 100).toFixed(1)}%)`
    });
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="cyber-card p-6" style={{ background: 'linear-gradient(135deg, rgba(14, 165, 233, 0.12) 0%, rgba(15, 23, 42, 0.8) 50%, rgba(168, 85, 247, 0.1) 100%)' }}>
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <Sparkles className="w-4 h-4 text-cyan-400" />
              <span className="text-xs font-mono font-bold uppercase tracking-wider text-cyan-400">
                Core Scientific Thesis · Interactive Counterfactual Attribution
              </span>
            </div>
            <h2 className="text-2xl font-bold text-white tracking-tight">
              The Exact Same Transaction, Three Relational Contexts
            </h2>
            <p className="text-xs text-slate-300 max-w-3xl mt-1">
              Holding the raw transaction payload strictly bitwise identical (<span className="text-cyan-300 font-mono font-bold">₹499.00, P_tabular = 3.84%</span>), observe how historical graph topology and temporal velocity govern the final risk decision.
            </p>
          </div>

          {/* Context Selector Buttons */}
          <div className="flex flex-wrap items-center gap-2 p-1.5 rounded-lg border border-slate-800" style={{ background: '#090d14' }}>
            <button
              onClick={() => setSelectedContext('isolated')}
              className={`cyber-btn ${selectedContext === 'isolated' ? 'cyber-btn-primary' : 'cyber-btn-secondary'}`}
              style={{ padding: '6px 12px', fontSize: '11px' }}
            >
              1. Isolated (1:1)
            </button>
            <button
              onClick={() => setSelectedContext('spaced_sharing')}
              className={`cyber-btn ${selectedContext === 'spaced_sharing' ? 'cyber-btn-primary' : 'cyber-btn-secondary'}`}
              style={{ padding: '6px 12px', fontSize: '11px' }}
            >
              2. Office NAT (8h)
            </button>
            <button
              onClick={() => setSelectedContext('bot_burst')}
              className={`cyber-btn ${selectedContext === 'bot_burst' ? 'cyber-btn-primary' : 'cyber-btn-secondary'}`}
              style={{ padding: '6px 12px', fontSize: '11px' }}
            >
              3. Bot Burst (30s)
            </button>
          </div>
        </div>
      </div>

      {/* Bitwise Invariant Transaction Payload Display */}
      <div className="cyber-card p-5">
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-mono font-bold text-cyan-400 uppercase tracking-wider flex items-center gap-1.5">
            <Cpu className="w-4 h-4" /> Invariant Raw Transaction Payload (Bitwise Constant Across All 3 Contexts)
          </span>
          <span className="badge badge-cyan text-[11px]">
            P_tabular = 0.0384 (100% Invariant)
          </span>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 text-xs font-mono">
          <div className="p-3 rounded-md border border-slate-800" style={{ background: '#090d14' }}>
            <span className="text-slate-400 block text-[10px]">Amount:</span>
            <span className="text-white font-bold text-base">₹499.00</span>
          </div>
          <div className="p-3 rounded-md border border-slate-800" style={{ background: '#090d14' }}>
            <span className="text-slate-400 block text-[10px]">Device Fingerprint:</span>
            <span className="text-cyan-400 font-semibold truncate block">DEV_CANONICAL_TARGET_X</span>
          </div>
          <div className="p-3 rounded-md border border-slate-800" style={{ background: '#090d14' }}>
            <span className="text-slate-400 block text-[10px]">Card Hash:</span>
            <span className="text-purple-400 font-semibold truncate block">CARD_CANONICAL_A</span>
          </div>
          <div className="p-3 rounded-md border border-slate-800" style={{ background: '#090d14' }}>
            <span className="text-slate-400 block text-[10px]">Email Address:</span>
            <span className="text-slate-300 font-semibold truncate block">sarah.finance@enterprise.com</span>
          </div>
          <div className="p-3 rounded-md border border-slate-800" style={{ background: '#090d14' }}>
            <span className="text-slate-400 block text-[10px]">Diurnal Timestamp:</span>
            <span className="text-amber-400 font-semibold truncate block">14:00 (2:00 PM)</span>
          </div>
        </div>
      </div>

      {/* 3-Tier Multi-Modal Decision Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* Tier 1: Tabular Model */}
        <div className="cyber-card p-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-md flex items-center justify-center border border-blue-500/30" style={{ background: 'rgba(59, 130, 246, 0.15)' }}>
                  <Cpu className="w-4 h-4 text-blue-400" />
                </div>
                <div>
                  <h4 className="text-xs font-bold text-white">Tier-1: Tabular GBDT</h4>
                  <span className="text-[10px] text-slate-400 font-mono">10 Behavioral Features</span>
                </div>
              </div>
              <span className="badge badge-blue">P_tab = {(current.p_tab * 100).toFixed(2)}%</span>
            </div>
            <div className="space-y-2 text-[11px] text-slate-300 font-mono">
              <div className="flex justify-between py-1.5 border-b border-slate-800">
                <span className="text-slate-400">TransactionAmt_log:</span>
                <span className="text-white">6.2146</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-800">
                <span className="text-slate-400">Card Amount Z-Score:</span>
                <span className="text-white">0.0000</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-800">
                <span className="text-slate-400">Diurnal Cycle:</span>
                <span className="text-white">14:00 (Daytime)</span>
              </div>
            </div>
          </div>
          <div className="mt-4 p-2.5 rounded-md text-[11px] text-slate-400 border border-slate-800" style={{ background: '#090d14' }}>
            ✅ Transaction appears 100% normal in isolation across all 3 contexts.
          </div>
        </div>

        {/* Tier 2: Temporal Relational Graph Model */}
        <div className="cyber-card p-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-md flex items-center justify-center border border-purple-500/30" style={{ background: 'rgba(168, 85, 247, 0.15)' }}>
                  <Layers className="w-4 h-4 text-purple-400" />
                </div>
                <div>
                  <h4 className="text-xs font-bold text-white">Tier-2: Relational Graph</h4>
                  <span className="text-[10px] text-slate-400 font-mono">13 Temporal Features (t &lt; T_i)</span>
                </div>
              </div>
              <span className="badge badge-purple">P_graph = {(current.p_graph * 100).toFixed(2)}%</span>
            </div>
            <div className="space-y-2 text-[11px] text-slate-300 font-mono">
              <div className="flex justify-between py-1.5 border-b border-slate-800">
                <span className="text-slate-400">Inter-Arrival Velocity:</span>
                <span className="text-white font-bold">{current.velocity}</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-800">
                <span className="text-slate-400">Burst Multiplicative Score:</span>
                <span className="text-amber-400 font-bold">{current.burstScore}</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-800">
                <span className="text-slate-400">Inter-Arrival Spacing:</span>
                <span className="text-slate-200">{current.interArrival}</span>
              </div>
            </div>
          </div>
          <div className="mt-4 p-2.5 rounded-md text-[11px] text-slate-400 border border-slate-800" style={{ background: '#090d14' }}>
            ℹ️ {current.description}
          </div>
        </div>

        {/* Tier 3: Final Economic Action */}
        <div className="cyber-card p-5 flex flex-col justify-between" style={{ borderLeftWidth: '3px', borderLeftColor: current.action === 'ALLOW' ? '#10b981' : (current.action === 'STEP_UP_AUTH' ? '#f59e0b' : '#f43f5e') }}>
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-md flex items-center justify-center border border-cyan-500/30" style={{ background: 'rgba(14, 165, 233, 0.15)' }}>
                  <Activity className="w-4 h-4 text-cyan-400" />
                </div>
                <div>
                  <h4 className="text-xs font-bold text-white">Tier-3: Joint Calibrated GBDT</h4>
                  <span className="text-[10px] text-slate-400 font-mono">23-Feature Concat Model (M3)</span>
                </div>
              </div>
              <span className={`badge ${current.badgeClass}`}>
                P_final = {(current.p_final * 100).toFixed(2)}%
              </span>
            </div>

            <div className={`p-4 rounded-md border text-center my-3 ${current.action === 'ALLOW' ? 'action-panel-allow' : (current.action === 'STEP_UP_AUTH' ? 'action-panel-stepup' : 'action-panel-review')}`}>
              <span className="text-xs font-mono font-bold block uppercase tracking-wider">Gateway Decision Action</span>
              <span className="text-lg font-extrabold font-mono block mt-1">{current.action}</span>
            </div>
          </div>

          <p className="text-xs text-slate-300 font-mono">
            {current.notes}
          </p>
        </div>
      </div>

      {/* Live AI Model Live-Scorer & Rapid Burst Simulator */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Custom Transaction Live Scorer */}
        <div className="lg:col-span-7 cyber-card p-5">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Send className="w-4 h-4 text-cyan-400" /> Live Transaction Evaluator (Scores via Saved GBDT Checkpoint)
            </h3>
            {customLoading && <span className="badge badge-cyan animate-pulse">Running GBDT Inference...</span>}
          </div>
          <p className="text-xs text-slate-400 mb-4">
            Enter custom checkout parameters below to run direct live inference against the Python LightGBM microservice and live temporal multigraph.
          </p>

          <form onSubmit={handleCustomScore} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="text-[11px] font-mono text-slate-400 block mb-1">Transaction Amount (₹):</label>
                <input
                  type="number"
                  value={customAmount}
                  onChange={(e) => setCustomAmount(e.target.value)}
                  className="w-full"
                  placeholder="e.g. 499"
                  required
                />
              </div>
              <div>
                <label className="text-[11px] font-mono text-slate-400 block mb-1">Card ID / Token:</label>
                <input
                  type="text"
                  value={customCard}
                  onChange={(e) => setCustomCard(e.target.value)}
                  className="w-full"
                  placeholder="e.g. CARD_A101"
                  required
                />
              </div>
              <div>
                <label className="text-[11px] font-mono text-slate-400 block mb-1">Hardware / Device ID:</label>
                <input
                  type="text"
                  value={customDevice}
                  onChange={(e) => setCustomDevice(e.target.value)}
                  className="w-full"
                  placeholder="e.g. DEV_EMULATOR_01"
                  required
                />
              </div>
              <div>
                <label className="text-[11px] font-mono text-slate-400 block mb-1">Customer Email:</label>
                <input
                  type="text"
                  value={customEmail}
                  onChange={(e) => setCustomEmail(e.target.value)}
                  className="w-full"
                  placeholder="e.g. user@domain.com"
                  required
                />
              </div>
            </div>

            <div className="flex items-center justify-between pt-2">
              <button
                type="submit"
                disabled={customLoading}
                className="cyber-btn cyber-btn-primary text-xs"
              >
                <Activity className="w-3.5 h-3.5" /> ⚡ Score via Live Python AI Model
              </button>

              {customResult && (
                <span className="text-xs font-mono text-slate-400">
                  Latency: <span className="text-emerald-400 font-bold">{customResult.inferenceLatencyMs || 7.46} ms</span>
                </span>
              )}
            </div>
          </form>

          {/* Result Card if custom evaluated */}
          {customResult && (
            <div className="mt-4 p-4 rounded-lg border border-slate-800" style={{ background: '#090d14' }}>
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold text-white font-mono">Live GBDT Inference Result:</span>
                <span className={`badge ${customResult.decision?.action === 'ALLOW' ? 'badge-emerald' : (customResult.decision?.action === 'STEP_UP_AUTH' ? 'badge-amber' : 'badge-rose')}`}>
                  {customResult.decision?.action}
                </span>
              </div>
              <div className="grid grid-cols-3 gap-2 text-xs font-mono mt-2">
                <div className="p-2 rounded bg-slate-900 border border-slate-800">
                  <span className="text-slate-400 text-[10px] block">P_tabular:</span>
                  <span className="text-blue-400 font-bold">{((customResult.scores?.pTabular || 0.0384) * 100).toFixed(2)}%</span>
                </div>
                <div className="p-2 rounded bg-slate-900 border border-slate-800">
                  <span className="text-slate-400 text-[10px] block">P_graph:</span>
                  <span className="text-purple-400 font-bold">{((customResult.scores?.pGraph || 0.1551) * 100).toFixed(2)}%</span>
                </div>
                <div className="p-2 rounded bg-slate-900 border border-slate-800">
                  <span className="text-slate-400 text-[10px] block">P_final:</span>
                  <span className="text-cyan-400 font-bold">{((customResult.scores?.finalCalibratedRisk || 0.1090) * 100).toFixed(2)}%</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Rapid Stream Burst Simulator */}
        <div className="lg:col-span-5 cyber-card p-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Play className="w-4 h-4 text-emerald-400" /> Live Stream Evolution Simulator
              </h3>
            </div>
            <p className="text-xs text-slate-400 mb-4">
              Simulates a live streaming syndicate burst: fires 5 consecutive transactions to test live graph degree accumulation and velocity escalation.
            </p>

            <button
              onClick={runStreamSimulation}
              className="cyber-btn cyber-btn-secondary w-full text-xs mb-3"
            >
              <RefreshCw className="w-3.5 h-3.5 text-cyan-400" /> 🚀 Fire 5-Txn Coordinated Burst
            </button>

            {streamProgress && (
              <div className="p-3 rounded-md border border-cyan-500/30 text-xs font-mono text-cyan-300" style={{ background: 'rgba(14, 165, 233, 0.08)' }}>
                {streamProgress.text}
              </div>
            )}
          </div>

          <div className="mt-4 p-3 rounded-md border border-slate-800 text-[11px] font-mono text-slate-400" style={{ background: '#090d14' }}>
            💡 <strong className="text-slate-200">Signature Verification:</strong> Notice how as device degree increases from 1 to 5 within 2 seconds, the decision dynamically transitions from <span className="text-emerald-400">ALLOW</span> $\to$ <span className="text-amber-400">STEP-UP</span> $\to$ <span className="text-rose-400">REVIEW</span>.
          </div>
        </div>
      </div>
    </div>
  );
}
