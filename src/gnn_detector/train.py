"""Training utilities for GraphSAGE-based mule detection."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

import numpy as np

from src.gnn_detector.graph_builder import csv_text_to_pyg_graph
from src.gnn_detector.model import MuleGraphSAGE

try:
    import torch
    import torch.nn.functional as F
except Exception:  # pragma: no cover
    torch = None
    F = None


@dataclass
class TrainingConfig:
    epochs: int = 40
    lr: float = 1e-3
    weight_decay: float = 1e-4
    hidden_dim: int = 64
    out_dir: str = "models"
    model_name: str = "gnn_mule_detector.pt"
    seed: int = 42


def _require_torch() -> None:
    if torch is None or F is None:
        raise RuntimeError("torch is required for GraphSAGE training")


def set_seed(seed: int) -> None:
    np.random.seed(seed)
    if torch is not None:
        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)


def evaluate_binary(y_true: np.ndarray, y_prob: np.ndarray) -> Dict[str, float]:
    if y_true.size == 0:
        return {"accuracy": 0.0, "precision": 0.0, "recall": 0.0, "f1": 0.0, "roc_auc": 0.0}

    y_pred = (y_prob >= 0.5).astype(np.int64)
    tp = int(((y_true == 1) & (y_pred == 1)).sum())
    tn = int(((y_true == 0) & (y_pred == 0)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    fn = int(((y_true == 1) & (y_pred == 0)).sum())

    accuracy = (tp + tn) / max(len(y_true), 1)
    precision = tp / max(tp + fp, 1)
    recall = tp / max(tp + fn, 1)
    f1 = (2 * precision * recall) / max(precision + recall, 1e-9)

    # Lightweight ROC AUC approximation suitable for unavailable sklearn environments.
    positives = y_prob[y_true == 1]
    negatives = y_prob[y_true == 0]
    if positives.size and negatives.size:
        auc = float(np.mean([float(p > n) + 0.5 * float(p == n) for p in positives for n in negatives]))
    else:
        auc = 0.0

    return {
        "accuracy": float(round(accuracy, 4)),
        "precision": float(round(precision, 4)),
        "recall": float(round(recall, 4)),
        "f1": float(round(f1, 4)),
        "roc_auc": float(round(auc, 4)),
    }


def train_from_csv_text(csv_text: str, cfg: TrainingConfig | None = None) -> Dict[str, float]:
    """Train GraphSAGE on CSV transaction graph and persist checkpoint."""
    _require_torch()
    cfg = cfg or TrainingConfig()
    set_seed(cfg.seed)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    bundle = csv_text_to_pyg_graph(csv_text)
    data = bundle.data.to(device)

    positives = int(float(data.y.sum().item()))
    negatives = int(int(data.y.shape[0]) - positives)
    if positives == 0 or negatives == 0:
        raise RuntimeError(
            "Dataset does not contain both fraud and non-fraud labels. "
            "Provide explicit source labels (is_fraud/status) for supervised training."
        )

    model = MuleGraphSAGE(in_dim=data.x.shape[1], hidden_dim=cfg.hidden_dim).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=cfg.lr, weight_decay=cfg.weight_decay)

    best_val_f1 = -1.0
    best_state = None

    for epoch in range(1, cfg.epochs + 1):
        model.train()
        optimizer.zero_grad()

        logits = model(data.x, data.edge_index)
        train_logits = logits[data.train_mask]
        train_targets = data.y[data.train_mask]
        if train_logits.numel() == 0:
            raise RuntimeError("Training split is empty; provide a larger dataset")

        loss = F.binary_cross_entropy_with_logits(train_logits, train_targets)
        loss.backward()
        optimizer.step()

        model.eval()
        with torch.no_grad():
            val_logits = model(data.x, data.edge_index)[data.val_mask]
            val_prob = torch.sigmoid(val_logits).detach().cpu().numpy() if val_logits.numel() else np.array([])
            val_true = data.y[data.val_mask].detach().cpu().numpy() if val_logits.numel() else np.array([])
            val_metrics = evaluate_binary(val_true, val_prob)

        if val_metrics["f1"] > best_val_f1:
            best_val_f1 = val_metrics["f1"]
            best_state = {
                "model_state_dict": model.state_dict(),
                "config": {
                    "num_features": int(data.x.shape[1]),
                    "hidden_dim": int(cfg.hidden_dim),
                    "epochs": int(cfg.epochs),
                    "lr": float(cfg.lr),
                    "weight_decay": float(cfg.weight_decay),
                    "seed": int(cfg.seed),
                },
                "val_metrics": val_metrics,
                "metadata": {
                    "node_ids": bundle.node_ids,
                    "feature_names": bundle.feature_names,
                    "transaction_count": len(bundle.transactions),
                    "edge_count": int(data.edge_index.shape[1]),
                    "node_count": int(data.x.shape[0]),
                },
            }

    if best_state is None:
        raise RuntimeError("Training failed to produce a valid model state")

    model.load_state_dict(best_state["model_state_dict"])
    model.eval()

    with torch.no_grad():
        test_logits = model(data.x, data.edge_index)[data.test_mask]
        test_prob = torch.sigmoid(test_logits).detach().cpu().numpy() if test_logits.numel() else np.array([])
        test_true = data.y[data.test_mask].detach().cpu().numpy() if test_logits.numel() else np.array([])
        test_metrics = evaluate_binary(test_true, test_prob)

    out_dir = Path(cfg.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    model_path = out_dir / cfg.model_name

    torch.save(
        {
            "model_state_dict": model.state_dict(),
            "config": best_state["config"],
            "val_metrics": best_state["val_metrics"],
            "test_metrics": test_metrics,
            "metadata": best_state["metadata"],
        },
        model_path,
    )

    return {
        **test_metrics,
        "model_path": str(model_path),
        "graph_node_count": best_state["metadata"]["node_count"],
        "graph_edge_count": best_state["metadata"]["edge_count"],
        "transaction_count": best_state["metadata"]["transaction_count"],
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train GraphSAGE mule detector from CSV")
    parser.add_argument("--csv", required=True, help="Path to CSV dataset")
    parser.add_argument("--epochs", type=int, default=40)
    parser.add_argument("--hidden-dim", type=int, default=64)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--out-dir", type=str, default="models")
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    csv_text = Path(args.csv).read_text(encoding="utf-8")
    cfg = TrainingConfig(
        epochs=args.epochs,
        hidden_dim=args.hidden_dim,
        lr=args.lr,
        weight_decay=args.weight_decay,
        out_dir=args.out_dir,
        seed=args.seed,
    )
    metrics = train_from_csv_text(csv_text, cfg)
    print(metrics)


if __name__ == "__main__":
    main()
