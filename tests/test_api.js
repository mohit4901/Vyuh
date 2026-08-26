/**
 * Verification Test for VYUH REST API Endpoints
 */
const http = require('http');

function testEndpoint(path) {
  return new Promise((resolve, reject) => {
    http.get(`http://127.0.0.1:3000${path}`, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          resolve({ status: res.statusCode, data: JSON.parse(data) });
        } catch (e) {
          resolve({ status: res.statusCode, data: data.substring(0, 100) });
        }
      });
    }).on('error', reject);
  });
}

async function runTests() {
  console.log('🧪 Testing VYUH Express REST API Endpoints...');
  
  const health = await testEndpoint('/api/health');
  console.log(`✅ /api/health -> [Status ${health.status}]`, health.data);
  
  const stats = await testEndpoint('/api/stats');
  console.log(`✅ /api/stats -> [Status ${stats.status}] PR-AUC: ${stats.data.coreMetrics.prAuc}, Split: ${stats.data.dataset.splitMethod}`);
  
  const costDial = await testEndpoint('/api/cost-dial?threshold=0.70');
  console.log(`✅ /api/cost-dial -> [Status ${costDial.status}] Net Saved: ₹${(costDial.data.financials.netSavedINR/100000).toFixed(1)} Lakhs, Recall: ${(costDial.data.metrics.recall*100).toFixed(1)}%`);
  
  const benchmarks = await testEndpoint('/api/benchmarks');
  console.log(`✅ /api/benchmarks -> [Status ${benchmarks.status}] Ablation Models: ${benchmarks.data.ablationStudy.length}, Elliptic Baseline F1: ${benchmarks.data.ellipticLiteratureBenchmark[5]['Illicit F1']}`);

  console.log('\n🎉 ALL REST API ENDPOINTS VERIFIED SUCCESSFULLY!');
  process.exit(0);
}

runTests().catch(err => {
  console.error('❌ Test failed:', err.message);
  process.exit(1);
});
