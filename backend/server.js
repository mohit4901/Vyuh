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
    architecture: {
      canonicalModel: 'M3: 23-Feature Joint Temporal-Relational GBDT',
      tier1Tabular: {
        model: 'M1: Tabular LightGBM Baseline (10 Features)',
        features: 'Amount, LogAmt, Cyclical Hour (sin/cos), Night Indicator, Rolling Card Velocity & Z-Score',
        purpose: 'Isolated transaction-level anomaly detection'
      },
      tier2Relational: {
        model: 'M2: Temporal Relational Graph GBDT (13 Features)',
        features: '24h Device/Card Degrees, 1h Burst Velocities, Ring Size, 2-Hop Neighborhoods, Switch Rates',
        purpose: 'Temporal relational coordination & abuse detection'
      },
      tier3Joint: {
        model: 'M3: Joint Concat GBDT (23 Features) + M4 Isotonic Calibration',
        features: '23 Features (10 Tabular + 13 Temporal Relational Jointly Optimized)',
        purpose: 'Canonical Winner — High-capacity multi-modal risk scoring'
      }
    },
    dataset: {
      name: 'IEEE-CIS Fraud Detection (Untouched Historical Holdout)',
      totalRecords: 590540,
      heldOutTestSet: 118108,
      temporalTrainSet: 472432,
      rawFraudRate: '3.44%',
      splitMethod: 'Strict Chronological Temporal Split (58-second gap, zero future leakage)'
    },
    coreMetrics: {
      prAucBaselineM1: 0.1124,
      prAucRelationalM2: 0.1251,
      prAucJointM3: 0.1456,
      prAucCalibratedM4: 0.1402,
      deltaPrAuc: 0.0333,
      deltaPrAucRelativeLift: '+29.6%',
      bootstrap95CI: [0.0247, 0.0418],
      recallAt1PctFprM1: '7.60%',
      recallAt1PctFprM3: '11.49%',
      recallAt1PctFprRelativeLift: '+51.2%',
      recallAt05PctFprM1: '3.94%',
      recallAt05PctFprM3: '7.31%',
      recallAt05PctFprRelativeLift: '+85.5%',
      latencyP50Ms: 7.46,
      latencyP95Ms: 8.38,
      latencyP99Ms: 13.55,
      graphTraversalP50Ms: 0.514,
      activeThreshold: 0.15
    }
  });
});

/**
 * Adaptive Risk Budget (Enterprise Merchant Policy Endpoint)
 */
app.get('/api/risk-budget', (req, res) => {
  const profile = req.query.profile || 'high_ticket_electronics';
  const customBudget = req.query.budget ? parseFloat(req.query.budget) : null;
  const customAOV = req.query.aov ? parseFloat(req.query.aov) : null;

  const result = decisionEngine.calculateAdaptiveRiskBudget(profile, customBudget, customAOV);
  res.json(result);
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
  const threshold = parseFloat(req.query.threshold) || 0.52;
  const aov = parseFloat(req.query.aov) || 1850;
  const friction = parseFloat(req.query.friction) || 350;

  const result = decisionEngine.calculateCostDial(threshold, aov, friction);
  res.json(result);
});

/**
 * Live Transaction Scoring (Bridges to Python Live Inference Service)
 */
app.post('/api/score', async (req, res) => {
  const txnData = req.body;
  if (!txnData) {
    return res.status(400).json({ error: 'Transaction payload required' });
  }

  try {
    const result = await decisionEngine.evaluateTransaction(txnData);
    if (result.status === 'SERVICE_UNAVAILABLE') {
      return res.status(503).json(result);
    }
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
    if (result.status === 'SERVICE_UNAVAILABLE') {
      return res.status(503).json(result);
    }
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
    finalIncrementalStudy: decisionEngine.finalIncrementalStudy,
    adversarialResults: decisionEngine.adversarialResults,
    economicScenario: decisionEngine.economicScenario,
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
