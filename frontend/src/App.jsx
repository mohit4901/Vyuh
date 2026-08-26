import React, { useState } from 'react';
import Header from './components/Header';
import TwoWorldsDemo from './components/TwoWorldsDemo';
import NetworkGraph from './components/NetworkGraph';
import InvestigationCopilot from './components/InvestigationCopilot';
import CostDial from './components/CostDial';
import BenchmarksView from './components/BenchmarksView';
import AuditTrail from './components/AuditTrail';
import { Shield, Sparkles, Heart } from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('two-worlds');

  return (
    <div className="min-h-screen bg-[#06090e] text-slate-100 flex flex-col font-sans selection:bg-cyan-500/30 selection:text-cyan-200">
      {/* Navbar Header */}
      <Header activeTab={activeTab} setActiveTab={setActiveTab} />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-6">
        {activeTab === 'two-worlds' && <TwoWorldsDemo onSelectGraphNode={() => setActiveTab('graph')} />}
        {activeTab === 'graph' && <NetworkGraph />}
        {activeTab === 'copilot' && <InvestigationCopilot />}
        {activeTab === 'cost-dial' && <CostDial />}
        {activeTab === 'benchmarks' && <BenchmarksView />}
        {activeTab === 'audit' && <AuditTrail />}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-[#04060a] py-6 text-xs text-slate-500 font-mono mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Shield className="w-4 h-4 text-cyan-400" />
            <span>VYUH (व्यूह) 2.0 · Razorpay AI Buildathon 2026</span>
          </div>

          <div className="flex items-center gap-4 text-[11px]">
            <span>Track 02: AI Risk Manager</span>
            <span>•</span>
            <span>Zero Temporal Leakage</span>
            <span>•</span>
            <span>Strictly Defense-Only</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
