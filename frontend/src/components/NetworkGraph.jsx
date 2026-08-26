import React, { useEffect, useRef, useState } from 'react';
import cytoscape from 'cytoscape';
import { Network, ZoomIn, ZoomOut, RotateCcw, Info, ShieldAlert, Users, CreditCard, Laptop } from 'lucide-react';

export default function NetworkGraph() {
  const containerRef = useRef(null);
  const cyRef = useRef(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [graphStats, setGraphStats] = useState({
    totalAccounts: 42,
    sharedDevices: 1,
    sharedCards: 3,
    confirmedFraudNodes: 3,
    suspiciousVolumeINR: '₹20,958'
  });

  useEffect(() => {
    if (!containerRef.current) return;

    // Load sample fraud ring payload
    fetch('/api/graph/sample')
      .then(res => res.json())
      .then(data => {
        const elements = data.elements || [];
        
        // Initialize Cytoscape
        cyRef.current = cytoscape({
          container: containerRef.current,
          elements: elements.length > 0 ? elements : getFallbackElements(),
          style: [
            {
              selector: 'node[type = "transaction"]',
              style: {
                'background-color': '#f43f5e',
                'label': 'data(label)',
                'color': '#f8fafc',
                'font-size': '9px',
                'font-family': 'JetBrains Mono',
                'text-valign': 'bottom',
                'text-margin-y': 4,
                'width': 24,
                'height': 24,
                'border-width': 2,
                'border-color': '#fda4af'
              }
            },
            {
              selector: 'node[type = "device"]',
              style: {
                'background-color': '#38bdf8',
                'label': 'data(label)',
                'color': '#38bdf8',
                'font-size': '10px',
                'font-weight': 'bold',
                'font-family': 'JetBrains Mono',
                'text-valign': 'top',
                'text-margin-y': -4,
                'width': 36,
                'height': 36,
                'border-width': 3,
                'border-color': '#bae6fd'
              }
            },
            {
              selector: 'node[type = "card"]',
              style: {
                'background-color': '#a855f7',
                'label': 'data(label)',
                'color': '#c084fc',
                'font-size': '9px',
                'font-family': 'JetBrains Mono',
                'text-valign': 'bottom',
                'text-margin-y': 4,
                'width': 28,
                'height': 28,
                'border-width': 2,
                'border-color': '#e9d5ff'
              }
            },
            {
              selector: 'node[type = "email"]',
              style: {
                'background-color': '#f59e0b',
                'label': 'data(label)',
                'color': '#fbbf24',
                'font-size': '8px',
                'font-family': 'JetBrains Mono',
                'width': 20,
                'height': 20
              }
            },
            {
              selector: 'edge',
              style: {
                'width': 1.5,
                'line-color': '#334155',
                'curve-style': 'bezier',
                'opacity': 0.7
              }
            },
            {
              selector: ':selected',
              style: {
                'border-width': 4,
                'border-color': '#38bdf8',
                'line-color': '#38bdf8',
                'opacity': 1.0
              }
            }
          ],
          layout: {
            name: 'cose',
            idealEdgeLength: 60,
            nodeOverlap: 20,
            refresh: 20,
            fit: true,
            padding: 30,
            randomize: false,
            componentSpacing: 100,
            nodeRepulsion: 400000,
            edgeElasticity: 100,
            nestingFactor: 5,
            gravity: 80,
            numIter: 1000
          }
        });

        // Node click listener
        cyRef.current.on('tap', 'node', (evt) => {
          const node = evt.target;
          setSelectedNode(node.data());
        });

        cyRef.current.on('tap', (evt) => {
          if (evt.target === cyRef.current) {
            setSelectedNode(null);
          }
        });
      })
      .catch(err => {
        console.warn('Could not load graph payload, using fallback:', err);
      });

    return () => {
      if (cyRef.current) {
        cyRef.current.destroy();
      }
    };
  }, []);

  const handleZoomIn = () => cyRef.current?.zoom(cyRef.current.zoom() * 1.25);
  const handleZoomOut = () => cyRef.current?.zoom(cyRef.current.zoom() * 0.8);
  const handleFit = () => cyRef.current?.fit();

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="cyber-card p-5 bg-gradient-to-r from-slate-900 via-slate-900/90 to-cyan-950/40">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Network className="w-4 h-4 text-cyan-400" />
              <span className="text-xs font-mono font-semibold uppercase tracking-wider text-cyan-400">
                Stage 2 Dynamic Graph Sentinel
              </span>
            </div>
            <h2 className="text-xl font-bold text-white tracking-tight">
              Coordinated Fraud Syndicate Ring (#RING-017)
            </h2>
            <p className="text-xs text-slate-300 max-w-2xl mt-1">
              Interactive topological entity-relationship graph. Observe how 42 micro-transactions are tethered to single hardware fingerprint <code className="text-cyan-400">MacIntel-X88</code> and card cluster <code className="text-purple-400">4111-XXXX-2849</code>.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="badge badge-rose text-xs">
              <ShieldAlert className="w-3.5 h-3.5" /> 42 Accounts Exposed
            </span>
          </div>
        </div>
      </div>

      {/* Ring Statistics Bar */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 text-xs font-mono">
        <div className="cyber-card p-3 bg-slate-900/70 border-slate-800">
          <span className="text-slate-400 block text-[11px]">Member Accounts:</span>
          <span className="text-white font-bold text-base flex items-center gap-1.5 mt-0.5">
            <Users className="w-4 h-4 text-rose-400" /> {graphStats.totalAccounts}
          </span>
        </div>
        <div className="cyber-card p-3 bg-slate-900/70 border-slate-800">
          <span className="text-slate-400 block text-[11px]">Shared Hardware:</span>
          <span className="text-cyan-400 font-bold text-base flex items-center gap-1.5 mt-0.5">
            <Laptop className="w-4 h-4 text-cyan-400" /> {graphStats.sharedDevices} Device
          </span>
        </div>
        <div className="cyber-card p-3 bg-slate-900/70 border-slate-800">
          <span className="text-slate-400 block text-[11px]">Card Subnets:</span>
          <span className="text-purple-400 font-bold text-base flex items-center gap-1.5 mt-0.5">
            <CreditCard className="w-4 h-4 text-purple-400" /> {graphStats.sharedCards} Cards
          </span>
        </div>
        <div className="cyber-card p-3 bg-slate-900/70 border-slate-800">
          <span className="text-slate-400 block text-[11px]">Confirmed Chargebacks:</span>
          <span className="text-rose-400 font-bold text-base flex items-center gap-1.5 mt-0.5">
            <ShieldAlert className="w-4 h-4 text-rose-400" /> {graphStats.confirmedFraudNodes} Nodes
          </span>
        </div>
        <div className="cyber-card p-3 bg-slate-900/70 border-slate-800">
          <span className="text-slate-400 block text-[11px]">Burst Volume:</span>
          <span className="text-amber-400 font-bold text-base flex items-center gap-1.5 mt-0.5">
            {graphStats.suspiciousVolumeINR}
          </span>
        </div>
      </div>

      {/* Main Canvas + Inspector Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Cytoscape Canvas */}
        <div className="lg:col-span-3 cyber-card p-2 relative bg-[#070b10] border-slate-800 h-[520px] rounded-xl overflow-hidden">
          {/* Controls Overlay */}
          <div className="absolute top-4 right-4 z-10 flex flex-col gap-1.5 bg-slate-900/90 p-1.5 rounded-lg border border-slate-700/80 backdrop-blur-md">
            <button onClick={handleZoomIn} className="p-1.5 rounded hover:bg-slate-800 text-slate-300 hover:text-white" title="Zoom In">
              <ZoomIn className="w-4 h-4" />
            </button>
            <button onClick={handleZoomOut} className="p-1.5 rounded hover:bg-slate-800 text-slate-300 hover:text-white" title="Zoom Out">
              <ZoomOut className="w-4 h-4" />
            </button>
            <button onClick={handleFit} className="p-1.5 rounded hover:bg-slate-800 text-slate-300 hover:text-white" title="Reset View">
              <RotateCcw className="w-4 h-4" />
            </button>
          </div>

          {/* Legend */}
          <div className="absolute bottom-4 left-4 z-10 flex flex-wrap gap-2.5 bg-slate-900/90 px-3 py-2 rounded-lg border border-slate-700/80 backdrop-blur-md text-[11px] font-mono">
            <span className="flex items-center gap-1.5 text-rose-300">
              <span className="w-2.5 h-2.5 rounded-full bg-rose-500"></span> Fraud Ring Order
            </span>
            <span className="flex items-center gap-1.5 text-cyan-300">
              <span className="w-2.5 h-2.5 rounded-full bg-cyan-400"></span> Shared Device
            </span>
            <span className="flex items-center gap-1.5 text-purple-300">
              <span className="w-2.5 h-2.5 rounded-full bg-purple-500"></span> Shared Card
            </span>
          </div>

          <div ref={containerRef} className="w-full h-full"></div>
        </div>

        {/* Node Detail Inspector */}
        <div className="cyber-card p-5 space-y-4 bg-slate-900/60 border-slate-800 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 mb-3 pb-2 border-b border-slate-800">
              <Info className="w-4 h-4 text-cyan-400" />
              <h3 className="text-sm font-bold text-white">Entity Inspector</h3>
            </div>

            {selectedNode ? (
              <div className="space-y-3 text-xs font-mono">
                <div>
                  <span className="text-slate-400 block text-[11px]">Entity Label:</span>
                  <span className="text-white font-bold text-sm">{selectedNode.label}</span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[11px]">Entity Type:</span>
                  <span className="badge badge-cyan text-[10px] mt-0.5">{selectedNode.type}</span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[11px]">Fraud Classification:</span>
                  <span className={`badge ${selectedNode.isFraud ? 'badge-rose' : 'badge-emerald'} text-[10px] mt-0.5`}>
                    {selectedNode.isFraud ? 'CONFIRMED SYNDICATE' : 'CONNECTED NODE'}
                  </span>
                </div>
                {selectedNode.amount > 0 && (
                  <div>
                    <span className="text-slate-400 block text-[11px]">Order Amount:</span>
                    <span className="text-emerald-400 font-bold">₹{selectedNode.amount}</span>
                  </div>
                )}
                <div>
                  <span className="text-slate-400 block text-[11px]">Louvain Community:</span>
                  <span className="text-purple-400 font-semibold">Cluster #RING-017</span>
                </div>
              </div>
            ) : (
              <div className="py-12 text-center text-xs text-slate-500 space-y-2 font-mono">
                <Network className="w-8 h-8 mx-auto text-slate-600 opacity-50" />
                <p>Click any node on the graph canvas to inspect topological forensic links.</p>
              </div>
            )}
          </div>

          <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 text-[11px] text-slate-400">
            <span className="text-cyan-400 font-semibold block mb-0.5 font-mono">Graph Extraction Speed:</span>
            Vectorized Louvain extracted across 118k test nodes in <strong>1.84s</strong>.
          </div>
        </div>
      </div>
    </div>
  );
}

function getFallbackElements() {
  const elements = [
    { data: { id: 'dev_X88', label: 'Device: MacIntel-X88', type: 'device', isFraud: true } },
    { data: { id: 'card_2849', label: 'Card: 4111-XXXX-2849', type: 'card', isFraud: true } }
  ];
  for (let i = 1; i <= 15; i++) {
    const txnId = `txn_${4400 + i}`;
    elements.push({
      data: { id: txnId, label: `Order #${4400 + i}`, type: 'transaction', isFraud: true, amount: 499 }
    });
    elements.push({ data: { id: `e1_${i}`, source: txnId, target: 'dev_X88' } });
    if (i % 2 === 0) {
      elements.push({ data: { id: `e2_${i}`, source: txnId, target: 'card_2849' } });
    }
  }
  return elements;
}
