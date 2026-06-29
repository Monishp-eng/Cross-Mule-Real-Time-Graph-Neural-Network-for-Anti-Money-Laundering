"""Inference and analytics utilities for trained GraphSAGE mule detection."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from collections import defaultdict, deque
from datetime import datetime, timezone
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from src.gnn_detector.graph_builder import csv_text_to_pyg_graph
from src.gnn_detector.model import MuleGraphSAGE

try:
    import torch
except Exception:  # pragma: no cover
    torch = None


_MODEL_CACHE: Dict[str, Dict[str, Any]] = {}

try:
    from sklearn.cluster import KMeans
except Exception:  # pragma: no cover
    KMeans = None


def _require_torch() -> None:
    if torch is None:
        raise RuntimeError("torch is required for GraphSAGE inference")


def _load_or_get_cached_model(model_path: str, feature_dim: int) -> Tuple[Any, Dict[str, Any], Path]:
    """Load a GraphSAGE model once and reuse it across predict requests.

    Cache invalidates automatically when model file mtime changes.
    """
    _require_torch()

    checkpoint_path = Path(model_path)
    if not checkpoint_path.exists():
        raise FileNotFoundError(f"Trained model not found at {model_path}")

    resolved = str(checkpoint_path.resolve())
    mtime = checkpoint_path.stat().st_mtime
    cached = _MODEL_CACHE.get(resolved)
    if cached and float(cached.get("mtime", 0.0)) == float(mtime):
        return cached["model"], cached["config"], checkpoint_path

    checkpoint = torch.load(checkpoint_path, map_location="cpu")
    cfg = checkpoint.get("config", {})
    in_dim = int(cfg.get("num_features", feature_dim))
    hidden_dim = int(cfg.get("hidden_dim", 64))

    model = MuleGraphSAGE(in_dim=in_dim, hidden_dim=hidden_dim)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    _MODEL_CACHE[resolved] = {
        "mtime": float(mtime),
        "model": model,
        "config": cfg,
    }
    return model, cfg, checkpoint_path


def _connected_components_for_high_risk(node_ids: List[str], edge_pairs: List[tuple[int, int]], high_risk_indices: set[int]) -> List[List[str]]:
    adjacency: Dict[int, set[int]] = defaultdict(set)
    for src, dst in edge_pairs:
        if src in high_risk_indices and dst in high_risk_indices:
            adjacency[src].add(dst)
            adjacency[dst].add(src)

    visited: set[int] = set()
    components: List[List[str]] = []
    for node_idx in high_risk_indices:
        if node_idx in visited:
            continue
        queue = deque([node_idx])
        visited.add(node_idx)
        component: List[str] = []
        while queue:
            current = queue.popleft()
            component.append(node_ids[current])
            for neighbor in adjacency.get(current, set()):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        components.append(sorted(component))

    return components


def _safe_timestamp(value: Any) -> datetime:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
    text = str(value or "").strip()
    if not text:
        return datetime.now(timezone.utc)
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed
    except ValueError:
        return datetime.now(timezone.utc)


def _get_async_analytics_config() -> Dict[str, Any]:
    min_transactions = max(1, int(os.getenv("GNN_ASYNC_ANALYTICS_MIN_TRANSACTIONS", "250")))
    force_async = os.getenv("GNN_ASYNC_ANALYTICS_FORCE", "false").strip().lower() in {"1", "true", "yes", "on"}
    timeout_seconds = float(os.getenv("GNN_ASYNC_ANALYTICS_TIMEOUT_SECONDS", "6"))
    return {
        "min_transactions": min_transactions,
        "force_async": force_async,
        "timeout_seconds": max(1.0, timeout_seconds),
    }


def cluster_detection(
    *,
    node_ids: List[str],
    embeddings: np.ndarray,
    node_risk_scores: Dict[str, float],
    edge_pairs: List[Tuple[int, int]],
    risk_threshold: float = 0.5,
    max_clusters: int = 4,
) -> List[Dict[str, Any]]:
    """Detect mule rings as clusters of high-risk nodes from GraphSAGE embeddings."""
    high_indices = [idx for idx, node_id in enumerate(node_ids) if float(node_risk_scores.get(node_id, 0.0)) >= risk_threshold]
    if not high_indices:
        soft_threshold = max(0.35, risk_threshold - 0.12)
        high_indices = [idx for idx, node_id in enumerate(node_ids) if float(node_risk_scores.get(node_id, 0.0)) >= soft_threshold]
    if not high_indices and node_ids:
        ranked = sorted(range(len(node_ids)), key=lambda idx: float(node_risk_scores.get(node_ids[idx], 0.0)), reverse=True)
        high_indices = ranked[: min(3, len(ranked))]
    if not high_indices:
        return []

    clusters: List[Dict[str, Any]] = []
    if KMeans is not None and len(high_indices) >= 2:
        high_embeddings = embeddings[high_indices]
        cluster_count = max(1, min(max_clusters, len(high_indices)))
        kmeans = KMeans(n_clusters=cluster_count, random_state=42, n_init=10)
        labels = kmeans.fit_predict(high_embeddings)

        grouped: Dict[int, List[str]] = defaultdict(list)
        for local_idx, label in enumerate(labels):
            grouped[int(label)].append(node_ids[high_indices[local_idx]])

        for cluster_id, account_ids in grouped.items():
            avg_risk = float(np.mean([node_risk_scores.get(account_id, 0.0) for account_id in account_ids]))
            clusters.append(
                {
                    "cluster_id": f"MULE_CLUSTER_{cluster_id}",
                    "account_ids": sorted(account_ids),
                    "average_risk_score": float(round(avg_risk, 4)),
                    "size": len(account_ids),
                    "method": "kmeans_embeddings",
                }
            )
    else:
        components = _connected_components_for_high_risk(node_ids, edge_pairs, set(high_indices))
        for idx, account_ids in enumerate(components):
            avg_risk = float(np.mean([node_risk_scores.get(account_id, 0.0) for account_id in account_ids]))
            clusters.append(
                {
                    "cluster_id": f"MULE_CLUSTER_{idx}",
                    "account_ids": sorted(account_ids),
                    "average_risk_score": float(round(avg_risk, 4)),
                    "size": len(account_ids),
                    "method": "connected_components",
                }
            )

    clusters.sort(key=lambda row: row["average_risk_score"], reverse=True)
    return clusters


def velocity_analysis(
    transactions: List[Dict[str, Any]],
    node_risk_scores: Dict[str, float],
    *,
    rapid_window_minutes: float = 12.0,
    max_paths: int = 120,
    max_depth: int = 4,
    max_branch_per_node: int = 12,
) -> Dict[str, Any]:
    """Analyze rapid transaction movement and suspicious multi-hop paths."""
    if not transactions:
        return {
            "rapid_edges": [],
            "flagged_paths": [],
            "node_velocity_scores": {},
            "velocity_by_transaction": {},
        }

    indexed: List[Dict[str, Any]] = []
    for tx in transactions:
        timestamp = _safe_timestamp(tx.get("timestamp") or tx.get("timestamp_iso"))
        indexed.append({**tx, "_ts": timestamp})
    indexed.sort(key=lambda row: row["_ts"])

    rapid_edges: List[Dict[str, Any]] = []
    velocity_by_transaction: Dict[str, float] = {}
    node_velocity_acc: Dict[str, List[float]] = defaultdict(list)
    outgoing: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    by_sender: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for tx in indexed:
        sender = str(tx.get("sender_id") or "")
        receiver = str(tx.get("receiver_id") or "")
        if sender:
            by_sender[sender].append(tx)
        if sender and receiver:
            outgoing[sender].append(tx)

    # Receiver->sender linkage captures actual fund movement chains (A->B then B->C).
    for tx in indexed:
        sender = str(tx.get("sender_id") or "")
        receiver = str(tx.get("receiver_id") or "")
        if not sender or not receiver:
            continue

        next_candidates = outgoing.get(receiver, [])
        best_gap: Optional[float] = None
        best_next: Optional[Dict[str, Any]] = None
        for candidate in next_candidates:
            gap = (candidate["_ts"] - tx["_ts"]).total_seconds() / 60.0
            if gap < 0 or gap > rapid_window_minutes:
                continue
            if best_gap is None or gap < best_gap:
                best_gap = gap
                best_next = candidate

        if best_next is None or best_gap is None:
            continue

        speed_score = float(round(max(0.0, 1.0 - (best_gap / max(rapid_window_minutes, 0.001))), 4))
        tx_id = str(tx.get("transaction_id") or "")
        next_tx_id = str(best_next.get("transaction_id") or "")
        if tx_id:
            velocity_by_transaction[tx_id] = max(speed_score, velocity_by_transaction.get(tx_id, 0.0))
        if next_tx_id:
            velocity_by_transaction[next_tx_id] = max(speed_score, velocity_by_transaction.get(next_tx_id, 0.0))

        node_velocity_acc[sender].append(speed_score)
        node_velocity_acc[receiver].append(speed_score)
        next_receiver = str(best_next.get("receiver_id") or "")
        if next_receiver:
            node_velocity_acc[next_receiver].append(speed_score)

        rapid_edges.append(
            {
                "transaction_id": tx_id,
                "sender_id": sender,
                "receiver_id": receiver,
                "next_transaction_id": next_tx_id,
                "next_receiver_id": next_receiver,
                "gap_minutes": float(round(best_gap, 4)),
                "velocity_score": speed_score,
            }
        )

    # Keep same-sender burst detection as a secondary velocity signal.
    for sender, sender_txs in by_sender.items():
        sender_txs.sort(key=lambda row: row["_ts"])
        for prev_tx, curr_tx in zip(sender_txs, sender_txs[1:]):
            gap_minutes = max((curr_tx["_ts"] - prev_tx["_ts"]).total_seconds() / 60.0, 0.0)
            if gap_minutes > rapid_window_minutes:
                continue
            speed_score = float(round(max(0.0, 1.0 - (gap_minutes / max(rapid_window_minutes, 0.001))), 4))
            tx_id = str(curr_tx.get("transaction_id") or "")
            if tx_id:
                velocity_by_transaction[tx_id] = max(speed_score, velocity_by_transaction.get(tx_id, 0.0))

            node_velocity_acc[sender].append(speed_score)
            receiver = str(curr_tx.get("receiver_id") or "")
            if receiver:
                node_velocity_acc[receiver].append(speed_score)

            rapid_edges.append(
                {
                    "transaction_id": tx_id,
                    "sender_id": sender,
                    "receiver_id": receiver,
                    "gap_minutes": float(round(gap_minutes, 4)),
                    "velocity_score": speed_score,
                }
            )

    for sender, sender_txs in outgoing.items():
        sender_txs.sort(key=lambda row: row["_ts"])
        if len(sender_txs) > max_branch_per_node:
            outgoing[sender] = sender_txs[:max_branch_per_node]

    flagged_paths: List[Dict[str, Any]] = []

    def extend_path(
        current_tx: Dict[str, Any],
        node_path: List[str],
        tx_ids: List[str],
        risk_series: List[float],
        time_gaps: List[float],
        depth: int,
    ) -> None:
        if len(flagged_paths) >= max_paths or depth >= max_depth:
            return

        next_sender = str(current_tx.get("receiver_id") or "")
        if not next_sender:
            return

        next_candidates = outgoing.get(next_sender, [])
        for candidate in next_candidates:
            gap = (candidate["_ts"] - current_tx["_ts"]).total_seconds() / 60.0
            if gap < 0 or gap > rapid_window_minutes:
                continue

            next_receiver = str(candidate.get("receiver_id") or "")
            next_tx_id = str(candidate.get("transaction_id") or f"PATH_TX_{len(tx_ids)}")
            next_risk = float(node_risk_scores.get(next_receiver, 0.0))

            next_node_path = [*node_path, next_receiver]
            next_tx_ids = [*tx_ids, next_tx_id]
            next_risk_series = [*risk_series, next_risk]
            next_time_gaps = [*time_gaps, float(round(gap, 4))]

            if len(next_tx_ids) >= 2:
                max_gap = max(next_time_gaps)
                mean_path_risk = float(np.mean(next_risk_series))
                max_path_risk = float(max(next_risk_series))
                qualifies_risk = max_path_risk >= 0.35 or mean_path_risk >= 0.3
                qualifies_speed = max_gap <= rapid_window_minutes
                if qualifies_risk and qualifies_speed:
                    flagged_paths.append(
                        {
                            "path_id": f"PATH_{len(flagged_paths)}",
                            "node_path": next_node_path,
                            "transaction_ids": next_tx_ids,
                            "hop_count": len(next_tx_ids),
                            "time_gaps_minutes": next_time_gaps,
                            "max_gap_minutes": float(round(max_gap, 4)),
                            "cumulative_risk": float(round(mean_path_risk, 4)),
                            "risk_series": [float(round(v, 4)) for v in next_risk_series],
                            "velocity_score": float(round(1.0 - (max_gap / max(rapid_window_minutes, 0.001)), 4)),
                        }
                    )

            extend_path(candidate, next_node_path, next_tx_ids, next_risk_series, next_time_gaps, depth + 1)

    for root_tx in indexed:
        start_sender = str(root_tx.get("sender_id") or "")
        start_receiver = str(root_tx.get("receiver_id") or "")
        if not start_sender or not start_receiver:
            continue
        root_tx_id = str(root_tx.get("transaction_id") or "PATH_TX_0")
        root_risks = [
            float(node_risk_scores.get(start_sender, 0.0)),
            float(node_risk_scores.get(start_receiver, 0.0)),
        ]
        extend_path(root_tx, [start_sender, start_receiver], [root_tx_id], root_risks, [], 1)
        if len(flagged_paths) >= max_paths:
            break

    node_velocity_scores = {
        node_id: float(round(float(np.mean(scores)), 4))
        for node_id, scores in node_velocity_acc.items()
        if scores
    }

    return {
        "rapid_edges": rapid_edges,
        "flagged_paths": flagged_paths,
        "node_velocity_scores": node_velocity_scores,
        "velocity_by_transaction": velocity_by_transaction,
    }


def explain_predictions(
    *,
    node_ids: List[str],
    probabilities: np.ndarray,
    node_features: np.ndarray,
    neighbors: Dict[int, set[int]],
    transactions: List[Dict[str, Any]],
    node_risk_scores: Dict[str, float],
    velocity_result: Dict[str, Any],
    risk_threshold: float = 0.5,
) -> List[Dict[str, Any]]:
    """Create human-readable reasons per flagged node."""
    channels_by_node: Dict[str, set[str]] = defaultdict(set)
    for tx in transactions:
        sender = str(tx.get("sender_id") or "")
        receiver = str(tx.get("receiver_id") or "")
        channel = str(tx.get("transaction_type") or tx.get("channel") or "UNKNOWN").upper()
        if sender:
            channels_by_node[sender].add(channel)
        if receiver:
            channels_by_node[receiver].add(channel)

    nodes_in_flagged_paths: set[str] = set()
    for path in velocity_result.get("flagged_paths", []):
        for node in path.get("node_path", []):
            nodes_in_flagged_paths.add(str(node))

    node_velocity_scores = velocity_result.get("node_velocity_scores", {})
    explanations: List[Dict[str, Any]] = []

    for idx, node_id in enumerate(node_ids):
        probability = float(probabilities[idx])
        node_feature = node_features[idx]
        risky_neighbors = sum(1 for neighbor_idx in neighbors.get(idx, set()) if float(probabilities[neighbor_idx]) >= risk_threshold)

        reasons: List[str] = []
        if float(node_feature[0]) >= 0.35:
            reasons.append("High transaction frequency")
        if risky_neighbors >= 2:
            reasons.append("Connected to high-risk nodes")
        if float(node_velocity_scores.get(node_id, 0.0)) >= 0.3 or node_id in nodes_in_flagged_paths:
            reasons.append("Rapid fund movement")
        if len(channels_by_node.get(node_id, set())) >= 2:
            reasons.append("Multiple transaction channels used")
        if probability >= 0.85:
            reasons.append("GraphSAGE model indicates very high risk")

        should_flag = probability >= risk_threshold or float(node_velocity_scores.get(node_id, 0.0)) >= 0.35
        if should_flag:
            explanations.append(
                {
                    "node_id": node_id,
                    "risk_score": float(round(node_risk_scores.get(node_id, probability), 4)),
                    "reasons": reasons or ["Elevated graph risk"],
                    "velocity_score": float(round(node_velocity_scores.get(node_id, 0.0), 4)),
                    "risky_neighbor_count": risky_neighbors,
                    "channels": sorted(channels_by_node.get(node_id, set())),
                }
            )

    explanations.sort(key=lambda row: row["risk_score"], reverse=True)
    return explanations


def predict_from_csv_text(csv_text: str, model_path: str = "models/gnn_mule_detector.pt", risk_threshold: float = 0.5) -> Dict[str, Any]:
    """Run GraphSAGE inference and produce risks, mule rings, velocity paths, and explanations."""
    _require_torch()
    bundle = csv_text_to_pyg_graph(csv_text)
    data = bundle.data

    model, _, checkpoint_path = _load_or_get_cached_model(model_path, int(data.x.shape[1]))

    with torch.no_grad():
        logits = model(data.x, data.edge_index)
        probabilities = torch.sigmoid(logits).detach().cpu().numpy()
        embeddings = model.embed(data.x, data.edge_index).detach().cpu().numpy()
        node_features = data.x.detach().cpu().numpy()

    node_risk_scores = {node_id: float(round(probabilities[idx], 4)) for idx, node_id in enumerate(bundle.node_ids)}

    # Count risky neighbors for explainability.
    neighbors: Dict[int, set[int]] = defaultdict(set)
    edge_pairs = []
    edge_index_np = data.edge_index.detach().cpu().numpy()
    for src, dst in zip(edge_index_np[0], edge_index_np[1]):
        src_idx = int(src)
        dst_idx = int(dst)
        neighbors[src_idx].add(dst_idx)
        neighbors[dst_idx].add(src_idx)
        edge_pairs.append((src_idx, dst_idx))

    tx_count = len(bundle.transactions)
    async_config = _get_async_analytics_config()
    use_async_analytics = async_config["force_async"] or tx_count >= async_config["min_transactions"]
    rapid_window_minutes = 12.0
    max_paths = 240 if tx_count < 1500 else 120

    if use_async_analytics:
        with ThreadPoolExecutor(max_workers=2, thread_name_prefix="gnn-analytics") as executor:
            velocity_future = executor.submit(
                velocity_analysis,
                bundle.transactions,
                node_risk_scores,
                rapid_window_minutes=rapid_window_minutes,
                max_paths=max_paths,
            )
            cluster_future = executor.submit(
                cluster_detection,
                node_ids=bundle.node_ids,
                embeddings=embeddings,
                node_risk_scores=node_risk_scores,
                edge_pairs=edge_pairs,
                risk_threshold=risk_threshold,
            )

            timeout_seconds = async_config["timeout_seconds"] if tx_count < 2500 else max(2.0, async_config["timeout_seconds"] - 2.0)
            try:
                velocity_result = velocity_future.result(timeout=timeout_seconds)
            except FutureTimeoutError:
                velocity_result = velocity_analysis(
                    bundle.transactions,
                    node_risk_scores,
                    rapid_window_minutes=rapid_window_minutes,
                    max_paths=60,
                    max_depth=3,
                    max_branch_per_node=8,
                )

            try:
                clusters = cluster_future.result(timeout=timeout_seconds)
            except FutureTimeoutError:
                clusters = cluster_detection(
                    node_ids=bundle.node_ids,
                    embeddings=embeddings,
                    node_risk_scores=node_risk_scores,
                    edge_pairs=edge_pairs,
                    risk_threshold=max(0.45, risk_threshold - 0.05),
                    max_clusters=3,
                )
    else:
        velocity_result = velocity_analysis(
            bundle.transactions,
            node_risk_scores,
            rapid_window_minutes=rapid_window_minutes,
            max_paths=max_paths,
        )
        clusters = cluster_detection(
            node_ids=bundle.node_ids,
            embeddings=embeddings,
            node_risk_scores=node_risk_scores,
            edge_pairs=edge_pairs,
            risk_threshold=risk_threshold,
        )

    explanations = explain_predictions(
        node_ids=bundle.node_ids,
        probabilities=probabilities,
        node_features=node_features,
        neighbors=neighbors,
        transactions=bundle.transactions,
        node_risk_scores=node_risk_scores,
        velocity_result=velocity_result,
        risk_threshold=risk_threshold,
    )

    suspicious_nodes = [
        {
            "account_id": row["node_id"],
            "risk_score": row["risk_score"],
            "reasons": row["reasons"],
            "velocity_score": row.get("velocity_score", 0.0),
        }
        for row in explanations
        if row["risk_score"] >= risk_threshold or row.get("velocity_score", 0.0) >= 0.35
    ]

    edge_anomalies = []
    edge_attr_np = data.edge_attr.detach().cpu().numpy() if getattr(data, "edge_attr", None) is not None else np.zeros((edge_index_np.shape[1], 3), dtype=np.float32)
    for tx_idx, tx in enumerate(bundle.transactions):
        sender = tx.get("sender_id")
        receiver = tx.get("receiver_id")
        sender_prob = node_risk_scores.get(sender, 0.0)
        receiver_prob = node_risk_scores.get(receiver, 0.0)
        edge_feature = edge_attr_np[tx_idx] if tx_idx < edge_attr_np.shape[0] else np.array([0.0, 0.0, 0.0])
        anomaly_score = min(1.0, (0.45 * sender_prob) + (0.35 * receiver_prob) + (0.15 * float(edge_feature[0])) + (0.05 * (1.0 - float(edge_feature[2]))))

        reasons = []
        if float(edge_feature[0]) >= 0.08:
            reasons.append("high_transfer_amount")
        if float(edge_feature[2]) <= 0.05:
            reasons.append("rapid_time_delta")
        if sender_prob >= risk_threshold or receiver_prob >= risk_threshold:
            reasons.append("connected_to_high_risk_node")
        velocity_score = float(velocity_result.get("velocity_by_transaction", {}).get(str(tx.get("transaction_id")), 0.0))
        if velocity_score >= 0.3:
            reasons.append("high_velocity_chain")

        edge_anomalies.append(
            {
                "transaction_id": tx.get("transaction_id"),
                "sender_id": sender,
                "receiver_id": receiver,
                "anomaly_score": float(round(anomaly_score, 4)),
                "suspicious": anomaly_score >= max(0.45, risk_threshold - 0.05),
                "velocity_score": float(round(velocity_score, 4)),
                "reasons": reasons or ["graph_pattern_risk"],
            }
        )

    flagged_paths = velocity_result.get("flagged_paths", [])

    return {
        "node_risk_scores": node_risk_scores,
        "suspicious_nodes": suspicious_nodes,
        "explanations": explanations,
        "clusters": clusters,
        "edge_anomalies": edge_anomalies,
        "flagged_paths": flagged_paths,
        "velocity": {
            "rapid_edges": velocity_result.get("rapid_edges", []),
            "node_velocity_scores": velocity_result.get("node_velocity_scores", {}),
            "window_minutes": 12.0,
        },
        "graph_summary": {
            "node_count": len(bundle.node_ids),
            "edge_count": int(data.edge_index.shape[1]),
            "high_risk_count": len(suspicious_nodes),
            "cluster_count": len(clusters),
            "flagged_path_count": len(flagged_paths),
        },
        "model_path": str(checkpoint_path),
        "model_type": "gnn_graphsage",
        "performance": {
            "clustering_nodes": len(clusters),
            "analyzed_transactions": len(bundle.transactions),
            "async_analytics_enabled": use_async_analytics,
            "analytics_mode": "threaded" if use_async_analytics else "inline",
            "async_analytics_config": async_config,
        },
    }
