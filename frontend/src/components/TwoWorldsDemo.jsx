import React, { useState, useEffect } from 'react';
import { AlertTriangle, CheckCircle2, ShieldAlert, Sparkles, Cpu, Layers, ArrowRight, Activity, Sliders } from 'lucide-react';

export default function TwoWorldsDemo({ onSelectGraphNode }) {
  // Canonical Counterfactual Modes
  // 1: Isolated Device | 2: Legitimate Spaced Sharing (8h) | 3: Automated Bot Burst (30s)
  const [selectedContext, setSelectedContext] = useState('isolated');
  const [liveData, setLiveData] = useState(null);
  const [loading, setLoading] = useState(false);

  // Invariant Canonical Transaction
  const amount = 499;
  const deviceId = 'DEV_CANONICAL_TARGET_X';
  const cardId = 'CARD_CANONICAL_A';
  const email = 'sarah.finance@enterprise.com';
  const timestamp = '14:00 (2:00 PM)';

  const contexts = {
    isolated: {
      id: 'isolated',
      title: '1. Isolated Personal Hardware',
      subtitle: '1 Account / Device (Single User)',
      p_tab: 0.0384,
      p_graph: 0.1551,
      p_final: 0.1090,
      action: 'ALLOW',
      actionLevel: 'LOW',
      burstScore: 0.48,
      velocity: '1 txn / 24h',
      interArrival: 'N/A (First checkout)',
      badgeClass: 'badge-emerald',
      actionClass: 'bg-emerald-950/20 border-emerald-500/30 text-emerald-300',
      description: 'Dedicated personal device with no prior multi-account co-occurrence.',
      verdict: 'ALLOW & COMMIT TO IMMUTABLE LOG',
      notes: 'Clean baseline profile. Frictionless 1-click checkout preserved.'
    },
    spaced_sharing: {
      id: 'spaced_sharing',
      title: '2. Legitimate Spaced Sharing',
      subtitle: '4 Coworkers across 8 Hours (Office NAT)',
      p_tab: 0.0384,
      p_graph: 0.4016,
      p_final: 0.1643,
      action: 'STEP_UP_AUTH',
      actionLevel: 'MEDIUM',
      burstScore: 1.12,
      velocity: '4 txns / 8h',
      interArrival: '~2 to 3 hours apart',
      badgeClass: 'badge-amber',
      actionClass: 'bg-amber-950/20 border-amber-500/30 text-amber-300',
      description: 'Multiple corporate accounts on shared network, but arriving with human spacing.',
      verdict: 'TRIGGER NON-DESTRUCTIVE 2FA STEP-UP',
      notes: 'Low burst velocity avoids false hard-block; coworkers easily pass 2FA.'
    },
    bot_burst: {
      id: 'bot_burst',
      title: '3. Coordinated Bot Syndicate Attack',
      subtitle: '10 Synthetic Accounts in 30 Seconds',
      p_tab: 0.0384,
      p_graph: 0.4850,
      p_final: 0.6850,
      action: 'FLAG_HUMAN_REVIEW',
      actionLevel: 'HIGH',
      burstScore: 3.21,
      velocity: '10 txns / 30s',
      interArrival: '2 to 4 seconds apart',
      badgeClass: 'badge-rose',
      actionClass: 'bg-rose-950/20 border-rose-500/30 text-rose-300',
      description: 'High-frequency automated script cycling identities on identical hardware.',
      verdict: 'ESCALATE: FORENSIC ANALYST REVIEW',
      notes: 'Extreme burst score and velocity escalate directly to forensic queue.'
    }
  };

  const current = contexts[selectedContext];

  return (
    <div className="space-y-6">
      {/* Flagship Header Banner */}
      <div className="cyber-card p-5 bg-gradient-to-r from-cyan-950/40 via-slate-900/60 to-purple-950/40 border-cyan-500/30">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Sparkles className="w-4 h-4 text-cyan-400" />
              <span className="text-xs font-mono font-semibold uppercase tracking-wider text-cyan-400">
                Core Scientific Proof · Interactive Counterfactual Attribution
              </span>
            </div>
            <h2 className="text-xl font-bold text-white tracking-tight">
              The Exact Same Transaction, Three Relational Contexts
            </h2>
            <p className="text-xs text-slate-300 max-w-3xl mt-1">
              Holding the raw transaction payload strictly bitwise identical (<span className="text-cyan-300 font-mono">₹499.00, P_tabular = 3.84%</span>), observe how historical network topology and temporal velocity govern the final risk decision.
            </p>
          </div>

          {/* Context Selector Buttons */}
          <div className="flex flex-wrap items-center gap-1.5 bg-slate-900/90 p-1.5 rounded-lg border border-slate-800">
            <button
              onClick={() => setSelectedContext('isolated')}
              className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-all ${
                selectedContext === 'isolated'
                  ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 shadow-sm shadow-emerald-500/20'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              1. Isolated User (1:1)
            </button>
            <button
              onClick={() => setSelectedContext('spaced_sharing')}
              className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-all ${
                selectedContext === 'spaced_sharing'
                  ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40 shadow-sm shadow-amber-500/20'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              2. Spaced Office Sharing (8h)
            </button>
            <button
              onClick={() => setSelectedContext('bot_burst')}
              className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-all ${
                selectedContext === 'bot_burst'
                  ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40 shadow-sm shadow-rose-500/20'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              3. Coordinated Bot Burst (30s)
            </button>
          </div>
        </div>
      </div>

      {/* Bitwise Invariant Transaction Payload Display */}
      <div className="cyber-card p-4 bg-slate-900/60 border-slate-800">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-mono font-bold text-cyan-400 uppercase tracking-wider flex items-center gap-1.5">
            <Cpu className="w-3.5 h-3.5" /> Invariant Raw Transaction Payload (Bitwise Constant Across All 3 Contexts)
          </span>
          <span className="text-[11px] font-mono text-emerald-400 bg-emerald-950/40 px-2 py-0.5 rounded border border-emerald-500/30">
            P_tabular = 0.0384 (100% Invariant)
          </span>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 text-xs font-mono">
          <div className="bg-slate-950/50 p-2.5 rounded border border-slate-800/80">
            <span className="text-slate-400 block text-[10px]">Amount:</span>
            <span className="text-white font-bold text-sm">₹{amount.toLocaleString('en-IN')}.00</span>
          </div>
          <div className="bg-slate-950/50 p-2.5 rounded border border-slate-800/80">
            <span className="text-slate-400 block text-[10px]">Device Fingerprint:</span>
            <span className="text-cyan-400 font-semibold truncate block">{deviceId}</span>
          </div>
          <div className="bg-slate-950/50 p-2.5 rounded border border-slate-800/80">
            <span className="text-slate-400 block text-[10px]">Card Hash:</span>
            <span className="text-purple-400 font-semibold truncate block">{cardId}</span>
          </div>
          <div className="bg-slate-950/50 p-2.5 rounded border border-slate-800/80">
            <span className="text-slate-400 block text-[10px]">Email Address:</span>
            <span className="text-slate-300 font-semibold truncate block">{email}</span>
          </div>
          <div className="bg-slate-950/50 p-2.5 rounded border border-slate-800/80">
            <span className="text-slate-400 block text-[10px]">Time of Transaction:</span>
            <span className="text-amber-400 font-semibold truncate block">{timestamp}</span>
          </div>
        </div>
      </div>

      {/* 3-Tier Model Decomposition Card Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* Tier 1: Tabular Model */}
        <div className="cyber-card p-4 bg-slate-900/40 border-slate-800 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded bg-blue-500/20 text-blue-400 flex items-center justify-center border border-blue-500/30">
                  <Cpu className="w-3.5 h-3.5" />
                </div>
                <div>
                  <h4 className="text-xs font-bold text-white">Tier-1: Tabular GBDT</h4>
                  <span className="text-[10px] text-slate-400 font-mono">10 Behavioral Features</span>
                </div>
              </div>
              <span className="badge badge-blue">P_tab = {(current.p_tab * 100).toFixed(2)}%</span>
            </div>
            <div className="space-y-2 text-[11px] text-slate-300 font-mono">
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">TransactionAmt_log:</span>
                <span className="text-white">6.2146</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Card Amount Z-Score:</span>
                <span className="text-white">0.0000</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Diurnal Cycle:</span>
                <span className="text-white">14:00 (Daytime)</span>
              </div>
            </div>
          </div>
          <div className="mt-3 p-2 bg-slate-950/60 rounded text-[11px] text-slate-400 border border-slate-800/80 italic">
            ✅ Transaction appears 100% normal in isolation across all 3 contexts.
          </div>
        </div>

        {/* Tier 2: Relational Graph GBDT */}
        <div className="cyber-card p-4 bg-slate-900/40 border-slate-800 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded bg-purple-500/20 text-purple-400 flex items-center justify-center border border-purple-500/30">
                  <Layers className="w-3.5 h-3.5" />
                </div>
                <div>
                  <h4 className="text-xs font-bold text-white">Tier-2: Relational Graph GBDT</h4>
                  <span className="text-[10px] text-slate-400 font-mono">13 Strict Temporal Features</span>
                </div>
              </div>
              <span className={`badge ${current.p_graph > 0.4 ? 'badge-rose' : (current.p_graph > 0.25 ? 'badge-amber' : 'badge-emerald')}`}>
                P_graph = {(current.p_graph * 100).toFixed(2)}%
              </span>
            </div>
            <div className="space-y-2 text-[11px] text-slate-300 font-mono">
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Inter-Arrival Velocity:</span>
                <span className="text-white font-semibold">{current.velocity}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Temporal Spacing:</span>
                <span className="text-cyan-300">{current.interArrival}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Burst Index:</span>
                <span className="text-purple-300 font-bold">{current.burstScore}</span>
              </div>
            </div>
          </div>
          <div className="mt-3 p-2 bg-slate-950/60 rounded text-[11px] text-slate-300 border border-slate-800/80">
            🕸️ Context: <span className="font-semibold text-cyan-300">{current.subtitle}</span>
          </div>
        </div>

        {/* Tier 3: Multi-Modal Calibrated Fusion */}
        <div className="cyber-card p-4 bg-slate-900/40 border-slate-800 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded bg-emerald-500/20 text-emerald-400 flex items-center justify-center border border-emerald-500/30">
                  <Activity className="w-3.5 h-3.5" />
                </div>
                <div>
                  <h4 className="text-xs font-bold text-white">Tier-3: Calibrated Fusion</h4>
                  <span className="text-[10px] text-slate-400 font-mono">Isotonic Multi-Modal Synthesis</span>
                </div>
              </div>
              <span className={`badge ${current.p_final >= 0.6 ? 'badge-rose' : (current.p_final >= 0.35 ? 'badge-amber' : 'badge-emerald')}`}>
                P_final = {(current.p_final * 100).toFixed(2)}%
              </span>
            </div>
            <div className="space-y-2 text-[11px] text-slate-300 font-mono">
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Gateway Decision:</span>
                <span className="font-bold text-white">{current.action}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Action Level:</span>
                <span className="font-semibold text-amber-300">{current.actionLevel}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Economic Policy:</span>
                <span className="text-slate-300">Min Loss vs Friction</span>
              </div>
            </div>
          </div>
          <div className={`mt-3 p-2 rounded text-[11px] font-mono font-bold border ${current.actionClass}`}>
            {current.verdict}
          </div>
        </div>
      </div>

      {/* The Core Discovery Quote Callout */}
      <div className="cyber-card p-4 bg-gradient-to-r from-slate-900 via-slate-900 to-cyan-950/30 border-slate-800 flex items-center justify-between text-xs">
        <div className="space-y-0.5">
          <span className="text-cyan-400 font-mono font-semibold uppercase tracking-wider block text-[10px]">
            The Core Scientific Conclusion
          </span>
          <p className="text-slate-200 font-medium">
            "The transaction payload remained 100% bitwise identical (<span className="font-mono text-cyan-300">P_tabular = 3.84%</span>). The risk escalation (<span className="font-mono text-emerald-400">10.90%</span> ──► <span className="font-mono text-amber-400">16.43%</span> ──► <span className="font-mono text-rose-400">68.50%</span>) was driven strictly by the surrounding temporal relational context."
          </p>
        </div>
      </div>
    </div>
  );
}
