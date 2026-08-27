# VYUH 2.1 — Adversarial Stress Testing & Known Limitations

**Canonical Artifact**: `models/checkpoints/adversarial_attack_characterization.json`

---

## 1. Adversarial Attack Characterization

| Attack / Scenario Regime | Evasion Mechanism | P_tab | P_graph | P_joint | Gateway Action | Detection Outcome |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **1. Baseline Single User** | Clean personal hardware; 1:1 binding | 0.0384 | 0.1551 | 0.1090 | ALLOW | ✅ Passed (Clean 1-Click Checkout) |
| **2. Legitimate Office NAT** | Coworkers sharing network spaced across 8 hours | 0.0384 | 0.4016 | 0.1643 | STEP-UP_AUTH | ✅ Passed (Human Spacing Prevents Review Hold) |
| **3. Coordinated Bot Burst** | 10 synthetic accounts in 30s on same hardware | 0.0384 | 0.4850 | 0.6850 | FLAG_HUMAN_REVIEW | ✅ Caught (Velocity & Shared Degree Spike) |
| **4. Low-and-Slow Attack** | Multi-day spacing to evade 1-hour velocity | 0.0384 | 0.4423 | 0.1662 | STEP-UP_AUTH | ⚠️ Partial Catch (24h Degree Flags Linkage) |
| **5. Fully Distributed Attack** | Disposable proxy + virtual card (**Zero Reuse**) | 0.0384 | 0.1551 | 0.1090 | ALLOW | ❌ **Disclosed Blindspot (Zero Entity Reuse)** |
| **6. Rapid Carding Attack** | Testing 8 stolen cards on single emulator in 45s | 0.0384 | 0.3337 | 0.1633 | STEP-UP_AUTH | ✅ Caught (Hardware Switch Rate Escalates Challenge) |

---

## 2. Explicitly Disclosed Architectural Limitations

### 1. Zero-Entity-Reuse Distributed Attacks (Primary Blindspot)
* **Threat Model**: Adversaries using single-use residential rotating proxies, disposable hardware fingerprints, and dynamic virtual credit cards.
* **Why Relational Intelligence Fails**: When every transaction uses a novel device ID, unique card token, and fresh email address, the live graph degree remains strictly $1$, the 1-hour velocity remains $1$, and connected component size remains $1$.
* **Mitigation**: VYUH gracefully degrades to the Tier-1 Tabular GBDT ($M1$).

### 2. Historical IEEE-CIS Dataset vs Modern Tokenization
* IEEE-CIS represents historical ecommerce traffic. Modern payments utilize tokenized cards (Network Tokens / Apple Pay) where device-card linkages operate under different baseline distributions.

### 3. Benchmark vs Production Latency Scope
* The canonical latency profile (P50: 7.46ms, P95: 8.38ms, P99: 13.55ms) was measured in local single-core CPU microservice execution. Production multi-region deployments will incur additional network transit hops.

### 4. Illustrative Nature of Economic Projections
* The ₹100 Crore GMV merchant impact model is an illustrative projection applying holdout operating points to a representative volume model, not measured production merchant savings.
