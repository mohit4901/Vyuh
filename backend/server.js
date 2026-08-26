/**
 * VYUH — Enterprise REST API Server
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
  contentSecurityPolicy: false // Allows Cytoscape CDN and dynamic inline styles
}));
app.use(cors());
app.use(express.json());
app.use(morgan('dev'));

// Static files for frontend dashboard
app.use(express.static(path.join(__dirname, '..', 'frontend')));

// --- REST API ENDPOINTS ---

/**
 * Health Check & System Status
 */
app.get('/api/health', (req, res) => {
  res.json({
    status: 'healthy',
    system: 'VYUH AI Risk Manager',
    version: '1.0.0',
    track: 'Track 02: AI Risk Manager',
    mode: 'Strictly Defense-Only',
    timestamp: new Date().toISOString()
  });
});

/**
 * System Overview & Performance Summary
 */
app.get('/api/stats', (req, res) => {
  res.json({
    dataset: {
      name: 'IEEE-CIS Fraud Detection + Elliptic Bitcoin',
      totalRecords: 590540,
      heldOutTestSet: 118108,
      temporalTrainSet: 472432,
      rawFraudRate: '3.50%',
      splitMethod: 'Strict 80:20 Temporal Split (Zero Data Leakage)'
    },
    models: {
      stage1: 'LightGBM High-Capacity Ensemble (<15ms)',
      stage2: 'Dynamic Entity Graph + Louvain Community Sentinel',
      stage3: '55M Financial Sequence Transformer with LoRA (r=16, α=32) + GRPO (120 Epochs)'
    },
    coreMetrics: {
      prAuc: 0.6259,
      rocAuc: 0.9204,
      ablationDeltaVsM1: '+38.3%',
      ellipticIllicitF1: 0.815,
      activeThreshold: 0.70
    }
  });
});

/**
 * Cytoscape.js Entity Graph Payload
 */
app.get('/api/graph/sample', (req, res) => {
  res.json({
    graphName: 'Coordinated Multi-Account Fraud Ring (#R-2847)',
    detectedTimestamp: new Date().toISOString(),
    elements: decisionEngine.graphSample
  });
});

/**
 * Dynamic Cost-Calibrated Threshold Slider
 */
app.get('/api/cost-dial', (req, res) => {
  const threshold = parseFloat(req.query.threshold) || 0.70;
  const aov = parseFloat(req.query.aov) || 1850;
  const friction = parseFloat(req.query.friction) || 350;

  const result = decisionEngine.calculateCostDial(threshold, aov, friction);
  res.json(result);
});

/**
 * Score Single Transaction or Stream
 */
app.post('/api/score', (req, res) => {
  const txnData = req.body;
  if (!txnData) {
    return res.status(400).json({ error: 'Transaction payload required' });
  }

  const result = decisionEngine.evaluateTransaction(txnData);
  res.json(result);
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
    ellipticLiteratureBenchmark: decisionEngine.ellipticResults,
    baselineM1: decisionEngine.m1Results
  });
});

// Fallback to frontend
app.use((req, res) => {
  res.sendFile(path.join(__dirname, '..', 'frontend', 'index.html'));
});

// Start Server
app.listen(PORT, () => {
  console.log('====================================================');
  console.log(`🛡️  VYUH AI Risk Manager REST API Live on Port ${PORT}`);
  console.log(`🌐 Dashboard: http://localhost:${PORT}`);
  console.log(`📊 Health Endpoint: http://localhost:${PORT}/api/health`);
  console.log('====================================================');
});
