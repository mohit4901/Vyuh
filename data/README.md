# Data Management & Preprocessing

This directory manages the raw and processed datasets used for training and evaluating VYUH.

---

## 1. Datasets Used

### Primary Dataset: IEEE-CIS Fraud Detection
* **Source**: [IEEE-CIS Fraud Detection Competition (Vesta Corp / Kaggle)](https://www.kaggle.com/c/ieee-fraud-detection)
* **Total Transactions**: 590,540 real-world e-commerce checkout records
* **Total Raw Features**: 394 features across transaction and identity tables
* **Split Methodology**: Chronological holdout split (80% Train: 472,432 rows, 20% Test: 118,108 rows) with a strict 58-second temporal gap.

---

## 2. Expected Directory Structure

```
data/
├── README.md                      # This documentation
├── download.py                    # Automated dataset fetcher script
├── raw/
│   └── ieee-cis/
│       ├── train_transaction.csv  # Raw IEEE-CIS transaction table
│       └── train_identity.csv     # Raw IEEE-CIS device identity table
├── processed/
│   ├── train.pkl                  # 472,432 chronological training rows
│   └── test.pkl                   # 118,108 untouched historical holdout rows
└── graphs/
    └── ieee_entity_graph.json     # Precomputed entity graph structure
```

---

## 3. How to Obtain and Prepare Data

### Step 1: Set Kaggle Credentials
Set your Kaggle credentials via standard environment variables or `~/.kaggle/kaggle.json`:
```bash
export KAGGLE_USERNAME="your_kaggle_username"
export KAGGLE_KEY="your_kaggle_api_key"
```

### Step 2: Download the Raw Dataset
Run the download script:
```bash
python data/download.py
```

### Step 3: Chronological Splitting & Feature Extraction
The preprocessing pipeline sorts transactions chronologically by timestamp (`TransactionDT`), ensuring all relational and graph features are computed strictly backward-looking ($t < T_i$) without future information leakage.
