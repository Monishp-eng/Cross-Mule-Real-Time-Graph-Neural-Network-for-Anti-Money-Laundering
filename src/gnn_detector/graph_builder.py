"""Conversion utilities from CSV transactions to PyTorch Geometric graph data."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

import numpy as np

from src.data_ingestion.csv_graph_pipeline import build_account_feature_table, load_csv_dataframe, normalize_csv_transactions

try:
    import torch
    from torch_geometric.data import Data
except Exception:  # pragma: no cover
    torch = None
    Data = None


TX_TYPE_TO_CODE = {
    "MOBILE": 0,
    "WEB": 1,
    "ATM": 2,
    "UPI": 3,
}


@dataclass
class GraphBuildResult:
    """Graph tensor bundle with useful lookup metadata."""

    data: Any
    node_ids: List[str]
    node_index: Dict[str, int]
    transactions: List[Dict[str, Any]]
    feature_names: List[str]


def _require_torch() -> None:
    if torch is None or Data is None:
        raise RuntimeError("torch and torch_geometric are required for GNN graph conversion")


def _compute_node_label(row: Dict[str, Any]) -> float:
    # Use explicit fraud annotations only (if provided in dataset) to avoid
    # circular learning from internal risk heuristics.
    fraud_ratio = float(row.get("fraud_ratio", 0.0) or 0.0)
    return 1.0 if fraud_ratio >= 0.5 else 0.0


def _node_feature_vector(row: Dict[str, Any]) -> np.ndarray:
    txn_count = float(row.get("txn_count_24h", 0.0))
    sent_total = float(row.get("sent_total", 0.0))
    received_total = float(row.get("received_total", 0.0))
    avg_amount = float(row.get("avg_amount", 0.0))
    device_count = float(row.get("device_count", 0.0))
    counterparties = float(row.get("unique_counterparties", 0.0))
    velocity_score = float(row.get("velocity_score", 0.0))
    account_age = float(row.get("account_age_days", 30.0))
    structuring_score = float(row.get("structuring_score", 0.0))

    return np.array(
        [
            min(txn_count / 100.0, 1.0),
            min(sent_total / 100000.0, 1.0),
            min(received_total / 100000.0, 1.0),
            min(avg_amount / 10000.0, 1.0),
            min(device_count / 10.0, 1.0),
            min(counterparties / 50.0, 1.0),
            min(velocity_score, 1.0),
            min(account_age / 30.0, 1.0),
            min(structuring_score, 1.0),
            1.0 if bool(row.get("has_high_velocity", False)) else 0.0,
        ],
        dtype=np.float32,
    )


def transactions_to_pyg_graph(transactions: List[Dict[str, Any]]) -> GraphBuildResult:
    """Build Data(x, edge_index, edge_attr, y, masks) from normalized transactions."""
    _require_torch()

    account_df = build_account_feature_table(transactions)
    if account_df.empty:
        raise ValueError("No account features could be built from the dataset")

    feature_names = [
        "txn_count_norm",
        "sent_total_norm",
        "received_total_norm",
        "avg_amount_norm",
        "device_count_norm",
        "counterparty_norm",
        "velocity_score",
        "account_age_norm",
        "structuring_score",
        "has_high_velocity",
    ]

    node_ids = account_df["account_id"].tolist()
    node_index = {account_id: idx for idx, account_id in enumerate(node_ids)}

    x_matrix = []
    y_vector = []
    for row in account_df.to_dict(orient="records"):
        x_matrix.append(_node_feature_vector(row))
        y_vector.append(_compute_node_label(row))

    edge_src: List[int] = []
    edge_dst: List[int] = []
    edge_attr: List[List[float]] = []
    for tx in transactions:
        sender = tx.get("sender_id")
        receiver = tx.get("receiver_id")
        if sender not in node_index or receiver not in node_index:
            continue

        amount = float(tx.get("amount", 0.0))
        tx_type_code = TX_TYPE_TO_CODE.get(str(tx.get("transaction_type", "MOBILE")).upper(), 0)
        time_diff_minutes = float(tx.get("time_diff_minutes", 0.0))

        edge_src.append(node_index[sender])
        edge_dst.append(node_index[receiver])
        edge_attr.append(
            [
                min(amount / 100000.0, 1.0),
                tx_type_code / 3.0,
                min(time_diff_minutes / 60.0, 1.0),
            ]
        )

    if not edge_src:
        for idx in range(len(node_ids)):
            edge_src.append(idx)
            edge_dst.append(idx)
            edge_attr.append([0.0, 0.0, 0.0])

    x = torch.tensor(np.vstack(x_matrix), dtype=torch.float32)
    y = torch.tensor(y_vector, dtype=torch.float32)
    edge_index = torch.tensor([edge_src, edge_dst], dtype=torch.long)
    edge_attr_tensor = torch.tensor(np.array(edge_attr, dtype=np.float32), dtype=torch.float32)

    data = Data(x=x, edge_index=edge_index, edge_attr=edge_attr_tensor, y=y)
    num_nodes = x.shape[0]

    perm = np.random.permutation(num_nodes)
    train_cut = max(1, int(num_nodes * 0.7))
    val_cut = max(train_cut + 1, int(num_nodes * 0.85)) if num_nodes > 2 else num_nodes

    data.train_mask = torch.zeros(num_nodes, dtype=torch.bool)
    data.val_mask = torch.zeros(num_nodes, dtype=torch.bool)
    data.test_mask = torch.zeros(num_nodes, dtype=torch.bool)

    data.train_mask[torch.tensor(perm[:train_cut], dtype=torch.long)] = True
    if train_cut < val_cut:
        data.val_mask[torch.tensor(perm[train_cut:val_cut], dtype=torch.long)] = True
    if val_cut < num_nodes:
        data.test_mask[torch.tensor(perm[val_cut:], dtype=torch.long)] = True

    return GraphBuildResult(
        data=data,
        node_ids=node_ids,
        node_index=node_index,
        transactions=transactions,
        feature_names=feature_names,
    )


def csv_text_to_pyg_graph(csv_text: str) -> GraphBuildResult:
    """Parse CSV text, normalize channel payloads, and build a PyG graph."""
    df = load_csv_dataframe(csv_text)
    transactions = normalize_csv_transactions(df)
    if not transactions:
        raise ValueError("CSV dataset did not contain any valid transactions")
    return transactions_to_pyg_graph(transactions)
