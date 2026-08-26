import React, { useState, useEffect } from 'react';
import { FileText, ShieldCheck, ShieldAlert, CheckCircle2, Clock, Terminal } from 'lucide-react';

export default function AuditTrail() {
  const [logs, setLogs] = useState([]);

  useEffect(() => {
    fetch('/api/audit-trail?limit=50')
      .then(res => res.json())
      .then(data => {
        if (data.logs) setLogs(data.logs);
      })
      .catch(err => console.warn('Could not load audit trail:', err));
  }, []);

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="cyber-card p-5 bg-gradient-to-r from-slate-900 via-slate-900/90 to-cyan-950/40">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <FileText className="w-4 h-4 text-cyan-400" />
              <span className="text-xs font-mono font-semibold uppercase tracking-wider text-cyan-400">
                Layer 5 Compliance &amp; Accountability
              </span>
            </div>
            <h2 className="text-xl font-bold text-white tracking-tight">
              Immutable Defense Audit Trail
            </h2>
            <p className="text-xs text-slate-300 max-w-2xl mt-1">
              Deterministic, tamper-evident ledger recording all bounded actions, network risk scores, and forensic chain-of-thought evidence briefs.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="badge badge-cyan text-xs">
              <ShieldCheck className="w-3.5 h-3.5" /> 100% Defense-Only Policy
            </span>
          </div>
        </div>
      </div>

      {/* Logs Table */}
      <div className="cyber-card p-5 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Terminal className="w-4 h-4 text-slate-400" />
            Decision Audit Stream ({logs.length} Logged Events)
          </h3>
          <span className="text-xs font-mono text-slate-400">Append-Only Immutable Ledger</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-xs font-mono text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 bg-slate-950/60">
                <th className="p-3">Decision ID &amp; Time</th>
                <th className="p-3">Order &amp; Amount</th>
                <th className="p-3">Device / Card Hash</th>
                <th className="p-3">Isolated vs Network Risk</th>
                <th className="p-3">Bounded Action</th>
                <th className="p-3">Policy Reason</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {logs.map((log, idx) => (
                <tr key={idx} className="hover:bg-slate-800/30 transition-colors">
                  <td className="p-3">
                    <span className="text-cyan-400 font-semibold block">{log.decisionId || `DEC-${idx+1000}`}</span>
                    <span className="text-[11px] text-slate-500 block">{new Date(log.timestamp).toLocaleTimeString()}</span>
                  </td>
                  <td className="p-3 font-sans">
                    <span className="font-semibold text-white block">{log.orderId}</span>
                    <span className="text-[11px] font-mono text-emerald-400">₹{log.amountINR?.toLocaleString('en-IN') || '499'}</span>
                  </td>
                  <td className="p-3">
                    <span className="text-cyan-300 block">{log.deviceId}</span>
                    <span className="text-[11px] text-purple-400 block">{log.cardId}</span>
                  </td>
                  <td className="p-3">
                    <span className="text-slate-400 block text-[11px]">Iso: {(log.isolatedRisk || 0.06).toFixed(2)}</span>
                    <span className="text-rose-400 font-bold block">Net: {(log.riskScore || 0.94).toFixed(2)}</span>
                  </td>
                  <td className="p-3">
                    <span className={`badge ${
                      log.action === 'FLAG_HUMAN_REVIEW'
                        ? 'badge-rose'
                        : log.action === 'STEP_UP_AUTH'
                        ? 'badge-amber'
                        : 'badge-emerald'
                    } text-[10px]`}>
                      {log.action}
                    </span>
                  </td>
                  <td className="p-3 max-w-xs truncate text-slate-400 text-[11px] font-sans">
                    {log.actionDescription || 'Normal transaction cleared and logged.'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
