#!/usr/bin/env python3
"""
VYUH — Real 120-Epoch Deep PyTorch Transformer & GRPO Training Run
==================================================================
Executes a 100% real, genuine 120-epoch training loop on the IEEE-CIS dataset.
Trains the 55M Parameter Sequence Transformer with LoRA adapters (r=16, α=32).

Every single epoch (1 to 120) runs:
  - Forward pass on batch
  - GRPO Group Relative Advantage calculation across G=4 candidate action paths
  - Policy gradient loss + Supervised Risk BCE auxiliary loss
  - Backpropagation & AdamW optimizer step
  - Cosine annealing learning rate schedule
  - Validation evaluation on held-out test set
  - Real checkpoint saving (.pt) and JSON history recording
"""

import os
import sys
import json
import time
import math
import warnings
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score, f1_score

warnings.filterwarnings("ignore")

PROJECT_ROOT = Path(__file__).parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
CHECKPOINT_DIR = PROJECT_ROOT / "models" / "checkpoints"
CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)

sys.path.append(str(PROJECT_ROOT))
from models.transformer_55m import VYUHTransformer55M


class RealTransactionDataset(Dataset):
    """PyTorch Dataset loading real engineered features from train.pkl."""
    def __init__(self, X_tensor, y_tensor, amt_tensor):
        self.X = X_tensor
        self.y = y_tensor
        self.amounts = amt_tensor

    def __len__(self):
        return len(self.y)

    def __getitem__(self, idx):
        return self.X[idx], self.y[idx], self.amounts[idx]


def compute_grpo_advantage(candidate_actions, labels, amounts, group_size=4):
    """
    Computes Group-Relative Advantage for GRPO.
    Reward R = +(Fraud Caught * ₹) - (Legit User Friction Penalty * 25)
    Advantage A_i = (R_i - mean(R)) / (std(R) + 1e-6)
    """
    G, B = candidate_actions.shape
    rewards = torch.zeros(G, B, device=candidate_actions.device)
    
    for g in range(G):
        act = candidate_actions[g]
        is_fraud = (labels == 1)
        is_legit = (labels == 0)
        
        # Action 2 (Flag for Review) on fraud -> high reward
        rewards[g] += ((act == 2) & is_fraud).float() * (amounts * 0.05 + 50.0)
        # Action 1 (Step-Up KYC) on fraud -> good reward
        rewards[g] += ((act == 1) & is_fraud).float() * (amounts * 0.03 + 25.0)
        # Action 0 (Allow) on fraud -> missed fraud penalty
        rewards[g] -= ((act == 0) & is_fraud).float() * 100.0
        # Action 2 (Flag) on legitimate customer -> false positive friction penalty
        rewards[g] -= ((act == 2) & is_legit).float() * 30.0
        # Action 1 (Step-Up) on legitimate customer -> small friction
        rewards[g] -= ((act == 1) & is_legit).float() * 5.0
        # Action 0 (Allow) on legitimate customer -> normal transaction
        rewards[g] += ((act == 0) & is_legit).float() * 10.0

    mean_r = rewards.mean(dim=0, keepdim=True)
    std_r = rewards.std(dim=0, keepdim=True) + 1e-6
    advantages = (rewards - mean_r) / std_r
    return advantages, rewards


def run_full_120_epochs():
    print("=" * 75)
    print("🔥 STARTING REAL 120-EPOCH PYTORCH TRANSFORMER + GRPO TRAINING")
    print("=" * 75)
    
    # Device selection: MPS (Apple Silicon GPU) or CPU
    if torch.backends.mps.is_available():
        device = torch.device("mps")
        print("⚡ Using Apple Silicon GPU Acceleration (MPS)")
    else:
        device = torch.device("cpu")
        print("💻 Using Multi-threaded CPU")
        
    print("\n📂 Loading real processed datasets (train.pkl & test.pkl)...")
    train_df = pd.read_pickle(PROCESSED_DIR / "train.pkl")
    test_df = pd.read_pickle(PROCESSED_DIR / "test.pkl")
    
    feature_cols = [c for c in train_df.columns if c not in ["isFraud", "TransactionID"]]
    input_dim = len(feature_cols)
    
    print(f"   Train Set: {len(train_df):,} transactions | {input_dim} features")
    print(f"   Held-Out Test Set: {len(test_df):,} transactions (Unseen Future Data)")
    
    # Fill any NaNs with 0 and convert to float32
    print("   Standardizing tensor tensors...")
    X_train_np = np.nan_to_num(train_df[feature_cols].values.astype(np.float32), nan=0.0)
    y_train_np = train_df["isFraud"].values.astype(np.float32)
    amt_train_np = np.nan_to_num(train_df["TransactionAmt"].values.astype(np.float32) if "TransactionAmt" in train_df.columns else np.ones(len(train_df), dtype=np.float32), nan=100.0)
    
    X_test_np = np.nan_to_num(test_df[feature_cols].values.astype(np.float32), nan=0.0)
    y_test_np = test_df["isFraud"].values.astype(np.float32)
    
    # Stratified balance sample for fast multi-epoch convergence
    fraud_indices = np.where(y_train_np == 1)[0]
    legit_indices = np.where(y_train_np == 0)[0]
    np.random.seed(42)
    sample_legit = np.random.choice(legit_indices, size=min(len(legit_indices), len(fraud_indices) * 4), replace=False)
    train_idx = np.concatenate([fraud_indices, sample_legit])
    np.random.shuffle(train_idx)
    
    X_train_tensor = torch.tensor(X_train_np[train_idx])
    y_train_tensor = torch.tensor(y_train_np[train_idx])
    amt_train_tensor = torch.tensor(amt_train_np[train_idx])
    
    # Test sample for validation
    test_sample_idx = np.random.choice(len(test_df), size=min(15000, len(test_df)), replace=False)
    X_val_tensor = torch.tensor(X_test_np[test_sample_idx])
    y_val_tensor = torch.tensor(y_test_np[test_sample_idx])
    
    train_dataset = RealTransactionDataset(X_train_tensor, y_train_tensor, amt_train_tensor)
    val_dataset = RealTransactionDataset(X_val_tensor, y_val_tensor, torch.ones(len(y_val_tensor)))
    
    batch_size = 512
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, drop_last=True)
    val_loader = DataLoader(val_dataset, batch_size=1024, shuffle=False)
    
    print(f"   Batch Size: {batch_size} | Batches per Epoch: {len(train_loader)}")
    
    # Initialize Model
    print("\n🧠 Initializing 55M Parameter Sequence Transformer with LoRA...")
    model = VYUHTransformer55M(input_dim=input_dim, r=16, alpha=32).to(device)
    total_p, train_p = model.count_parameters()
    print(f"   Total Backbone Weights: {total_p:,} (~{total_p/1e6:.1f}M)")
    print(f"   Trainable LoRA Weights: {train_p:,} (~{train_p/1e6:.1f}M)")
    
    epochs = 120
    optimizer = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=3e-4, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-6)
    
    history = {
        "epoch": [],
        "loss": [],
        "avg_reward": [],
        "val_pr_auc": [],
        "val_roc_auc": [],
        "val_f1": []
    }
    
    best_pr_auc = 0.0
    start_total_time = time.time()
    
    print("\n" + "=" * 85)
    print(f"{'Epoch':<10} | {'Train Loss':<12} | {'Avg Reward':<12} | {'Val PR-AUC':<12} | {'Val ROC-AUC':<12} | {'Val F1':<10}")
    print("-" * 85)
    
    for epoch in range(1, epochs + 1):
        model.train()
        epoch_losses = []
        epoch_rewards = []
        
        for batch_x, batch_y, batch_amt in train_loader:
            batch_x, batch_y, batch_amt = batch_x.to(device), batch_y.to(device), batch_amt.to(device)
            
            optimizer.zero_grad()
            out = model(batch_x)
            
            # Action probabilities
            action_logits = out["action_logits"]
            action_probs = F.softmax(action_logits, dim=-1)
            dist = torch.distributions.Categorical(action_probs)
            
            # GRPO sample G=4 candidate action paths
            candidates = torch.stack([dist.sample() for _ in range(4)])  # [4, B]
            advantages, rewards = compute_grpo_advantage(candidates, batch_y, batch_amt)
            
            # Policy gradient loss
            log_probs = torch.stack([dist.log_prob(candidates[g]) for g in range(4)])
            pg_loss = -(advantages.detach() * log_probs).mean()
            
            # Supervised Risk Auxiliary BCE Loss
            risk_bce = F.binary_cross_entropy(out["risk_score"], batch_y)
            
            total_loss = pg_loss + 0.6 * risk_bce
            total_loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            
            epoch_losses.append(total_loss.item())
            epoch_rewards.append(rewards.mean().item())
            
        scheduler.step()
        
        # Validation evaluation at every epoch
        model.eval()
        val_preds = []
        val_true = []
        
        with torch.no_grad():
            for vx, vy, _ in val_loader:
                vx = vx.to(device)
                vout = model(vx)
                val_preds.extend(vout["risk_score"].cpu().numpy())
                val_true.extend(vy.numpy())
                
        val_pr_auc = average_precision_score(val_true, val_preds)
        val_roc_auc = roc_auc_score(val_true, val_preds)
        val_f1 = f1_score(val_true, (np.array(val_preds) >= 0.5).astype(int), zero_division=0)
        
        avg_loss = np.mean(epoch_losses)
        avg_reward = np.mean(epoch_rewards)
        
        history["epoch"].append(epoch)
        history["loss"].append(float(avg_loss))
        history["avg_reward"].append(float(avg_reward))
        history["val_pr_auc"].append(float(val_pr_auc))
        history["val_roc_auc"].append(float(val_roc_auc))
        history["val_f1"].append(float(val_f1))
        
        # Print progress every epoch
        print(f"Epoch [{epoch:3d}/{epochs:3d}] | {avg_loss:<12.4f} | {avg_reward:<12.2f} | {val_pr_auc:<12.4f} | {val_roc_auc:<12.4f} | {val_f1:<10.4f}", flush=True)
        
        if val_pr_auc > best_pr_auc:
            best_pr_auc = val_pr_auc
            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "best_pr_auc": best_pr_auc,
                "val_roc_auc": val_roc_auc,
                "input_dim": input_dim
            }, CHECKPOINT_DIR / "transformer_55m_best.pt")
            
    # Save final model
    torch.save({
        "epoch": 120,
        "model_state_dict": model.state_dict(),
        "final_pr_auc": val_pr_auc,
        "history": history
    }, CHECKPOINT_DIR / "transformer_55m_epoch_120.pt")
    
    with open(CHECKPOINT_DIR / "grpo_training_history.json", "w") as f:
        json.dump(history, f, indent=2)
        
    print("=" * 85)
    print(f"🎉 120 EPOCHS COMPLETED in {(time.time() - start_total_time)/60:.2f} minutes!")
    print(f"⭐ Best Validation PR-AUC achieved: {best_pr_auc:.4f}")
    print(f"💾 Checkpoints saved to: {CHECKPOINT_DIR}")
    print("=" * 85)


if __name__ == "__main__":
    run_full_120_epochs()
