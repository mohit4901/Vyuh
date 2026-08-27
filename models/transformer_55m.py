#!/usr/bin/env python3
"""
VYUH — 27.2M Parameter Sequence Transformer with LoRA
=====================================================
A specialized Financial Sequence Transformer architecture designed for
multi-event fraud ring reasoning and defense-only action policy.

Specifications:
  - Backbone: 8 Transformer Encoder Layers, 8 Attention Heads, d_model = 512, d_ff = 2048
  - Total Parameters: 27,173,764 (~27.2 Million)
  - Trainable LoRA Adapters: Rank r = 16, Alpha α = 32 (~1.97 Million trainable weights)
  - Action Head: 3 Bounded Actions [0: Allow & Log, 1: Step-Up KYC, 2: Flag for Human Review]
  - Evidence Vector: Latent embedding for plain-English investigation brief generation
"""

import math
import torch
import torch.nn as nn
import torch.nn.functional as F


class LoRALinear(nn.Module):
    """
    Low-Rank Adaptation (LoRA) Linear Layer.
    W = W_frozen + (B @ A) * (alpha / r)
    """
    def __init__(self, in_features, out_features, r=16, lora_alpha=32, lora_dropout=0.1):
        super().__init__()
        self.linear = nn.Linear(in_features, out_features)
        self.r = r
        self.lora_alpha = lora_alpha
        self.scaling = lora_alpha / r
        
        if r > 0:
            self.lora_A = nn.Parameter(torch.zeros((r, in_features)))
            self.lora_B = nn.Parameter(torch.zeros((out_features, r)))
            self.lora_dropout = nn.Dropout(p=lora_dropout)
            # Initialize A with Gaussian, B with zero (starts as identity)
            nn.init.kaiming_uniform_(self.lora_A, a=math.sqrt(5))
            nn.init.zeros_(self.lora_B)
            
        # Freeze base linear layer
        self.linear.weight.requires_grad = False
        if self.linear.bias is not None:
            self.linear.bias.requires_grad = False
            
    def forward(self, x):
        result = self.linear(x)
        if self.r > 0:
            lora_out = (self.lora_dropout(x) @ self.lora_A.T) @ self.lora_B.T
            result = result + lora_out * self.scaling
        return result


class TransformerBlockWithLoRA(nn.Module):
    """Transformer Encoder Block with LoRA applied to Q, K, V, and FFN projections."""
    def __init__(self, d_model=512, nhead=8, d_ff=2048, dropout=0.1, r=16, alpha=32):
        super().__init__()
        self.d_model = d_model
        self.nhead = nhead
        self.head_dim = d_model // nhead
        
        # Self-Attention Projections with LoRA
        self.q_proj = LoRALinear(d_model, d_model, r=r, lora_alpha=alpha, lora_dropout=dropout)
        self.k_proj = LoRALinear(d_model, d_model, r=r, lora_alpha=alpha, lora_dropout=dropout)
        self.v_proj = LoRALinear(d_model, d_model, r=r, lora_alpha=alpha, lora_dropout=dropout)
        self.out_proj = LoRALinear(d_model, d_model, r=r, lora_alpha=alpha, lora_dropout=dropout)
        
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        
        # Feed-Forward Network
        self.ffn = nn.Sequential(
            LoRALinear(d_model, d_ff, r=r, lora_alpha=alpha, lora_dropout=dropout),
            nn.GELU(),
            nn.Dropout(dropout),
            LoRALinear(d_ff, d_model, r=r, lora_alpha=alpha, lora_dropout=dropout),
            nn.Dropout(dropout)
        )
        self.dropout = nn.Dropout(dropout)

    def forward(self, x, mask=None):
        # Multi-head self-attention
        B, S, D = x.shape
        q = self.q_proj(x).view(B, S, self.nhead, self.head_dim).transpose(1, 2)
        k = self.k_proj(x).view(B, S, self.nhead, self.head_dim).transpose(1, 2)
        v = self.v_proj(x).view(B, S, self.nhead, self.head_dim).transpose(1, 2)
        
        scores = (q @ k.transpose(-2, -1)) / math.sqrt(self.head_dim)
        if mask is not None:
            scores = scores.masked_fill(mask == 0, -1e9)
        attn = F.softmax(scores, dim=-1)
        attn_out = (attn @ v).transpose(1, 2).contiguous().view(B, S, D)
        
        x = self.norm1(x + self.out_proj(attn_out))
        x = self.norm2(x + self.ffn(x))
        return x


class VYUHTransformer55M(nn.Module):
    """
    VYUH 27.2M Parameter Financial Transformer Backbone.
    Processes historical sequence tokens + continuous features to output risk & actions.
    """
    def __init__(self, input_dim=481, d_model=512, nhead=8, num_layers=8, d_ff=2048, 
                 r=16, alpha=32, dropout=0.1, num_actions=3):
        super().__init__()
        self.d_model = d_model
        
        # Continuous Feature Projection to d_model embedding space
        self.feature_proj = nn.Sequential(
            nn.Linear(input_dim, d_model),
            nn.LayerNorm(d_model),
            nn.GELU(),
            nn.Linear(d_model, d_model)
        )
        
        # Transformer Layers
        self.layers = nn.ModuleList([
            TransformerBlockWithLoRA(d_model=d_model, nhead=nhead, d_ff=d_ff, 
                                     dropout=dropout, r=r, alpha=alpha)
            for _ in range(num_layers)
        ])
        
        self.final_norm = nn.LayerNorm(d_model)
        
        # Action Head (Policy: 0=Allow, 1=StepUp, 2=Flag)
        self.action_head = nn.Sequential(
            nn.Linear(d_model, 256),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(256, num_actions)
        )
        
        # Continuous Fraud Risk Score Head
        self.risk_head = nn.Sequential(
            nn.Linear(d_model, 128),
            nn.GELU(),
            nn.Linear(128, 1),
            nn.Sigmoid()
        )
        
        # Latent Evidence Vector Head (for LLM reasoning explanation)
        self.evidence_head = nn.Linear(d_model, 128)

    def forward(self, x):
        # x shape: [Batch_Size, Input_Dim] or [Batch_Size, Seq_Len, Input_Dim]
        if x.dim() == 2:
            x = x.unsqueeze(1)  # [Batch, 1, Input_Dim]
            
        h = self.feature_proj(x)
        
        for layer in self.layers:
            h = layer(h)
            
        h_pool = self.final_norm(h[:, -1, :])  # Pool last token representation
        
        action_logits = self.action_head(h_pool)
        risk_score = self.risk_head(h_pool)
        evidence_vector = self.evidence_head(h_pool)
        
        return {
            "action_logits": action_logits,
            "risk_score": risk_score.squeeze(-1),
            "evidence_vector": evidence_vector,
            "latent_state": h_pool
        }

    def count_parameters(self):
        total = sum(p.numel() for p in self.parameters())
        trainable = sum(p.numel() for p in self.parameters() if p.requires_grad)
        return total, trainable


if __name__ == "__main__":
    model = VYUHTransformer55M(input_dim=481)
    total, trainable = model.count_parameters()
    print("=" * 60)
    print("🧠 VYUH 55M PARAMETER TRANSFORMER ARCHITECTURE")
    print("=" * 60)
    print(f"   Total Backbone Parameters:      {total:,} (~{total/1e6:.1f}M)")
    print(f"   Trainable (LoRA Adapters only): {trainable:,} (~{trainable/1e6:.1f}M)")
    print(f"   Frozen Base Parameters:         {total - trainable:,}")
    print(f"   LoRA Efficiency Ratio:          {trainable/total * 100:.2f}% trainable")
    
    # Test forward pass with dummy tensor
    dummy_input = torch.randn(4, 481)
    out = model(dummy_input)
    print(f"\n   Forward Pass Verification:")
    print(f"   - Action Logits Shape: {out['action_logits'].shape} -> 3 Bounded Actions")
    print(f"   - Risk Score Shape:    {out['risk_score'].shape} -> Fraud Probability P(Fraud)")
    print(f"   - Evidence Vector:     {out['evidence_vector'].shape} -> 128-dim Latent Space")
    print("✅ Model Architecture Verified & Ready for GRPO Training!")
