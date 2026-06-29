"""CSV transaction normalization and graph-building helpers.

This module turns flat transaction CSV rows into a unified transaction graph
and produces account-level feature tables for GNN training and real-time scoring.
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from io import StringIO
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd


CHANNEL_DEFAULTS = {
    "UPI": "UPI",
    "APP": "MOBILE",
    "MOBILE": "MOBILE",
    "WEB": "WEB",
    "ATM": "ATM",
}

TRANSACTION_TYPE_CODES = {
    "MOBILE": 0,
    "WEB": 1,
    "ATM": 2,
    "UPI": 3,
}

HIGH_RISK_COUNTRIES = {"KP", "IR", "SY", "CU", "RU"}


@dataclass
class CsvGraphArtifacts:
    """Convenience bundle for graph, feature, and report outputs."""

    dataframe: pd.DataFrame
    normalized_transactions: List[Dict[str, Any]]
    graph: Dict[str, Any]
    account_features: pd.DataFrame


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except Exception:
        return default


def _parse_timestamp(value: Any) -> datetime:
    if value is None or value == "":
        return datetime.now(timezone.utc)

    ts = pd.to_datetime(value, utc=True, errors="coerce")
    if pd.isna(ts):
        return datetime.now(timezone.utc)
    return ts.to_pydatetime()


def _parse_location(row: pd.Series) -> Dict[str, Any]:
    raw_location = row.get("location")
    if isinstance(raw_location, str) and raw_location.strip():
        try:
            decoded = json.loads(raw_location)
            if isinstance(decoded, dict):
                raw_location = decoded
        except Exception:
            raw_location = None

    latitude = row.get("latitude")
    longitude = row.get("longitude")
    country = row.get("country") or row.get("location_country") or "US"
    city = row.get("city") or row.get("location_city")

    if isinstance(raw_location, dict):
        latitude = raw_location.get("latitude", latitude)
        longitude = raw_location.get("longitude", longitude)
        country = raw_location.get("country", country)
        city = raw_location.get("city", city)

    return {
        "latitude": _safe_float(latitude, 0.0),
        "longitude": _safe_float(longitude, 0.0),
        "country": str(country or "US").upper(),
        "city": city,
    }


def load_csv_dataframe(csv_text: str) -> pd.DataFrame:
    """Read a CSV string into a dataframe and normalize obvious column aliases."""
    df = pd.read_csv(StringIO(csv_text))
    if df.empty:
        raise ValueError("CSV dataset is empty")

    df = df.copy()
    df.columns = [str(col).strip().lower() for col in df.columns]
    return df


def normalize_csv_transactions(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Convert CSV rows into the unified event payload shape used by the API."""
    if df.empty:
        return []

    rows = df.copy()
    timestamp_column = None
    for candidate in ("timestamp", "time", "transaction_time", "transfer_time", "withdrawal_time"):
        if candidate in rows.columns:
            timestamp_column = candidate
            break
    if timestamp_column is None:
        rows["_timestamp"] = pd.Series([datetime.now(timezone.utc)] * len(rows))
    else:
        rows["_timestamp"] = rows[timestamp_column].apply(_parse_timestamp)
    rows = rows.sort_values("_timestamp")

    normalized: List[Dict[str, Any]] = []
    last_seen_by_sender: Dict[str, datetime] = {}

    for idx, (_, row) in enumerate(rows.iterrows()):
        transaction_type = str(row.get("transaction_type") or row.get("channel") or "MOBILE").strip().upper()
        channel = CHANNEL_DEFAULTS.get(transaction_type, transaction_type if transaction_type in CHANNEL_DEFAULTS else "MOBILE")
        raw_status = str(row.get("status") or row.get("transaction_status") or "").strip()
        raw_is_fraud = row.get("is_fraud")
        is_fraud = False
        if raw_is_fraud is not None and raw_is_fraud != "":
            try:
                is_fraud = int(float(raw_is_fraud)) == 1
            except Exception:
                is_fraud = str(raw_is_fraud).strip().lower() in {"true", "yes", "y", "1"}
        raw_fraud_reason = str(row.get("fraud_reason") or row.get("reason") or "").strip()
        sender_id = str(
            row.get("sender_id")
            or row.get("source_account_id")
            or row.get("user_id")
            or row.get("from_account")
            or f"SENDER_{idx}"
        ).strip()
        receiver_id = str(
            row.get("receiver_id")
            or row.get("dest_account_id")
            or row.get("beneficiary_account")
            or row.get("to_account")
            or row.get("wallet_id")
            or f"RECEIVER_{idx}"
        ).strip()
        amount = _safe_float(row.get("amount") or row.get("transfer_amount") or row.get("txn_amount") or row.get("withdrawal_amount"), 0.0)
        timestamp = row.get("_timestamp")
        timestamp_iso = timestamp.isoformat().replace("+00:00", "Z") if isinstance(timestamp, datetime) else datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        device_id = str(row.get("device_id") or row.get("device_fingerprint") or row.get("browser_fingerprint") or f"DEVICE_{idx}")
        location = _parse_location(row)
        transaction_id = str(
            row.get("transaction_id")
            or row.get("event_id")
            or row.get("transaction_id ")
            or row.get("txn_ref_id")
            or f"TXN_{idx}"
        )

        if channel == "ATM":
            raw_event = {
                "event_id": transaction_id,
                "terminal_id": receiver_id if receiver_id else str(row.get("terminal_id") or f"ATM_{idx}"),
                "card_number_last4": str(row.get("card_number_last4") or "0000"),
                "withdrawal_amount": amount,
                "withdrawal_time": timestamp_iso,
                "location": location,
            }
        elif channel == "UPI":
            raw_event = {
                "upi_id": sender_id,
                "recipient_upi": receiver_id,
                "txn_amount": amount,
                "txn_ref_id": transaction_id,
                "timestamp": timestamp_iso,
            }
        elif channel == "WEB":
            raw_event = {
                "event_id": transaction_id,
                "user_id": sender_id,
                "beneficiary_account": receiver_id,
                "transfer_amount": amount,
                "transfer_time": timestamp_iso,
                "ip_address": str(row.get("ip_address") or ""),
                "browser_fingerprint": device_id,
                "location": location,
            }
        else:
            raw_event = {
                "event_id": transaction_id,
                "user_id": sender_id,
                "transfer_to_wallet": receiver_id,
                "transfer_amount": amount,
                "transfer_time": timestamp_iso,
                "device_fingerprint": device_id,
                "ip_address": str(row.get("ip_address") or ""),
                "location": location,
            }

        previous_seen = last_seen_by_sender.get(sender_id)
        time_diff_minutes = 0.0
        if previous_seen is not None:
            time_diff_minutes = max((timestamp.to_pydatetime() - previous_seen).total_seconds() / 60.0, 0.0)
        last_seen_by_sender[sender_id] = timestamp.to_pydatetime()

        normalized.append(
            {
                "transaction_id": transaction_id,
                "channel": channel,
                "transaction_type": channel,
                "sender_id": sender_id,
                "receiver_id": receiver_id,
                "amount": amount,
                "timestamp": timestamp,
                "timestamp_iso": timestamp_iso,
                "device_id": device_id,
                "location": location,
                "currency": str(row.get("currency") or "INR").upper(),
                "name": str(row.get("name") or row.get("customer_name") or "").strip() or None,
                "mobile_number": str(row.get("mobile_number") or row.get("mobile") or row.get("phone_number") or "").strip() or None,
                "account_number": str(row.get("account_number") or sender_id).strip() or sender_id,
                "account_product_type": str(row.get("account_product_type") or row.get("account_product") or row.get("product_type") or "").strip() or None,
                "narration": str(row.get("narration") or row.get("description") or row.get("remarks") or "").strip() or None,
                "pincode": str(row.get("pincode") or row.get("pin_code") or row.get("postal_code") or "").strip() or None,
                "source_status": raw_status or None,
                "source_is_fraud": is_fraud,
                "source_fraud_reason": raw_fraud_reason or None,
                "time_diff_minutes": round(time_diff_minutes, 4),
                "raw_event": raw_event,
                "risk_hint_country": location["country"],
                "transaction_type_code": TRANSACTION_TYPE_CODES.get(channel, 0),
            }
        )

    return normalized


def build_account_feature_table(transactions: List[Dict[str, Any]]) -> pd.DataFrame:
    """Build account-level features suitable for GraphSAGE training or inference."""
    if not transactions:
        return pd.DataFrame()

    account_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
        "sent_count": 0,
        "received_count": 0,
        "sent_total": 0.0,
        "received_total": 0.0,
        "amounts": [],
        "device_ids": set(),
        "counterparties": set(),
        "countries": set(),
        "timestamps": [],
        "risk_history": [],
        "fraud_event_count": 0,
        "labeled_event_count": 0,
    })

    for tx in transactions:
        sender = tx["sender_id"]
        receiver = tx["receiver_id"]
        amount = float(tx["amount"])
        ts = tx["timestamp"]
        country = tx["location"].get("country", "US")
        device_id = tx.get("device_id", "UNKNOWN")
        pseudo_risk = 1.0 if amount >= 10000 else 0.6 if amount >= 5000 else 0.2
        source_is_fraud = bool(tx.get("source_is_fraud", False))

        sender_stats = account_stats[sender]
        sender_stats["sent_count"] += 1
        sender_stats["sent_total"] += amount
        sender_stats["amounts"].append(amount)
        sender_stats["device_ids"].add(device_id)
        sender_stats["counterparties"].add(receiver)
        sender_stats["countries"].add(country)
        sender_stats["timestamps"].append(ts)
        sender_stats["risk_history"].append(pseudo_risk)
        sender_stats["labeled_event_count"] += 1
        sender_stats["fraud_event_count"] += int(source_is_fraud)

        receiver_stats = account_stats[receiver]
        receiver_stats["received_count"] += 1
        receiver_stats["received_total"] += amount
        receiver_stats["amounts"].append(amount)
        receiver_stats["device_ids"].add(device_id)
        receiver_stats["counterparties"].add(sender)
        receiver_stats["countries"].add(country)
        receiver_stats["timestamps"].append(ts)
        receiver_stats["risk_history"].append(pseudo_risk)
        receiver_stats["labeled_event_count"] += 1
        receiver_stats["fraud_event_count"] += int(source_is_fraud)

    features: List[Dict[str, Any]] = []
    now = max(tx["timestamp"] for tx in transactions)

    for account_id, stats in account_stats.items():
        timestamps = sorted(stats["timestamps"])
        first_seen = timestamps[0]
        last_seen = timestamps[-1]
        span_days = max((last_seen - first_seen).total_seconds() / 86400.0, 1.0)
        total_txn_count = stats["sent_count"] + stats["received_count"]
        unique_counterparties = len(stats["counterparties"])
        device_count = len(stats["device_ids"])
        avg_amount = sum(stats["amounts"]) / len(stats["amounts"]) if stats["amounts"] else 0.0
        balance_proxy = stats["received_total"] - stats["sent_total"]
        velocity_score = min(total_txn_count / 20.0, 1.0)
        structuring_score = 0.0
        if len(stats["amounts"]) >= 4:
            near_threshold = sum(1 for amount in stats["amounts"] if 300 <= amount <= 2500 or 9000 <= amount < 10000)
            structuring_score = min(1.0, near_threshold / len(stats["amounts"]))
        country_risk = 1.0 if any(country in HIGH_RISK_COUNTRIES for country in stats["countries"]) else 0.0
        labeled_event_count = int(stats.get("labeled_event_count", 0) or 0)
        fraud_event_count = int(stats.get("fraud_event_count", 0) or 0)
        fraud_ratio = float(fraud_event_count / labeled_event_count) if labeled_event_count > 0 else 0.0

        features.append(
            {
                "account_id": account_id,
                "account_age_days": min(span_days, 30.0),
                "velocity_score": velocity_score,
                "balance": max(0.0, min(abs(balance_proxy), 10000.0)),
                "txn_count_24h": min(total_txn_count, 100),
                "unique_counterparties": min(unique_counterparties, 50),
                "device_count": min(device_count, 10),
                "avg_amount": min(avg_amount, 10000.0),
                "structuring_score": structuring_score,
                "country_risk": country_risk,
                "is_new": span_days <= 7,
                "has_high_velocity": total_txn_count >= 12,
                "risk_history": stats["risk_history"],
                "countries": sorted(stats["countries"]),
                "first_seen": first_seen,
                "last_seen": last_seen,
                "sent_total": stats["sent_total"],
                "received_total": stats["received_total"],
                "counterparties": sorted(stats["counterparties"]),
                "labeled_event_count": labeled_event_count,
                "fraud_event_count": fraud_event_count,
                "fraud_ratio": round(fraud_ratio, 4),
            }
        )

    frame = pd.DataFrame(features)
    if not frame.empty:
        frame = frame.sort_values(["txn_count_24h", "avg_amount"], ascending=False).reset_index(drop=True)
    return frame


def build_graph_snapshot(transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Create a UI-friendly graph snapshot with nodes and directed edges."""
    if not transactions:
        return {"nodes": [], "links": [], "clusters": [], "summary": {"node_count": 0, "edge_count": 0}}

    account_features = build_account_feature_table(transactions)
    feature_lookup = {row.account_id: row for row in account_features.itertuples(index=False)}

    nodes: List[Dict[str, Any]] = []
    links: List[Dict[str, Any]] = []
    seen_nodes: set[str] = set()

    def add_node(node_id: str, label: str, node_type: str, suspicious: bool = False, **attrs: Any) -> None:
        if node_id in seen_nodes:
            return
        seen_nodes.add(node_id)
        nodes.append({"id": node_id, "label": label, "type": node_type, "suspicious": suspicious, **attrs})

    for row in account_features.itertuples(index=False):
        risk_score = min(
            1.0,
            (0.30 * row.velocity_score)
            + (0.20 * (row.unique_counterparties / 50.0))
            + (0.18 * row.structuring_score)
            + (0.12 * (1.0 if row.is_new else 0.0))
            + (0.10 * (row.device_count / 10.0))
            + (0.10 * (1.0 if any(country in HIGH_RISK_COUNTRIES for country in row.countries) else 0.0)),
        )
        add_node(
            row.account_id,
            row.account_id,
            "account",
            suspicious=risk_score >= 0.55,
            risk_score=round(risk_score, 4),
            account_age_days=round(float(row.account_age_days), 2),
            txn_count_24h=int(row.txn_count_24h),
            unique_counterparties=int(row.unique_counterparties),
            device_count=int(row.device_count),
        )

    for tx in transactions:
        sender = tx["sender_id"]
        receiver = tx["receiver_id"]
        tx_id = tx["transaction_id"]
        device_id = tx.get("device_id")
        location = tx.get("location", {})
        edge_time = tx.get("timestamp_iso")

        sender_risk = float(feature_lookup.get(sender).velocity_score if sender in feature_lookup else 0.0)
        receiver_risk = float(feature_lookup.get(receiver).velocity_score if receiver in feature_lookup else 0.0)
        suspicious = tx["amount"] >= 5000 or tx["time_diff_minutes"] <= 5.0

        add_node(tx_id, tx_id, "transaction", suspicious=suspicious, amount=tx["amount"], transaction_type=tx["transaction_type"])
        if device_id:
            add_node(device_id, device_id, "device", suspicious=suspicious)
        location_id = f"LOC_{location.get('country', 'US')}_{int(location.get('latitude', 0.0))}_{int(location.get('longitude', 0.0))}"
        add_node(location_id, location_id, "location", suspicious=location.get("country") in HIGH_RISK_COUNTRIES)

        links.append(
            {
                "source": sender,
                "target": receiver,
                "transaction_id": tx_id,
                "amount": tx["amount"],
                "transaction_type": tx["transaction_type"],
                "time_diff_minutes": tx["time_diff_minutes"],
                "suspicious": suspicious,
                "timestamp": edge_time,
            }
        )
        links.append({"source": tx_id, "target": sender, "transaction_id": tx_id, "type": "PART_OF", "suspicious": suspicious})
        if device_id:
            links.append({"source": sender, "target": device_id, "transaction_id": tx_id, "type": "IS_ON_DEVICE", "suspicious": suspicious})
            links.append({"source": device_id, "target": location_id, "transaction_id": tx_id, "type": "LOCATED_AT", "suspicious": suspicious})

    clusters = []
    if account_features.shape[0] > 0:
        risky_accounts = [row.account_id for row in account_features.itertuples(index=False) if len(row.counterparties) >= 4 or row.txn_count_24h >= 10]
        if risky_accounts:
            clusters.append({"cluster_id": "MULE_CLUSTER_1", "members": risky_accounts[:20], "risk": 0.7})

    return {
        "nodes": nodes,
        "links": links,
        "clusters": clusters,
        "summary": {
            "node_count": len(nodes),
            "edge_count": len(links),
            "transaction_count": len(transactions),
            "account_count": int(account_features.shape[0]),
        },
    }


def build_report_rows(scored_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convert scored transactions into downloadable CSV report rows."""
    rows: List[Dict[str, Any]] = []
    for result in scored_results:
        top_features = result.get("explainability", {}).get("top_features", {})
        reasons = result.get("reasons") or result.get("explainability", {}).get("reasons") or []
        account_id = top_features.get("user_id") or top_features.get("account_id") or result.get("transaction_id")
        compliance = result.get("compliance_report", {}) if isinstance(result.get("compliance_report", {}), dict) else {}
        sanctions = result.get("sanctions_screening", {}) if isinstance(result.get("sanctions_screening", {}), dict) else {}
        complexity = result.get("transaction_complexity", {}) if isinstance(result.get("transaction_complexity", {}), dict) else {}
        jurisdiction = result.get("jurisdiction_risk", {}) if isinstance(result.get("jurisdiction_risk", {}), dict) else {}
        privacy = result.get("privacy_safe_intelligence", {}) if isinstance(result.get("privacy_safe_intelligence", {}), dict) else {}
        accounts_involved = compliance.get("accounts_involved") or []
        transaction_path = compliance.get("transaction_path") or []
        history_summary = (
            f"txn_1h={top_features.get('current_txn_count_1h', 0)}; "
            f"counterparties={top_features.get('unique_counterparties', 0)}; "
            f"device_count={top_features.get('device_count', 0)}; "
            f"target_countries={','.join(top_features.get('target_countries', []) or [])}"
        )
        rows.append(
            {
                "case_id": compliance.get("case_id") or compliance.get("report_id") or result.get("transaction_id"),
                "account_id": account_id,
                "accounts_involved": ";".join(str(item) for item in accounts_involved),
                "risk_score": round(float(result.get("risk_score", 0.0)), 4),
                "confidence_score": round(float(result.get("confidence_score", result.get("confidence", 0.0))), 4),
                "decision": result.get("decision", "ALLOW"),
                "reason_for_flag": "; ".join(reasons) if reasons else "No reason supplied",
                "explanation": compliance.get("why_flagged") or compliance.get("reason_for_flag") or "; ".join(reasons),
                "detected_patterns": "; ".join(compliance.get("detected_patterns", reasons) or reasons),
                "transaction_path": " -> ".join(str(item) for item in transaction_path),
                "transaction_history_summary": history_summary,
                "transaction_id": result.get("transaction_id", "-"),
                "timestamp": result.get("timestamp", "-"),
                "sanctions_flag": bool(sanctions.get("sanctions_flag", False)),
                "sanctions_score": round(float(sanctions.get("sanctions_score", 0.0)), 4),
                "matched_entity": sanctions.get("matched_entity") or "",
                "complexity_score": round(float(complexity.get("complexity_score", 0.0)), 2),
                "complexity_type": complexity.get("complexity_type") or "",
                "jurisdiction_score": round(float(jurisdiction.get("jurisdiction_score", 0.0)), 4),
                "jurisdiction_band": jurisdiction.get("risk_band") or "",
                "privacy_match_count": int(privacy.get("match_count", 0) or 0),
            }
        )

    if not rows:
        rows.append(
            {
                "account_id": "NO_DATA",
                "risk_score": 0.0,
                "decision": "ALLOW",
                "reason_for_flag": "No transactions available yet",
                "transaction_history_summary": "txn_1h=0; counterparties=0; device_count=0; target_countries=",
                "transaction_id": "NO_DATA",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    return rows
