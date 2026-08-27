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
    <header className="border-b border-[#1e293b] bg-[#090d14]/90 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Brand & Badge */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500/20 to-blue-600/30 border border-cyan-500/40 flex items-center justify-center shadow-lg shadow-cyan-500/10">
            <Shield className="w-5 h-5 text-cyan-400" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold tracking-tight text-white font-sans flex items-center gap-1.5">
                VYUH <span className="text-cyan-400 font-mono font-medium text-sm">(व्यूह) 2.1</span>
              </h1>
              <span className="badge badge-cyan text-[10px] py-0.5">Track 02: AI Risk Manager</span>
            </div>
            <p className="text-xs text-slate-400 font-mono">
              Temporal Relational Fraud Intelligence Gateway
            </p>
          </div>
        </div>

        {/* Status Indicators */}
        <div className="hidden lg:flex items-center gap-3 text-xs font-mono">
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
            <span className="pulse-dot bg-emerald-400"></span>
            Inference: P50 = 7.46ms (Single-Core CPU)
          </div>
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
            100% Defense-Only
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6">
        <nav className="flex space-x-1 overflow-x-auto py-2 no-scrollbar">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`flex items-center gap-2 px-3.5 py-2 text-xs font-semibold rounded-lg transition-all whitespace-nowrap ${
                  isActive
                    ? 'bg-cyan-500/15 text-cyan-400 border border-cyan-500/40 shadow-sm shadow-cyan-500/20'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40 border border-transparent'
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-cyan-400' : 'text-slate-500'}`} />
                {item.label}
              </button>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
