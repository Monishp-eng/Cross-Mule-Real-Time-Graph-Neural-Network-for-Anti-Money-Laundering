"""
PyTorch Geometric training script for mule account node classification.

Usage:
  python -m src.gnn_detector.train
  python -m src.gnn_detector.train --epochs 100 --num-nodes 3000
"""

from __future__ import annotations

import argparse
import os
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

import numpy as np
import torch
import torch.nn.functional as F
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from torch import nn
from torch_geometric.data import Data
from torch_geometric.nn import SAGEConv


@dataclass
class TrainingConfig:
    epochs: int = 60
    lr: float = 1e-3
    weight_decay: float = 1e-4
    hidden_dim: int = 64
    num_features: int = 10
    num_nodes: int = 2000
    fraud_ratio: float = 0.2
    out_dir: str = "models"
    seed: int = 42


class MuleGraphSAGE(nn.Module):
    def __init__(self, in_dim: int, hidden_dim: int):
        super().__init__()
        self.conv1 = SAGEConv(in_dim, hidden_dim)
        self.conv2 = SAGEConv(hidden_dim, hidden_dim)
        self.head = nn.Linear(hidden_dim, 1)

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        x = self.conv1(x, edge_index)
        x = F.relu(x)
        x = F.dropout(x, p=0.2, training=self.training)
        x = self.conv2(x, edge_index)
        x = F.relu(x)
        logits = self.head(x).squeeze(-1)
        return logits


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def build_synthetic_graph(cfg: TrainingConfig) -> Data:
    """Create a synthetic graph with ring/star patterns for mule accounts."""
    n = cfg.num_nodes
    feat = np.zeros((n, cfg.num_features), dtype=np.float32)

    labels = np.zeros((n,), dtype=np.float32)
    fraud_count = int(n * cfg.fraud_ratio)
    fraud_nodes = set(np.random.choice(n, size=fraud_count, replace=False).tolist())

    edge_src = []
    edge_dst = []

    for i in range(n):
        is_fraud = i in fraud_nodes
        labels[i] = 1.0 if is_fraud else 0.0

        # Feature layout mirrors SimpleGNNDetector assumptions.
        account_age = np.random.randint(1, 10) if is_fraud else np.random.randint(20, 180)
        velocity = np.random.uniform(0.65, 1.0) if is_fraud else np.random.uniform(0.02, 0.45)
        balance = np.random.uniform(100, 3000) if is_fraud else np.random.uniform(1500, 12000)
        txn_24h = np.random.randint(30, 120) if is_fraud else np.random.randint(1, 25)
        counterparties = np.random.randint(15, 55) if is_fraud else np.random.randint(1, 18)
        device_count = np.random.randint(5, 15) if is_fraud else np.random.randint(1, 4)
        avg_amount = np.random.uniform(600, 9000) if is_fraud else np.random.uniform(50, 2500)
        structuring = np.random.uniform(0.5, 1.0) if is_fraud else np.random.uniform(0.0, 0.3)
        is_new = 1.0 if account_age <= 7 else 0.0
        has_high_velocity = 1.0 if velocity > 0.7 else 0.0

        feat[i] = np.array(
            [
                min(account_age / 30.0, 1.0),
                velocity,
                min(balance / 10000.0, 1.0),
                min(txn_24h / 100.0, 1.0),
                min(counterparties / 50.0, 1.0),
                min(device_count / 10.0, 1.0),
                min(avg_amount / 10000.0, 1.0),
                structuring,
                is_new,
                has_high_velocity,
            ],
            dtype=np.float32,
        )

    # Normal traffic edges.
    for i in range(n):
        degree = np.random.randint(2, 8)
        neighbors = np.random.choice(n, size=degree, replace=False)
        for nb in neighbors:
            if nb != i:
                edge_src.append(i)
                edge_dst.append(int(nb))

    # Inject suspicious ring/star motifs among fraud nodes.
    fraud_list = list(fraud_nodes)
    if len(fraud_list) >= 12:
        ring = fraud_list[:8]
        for idx in range(len(ring)):
            edge_src.append(ring[idx])
            edge_dst.append(ring[(idx + 1) % len(ring)])

        hub = fraud_list[8]
        for spoke in fraud_list[9:12]:
            edge_src.append(hub)
            edge_dst.append(spoke)
            edge_src.append(spoke)
            edge_dst.append(hub)

    edge_index = torch.tensor([edge_src, edge_dst], dtype=torch.long)
    x = torch.tensor(feat, dtype=torch.float32)
    y = torch.tensor(labels, dtype=torch.float32)

    perm = np.random.permutation(n)
    train_cut = int(0.7 * n)
    val_cut = int(0.85 * n)

    train_idx = torch.tensor(perm[:train_cut], dtype=torch.long)
    val_idx = torch.tensor(perm[train_cut:val_cut], dtype=torch.long)
    test_idx = torch.tensor(perm[val_cut:], dtype=torch.long)

    data = Data(x=x, edge_index=edge_index, y=y)
    data.train_mask = torch.zeros(n, dtype=torch.bool)
    data.val_mask = torch.zeros(n, dtype=torch.bool)
    data.test_mask = torch.zeros(n, dtype=torch.bool)

    data.train_mask[train_idx] = True
    data.val_mask[val_idx] = True
    data.test_mask[test_idx] = True

    return data


def evaluate_binary(y_true: np.ndarray, y_prob: np.ndarray) -> Dict[str, float]:
    y_pred = (y_prob >= 0.5).astype(np.int64)
    metrics = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
    }
    # ROC AUC needs at least both classes present.
    if len(np.unique(y_true)) > 1:
        metrics["roc_auc"] = float(roc_auc_score(y_true, y_prob))
    else:
        metrics["roc_auc"] = 0.0
    return metrics


def train(cfg: TrainingConfig) -> Dict[str, float]:
    set_seed(cfg.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    data = build_synthetic_graph(cfg).to(device)
    model = MuleGraphSAGE(in_dim=cfg.num_features, hidden_dim=cfg.hidden_dim).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=cfg.lr, weight_decay=cfg.weight_decay)

    best_val_f1 = -1.0
    best_state = None

    for epoch in range(1, cfg.epochs + 1):
        model.train()
        optimizer.zero_grad()

        logits = model(data.x, data.edge_index)
        train_logits = logits[data.train_mask]
        train_targets = data.y[data.train_mask]

        loss = F.binary_cross_entropy_with_logits(train_logits, train_targets)
        loss.backward()
        optimizer.step()

        model.eval()
        with torch.no_grad():
            val_logits = model(data.x, data.edge_index)[data.val_mask]
            val_prob = torch.sigmoid(val_logits).detach().cpu().numpy()
            val_true = data.y[data.val_mask].detach().cpu().numpy()
            val_metrics = evaluate_binary(val_true, val_prob)

        if val_metrics["f1"] > best_val_f1:
            best_val_f1 = val_metrics["f1"]
            best_state = {
                "model_state_dict": model.state_dict(),
                "config": cfg.__dict__,
                "val_metrics": val_metrics,
            }

        if epoch % 10 == 0 or epoch == 1:
            print(
                f"epoch={epoch:03d} loss={loss.item():.4f} "
                f"val_f1={val_metrics['f1']:.4f} val_auc={val_metrics['roc_auc']:.4f}"
            )

    if best_state is None:
        raise RuntimeError("Training did not produce a valid model state")

    model.load_state_dict(best_state["model_state_dict"])
    model.eval()

    with torch.no_grad():
        test_logits = model(data.x, data.edge_index)[data.test_mask]
        test_prob = torch.sigmoid(test_logits).detach().cpu().numpy()
        test_true = data.y[data.test_mask].detach().cpu().numpy()
        test_metrics = evaluate_binary(test_true, test_prob)

    out_dir = Path(cfg.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    model_path = out_dir / "gnn_mule_detector.pt"
    torch.save(
        {
            "model_state_dict": model.state_dict(),
            "config": cfg.__dict__,
            "test_metrics": test_metrics,
        },
        model_path,
    )

    print(f"Saved model to: {model_path}")
    print(f"Test metrics: {test_metrics}")

    return test_metrics


def parse_args() -> TrainingConfig:
    parser = argparse.ArgumentParser(description="Train GraphSAGE mule detection model")
    parser.add_argument("--epochs", type=int, default=60)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--num-nodes", type=int, default=2000)
    parser.add_argument("--fraud-ratio", type=float, default=0.2)
    parser.add_argument("--hidden-dim", type=int, default=64)
    parser.add_argument("--out-dir", type=str, default="models")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    return TrainingConfig(
        epochs=args.epochs,
        lr=args.lr,
        num_nodes=args.num_nodes,
        fraud_ratio=args.fraud_ratio,
        hidden_dim=args.hidden_dim,
        out_dir=args.out_dir,
        seed=args.seed,
    )


if __name__ == "__main__":
    config = parse_args()
    train(config)
