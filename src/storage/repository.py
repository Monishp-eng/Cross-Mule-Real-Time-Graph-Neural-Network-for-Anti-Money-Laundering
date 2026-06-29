"""SQLite persistence for transactions, alerts, reports, and scores."""

from __future__ import annotations

import json
import os
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class SqliteRepository:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or os.getenv("SQLITE_DB_PATH", "data/mule_detection.sqlite3")
        self._lock = threading.Lock()
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                PRAGMA journal_mode=WAL;

                CREATE TABLE IF NOT EXISTS transactions (
                    transaction_id TEXT PRIMARY KEY,
                    source_account_id TEXT,
                    dest_account_id TEXT,
                    channel TEXT,
                    amount REAL,
                    timestamp TEXT,
                    payload_json TEXT,
                    created_at TEXT
                );

                CREATE TABLE IF NOT EXISTS risk_scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transaction_id TEXT,
                    case_id TEXT,
                    risk_score REAL,
                    confidence_score REAL,
                    decision TEXT,
                    ml_score REAL,
                    rule_score REAL,
                    sanctions_score REAL,
                    complexity_score REAL,
                    jurisdiction_score REAL,
                    payload_json TEXT,
                    created_at TEXT
                );

                CREATE TABLE IF NOT EXISTS sanctions_matches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transaction_id TEXT,
                    case_id TEXT,
                    matched_entity TEXT,
                    sanctions_score REAL,
                    payload_json TEXT,
                    created_at TEXT
                );

                CREATE TABLE IF NOT EXISTS reports (
                    case_id TEXT PRIMARY KEY,
                    transaction_id TEXT,
                    report_json TEXT,
                    created_at TEXT
                );

                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_id TEXT UNIQUE,
                    transaction_id TEXT,
                    case_id TEXT,
                    severity TEXT,
                    reason TEXT,
                    reviewed INTEGER DEFAULT 0,
                    payload_json TEXT,
                    created_at TEXT
                );

                CREATE TABLE IF NOT EXISTS auth_users (
                    user_id TEXT PRIMARY KEY,
                    email TEXT UNIQUE,
                    full_name TEXT,
                    password_hash TEXT,
                    created_at TEXT
                );

                CREATE TABLE IF NOT EXISTS notifications (
                    notification_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    email TEXT,
                    severity TEXT,
                    title TEXT,
                    message TEXT,
                    decision TEXT,
                    risk_score REAL,
                    transaction_id TEXT,
                    read INTEGER DEFAULT 0,
                    payload_json TEXT,
                    created_at TEXT
                );
                """
            )

    def upsert_auth_user(self, user: Dict[str, Any]) -> None:
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO auth_users(user_id, email, full_name, password_hash, created_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    email=excluded.email,
                    full_name=excluded.full_name,
                    password_hash=excluded.password_hash,
                    created_at=excluded.created_at
                """,
                (
                    user["user_id"],
                    user["email"],
                    user.get("full_name") or "",
                    user["password_hash"],
                    user.get("created_at") or _utc_now(),
                ),
            )

    def get_auth_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT user_id, email, full_name, password_hash, created_at FROM auth_users WHERE email = ? LIMIT 1",
                (email,),
            ).fetchone()
        if row is None:
            return None
        return dict(row)

    def get_auth_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT user_id, email, full_name, password_hash, created_at FROM auth_users WHERE user_id = ? LIMIT 1",
                (user_id,),
            ).fetchone()
        if row is None:
            return None
        return dict(row)

    def upsert_notification(self, notification: Dict[str, Any]) -> None:
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO notifications(notification_id, user_id, email, severity, title, message, decision, risk_score, transaction_id, read, payload_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(notification_id) DO UPDATE SET
                    user_id=excluded.user_id,
                    email=excluded.email,
                    severity=excluded.severity,
                    title=excluded.title,
                    message=excluded.message,
                    decision=excluded.decision,
                    risk_score=excluded.risk_score,
                    transaction_id=excluded.transaction_id,
                    read=excluded.read,
                    payload_json=excluded.payload_json,
                    created_at=excluded.created_at
                """,
                (
                    notification["notification_id"],
                    notification.get("user_id") or "",
                    notification.get("email") or "",
                    notification.get("severity") or "MEDIUM",
                    notification.get("title") or "Account security alert",
                    notification.get("message") or "",
                    notification.get("decision") or "",
                    float(notification.get("risk_score") or 0.0),
                    notification.get("transaction_id") or "",
                    1 if bool(notification.get("read")) else 0,
                    json.dumps(notification, default=str),
                    notification.get("created_at") or _utc_now(),
                ),
            )

    def list_notifications(self, *, user_id: Optional[str] = None, email: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        clauses = []
        params: List[Any] = []
        if user_id:
            clauses.append("user_id = ?")
            params.append(user_id)
        if email:
            clauses.append("email = ?")
            params.append(email)

        if not clauses:
            return []

        query = (
            "SELECT notification_id, user_id, email, severity, title, message, decision, risk_score, transaction_id, read, payload_json, created_at "
            "FROM notifications WHERE " + " OR ".join(clauses) + " ORDER BY created_at DESC LIMIT ?"
        )
        params.append(limit)

        with self._connect() as conn:
            rows = conn.execute(query, tuple(params)).fetchall()

        notifications = []
        for row in rows:
            item = dict(row)
            payload = item.get("payload_json") or "{}"
            try:
                item["payload"] = json.loads(payload)
            except Exception:
                item["payload"] = {}
            item["read"] = bool(item.get("read"))
            notifications.append(item)
        return notifications

    def mark_notification_read(self, notification_id: str, read: bool = True) -> bool:
        with self._lock, self._connect() as conn:
            cursor = conn.execute(
                "UPDATE notifications SET read = ? WHERE notification_id = ?",
                (1 if read else 0, notification_id),
            )
            return cursor.rowcount > 0

    def upsert_transaction(self, result: Dict[str, Any], raw_event: Dict[str, Any], normalized: Dict[str, Any]) -> None:
        transaction_id = str(result.get("transaction_id") or normalized.get("event_id") or raw_event.get("event_id") or "unknown")
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO transactions(transaction_id, source_account_id, dest_account_id, channel, amount, timestamp, payload_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(transaction_id) DO UPDATE SET
                    source_account_id=excluded.source_account_id,
                    dest_account_id=excluded.dest_account_id,
                    channel=excluded.channel,
                    amount=excluded.amount,
                    timestamp=excluded.timestamp,
                    payload_json=excluded.payload_json
                """,
                (
                    transaction_id,
                    normalized.get("source_account_id") or result.get("explainability", {}).get("top_features", {}).get("user_id"),
                    normalized.get("dest_account_id") or result.get("explainability", {}).get("top_features", {}).get("counterparty"),
                    normalized.get("channel") or raw_event.get("channel") or "UNKNOWN",
                    float(normalized.get("amount") or raw_event.get("amount") or 0.0),
                    normalized.get("timestamp") or raw_event.get("timestamp") or _utc_now(),
                    json.dumps({"raw_event": raw_event, "normalized": normalized}, default=str),
                    _utc_now(),
                ),
            )

    def save_result(self, result: Dict[str, Any], raw_event: Dict[str, Any], normalized: Dict[str, Any]) -> None:
        transaction_id = str(result.get("transaction_id") or normalized.get("event_id") or raw_event.get("event_id") or "unknown")
        compliance = result.get("compliance_report", {}) if isinstance(result.get("compliance_report", {}), dict) else {}
        sanctions = result.get("sanctions_screening", {}) if isinstance(result.get("sanctions_screening", {}), dict) else {}
        complexity = result.get("transaction_complexity", {}) if isinstance(result.get("transaction_complexity", {}), dict) else {}
        jurisdiction = result.get("jurisdiction_risk", {}) if isinstance(result.get("jurisdiction_risk", {}), dict) else {}
        case_id = compliance.get("case_id") or compliance.get("report_id") or result.get("transaction_id") or transaction_id

        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO risk_scores(transaction_id, case_id, risk_score, confidence_score, decision, ml_score, rule_score, sanctions_score, complexity_score, jurisdiction_score, payload_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    transaction_id,
                    case_id,
                    float(result.get("risk_score", 0.0)),
                    float(result.get("confidence_score", result.get("confidence", 0.0))),
                    result.get("decision", "ALLOW"),
                    float(result.get("ml_score", 0.0)),
                    float(result.get("rule_score", 0.0)),
                    float(sanctions.get("sanctions_score", 0.0)),
                    float(complexity.get("complexity_score", 0.0)),
                    float(jurisdiction.get("jurisdiction_score", 0.0)),
                    json.dumps(result, default=str),
                    _utc_now(),
                ),
            )

            if sanctions.get("sanctions_flag"):
                conn.execute(
                    """
                    INSERT INTO sanctions_matches(transaction_id, case_id, matched_entity, sanctions_score, payload_json, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        transaction_id,
                        case_id,
                        sanctions.get("matched_entity"),
                        float(sanctions.get("sanctions_score", 0.0)),
                        json.dumps(sanctions, default=str),
                        _utc_now(),
                    ),
                )

            conn.execute(
                """
                INSERT INTO reports(case_id, transaction_id, report_json, created_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(case_id) DO UPDATE SET
                    transaction_id=excluded.transaction_id,
                    report_json=excluded.report_json
                """,
                (case_id, transaction_id, json.dumps(compliance or result.get("compliance_report", {}), default=str), _utc_now()),
            )

            if str(result.get("decision", "")).upper() in {"FLAG", "BLOCK"}:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO alerts(alert_id, transaction_id, case_id, severity, reason, reviewed, payload_json, created_at)
                    VALUES (?, ?, ?, ?, ?, COALESCE((SELECT reviewed FROM alerts WHERE alert_id = ?), 0), ?, ?)
                    """,
                    (
                        case_id,
                        transaction_id,
                        case_id,
                        str(result.get("decision", "FLAG")).upper(),
                        compliance.get("why_flagged") or "; ".join(result.get("reasons", [])),
                        case_id,
                        json.dumps(result, default=str),
                        _utc_now(),
                    ),
                )

            self.upsert_transaction(result, raw_event, normalized)

    def recent_reports(self, limit: int = 20) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            cursor = conn.execute("SELECT case_id, transaction_id, report_json, created_at FROM reports ORDER BY created_at DESC LIMIT ?", (limit,))
            rows = []
            for row in cursor.fetchall():
                rows.append({
                    "case_id": row["case_id"],
                    "transaction_id": row["transaction_id"],
                    "report": json.loads(row["report_json"] or "{}"),
                    "created_at": row["created_at"],
                })
            return rows

