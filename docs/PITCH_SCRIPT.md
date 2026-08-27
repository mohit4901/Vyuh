# VYUH — 5-Minute Razorpay AI Buildathon Pitch Script

**Track**: Track 02: AI Risk Manager  
**Title**: VYUH (व्यूह) — Temporal Relational Fraud Intelligence

---

## ⏱️ Video / Interview Timeline & Structure

### [0:00 – 0:35] The Core Problem & The Relational Blindspot
> *"In payment risk management, individual transactions often look completely normal. A ₹499 checkout at 2:00 PM with a standard email and card has an individual tabular risk score of only 3.8%. A transaction-level model can see very little reason to escalate this payment. But for coordinated multi-account abuse, the fraud signal does not live inside a single transaction—it lives in the temporal relationships between otherwise ordinary transactions across shared hardware and card subnets."*

### [0:35 – 1:20] The Engineering Insight & Evolution
> *"VYUH detects fraud not only from what a payment looks like, but from what is happening around it over time.  
> When we built our first prototype, we discovered our early 94.5% syndicate recall was driven by a hand-coded heuristic shortcut rather than learned intelligence.  
> We eliminated the heuristic entirely, engineered 13 strict backward-looking temporal relational features, and trained a 23-feature joint GBDT using 5-fold cross-validation on historical IEEE-CIS data."*

### [1:20 – 2:10] Real-World Evidence & Statistical Significance
> *"On 118,108 untouched held-out transactions from IEEE-CIS, adding temporal relational features increased PR-AUC from 0.1124 to 0.1456—an absolute lift of +0.0333 (+29.6% relative lift), with a strictly positive bootstrap 95% confidence interval of [+0.0247, +0.0418].  
> Most importantly for payment operations, at a strict 1.0% false-positive rate, fraud recall increased from 7.60% to 11.49%—a +51.2% relative increase in caught fraud."*

### [2:10 – 3:15] The Canonical Counterfactual Demonstration
> *"The core finding of VYUH is simple: 'The transaction didn't change. The context did.'  
> Holding the raw ₹499 payload strictly bitwise identical:  
> On an isolated personal device, the joint risk is 10.9% and the gateway allows the transaction.  
> When 4 coworkers share an office network across 8 hours, human spacing yields a moderate 16.4% risk, triggering a non-blocking step-up.  
> But when a bot script replays 10 accounts on the same hardware within 30 seconds, the 1-hour velocity and degree explode the risk to 68.5%, escalating to an immediate forensic review.  
> The payment payload remained identical. Only its temporal relational context shifted."*

### [3:15 – 4:10] Production Latency, Failure Safety & Blindspot Transparency
> *"In production engineering, our in-memory graph traverses subgraphs in 0.51 milliseconds, achieving a P50 end-to-end latency of 7.46 milliseconds on standard CPU. If the Python process crashes under SIGKILL, our gateway fails closed with HTTP 503 and non-destructive 2FA.  
> And we are transparent about system boundaries: if an attacker uses single-use rotating proxies with disposable virtual cards and zero entity reuse, the graph degree is 1 and the relational signal is uninformative. In that regime, VYUH gracefully relies on transaction-level tabular anomaly detection."*

### [4:10 – 5:00] Illustrative Economics & Conclusion
> *"Finally, in an illustrative economic scenario on a ₹100 Crore / month GMV merchant volume, catching +51.2% more fraud at a fixed 1% false-positive rate prevents an incremental ₹5.83 Lakhs in chargeback losses every month.  
> VYUH does not claim that graphs magically solve all fraud. It measures where relational intelligence helps, where it fails, and what happens when the surrounding temporal context changes."*
