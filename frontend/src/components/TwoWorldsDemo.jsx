import React, { useState } from 'react';
import { AlertTriangle, CheckCircle2, ShieldAlert, Clock, ArrowRight, Sparkles, RefreshCw, Cpu, Split, HelpCircle } from 'lucide-react';

export default function TwoWorldsDemo({ onSelectGraphNode }) {
  const [amount, setAmount] = useState(499);
  const [deviceId, setDeviceId] = useState('MacIntel-X88');
  const [cardId, setCardId] = useState('4111-XXXX-2849');
  const [email, setEmail] = useState('rajesh.k@gmail.com');
  const [isSimulating, setIsSimulating] = useState(false);
  const [activeScenario, setActiveScenario] = useState('syndicate'); // 'syndicate' or 'clean'

  const handleScenarioChange = (scenario) => {
    setActiveScenario(scenario);
    if (scenario === 'syndicate') {
      setAmount(499);
      setDeviceId('MacIntel-X88');
      setCardId('4111-XXXX-2849');
      setEmail('rajesh.k@gmail.com');
    } else {
      setAmount(1250);
      setDeviceId('iPhone14-iOS17');
      setCardId('5241-XXXX-9102');
      setEmail('amit.verma@corp.in');
    }
  };

  const isSyndicate = activeScenario === 'syndicate';

  return (
    <div className="space-y-6">
      {/* Flagship Pitch Banner */}
      <div className="cyber-card p-5 bg-gradient-to-r from-cyan-950/40 via-slate-900/60 to-purple-950/40 border-cyan-500/30">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Sparkles className="w-4 h-4 text-cyan-400" />
              <span className="text-xs font-mono font-semibold uppercase tracking-wider text-cyan-400">
                Core Innovation Demonstration
              </span>
            </div>
            <h2 className="text-xl font-bold text-white tracking-tight">
              The Same Transaction, Two Worlds
            </h2>
            <p className="text-xs text-slate-300 max-w-3xl mt-1">
              Observe how a ₹499 transaction that appears 100% clean to traditional isolated classifiers is exposed as a coordinated 42-account syndicate once evaluated across the temporal entity graph.
            </p>
          </div>

          <div className="flex items-center gap-2 bg-slate-900/80 p-1.5 rounded-lg border border-slate-800">
            <button
              onClick={() => handleScenarioChange('syndicate')}
              className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-all ${
                isSyndicate
                  ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40 shadow-sm shadow-rose-500/20'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              🚨 Syndicate Ring Attack
            </button>
            <button
              onClick={() => handleScenarioChange('clean')}
              className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-all ${
                !isSyndicate
                  ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 shadow-sm shadow-emerald-500/20'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              ✅ Legitimate Payment
            </button>
          </div>
        </div>
      </div>

      {/* Transaction Attribute Inspector */}
      <div className="cyber-card p-4 grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono bg-slate-900/50">
        <div>
          <span className="text-slate-400 block text-[11px]">Transaction Amount:</span>
          <span className="text-white font-bold text-sm">₹{amount.toLocaleString('en-IN')}</span>
        </div>
        <div>
          <span className="text-slate-400 block text-[11px]">Device Fingerprint:</span>
          <span className="text-cyan-400 font-semibold truncate block">{deviceId}</span>
        </div>
        <div>
          <span className="text-slate-400 block text-[11px]">Card Hash Subnet:</span>
          <span className="text-purple-400 font-semibold truncate block">{cardId}</span>
        </div>
        <div>
          <span className="text-slate-400 block text-[11px]">Registered Email:</span>
          <span className="text-slate-300 font-semibold truncate block">{email}</span>
        </div>
      </div>

      {/* Side-by-Side Two Worlds Comparison */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* World A: Isolated Transaction Classifier */}
        <div className={`cyber-card p-5 relative overflow-hidden transition-all ${
          isSyndicate ? 'border-emerald-500/30' : 'border-emerald-500/30'
        }`}>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-slate-800 flex items-center justify-center text-slate-300 border border-slate-700">
                <Cpu className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white">WORLD A: Isolated Transaction View</h3>
                <span className="text-[11px] font-mono text-slate-400">Traditional Per-Order Classifier</span>
              </div>
            </div>
            <span className="badge badge-emerald">CLEAN ✅</span>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-400">Calculated Risk Score:</span>
              <span className="text-lg font-mono font-bold text-emerald-400">
                {isSyndicate ? '0.06' : '0.04'} <span className="text-xs text-slate-400 font-normal">/ 1.00</span>
              </span>
            </div>

            <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
              <div className="bg-emerald-500 h-2 rounded-full" style={{ width: isSyndicate ? '6%' : '4%' }}></div>
            </div>

            <div className="pt-2 border-t border-slate-800/80 space-y-1.5 text-xs text-slate-300">
              <p className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
                <span>Amount is within normal merchant ticket threshold (₹{amount})</span>
              </p>
              <p className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
                <span>Single checkout attempt on card (0 velocity anomalies in isolation)</span>
              </p>
              <p className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
                <span>Valid browser header & IP geo-consistency verified</span>
              </p>
            </div>
          </div>

          <div className="mt-4 p-3 rounded-lg bg-emerald-950/20 border border-emerald-500/30 flex items-center justify-between text-xs">
            <span className="font-mono text-emerald-300 font-medium">Recommended Action:</span>
            <span className="font-mono font-bold text-emerald-400 uppercase tracking-wider">ALLOW &amp; CLEAR</span>
          </div>
          <p className="text-[11px] text-slate-400 mt-2 italic text-center">
            ⚠️ Structural Blindspot: Fails to evaluate multi-account hardware replay across independent accounts.
          </p>
        </div>

        {/* World B: VYUH Temporal Entity Graph Sentinel */}
        <div className={`cyber-card p-5 relative overflow-hidden transition-all ${
          isSyndicate ? 'border-rose-500/40 glow-border-rose' : 'border-emerald-500/30'
        }`}>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <div className={`w-8 h-8 rounded-lg flex items-center justify-center border ${
                isSyndicate ? 'bg-rose-500/20 text-rose-400 border-rose-500/40' : 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40'
              }`}>
                <ShieldAlert className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white">WORLD B: VYUH Temporal Network Sentinel</h3>
                <span className="text-[11px] font-mono text-cyan-400">Graph + Burst Reasoning Layer</span>
              </div>
            </div>
            <span className={`badge ${isSyndicate ? 'badge-rose' : 'badge-emerald'}`}>
              {isSyndicate ? '🚨 FRAUD RING ALERT' : 'CLEAN NETWORK'}
            </span>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-400">Calibrated Network Risk:</span>
              <span className={`text-lg font-mono font-bold ${isSyndicate ? 'text-rose-400' : 'text-emerald-400'}`}>
                {isSyndicate ? '0.94' : '0.05'} <span className="text-xs text-slate-400 font-normal">/ 1.00</span>
              </span>
            </div>

            <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
              <div
                className={`h-2 rounded-full transition-all duration-500 ${isSyndicate ? 'bg-rose-500' : 'bg-emerald-500'}`}
                style={{ width: isSyndicate ? '94%' : '5%' }}
              ></div>
            </div>

            <div className="pt-2 border-t border-slate-800/80 space-y-1.5 text-xs text-slate-300">
              {isSyndicate ? (
                <>
                  <p className="flex items-center gap-2 text-rose-300">
                    <AlertTriangle className="w-3.5 h-3.5 text-rose-400 flex-shrink-0" />
                    <span>Hardware '{deviceId}' replayed across <strong>42 distinct user profiles</strong></span>
                  </p>
                  <p className="flex items-center gap-2 text-rose-300">
                    <AlertTriangle className="w-3.5 h-3.5 text-rose-400 flex-shrink-0" />
                    <span>Temporal Velocity Burst: <strong>42 transactions in 47 minutes</strong></span>
                  </p>
                  <p className="flex items-center gap-2 text-rose-300">
                    <AlertTriangle className="w-3.5 h-3.5 text-rose-400 flex-shrink-0" />
                    <span>Louvain Cluster #RING-017 contains 3 historically confirmed chargebacks</span>
                  </p>
                </>
              ) : (
                <>
                  <p className="flex items-center gap-2 text-emerald-300">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
                    <span>Dedicated personal hardware signature (1:1 account binding)</span>
                  </p>
                  <p className="flex items-center gap-2 text-emerald-300">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
                    <span>Zero community syndicate linkages or card subnet replay</span>
                  </p>
                </>
              )}
            </div>
          </div>

          <div className={`mt-4 p-3 rounded-lg flex items-center justify-between text-xs border ${
            isSyndicate ? 'bg-rose-950/20 border-rose-500/40 text-rose-300' : 'bg-emerald-950/20 border-emerald-500/30 text-emerald-300'
          }`}>
            <span className="font-mono font-medium">Bounded Action:</span>
            <span className={`font-mono font-bold uppercase tracking-wider ${isSyndicate ? 'text-rose-400' : 'text-emerald-400'}`}>
              {isSyndicate ? 'FLAG_HUMAN_REVIEW' : 'ALLOW'}
            </span>
          </div>
          <p className="text-[11px] text-slate-400 mt-2 text-center">
            {isSyndicate ? '🛡️ 100% Defense-Only: Escalate to risk analyst with forensic evidence brief. Zero auto-ban.' : 'Cleared & logged to immutable audit trail.'}
          </p>
        </div>
      </div>

      {/* Temporal "What Changed?" Diff Timeline & Counterfactuals */}
      {isSyndicate && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Temporal Diff Timeline */}
          <div className="cyber-card p-5 space-y-3">
            <div className="flex items-center gap-2 mb-2">
              <Clock className="w-4 h-4 text-cyan-400" />
              <h3 className="text-sm font-bold text-white">Temporal "What Changed?" Anomaly Timeline</h3>
            </div>
            <p className="text-xs text-slate-400">
              Explains why this entity transitioned from benign to high risk within the last 45 minutes:
            </p>

            <div className="space-y-2.5 pt-2 border-l-2 border-slate-800 ml-3 pl-4 text-xs font-mono">
              <div className="relative">
                <span className="absolute -left-[23px] top-1 w-2.5 h-2.5 rounded-full bg-emerald-400"></span>
                <div className="flex items-center justify-between text-slate-400">
                  <span className="text-emerald-400 font-bold">T - 42 min</span>
                  <span>Risk: 0.08 (CLEAN)</span>
                </div>
                <p className="text-slate-300 mt-0.5">First transaction observed on clean IP &amp; isolated device.</p>
              </div>

              <div className="relative">
                <span className="absolute -left-[23px] top-1 w-2.5 h-2.5 rounded-full bg-amber-400"></span>
                <div className="flex items-center justify-between text-slate-400">
                  <span className="text-amber-400 font-bold">T - 25 min</span>
                  <span>Risk: 0.42 (ELEVATING)</span>
                </div>
                <p className="text-slate-300 mt-0.5">Device reused across 4 unrelated user profiles within 10 min.</p>
              </div>

              <div className="relative">
                <span className="absolute -left-[23px] top-1 w-2.5 h-2.5 rounded-full bg-rose-400"></span>
                <div className="flex items-center justify-between text-slate-400">
                  <span className="text-rose-400 font-bold">T - 8 min</span>
                  <span>Risk: 0.78 (BURST)</span>
                </div>
                <p className="text-slate-300 mt-0.5">High-velocity micro-testing burst: 18 checkout attempts across 3 cards.</p>
              </div>

              <div className="relative">
                <span className="absolute -left-[23px] top-1 w-2.5 h-2.5 rounded-full bg-rose-500 animate-ping"></span>
                <span className="absolute -left-[23px] top-1 w-2.5 h-2.5 rounded-full bg-rose-500"></span>
                <div className="flex items-center justify-between text-rose-400">
                  <span className="font-bold">T - 0 min (Current)</span>
                  <span className="font-bold">Risk: 0.94 (ALERT)</span>
                </div>
                <p className="text-white font-medium mt-0.5">42-Account Syndicate confirmed. Escalated for human review.</p>
              </div>
            </div>
          </div>

          {/* Counterfactual Attribution Analysis */}
          <div className="cyber-card p-5 space-y-3">
            <div className="flex items-center gap-2 mb-2">
              <Split className="w-4 h-4 text-purple-400" />
              <h3 className="text-sm font-bold text-white">Counterfactual Sensitivity Analysis</h3>
            </div>
            <p className="text-xs text-slate-400">
              Mathematically proves which specific entity links are driving the risk elevation:
            </p>

            <div className="space-y-3 pt-1">
              <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800 space-y-1">
                <div className="flex items-center justify-between text-xs font-mono">
                  <span className="text-purple-300 font-semibold">Intervention: Remove Shared Hardware Link</span>
                  <span className="badge badge-purple text-[10px]">ΔRisk: -76.0%</span>
                </div>
                <p className="text-xs text-slate-300">
                  If this transaction occurred on a dedicated, private device, calibrated risk falls from <strong>0.94 → 0.18 (ALLOW)</strong>.
                </p>
              </div>

              <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800 space-y-1">
                <div className="flex items-center justify-between text-xs font-mono">
                  <span className="text-purple-300 font-semibold">Intervention: Remove Card Subnet Replay</span>
                  <span className="badge badge-purple text-[10px]">ΔRisk: -58.0%</span>
                </div>
                <p className="text-xs text-slate-300">
                  If this card had not appeared in previous unrelated merchant checkouts, risk drops from <strong>0.94 → 0.36 (STEP_UP_AUTH)</strong>.
                </p>
              </div>

              <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800 space-y-1">
                <div className="flex items-center justify-between text-xs font-mono">
                  <span className="text-cyan-300 font-semibold">Intervention: Complete Network Isolation</span>
                  <span className="badge badge-cyan text-[10px]">ΔRisk: -88.0%</span>
                </div>
                <p className="text-xs text-slate-300">
                  Without graph neighborhood context (per-transaction baseline), model evaluates risk at <strong>0.06 (ALLOW)</strong>.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
