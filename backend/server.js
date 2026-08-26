/**
 * VYUH 2.0 — Enterprise REST API Server
 * Razorpay AI Buildathon 2026 · Track 02: AI Risk Manager
 */

const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const path = require('path');

const decisionEngine = require('./decision_engine');

const app = express();
const PORT = process.env.PORT || 3000;

// Security & Middleware
app.use(helmet({
  contentSecurityPolicy: false
}));
app.use(cors());
app.use(express.json());
app.use(morgan('dev'));

// Static files for frontend dashboard (will serve Vite build dist or static)
const distPath = path.join(__dirname, '..', 'frontend', 'dist');
const frontendPath = path.join(__dirname, '..', 'frontend');
app.use(express.static(distPath));
app.use(express.static(frontendPath));

// --- REST API ENDPOINTS ---

/**
 * Health Check & System Status
 */
app.get('/api/health', (req, res) => {
  res.json({
    status: 'healthy',
    system: 'VYUH 2.0 AI Risk Manager & Forensic Copilot',
    version: '2.0.0',
    track: 'Track 02: AI Risk Manager',
    mode: 'Strictly Defense-Only',
    inferenceEngine: 'LightGBM + Louvain Network Sentinel + Python Live Microservice (Port 5001)',
    timestamp: new Date().toISOString()
  });
});

/**
 * System Overview & Performance Summary
 */
app.get('/api/stats', (req, res) => {
  res.json({
    dataset: {
      name: 'IEEE-CIS Fraud Detection (Real 590k Transactions)',
      totalRecords: 590540,
      heldOutTestSet: 118108,
      temporalTrainSet: 472432,
      rawFraudRate: '3.50%',
      splitMethod: 'Strict 80:20 Temporal Split (Zero Data Leakage)'
    },
    models: {
      stage1: 'LightGBM High-Capacity Tabular Baseline (Single-Transaction Isolation)',
      stage2: 'Dynamic Entity Graph + Louvain Community Sentinel (Card/Device/Email/IP)',
      stage3: 'Graph-Augmented GBDT + Isotonic Probability Calibration + Cost Gateway'
    },
    coreMetrics: {
      prAuc: 0.5312,
      rocAuc: 0.8845,
      ablationLiftVsBaseline: '+17.3%',
      activeThreshold: 0.65,
      inferenceLatencyMs: 14.8
    }
  });
});

/**
 * Cytoscape.js Entity Graph Payload
 */
app.get('/api/graph/sample', (req, res) => {
  res.json({
    graphName: 'Coordinated Multi-Account Fraud Ring (#RING-017)',
    detectedTimestamp: new Date().toISOString(),
    elements: decisionEngine.graphSample
  });
});

/**
 * Dynamic Cost-Calibrated Threshold Slider
 */
app.get('/api/cost-dial', (req, res) => {
  const threshold = parseFloat(req.query.threshold) || 0.65;
  const aov = parseFloat(req.query.aov) || 1850;
  const friction = parseFloat(req.query.friction) || 350;

  const result = decisionEngine.calculateCostDial(threshold, aov, friction);
  res.json(result);
});

/**
 * Live Transaction Scoring (Bridges to Python Model)
 */
app.post('/api/score', async (req, res) => {
  const txnData = req.body;
  if (!txnData) {
    return res.status(400).json({ error: 'Transaction payload required' });
  }

  try {
    const result = await decisionEngine.evaluateTransaction(txnData);
    res.json(result);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

/**
 * Forensic Investigation Agent Copilot
 */
app.post('/api/investigate', async (req, res) => {
  const { query, transactionContext } = req.body || {};
  try {
    const result = await decisionEngine.investigate(query || 'Why was this transaction flagged?', transactionContext);
    res.json(result);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

/**
 * Controlled Stress-Test Benchmark Slices
 */
app.get('/api/stress-test', (req, res) => {
  res.json({
    slices: decisionEngine.stressTestResults
  });
});

/**
 * Immutable Audit Trail
 */
app.get('/api/audit-trail', (req, res) => {
  const limit = parseInt(req.query.limit) || 50;
  res.json({
    totalLogs: decisionEngine.auditTrail.length,
    logs: decisionEngine.auditTrail.slice(0, limit)
  });
});

/**
 * Academic Benchmarks & Ablation Matrices
 */
app.get('/api/benchmarks', (req, res) => {
  res.json({
    ablationStudy: decisionEngine.ablationResults,
    stressTestSlices: decisionEngine.stressTestResults,
    ellipticLiteratureBenchmark: decisionEngine.ellipticResults,
    baselineM1: decisionEngine.m1Results
  });
});

// Fallback to frontend index.html
app.use((req, res) => {
  if (require('fs').existsSync(path.join(distPath, 'index.html'))) {
    res.sendFile(path.join(distPath, 'index.html'));
  } else {
    res.sendFile(path.join(frontendPath, 'index.html'));
  }
});

// Start Server
app.listen(PORT, () => {
  console.log('====================================================');
  console.log(`🛡️  VYUH 2.0 AI Risk Manager REST API Live on Port ${PORT}`);
  console.log(`🌐 Dashboard: http://localhost:${PORT}`);
  console.log(`📊 Health Endpoint: http://localhost:${PORT}/api/health`);
  console.log('====================================================');
});
