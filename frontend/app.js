/**
 * VYUH (व्यूह) — Frontend Application Engine
 * Renders Cytoscape.js Entity Graphs, Dynamic Cost Slider,
 * Real-Time Audit Feed, and Academic Benchmark Tables.
 */

let cy = null;

document.addEventListener('DOMContentLoaded', async () => {
  console.log('🛡️ VYUH Sentinel Dashboard Initializing...');

  await initializeCytoscape();
  await loadStats();
  await loadBenchmarks();
  await loadAuditTrail();
  setupCostDial();
  setupSimulator();
});

/**
 * 1. Initialize Cytoscape.js Entity-Ring Graph
 */
async function initializeCytoscape() {
  const container = document.getElementById('cy-container');
  if (!container) return;

  try {
    const res = await fetch('/api/graph/sample');
    const data = await res.json();
    const elements = data.elements || [];

    cy = cytoscape({
      container: container,
      elements: elements,
      style: [
        {
          selector: 'node',
          style: {
            'label': 'data(label)',
            'color': '#cbd5e1',
            'font-size': '9px',
            'font-family': 'JetBrains Mono',
            'text-valign': 'bottom',
            'text-margin-y': 4,
            'background-color': '#475569',
            'width': 22,
            'height': 22,
            'border-width': 1.5,
            'border-color': '#64748b'
          }
        },
        // Fraud Transactions
        {
          selector: 'node[type = "transaction"][?isFraud]',
          style: {
            'background-color': '#ef4444',
            'border-color': '#f87171',
            'width': 28,
            'height': 28,
            'shadow-blur': 12,
            'shadow-color': '#ef4444'
          }
        },
        // Normal Transactions
        {
          selector: 'node[type = "transaction"][!isFraud]',
          style: {
            'background-color': '#10b981',
            'border-color': '#34d399',
            'width': 20,
            'height': 20
          }
        },
        // Shared Devices (Critical Ring Hubs)
        {
          selector: 'node[type = "device"]',
          style: {
            'background-color': '#3b82f6',
            'border-color': '#93c5fd',
            'shape': 'diamond',
            'width': 34,
            'height': 34,
            'shadow-blur': 15,
            'shadow-color': '#3b82f6'
          }
        },
        // Cards
        {
          selector: 'node[type = "card"]',
          style: {
            'background-color': '#f59e0b',
            'border-color': '#fde68a',
            'shape': 'round-rectangle',
            'width': 28,
            'height': 20
          }
        },
        // Emails
        {
          selector: 'node[type = "email"]',
          style: {
            'background-color': '#a855f7',
            'border-color': '#e9d5ff',
            'shape': 'hexagon',
            'width': 24,
            'height': 24
          }
        },
        // Edges
        {
          selector: 'edge',
          style: {
            'width': 1.2,
            'line-color': 'rgba(255, 255, 255, 0.15)',
            'curve-style': 'bezier',
            'target-arrow-shape': 'none'
          }
        }
      ],
      layout: {
        name: 'cose',
        animate: false,
        randomize: false,
        componentSpacing: 60,
        nodeRepulsion: 800000,
        edgeElasticity: 100,
        nestingFactor: 5,
        gravity: 80,
        numIter: 1000
      }
    });

    // Node Click Event -> Inspection Drawer
    cy.on('tap', 'node', (evt) => {
      const node = evt.target;
      const data = node.data();
      const inspector = document.getElementById('node-inspector');
      const title = document.getElementById('inspector-title');
      const body = document.getElementById('inspector-body');

      inspector.classList.remove('hidden');
      title.innerText = `Entity Node: ${data.id}`;

      body.innerHTML = `
        <div><strong>Type:</strong> ${data.type ? data.type.toUpperCase() : 'UNKNOWN'}</div>
        <div><strong>Label:</strong> ${data.label || 'N/A'}</div>
        <div><strong>Status:</strong> <span style="color: ${data.isFraud ? '#ef4444' : '#10b981'}">${data.isFraud ? '🚨 FRAUD RING COLLUSION' : '✅ CLEAN'}</span></div>
        ${data.amount ? `<div><strong>Amount:</strong> ₹${data.amount.toFixed(2)}</div>` : ''}
        <div><strong>Connected Edges:</strong> ${node.connectedEdges().length} links</div>
      `;
    });

    document.getElementById('close-drawer')?.addEventListener('click', () => {
      document.getElementById('node-inspector')?.classList.add('hidden');
    });

  } catch (err) {
    console.error('Failed to load Cytoscape graph:', err);
  }
}

/**
 * 2. Load Core Stats
 */
async function loadStats() {
  try {
    const res = await fetch('/api/stats');
    const stats = await res.json();

    document.getElementById('stat-total-txns').innerText = stats.dataset.heldOutTestSet.toLocaleString();
    document.getElementById('stat-pr-auc').innerText = stats.coreMetrics.prAuc.toFixed(4);
  } catch (e) {
    console.warn('Could not load stats:', e);
  }
}

/**
 * 3. Interactive Cost-Calibrated Dial
 */
function setupCostDial() {
  const slider = document.getElementById('threshold-slider');
  if (!slider) return;

  const updateDial = async (val) => {
    const threshold = parseFloat(val);
    document.getElementById('active-threshold-val').innerText = `θ = ${threshold.toFixed(2)}`;

    try {
      const res = await fetch(`/api/cost-dial?threshold=${threshold}`);
      const data = await res.json();

      document.getElementById('dial-recall').innerText = `${(data.metrics.recall * 100).toFixed(1)}%`;
      document.getElementById('dial-fp-cost').innerText = `₹${(data.financials.falsePositiveFrictionINR / 1000).toFixed(1)}K`;
      document.getElementById('dial-fn-loss').innerText = `₹${(data.financials.fraudMissedLossINR / 100000).toFixed(1)}L`;
      
      const netSavedLakhs = (data.financials.netSavedINR / 100000).toFixed(1);
      document.getElementById('dial-net-saved').innerText = `₹${netSavedLakhs} Lakhs`;
      document.getElementById('stat-net-saved').innerText = `₹${netSavedLakhs}L`;
    } catch (e) {
      console.warn('Error updating cost dial:', e);
    }
  };

  slider.addEventListener('input', (e) => updateDial(e.target.value));
  updateDial(slider.value);
}

/**
 * 4. Load Benchmarks & 5-Model Ablation Table
 */
async function loadBenchmarks() {
  try {
    const res = await fetch('/api/benchmarks');
    const data = await res.json();

    // Ablation Table
    const ablationTbody = document.getElementById('ablation-tbody');
    if (ablationTbody && data.ablationStudy) {
      ablationTbody.innerHTML = data.ablationStudy.map((row, idx) => `
        <tr class="${idx === 4 ? 'table-highlight-row' : ''}">
          <td><strong>${row.Model}</strong></td>
          <td>${row['PR-AUC']}</td>
          <td>${row['ROC-AUC']}</td>
          <td>${row['F1-Score']}</td>
          <td><span class="delta-badge">${row['Delta vs M1']}</span></td>
        </tr>
      `).join('');
    }

    // Elliptic Benchmark Table
    const ellipticTbody = document.getElementById('elliptic-tbody');
    if (ellipticTbody && data.ellipticLiteratureBenchmark) {
      ellipticTbody.innerHTML = data.ellipticLiteratureBenchmark.map((row, idx) => `
        <tr class="${idx === 5 ? 'table-highlight-row' : ''}">
          <td><strong>${row['Model / Method']}</strong></td>
          <td>${row.Type}</td>
          <td><strong>${row['Illicit F1'].toFixed(3)}</strong></td>
        </tr>
      `).join('');
    }
  } catch (e) {
    console.warn('Error loading benchmarks:', e);
  }
}

/**
 * 5. Real-Time Defense-Only Audit Trail
 */
async function loadAuditTrail() {
  try {
    const res = await fetch('/api/audit-trail');
    const data = await res.json();

    const container = document.getElementById('audit-feed-container');
    if (!container || !data.logs) return;

    container.innerHTML = data.logs.map(log => `
      <div class="audit-item level-${log.actionLevel}">
        <div class="audit-header-row">
          <div>
            <span class="audit-id">${log.orderId}</span> · 
            <span>₹${log.amountINR}</span> · 
            <span style="color: var(--primary-blue)">${log.deviceId}</span>
          </div>
          <div class="audit-action-badge badge-${log.actionLevel}">${log.action}</div>
        </div>
        <div class="audit-brief">${log.evidenceBrief}</div>
      </div>
    `).join('');
  } catch (e) {
    console.warn('Error loading audit trail:', e);
  }
}

/**
 * 6. Live Ingestion Simulator
 */
function setupSimulator() {
  const btnRing = document.getElementById('btn-inject-ring');
  const btnNormal = document.getElementById('btn-inject-normal');

  btnRing?.addEventListener('click', async () => {
    btnRing.disabled = true;
    btnRing.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Analyzing Network Links...`;

    try {
      const res = await fetch('/api/score', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          orderId: `ORD-${Math.floor(100000 + Math.random() * 900000)}`,
          amount: 2499,
          cardId: '4111-XXXX-2849',
          deviceId: 'MacIntel-X88',
          email: 'syndicate_node@gmail.com',
          isRingMember: true,
          ringSize: 42,
          sharedDevices: 38
        })
      });
      const result = await res.json();
      await loadAuditTrail();
    } catch (e) {
      console.warn('Simulation error:', e);
    } finally {
      btnRing.disabled = false;
      btnRing.innerHTML = `<i class="fa-solid fa-triangle-exclamation"></i> Inject Coordinated Ring (42 Accounts)`;
    }
  });

  btnNormal?.addEventListener('click', async () => {
    try {
      await fetch('/api/score', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          orderId: `ORD-${Math.floor(100000 + Math.random() * 900000)}`,
          amount: 850,
          cardId: '5241-XXXX-4411',
          deviceId: `iPhone15-${Math.floor(10 + Math.random() * 90)}`,
          email: 'clean_buyer@gmail.com',
          isRingMember: false,
          ringSize: 1,
          sharedDevices: 1
        })
      });
      await loadAuditTrail();
    } catch (e) {
      console.warn('Normal injection error:', e);
    }
  });
}
