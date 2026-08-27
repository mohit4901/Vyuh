#!/usr/bin/env python3
"""
VYUH — Stage 2 High-Performance Dynamic Entity Graph Sentinel
=============================================================
Constructs a heterogeneous entity graph using vectorized edge extraction:
  - Transactions
  - Card entities (card1)
  - Device entities (DeviceInfo)
  - Email entities (P_emaildomain)
  - Address entities (addr1)

Runs Louvain community detection and extracts topological ring metrics in seconds.
Outputs:
  - data/processed/train_graph_feats.pkl
  - data/processed/test_graph_feats.pkl
  - data/graphs/fraud_ring_sample.json (for Cytoscape.js interactive visualization)
"""

import os
import sys
import pickle
import json
import time
import warnings
from pathlib import Path
from collections import defaultdict

import numpy as np
import pandas as pd
import networkx as nx
import community as community_louvain

warnings.filterwarnings("ignore")

PROJECT_ROOT = Path(__file__).parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
GRAPHS_DIR = PROJECT_ROOT / "data" / "graphs"
CHECKPOINT_DIR = PROJECT_ROOT / "models" / "checkpoints"
GRAPHS_DIR.mkdir(parents=True, exist_ok=True)
CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)


def build_and_extract_graph(df, dataset_name="train", sample_size=None):
    """Vectorized graph construction and community detection."""
    start_time = time.time()
    print(f"\n🕸️  Building Entity Graph for {dataset_name.upper()} ({len(df):,} transactions)...")
    
    if sample_size and len(df) > sample_size:
        df_work = df.sample(sample_size, random_state=42).copy()
    else:
        df_work = df.copy()
        
    G = nx.Graph()
    
    # 1. Vectorized edge lists
    edges = []
    
    # Txn -> Card
    card_mask = df_work["card1"].notna() & (df_work["card1"] != -999)
    txn_ids = [f"txn_{idx}" for idx in df_work.index]
    
    for idx, card in zip(df_work.index[card_mask], df_work.loc[card_mask, "card1"]):
        edges.append((f"txn_{idx}", f"card_{card}", "uses_card"))
        
    # Txn -> Device
    if "DeviceInfo" in df_work.columns:
        dev_mask = df_work["DeviceInfo"].notna() & (df_work["DeviceInfo"] != -999) & (df_work["DeviceInfo"] != "unknown")
        for idx, dev in zip(df_work.index[dev_mask], df_work.loc[dev_mask, "DeviceInfo"]):
            edges.append((f"txn_{idx}", f"dev_{dev}", "from_device"))
            
    # Txn -> Email
    if "P_emaildomain" in df_work.columns:
        email_mask = df_work["P_emaildomain"].notna() & (df_work["P_emaildomain"] != -999)
        for idx, email in zip(df_work.index[email_mask], df_work.loc[email_mask, "P_emaildomain"]):
            edges.append((f"txn_{idx}", f"email_{email}", "registered_email"))

    print(f"   Compiled {len(edges):,} entity edges in {time.time() - start_time:.2f}s")
    
    # Add edges to Graph
    G.add_edges_from([(u, v) for u, v, _ in edges])
    
    # Add node attributes
    for idx, row in df_work.iterrows():
        txn_id = f"txn_{idx}"
        if txn_id in G:
            G.nodes[txn_id]["is_fraud"] = int(row.get("isFraud", 0))
            G.nodes[txn_id]["amount"] = float(row.get("TransactionAmt", 0))
            G.nodes[txn_id]["node_type"] = "transaction"
            
    print(f"   Graph: {G.number_of_nodes():,} nodes | {G.number_of_edges():,} edges")
    
    # 2. Louvain Community Detection
    print("   Running Louvain Community Detection...")
    t0 = time.time()
    try:
        partition = community_louvain.best_partition(G, random_state=42)
        print(f"   Louvain finished in {time.time()-t0:.2f}s -> {len(set(partition.values())):,} communities.")
    except Exception as e:
        print(f"   Louvain fallback to Connected Components: {e}")
        partition = {}
        for comp_id, comp in enumerate(nx.connected_components(G)):
            for node in comp:
                partition[node] = comp_id
                
    comm_sizes = defaultdict(int)
    for node, comm_id in partition.items():
        comm_sizes[comm_id] += 1
        
    # Degrees
    degrees = dict(G.degree())
    
    # 3. Vectorized feature mapping
    print("   Mapping graph centrality & ring features to DataFrame...")
    community_ids = [partition.get(f"txn_{idx}", -1) for idx in df.index]
    ring_sizes = [comm_sizes.get(cid, 1) if cid != -1 else 1 for cid in community_ids]
    
    device_shared = []
    card_shared = []
    
    for idx, row in df.iterrows():
        dev = row.get("DeviceInfo", "")
        card = row.get("card1", "")
        device_shared.append(degrees.get(f"dev_{dev}", 0) if dev not in [-999, "unknown", ""] else 0)
        card_shared.append(degrees.get(f"card_{card}", 0) if card not in [-999, ""] else 0)
        
    graph_feats = pd.DataFrame({
        "graph_community_id": community_ids,
        "graph_ring_size": ring_sizes,
        "graph_device_shared_deg": device_shared,
        "graph_card_shared_deg": card_shared,
        "graph_is_large_ring": (np.array(ring_sizes) > 10).astype(int),
        "graph_burst_score": np.log1p(np.array(ring_sizes)) * np.log1p(np.array(device_shared) + 1)
    }, index=df.index)
    
    print(f"   ✅ {dataset_name.upper()} Graph Features complete in {time.time() - start_time:.2f}s")
    return graph_feats, G


def export_cytoscape_json(G, output_path, max_nodes=120):
    """Exports fraud ring cluster in Cytoscape format."""
    print("🎨 Generating Cytoscape JSON payload for interactive graph UI...")
    fraud_txns = [n for n, attr in G.nodes(data=True) if attr.get("is_fraud") == 1 and n.startswith("txn_")]
    
    selected_nodes = set()
    for ft in fraud_txns[:15]:
        selected_nodes.add(ft)
        selected_nodes.update(G.neighbors(ft))
        if len(selected_nodes) >= max_nodes:
            break
            
    sub_G = G.subgraph(list(selected_nodes)[:max_nodes])
    
    elements = []
    for node, attr in sub_G.nodes(data=True):
        if node.startswith("txn_"):
            ntype = "transaction"
            is_fraud = attr.get("is_fraud", 0)
            label = f"Order #{node.split('_')[1]}"
            amount = attr.get("amount", 499.0)
        elif node.startswith("card_"):
            ntype = "card"
            is_fraud = 0
            label = f"Card: {node.split('_')[1]}"
            amount = 0
        elif node.startswith("dev_"):
            ntype = "device"
            is_fraud = 0
            label = f"Device: {node.split('_')[1][:10]}"
            amount = 0
        elif node.startswith("email_"):
            ntype = "email"
            is_fraud = 0
            label = f"Email: {node.split('_')[1][:10]}"
            amount = 0
        else:
            ntype = "entity"
            is_fraud = 0
            label = node[:12]
            amount = 0
            
        elements.append({
            "data": {
                "id": str(node),
                "label": label,
                "type": ntype,
                "isFraud": bool(is_fraud),
                "amount": float(amount)
            }
        })
        
    for u, v in sub_G.edges():
        elements.append({
            "data": {
                "id": f"{u}_{v}",
                "source": str(u),
                "target": str(v),
                "label": "shared_link"
            }
        })
        
    with open(output_path, "w") as f:
        json.dump(elements, f, indent=2)
    print(f"   💾 Saved UI graph payload ({len(elements)} elements) to: {output_path}")


def main():
    print("=" * 60)
    print("🕸️  VYUH — STAGE 2 VECTORIZED GRAPH ENGINE")
    print("=" * 60)
    
    train_df = pd.read_pickle(PROCESSED_DIR / "train.pkl")
    test_df = pd.read_pickle(PROCESSED_DIR / "test.pkl")
    
    train_graph_feats, G_train = build_and_extract_graph(train_df, "train")
    test_graph_feats, G_test = build_and_extract_graph(test_df, "test")
    
    train_graph_feats.to_pickle(PROCESSED_DIR / "train_graph_feats.pkl")
    test_graph_feats.to_pickle(PROCESSED_DIR / "test_graph_feats.pkl")
    
    export_cytoscape_json(G_test, GRAPHS_DIR / "fraud_ring_sample.json")
    print("\n🎉 Stage 2 Graph Engine successfully completed!")


if __name__ == "__main__":
    main()
