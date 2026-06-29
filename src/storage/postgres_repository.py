"""PostgreSQL persistence for transactions, alerts, reports, and scores."""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import quote

try:  # pragma: no cover - optional dependency
    import psycopg  # type: ignore[import-not-found]
except Exception:  # pragma: no cover
    psycopg = None


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _build_dsn_from_env() -> str:
    explicit_dsn = os.getenv("POSTGRES_DSN", "").strip()
    if explicit_dsn:
        return explicit_dsn

    user = os.getenv("POSTGRES_USER", "").strip()
    password = os.getenv("POSTGRES_PASSWORD", "").strip()
    database = os.getenv("POSTGRES_DB", os.getenv("POSTGRES_DATABASE", "")).strip() or "mule_detection"
    host = os.getenv("POSTGRES_HOST", "").strip()
    port = os.getenv("POSTGRES_PORT", "5432").strip() or "5432"
    use_cloud_sql_socket = os.getenv("POSTGRES_USE_CLOUD_SQL_SOCKET", "false").strip().lower() in {"1", "true", "yes", "on"}
    instance_connection_name = os.getenv("POSTGRES_INSTANCE_CONNECTION_NAME", "").strip()

    if not (user and password):
        return ""

    if use_cloud_sql_socket and instance_connection_name:
        socket_path = f"/cloudsql/{instance_connection_name}"
        return f"postgresql://{quote(user)}:{quote(password)}@/{quote(database)}?host={quote(socket_path)}"

    if host:
        return f"postgresql://{quote(user)}:{quote(password)}@{host}:{port}/{quote(database)}"

    return ""


class PostgresRepository:
    def __init__(self, dsn: Optional[str] = None):
        if psycopg is None:
            raise RuntimeError("psycopg is required for PostgreSQL persistence")

        self.dsn = dsn or _build_dsn_from_env()
        if not self.dsn:
            raise RuntimeError("POSTGRES_DSN is required for PostgreSQL persistence")

        self._lock = threading.Lock()
        self._init_schema()

    def _connect(self):
        return psycopg.connect(self.dsn)

    def _init_schema(self) -> None:
        ddl = """
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id TEXT PRIMARY KEY,
            source_account_id TEXT,
            dest_account_id TEXT,
            channel TEXT,
            amount DOUBLE PRECISION,
            timestamp TEXT,
            payload_json JSONB,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS risk_scores (
            id BIGSERIAL PRIMARY KEY,
            transaction_id TEXT,
            case_id TEXT,
            risk_score DOUBLE PRECISION,
            confidence_score DOUBLE PRECISION,
            decision TEXT,
            ml_score DOUBLE PRECISION,
            rule_score DOUBLE PRECISION,
            sanctions_score DOUBLE PRECISION,
            complexity_score DOUBLE PRECISION,
            jurisdiction_score DOUBLE PRECISION,
            payload_json JSONB,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS sanctions_matches (
            id BIGSERIAL PRIMARY KEY,
            transaction_id TEXT,
            case_id TEXT,
            matched_entity TEXT,
            sanctions_score DOUBLE PRECISION,
            payload_json JSONB,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS reports (
            case_id TEXT PRIMARY KEY,
            transaction_id TEXT,
            report_json JSONB,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS alerts (
            id BIGSERIAL PRIMARY KEY,
            alert_id TEXT UNIQUE,
            transaction_id TEXT,
            case_id TEXT,
            severity TEXT,
            reason TEXT,
            reviewed BOOLEAN DEFAULT FALSE,
            payload_json JSONB,
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
            risk_score DOUBLE PRECISION,
            transaction_id TEXT,
            read BOOLEAN DEFAULT FALSE,
            payload_json JSONB,
            created_at TEXT
        );
        """
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(ddl)
            conn.commit()

    def upsert_auth_user(self, user: Dict[str, Any]) -> None:
        query = """
        INSERT INTO auth_users(user_id, email, full_name, password_hash, created_at)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (user_id) DO UPDATE SET
            email = EXCLUDED.email,
            full_name = EXCLUDED.full_name,
            password_hash = EXCLUDED.password_hash,
            created_at = EXCLUDED.created_at;
        """
        values = (user["user_id"], user["email"], user.get("full_name") or "", user["password_hash"], user.get("created_at") or _utc_now())
        with self._lock, self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(query, values)
            conn.commit()

    def get_auth_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT user_id, email, full_name, password_hash, created_at FROM auth_users WHERE email = %s LIMIT 1", (email,))
                row = cur.fetchone()
        if row is None:
            return None
        return dict(row)

    def get_auth_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT user_id, email, full_name, password_hash, created_at FROM auth_users WHERE user_id = %s LIMIT 1", (user_id,))
                row = cur.fetchone()
        if row is None:
            return None
        return dict(row)

    def upsert_notification(self, notification: Dict[str, Any]) -> None:
        query = """
        INSERT INTO notifications(notification_id, user_id, email, severity, title, message, decision, risk_score, transaction_id, read, payload_json, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s)
        ON CONFLICT (notification_id) DO UPDATE SET
            user_id = EXCLUDED.user_id,
            email = EXCLUDED.email,
            severity = EXCLUDED.severity,
            title = EXCLUDED.title,
            message = EXCLUDED.message,
            decision = EXCLUDED.decision,
            risk_score = EXCLUDED.risk_score,
            transaction_id = EXCLUDED.transaction_id,
            read = EXCLUDED.read,
            payload_json = EXCLUDED.payload_json,
            created_at = EXCLUDED.created_at;
        """
        values = (
            notification["notification_id"],
            notification.get("user_id") or "",
            notification.get("email") or "",
            notification.get("severity") or "MEDIUM",
            notification.get("title") or "Account security alert",
            notification.get("message") or "",
            notification.get("decision") or "",
            float(notification.get("risk_score") or 0.0),
            notification.get("transaction_id") or "",
            bool(notification.get("read")),
            json.dumps(notification, default=str),
            notification.get("created_at") or _utc_now(),
        )
        with self._lock, self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(query, values)
            conn.commit()

    def list_notifications(self, *, user_id: Optional[str] = None, email: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        clauses = []
        params: List[Any] = []
        if user_id:
            clauses.append("user_id = %s")
            params.append(user_id)
        if email:
            clauses.append("email = %s")
            params.append(email)
        if not clauses:
            return []

        params.append(limit)
        query = (
            "SELECT notification_id, user_id, email, severity, title, message, decision, risk_score, transaction_id, read, payload_json, created_at "
            "FROM notifications WHERE " + " OR ".join(clauses) + " ORDER BY created_at DESC LIMIT %s"
        )

        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(query, tuple(params))
                rows = cur.fetchall()

        notifications = []
        for row in rows:
            item = dict(row)
            payload = item.get("payload_json") or {}
            if isinstance(payload, str):
                try:
                    item["payload"] = json.loads(payload)
                except Exception:
                    item["payload"] = {}
            else:
                item["payload"] = payload
            item["read"] = bool(item.get("read"))
            notifications.append(item)
        return notifications

    def mark_notification_read(self, notification_id: str, read: bool = True) -> bool:
        with self._lock, self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE notifications SET read = %s WHERE notification_id = %s",
                    (bool(read), notification_id),
                )
                updated = cur.rowcount > 0
            conn.commit()
        return updated

    def upsert_transaction(self, result: Dict[str, Any], raw_event: Dict[str, Any], normalized: Dict[str, Any]) -> None:
        transaction_id = str(result.get("transaction_id") or normalized.get("event_id") or raw_event.get("event_id") or "unknown")
        query = """
        INSERT INTO transactions(transaction_id, source_account_id, dest_account_id, channel, amount, timestamp, payload_json, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s)
        ON CONFLICT (transaction_id) DO UPDATE SET
            source_account_id = EXCLUDED.source_account_id,
            dest_account_id = EXCLUDED.dest_account_id,
            channel = EXCLUDED.channel,
            amount = EXCLUDED.amount,
            timestamp = EXCLUDED.timestamp,
            payload_json = EXCLUDED.payload_json;
        """
        values = (
            transaction_id,
            normalized.get("source_account_id") or result.get("explainability", {}).get("top_features", {}).get("user_id"),
            normalized.get("dest_account_id") or result.get("explainability", {}).get("top_features", {}).get("counterparty"),
            normalized.get("channel") or raw_event.get("channel") or "UNKNOWN",
            float(normalized.get("amount") or raw_event.get("amount") or 0.0),
            normalized.get("timestamp") or raw_event.get("timestamp") or _utc_now(),
            json.dumps({"raw_event": raw_event, "normalized": normalized}, default=str),
            _utc_now(),
        )
        with self._lock, self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(query, values)
            conn.commit()

    def save_result(self, result: Dict[str, Any], raw_event: Dict[str, Any], normalized: Dict[str, Any]) -> None:
        transaction_id = str(result.get("transaction_id") or normalized.get("event_id") or raw_event.get("event_id") or "unknown")
        compliance = result.get("compliance_report", {}) if isinstance(result.get("compliance_report", {}), dict) else {}
        sanctions = result.get("sanctions_screening", {}) if isinstance(result.get("sanctions_screening", {}), dict) else {}
        complexity = result.get("transaction_complexity", {}) if isinstance(result.get("transaction_complexity", {}), dict) else {}
        jurisdiction = result.get("jurisdiction_risk", {}) if isinstance(result.get("jurisdiction_risk", {}), dict) else {}
        case_id = compliance.get("case_id") or compliance.get("report_id") or result.get("transaction_id") or transaction_id

        with self._lock, self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO risk_scores(transaction_id, case_id, risk_score, confidence_score, decision, ml_score, rule_score, sanctions_score, complexity_score, jurisdiction_score, payload_json, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s)
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
                    cur.execute(
                        """
                        INSERT INTO sanctions_matches(transaction_id, case_id, matched_entity, sanctions_score, payload_json, created_at)
                        VALUES (%s, %s, %s, %s, %s::jsonb, %s)
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

                cur.execute(
                    """
                    INSERT INTO reports(case_id, transaction_id, report_json, created_at)
                    VALUES (%s, %s, %s::jsonb, %s)
                    ON CONFLICT(case_id) DO UPDATE SET
                        transaction_id = EXCLUDED.transaction_id,
                        report_json = EXCLUDED.report_json;
                    """,
                    (case_id, transaction_id, json.dumps(compliance or result.get("compliance_report", {}), default=str), _utc_now()),
                )

                if str(result.get("decision", "")).upper() in {"FLAG", "BLOCK"}:
                    cur.execute(
                        """
                        INSERT INTO alerts(alert_id, transaction_id, case_id, severity, reason, reviewed, payload_json, created_at)
                        VALUES (%s, %s, %s, %s, %s, FALSE, %s::jsonb, %s)
                        ON CONFLICT(alert_id) DO UPDATE SET
                            transaction_id = EXCLUDED.transaction_id,
                            case_id = EXCLUDED.case_id,
                            severity = EXCLUDED.severity,
                            reason = EXCLUDED.reason,
                            payload_json = EXCLUDED.payload_json;
                        """,
                        (
                            case_id,
                            transaction_id,
                            case_id,
                            str(result.get("decision", "FLAG")).upper(),
                            compliance.get("why_flagged") or "; ".join(result.get("reasons", [])),
                            json.dumps(result, default=str),
                            _utc_now(),
                        ),
                    )

            conn.commit()

        self.upsert_transaction(result, raw_event, normalized)

    def recent_reports(self, limit: int = 20) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT case_id, transaction_id, report_json, created_at FROM reports ORDER BY created_at DESC LIMIT %s",
                    (limit,),
                )
                rows = cur.fetchall()

        return [
            {
                "case_id": row[0],
                "transaction_id": row[1],
                "report": row[2] if isinstance(row[2], dict) else json.loads(row[2] or "{}"),
                "created_at": row[3],
            }
            for row in rows
        ]
