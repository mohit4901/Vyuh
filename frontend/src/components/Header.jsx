import React from 'react';
import { Shield, Activity, Network, Sparkles, Sliders, BarChart3, FileText } from 'lucide-react';

export default function Header({ activeTab, setActiveTab }) {
  const navItems = [
    { id: 'two-worlds', label: 'Two Worlds Demo', icon: Sparkles },
    { id: 'graph', label: 'Fraud Ring Graph', icon: Network },
    { id: 'copilot', label: 'Investigation Copilot', icon: Activity },
    { id: 'cost-dial', label: '₹ Cost Calibration', icon: Sliders },
    { id: 'benchmarks', label: 'Verified Benchmarks', icon: BarChart3 },
    { id: 'audit', label: 'Audit Trail', icon: FileText },
  ];

  return (
    <header className="sticky top-0 z-50 border-b" style={{ background: 'rgba(9, 13, 20, 0.92)', borderColor: '#1e293b', backdropFilter: 'blur(16px)', WebkitBackdropFilter: 'blur(16px)' }}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3.5 flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Brand & Badge */}
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center rounded-lg border border-cyan-500/40" style={{ width: '42px', height: '42px', background: 'linear-gradient(135deg, rgba(14, 165, 233, 0.25) 0%, rgba(59, 130, 246, 0.35) 100%)', boxShadow: '0 0 20px rgba(56, 189, 248, 0.2)' }}>
            <Shield className="w-5 h-5 text-cyan-400" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold tracking-tight text-white font-sans flex items-center gap-1.5">
                VYUH <span className="text-cyan-400 font-mono font-semibold text-sm">(व्यूह)</span>
              </h1>
              <span className="badge badge-cyan text-[10px]">Track 02: AI Risk Manager</span>
            </div>
            <p className="text-xs text-slate-400 font-mono">
              Temporal Relational Fraud Intelligence Gateway
            </p>
          </div>
        </div>

        {/* Status Indicators */}
        <div className="hidden lg:flex items-center gap-3 text-xs font-mono">
          <div className="flex items-center gap-2 px-3 py-1 rounded-md border" style={{ background: 'rgba(16, 185, 129, 0.1)', borderColor: 'rgba(16, 185, 129, 0.3)', color: '#34d399' }}>
            <span className="pulse-dot bg-emerald-400"></span>
            <span>Live ML Engine: P50 = 7.46ms</span>
          </div>
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-md border" style={{ background: 'rgba(56, 189, 248, 0.1)', borderColor: 'rgba(56, 189, 248, 0.3)', color: '#38bdf8' }}>
            <span>Strictly Defense-Only</span>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6">
        <nav className="flex items-center gap-2 overflow-x-auto py-2" style={{ borderTop: '1px solid rgba(30, 41, 59, 0.5)' }}>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`nav-tab-btn ${isActive ? 'active' : ''}`}
              >
                <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-cyan-400' : 'text-slate-400'}`} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
