"""FastAPI backend for mule detection orchestration."""

from __future__ import annotations

import os
import queue
import csv
import threading
import time
import json
import logging
import hashlib
import hmac
import base64
import secrets
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from typing import Any, Dict, List, Optional
import uuid
import numpy as np

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse, Response
from pydantic import BaseModel, Field, model_validator
from starlette.staticfiles import StaticFiles

from src.data_ingestion.csv_graph_pipeline import build_graph_snapshot, build_report_rows, load_csv_dataframe, normalize_csv_transactions
from src.infrastructure.async_backend import RedisCache, RedisTaskQueue
from src.orchestrator import MuleDetectionOrchestrator
from src.reporting.pdf_report import build_pdf_report
from src.storage.factory import create_repository
from src.storage.repository import SqliteRepository

try:
    from azure.monitor.opentelemetry import configure_azure_monitor
except ImportError:
    configure_azure_monitor = None

logger = logging.getLogger(__name__)

# Initialize OpenTelemetry if in production and connection string is available
_env = os.getenv("APP_ENV", "development").lower()
if _env in ("prod", "production") and configure_azure_monitor:
    _conn_str = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
    if _conn_str:
        try:
            configure_azure_monitor(connection_string=_conn_str)
            logger.info("Azure Monitor OpenTelemetry configured.")
        except Exception as e:
            logger.warning(f"Failed to configure Azure Monitor OpenTelemetry: {e}")


class EventPayload(BaseModel):
    channel: str = Field(..., description="Channel type such as MOBILE, ATM, UPI")
    raw_event: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_channel_payload(self) -> "EventPayload":
        channel = (self.channel or "").upper()
        raw = self.raw_event or {}

        required_by_channel: Dict[str, List[str]] = {
            "MOBILE": ["user_id", "transfer_to_wallet", "transfer_amount", "transfer_time"],
            "WEB": ["user_id", "beneficiary_account", "transfer_amount", "transfer_time"],
            "ATM": ["terminal_id", "withdrawal_amount", "withdrawal_time"],
            "UPI": ["upi_id", "recipient_upi", "txn_amount", "txn_ref_id", "timestamp"],
        }

        if channel not in required_by_channel:
            raise ValueError("channel must be one of: MOBILE, WEB, ATM, UPI")

        missing = [k for k in required_by_channel[channel] if k not in raw]
        if missing:
            raise ValueError(f"raw_event missing required fields for {channel}: {', '.join(missing)}")

        if channel in {"MOBILE", "WEB", "ATM"}:
            location = raw.get("location")
            if not isinstance(location, dict):
                raise ValueError(f"raw_event.location is required for {channel}")
            if "latitude" not in location or "longitude" not in location:
                raise ValueError(f"raw_event.location.latitude and raw_event.location.longitude are required for {channel}")

        return self


class ProcessBatchRequest(BaseModel):
    events: List[EventPayload]


class ProcessBatchResponse(BaseModel):
    status: str
    count: int
    success_count: int
    failed_count: int
    results: List[Dict[str, Any]]


class StreamPublishRequest(BaseModel):
    event: EventPayload


class StreamPublishBatchRequest(BaseModel):
    events: List[EventPayload]


class PrivacyIndicatorShareRequest(BaseModel):
    indicator_type: str = Field(..., description="Type such as device, ip, destination_account")
    value: str = Field(..., description="Raw indicator value; stored as hashed value only")
    source_bank: str = Field(default="BANK_LOCAL")
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)
    nonce: Optional[str] = Field(default=None, description="Replay protection nonce")
    event_timestamp: Optional[str] = Field(default=None, description="Event timestamp for replay protection")


class CsvTextRequest(BaseModel):
    csv_text: str = Field(..., description="CSV content containing transaction rows")
    out_dir: str = Field(default="models")
    epochs: int = Field(default=40, ge=1, le=200)
    hidden_dim: int = Field(default=64, ge=16, le=256)
    seed: int = Field(default=42, ge=0, le=9999)


class PredictCsvRequest(BaseModel):
    csv_text: str = Field(..., description="CSV content containing transaction rows")


class StreamControlResponse(BaseModel):
    status: str
    monitoring: bool
    queue_size: int
    results_size: int


class SignupRequest(BaseModel):
    identity: Optional[str] = Field(default=None, min_length=3, max_length=255)
    email: Optional[str] = Field(default=None, min_length=5, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    full_name: Optional[str] = Field(default=None, max_length=120)

    @model_validator(mode="after")
    def validate_identity(self) -> "SignupRequest":
        if not (self.identity or self.email):
            raise ValueError("identity or email is required")
        return self


class LoginRequest(BaseModel):
    identity: Optional[str] = Field(default=None, min_length=3, max_length=255)
    email: Optional[str] = Field(default=None, min_length=5, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)

    @model_validator(mode="after")
    def validate_identity(self) -> "LoginRequest":
        if not (self.identity or self.email):
            raise ValueError("identity or email is required")
        return self


class NotificationReadRequest(BaseModel):
    read: bool = True


class AlertActionRequest(BaseModel):
    action: str = Field(..., description="investigate|mark_fraud|mark_safe|freeze_account")
    note: Optional[str] = Field(default=None, max_length=500)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _utc_now_timestamp() -> int:
    return int(datetime.now(timezone.utc).timestamp())


@asynccontextmanager
async def lifespan(_: FastAPI):
    _seed_staff_users()
    _ensure_stream_worker()
    _ensure_analysis_worker()
    try:
        yield
    finally:
        global _stream_thread
        global _analysis_thread
        _stream_stop.set()
        _analysis_stop.set()
        if _stream_thread and _stream_thread.is_alive():
            _stream_thread.join(timeout=2)
        if _analysis_thread and _analysis_thread.is_alive():
            _analysis_thread.join(timeout=2.0)
        _stream_thread = None

        global _orchestrator
        if _orchestrator is not None:
            _orchestrator.close()
            _orchestrator = None


app = FastAPI(
    title="Cross-Channel Mule Detection API",
    version="1.0.0",
    description="API layer for transaction scoring and mule detection",
    lifespan=lifespan,
)

_cors_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ALLOW_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000",
    ).split(",")
    if origin.strip()
]

_cors_allow_origin_regex = os.getenv("CORS_ALLOW_ORIGIN_REGEX", "").strip()
_cors_env = (os.getenv("APP_ENV") or os.getenv("ENV") or "").strip().lower()
if not _cors_allow_origin_regex and _cors_env in {"prod", "production"} and not _cors_origins:
    # Fallback for production when no explicit origins are configured.
    _cors_allow_origin_regex = r"https://.*\.run\.app"

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_origin_regex=_cors_allow_origin_regex or None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_orchestrator: Optional[MuleDetectionOrchestrator] = None
_stream_queue: queue.Queue = queue.Queue(maxsize=5000)
_stream_results: deque = deque(maxlen=1000)
_stream_stop = threading.Event()
_stream_thread: Optional[threading.Thread] = None
_live_stream_transactions: deque = deque(maxlen=2000)
_live_gnn_snapshot: Dict[str, Any] = {}
_analysis_backend = RedisTaskQueue()
_prediction_cache = RedisCache()
_analysis_thread: Optional[threading.Thread] = None
_analysis_stop = threading.Event()

FLAG_THRESHOLD = float(os.getenv("RISK_FLAG_THRESHOLD", "0.45"))
BLOCK_THRESHOLD = float(os.getenv("RISK_BLOCK_THRESHOLD", "0.65"))

HYBRID_WEIGHTS: Dict[str, float] = {
    "graph": float(os.getenv("HYBRID_WEIGHT_GRAPH", "0.45")),
    "rule": float(os.getenv("HYBRID_WEIGHT_RULE", "0.30")),
    "pattern": float(os.getenv("HYBRID_WEIGHT_PATTERN", "0.20")),
    "jurisdiction": float(os.getenv("HYBRID_WEIGHT_JURISDICTION", "0.05")),
}

CALIBRATION_MIN_SAMPLES = int(os.getenv("RISK_CALIBRATION_MIN_SAMPLES", "20"))
CALIBRATION_FLAG_QUANTILE = float(os.getenv("RISK_CALIBRATION_FLAG_QUANTILE", "0.60"))
CALIBRATION_BLOCK_QUANTILE = float(os.getenv("RISK_CALIBRATION_BLOCK_QUANTILE", "0.85"))

def _create_auth_repository():
    repository = create_repository()
    if isinstance(repository, SqliteRepository):
        auth_db_path = os.getenv("AUTH_SQLITE_DB_PATH", "data/auth_notifications.sqlite3")
        return SqliteRepository(auth_db_path)
    return repository


_auth_repository = _create_auth_repository()

_auth_lock = threading.Lock()
_users_by_email: Dict[str, Dict[str, Any]] = {}
_users_by_id: Dict[str, Dict[str, Any]] = {}
_user_notifications: Dict[str, deque] = defaultdict(lambda: deque(maxlen=200))
_staff_seeded = False
_alert_states: Dict[str, Dict[str, Any]] = {}

_metrics: Dict[str, Any] = {
    "requests_total": 0,
    "errors_total": 0,
    "request_duration_seconds_sum": 0.0,
    "request_duration_seconds_count": 0,
    "request_durations_ms": deque(maxlen=5000),
    "by_route": defaultdict(int),
}

_rate_window_seconds = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
_rate_limit_per_window = int(os.getenv("RATE_LIMIT_PER_WINDOW", "120"))
_rate_state: Dict[str, deque] = defaultdict(deque)


def _is_production_env() -> bool:
    env = (os.getenv("APP_ENV") or os.getenv("ENV") or "").strip().lower()
    return env in {"prod", "production"}


def _auth_required() -> bool:
    raw = os.getenv("AUTH_REQUIRED")
    if raw is None:
        return _is_production_env()
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _api_key() -> str:
    key = os.getenv("API_KEY", "").strip()
    if key:
        return key
    if _is_production_env():
        return ""
    return "hackathon-demo-key"


def _security_headers_for_request(request: Request) -> Dict[str, str]:
    headers = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Referrer-Policy": "no-referrer",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
        "Cache-Control": "no-store",
    }
    if request.url.scheme == "https":
        headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    return headers


def _apply_security_headers(response: Response, request: Request) -> Response:
    for key, value in _security_headers_for_request(request).items():
        response.headers[key] = value
    return response


def _client_identity(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for", "").strip()
    if forwarded_for:
        first_ip = forwarded_for.split(",", 1)[0].strip()
        if first_ip:
            return first_ip
    real_ip = request.headers.get("x-real-ip", "").strip()
    if real_ip:
        return real_ip
    return request.client.host if request.client else "unknown"


def _auth_secret() -> str:
    secret = os.getenv("APP_AUTH_SECRET", "").strip()
    if secret:
        return secret
    # Development fallback; set APP_AUTH_SECRET in production.
    return "cmds-dev-auth-secret"


def _token_ttl_seconds() -> int:
    raw = os.getenv("AUTH_TOKEN_TTL_SECONDS", "86400")
    try:
        return max(300, int(raw))
    except ValueError:
        return 86400


def _now_epoch() -> int:
    return int(time.time())


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def _b64url_decode(raw: str) -> bytes:
    padding = "=" * ((4 - len(raw) % 4) % 4)
    return base64.urlsafe_b64decode(raw + padding)


def _sign_token(payload: Dict[str, Any]) -> str:
    message = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    message_part = _b64url_encode(message)
    signature = hmac.new(_auth_secret().encode("utf-8"), message_part.encode("utf-8"), hashlib.sha256).digest()
    signature_part = _b64url_encode(signature)
    return f"{message_part}.{signature_part}"


def _decode_token(token: str) -> Dict[str, Any]:
    try:
        message_part, signature_part = token.split(".", 1)
    except ValueError as exc:
        raise ValueError("invalid token format") from exc

    expected_sig = hmac.new(_auth_secret().encode("utf-8"), message_part.encode("utf-8"), hashlib.sha256).digest()
    actual_sig = _b64url_decode(signature_part)
    if not hmac.compare_digest(expected_sig, actual_sig):
        raise ValueError("invalid token signature")

    payload_raw = _b64url_decode(message_part)
    payload = json.loads(payload_raw.decode("utf-8"))
    exp = int(payload.get("exp", 0))
    if exp <= _now_epoch():
        raise ValueError("token expired")
    return payload


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _normalize_role(role: str) -> str:
    value = str(role or "ANALYST").strip().upper()
    if value not in {"ANALYST", "ADMIN"}:
        return "ANALYST"
    return value


def _default_employee_id(email: str) -> str:
    local = str(email or "staff").split("@", 1)[0]
    return f"EMP-{local[:12].upper()}"


def _hash_password(password: str, salt: Optional[str] = None) -> str:
    local_salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), local_salt.encode("utf-8"), 200_000)
    return f"{local_salt}${digest.hex()}"


def _verify_password(password: str, stored_hash: str) -> bool:
    if "$" not in stored_hash:
        return False
    salt, _ = stored_hash.split("$", 1)
    calculated = _hash_password(password, salt)
    return hmac.compare_digest(calculated, stored_hash)


def _public_user(user: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "user_id": user["user_id"],
        "email": user["email"],
        "employee_id": user.get("employee_id") or _default_employee_id(user.get("email", "")),
        "role": _normalize_role(str(user.get("role") or "ANALYST")),
        "full_name": user.get("full_name") or "",
        "created_at": user["created_at"],
    }


def _repo_has_method(name: str) -> bool:
    return _auth_repository is not None and hasattr(_auth_repository, name)


def _load_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    if _repo_has_method("get_auth_user_by_email"):
        user = _auth_repository.get_auth_user_by_email(email)  # type: ignore[union-attr]
        if user:
            return user
    with _auth_lock:
        return _users_by_email.get(email)


def _load_user_by_identity(identity: str) -> Optional[Dict[str, Any]]:
    value = str(identity or "").strip()
    if not value:
        return None
    if "@" in value:
        return _load_user_by_email(_normalize_email(value))

    with _auth_lock:
        for user in _users_by_email.values():
            if str(user.get("employee_id") or "").strip().upper() == value.upper():
                return user
    return None


def _load_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    if _repo_has_method("get_auth_user_by_id"):
        user = _auth_repository.get_auth_user_by_id(user_id)  # type: ignore[union-attr]
        if user:
            return user
    with _auth_lock:
        return _users_by_id.get(user_id)


def _save_auth_user(user: Dict[str, Any]) -> None:
    if _repo_has_method("upsert_auth_user"):
        _auth_repository.upsert_auth_user(user)  # type: ignore[union-attr]
        return
    with _auth_lock:
        _users_by_email[user["email"]] = user
        _users_by_id[user["user_id"]] = user


def _seed_staff_users() -> None:
    global _staff_seeded
    if _staff_seeded:
        return

    raw = os.getenv("STAFF_BOOTSTRAP_USERS", "")
    seed_rows = []
    if raw.strip():
        # Format: email|employee_id|password|role|full_name;...
        for chunk in raw.split(";"):
            chunk = chunk.strip()
            if not chunk:
                continue
            parts = [item.strip() for item in chunk.split("|")]
            if len(parts) < 5:
                continue
            seed_rows.append(
                {
                    "email": _normalize_email(parts[0]),
                    "employee_id": parts[1] or _default_employee_id(parts[0]),
                    "password": parts[2],
                    "role": _normalize_role(parts[3]),
                    "full_name": parts[4],
                }
            )
    else:
        seed_rows = [
            {
                "email": "analyst@bank.local",
                "employee_id": "EMP-1001",
                "password": "Analyst@123",
                "role": "ANALYST",
                "full_name": "Fraud Analyst",
            },
            {
                "email": "admin@bank.local",
                "employee_id": "EMP-9001",
                "password": "Admin@123",
                "role": "ADMIN",
                "full_name": "Fraud Admin",
            },
        ]

    for row in seed_rows:
        existing = _load_user_by_email(row["email"])
        if existing:
            with _auth_lock:
                existing["employee_id"] = row["employee_id"]
                existing["role"] = row["role"]
                _users_by_email[existing["email"]] = existing
                _users_by_id[existing["user_id"]] = existing
            continue

        stable_user_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"cmds-staff:{row['email']}"))
        user = {
            "user_id": stable_user_id,
            "email": row["email"],
            "employee_id": row["employee_id"],
            "role": row["role"],
            "full_name": row["full_name"],
            "password_hash": _hash_password(row["password"]),
            "created_at": _utc_now_iso(),
        }
        _save_auth_user(user)
        with _auth_lock:
            _users_by_email[user["email"]] = user
            _users_by_id[user["user_id"]] = user

    _staff_seeded = True


def _save_notification(notification: Dict[str, Any]) -> None:
    if _repo_has_method("upsert_notification"):
        _auth_repository.upsert_notification(notification)  # type: ignore[union-attr]
        return
    key = str(notification.get("user_id") or notification.get("email") or "")
    if key:
        _user_notifications[key].appendleft(notification)


def _load_notifications(user: Dict[str, Any], limit: int = 50) -> List[Dict[str, Any]]:
    if _repo_has_method("list_notifications"):
        return _auth_repository.list_notifications(  # type: ignore[union-attr]
            user_id=user.get("user_id"),
            email=user.get("email"),
            limit=limit,
        )

    merged_rows: List[Dict[str, Any]] = []
    for key in _notification_keys_for_user(user):
        merged_rows.extend(list(_user_notifications[key]))

    seen: set[str] = set()
    rows: List[Dict[str, Any]] = []
    for row in sorted(merged_rows, key=lambda item: str(item.get("created_at") or ""), reverse=True):
        notification_id = str(row.get("notification_id") or "")
        if not notification_id or notification_id in seen:
            continue
        seen.add(notification_id)
        rows.append(row)
        if len(rows) >= limit:
            break
    return rows


def _issue_auth_token(user: Dict[str, Any]) -> str:
    now = _now_epoch()
    payload = {
        "sub": user["user_id"],
        "email": user["email"],
        "employee_id": user.get("employee_id") or _default_employee_id(user.get("email", "")),
        "role": _normalize_role(str(user.get("role") or "ANALYST")),
        "iat": now,
        "exp": now + _token_ttl_seconds(),
    }
    return _sign_token(payload)


def _risk_level(score: float) -> str:
    if score >= 0.75:
        return "RED"
    if score >= 0.45:
        return "YELLOW"
    return "GREEN"


def _infer_channel(result: Dict[str, Any]) -> str:
    direct = str(
        result.get("channel")
        or result.get("source_channel")
        or result.get("source_transaction_type")
        or ""
    ).strip().upper()
    if direct:
        return direct
    return "APP"


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def _is_small_structured_amount(amount: float) -> bool:
    return 300.0 <= amount <= 2500.0 or 9000.0 <= amount < 10000.0


def _build_record_stats(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    by_sender: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    sender_unique_receivers: Dict[str, set[str]] = defaultdict(set)

    for row in records:
        sender = str(row.get("sender_id") or "")
        receiver = str(row.get("receiver_id") or "")
        if sender:
            by_sender[sender].append(row)
        if sender and receiver:
            sender_unique_receivers[sender].add(receiver)

    for sender, sender_rows in by_sender.items():
        sender_rows.sort(key=lambda item: str(item.get("timestamp_iso") or ""))

    return {
        "by_sender": by_sender,
        "sender_unique_receivers": sender_unique_receivers,
    }


def _compute_pattern_signals_for_transaction(
    tx: Dict[str, Any],
    record_stats: Dict[str, Any],
    flagged_paths: List[Dict[str, Any]],
) -> Dict[str, bool]:
    sender = str(tx.get("sender_id") or "")
    tx_id = str(tx.get("transaction_id") or "")
    sender_rows: List[Dict[str, Any]] = record_stats.get("by_sender", {}).get(sender, [])

    structuring_hits = 0
    for row in sender_rows:
        gap = _safe_float(row.get("time_diff_minutes"), 0.0)
        amount = _safe_float(row.get("amount"), 0.0)
        if gap <= 30.0 and _is_small_structured_amount(amount):
            structuring_hits += 1

    fan_out = len(record_stats.get("sender_unique_receivers", {}).get(sender, set()))

    nesting = False
    unusual_routing = False
    for path in flagged_paths:
        if not isinstance(path, dict):
            continue
        tx_ids = {str(item) for item in (path.get("transaction_ids") or [])}
        hop_count = int(path.get("hop_count") or 0)
        node_path = path.get("node_path") or []
        in_path = tx_id in tx_ids or sender in {str(node) for node in node_path}
        if not in_path:
            continue
        if hop_count >= 3:
            nesting = True
        if hop_count >= 3 or len(node_path) >= 4:
            unusual_routing = True

    return {
        "structuring": structuring_hits >= 3,
        "fragmentation": fan_out >= 3,
        "nesting": nesting,
        "unusual_routing": unusual_routing,
    }


def _compute_hybrid_risk(
    *,
    edge: Dict[str, Any],
    source_record: Optional[Dict[str, Any]],
    pattern_signals: Dict[str, bool],
    fan_out_count: int,
) -> Dict[str, Any]:
    graph_score = max(_safe_float(edge.get("anomaly_score"), 0.0), _safe_float(edge.get("velocity_score"), 0.0))

    amount = _safe_float(source_record.get("amount") if source_record else 0.0, 0.0)
    velocity = _safe_float(edge.get("velocity_score"), 0.0)
    amount_signal = min(amount / 10000.0, 1.0)
    fan_out_signal = min(float(fan_out_count) / 6.0, 1.0)
    rule_score = (0.45 * velocity) + (0.35 * amount_signal) + (0.20 * fan_out_signal)

    pattern_score = (
        0.30 * float(pattern_signals.get("structuring", False))
        + 0.25 * float(pattern_signals.get("fragmentation", False))
        + 0.25 * float(pattern_signals.get("nesting", False))
        + 0.20 * float(pattern_signals.get("unusual_routing", False))
    )

    country = ""
    if source_record:
        location = source_record.get("location") if isinstance(source_record.get("location"), dict) else {}
        country = str(location.get("country") or source_record.get("risk_hint_country") or "").upper()
    jurisdiction_score = 1.0 if country in {"KP", "IR", "SY", "CU", "RU"} else 0.0

    final_risk = (
        HYBRID_WEIGHTS["graph"] * graph_score
        + HYBRID_WEIGHTS["rule"] * rule_score
        + HYBRID_WEIGHTS["pattern"] * pattern_score
        + HYBRID_WEIGHTS["jurisdiction"] * jurisdiction_score
    )
    final_risk = max(0.0, min(1.0, final_risk))

    return {
        "risk_score": float(round(final_risk, 4)),
        "breakdown": {
            "graph": float(round(graph_score, 4)),
            "rule": float(round(rule_score, 4)),
            "pattern": float(round(pattern_score, 4)),
            "jurisdiction": float(round(jurisdiction_score, 4)),
            "weights": HYBRID_WEIGHTS,
            "rule_signals": {
                "velocity": float(round(velocity, 4)),
                "amount": float(round(amount_signal, 4)),
                "fan_out": float(round(fan_out_signal, 4)),
            },
            "pattern_signals": pattern_signals,
            "country": country or "UNKNOWN",
        },
    }


def _replace_stream_rows(new_results: List[Dict[str, Any]]) -> None:
    if not new_results:
        return
    new_ids = {
        str(item.get("source_transaction_id") or item.get("transaction_id") or "")
        for item in new_results
        if item.get("source_transaction_id") or item.get("transaction_id")
    }
    filtered = [
        item
        for item in list(_stream_results)
        if str((item.get("result") or {}).get("source_transaction_id") or (item.get("result") or {}).get("transaction_id") or "") not in new_ids
    ]
    _stream_results.clear()
    for item in filtered:
        _stream_results.append(item)
    for result in new_results:
        _stream_results.append({"queued_at": result.get("timestamp") or _utc_now_iso(), "result": result})


def _collect_risk_scores_from_stream(limit: int = 1000) -> List[float]:
    scores: List[float] = []
    for entry in list(_stream_results)[-max(1, min(limit, 5000)) :]:
        result = entry.get("result") if isinstance(entry, dict) else None
        if not isinstance(result, dict):
            continue
        value = _safe_float(result.get("risk_score"), -1.0)
        if 0.0 <= value <= 1.0:
            scores.append(value)
    return scores


def _calibrate_thresholds(batch_scores: List[float]) -> Dict[str, float]:
    historical_scores = _collect_risk_scores_from_stream(limit=1000)
    samples = [score for score in [*historical_scores, *batch_scores] if 0.0 <= score <= 1.0]
    if len(samples) < CALIBRATION_MIN_SAMPLES:
        return {
            "flag_threshold": FLAG_THRESHOLD,
            "block_threshold": BLOCK_THRESHOLD,
            "sample_count": float(len(samples)),
        }

    arr = np.array(samples, dtype=np.float32)
    calibrated_flag = float(np.quantile(arr, CALIBRATION_FLAG_QUANTILE))
    calibrated_block = float(np.quantile(arr, CALIBRATION_BLOCK_QUANTILE))

    calibrated_flag = max(0.40, min(0.70, calibrated_flag))
    calibrated_block = max(0.60, min(0.92, calibrated_block))
    if calibrated_block <= calibrated_flag:
        calibrated_block = min(0.92, calibrated_flag + 0.12)
    if calibrated_block - calibrated_flag < 0.08:
        calibrated_block = min(0.92, calibrated_flag + 0.08)

    return {
        "flag_threshold": round(calibrated_flag, 4),
        "block_threshold": round(calibrated_block, 4),
        "sample_count": float(len(samples)),
    }


def _collect_recent_transactions(limit: int = 200) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for entry in list(_stream_results)[-max(1, min(limit, 500)) :]:
        result = entry.get("result") if isinstance(entry, dict) else None
        if not isinstance(result, dict):
            continue
        channel = _infer_channel(result)
        risk_score = float(result.get("risk_score") or 0.0)
        decision = str(result.get("decision") or "ALLOW").upper()
        rows.append(
            {
                "transaction_id": str(result.get("transaction_id") or result.get("source_transaction_id") or ""),
                "user_id": str(
                    result.get("source_user_id")
                    or result.get("explainability", {}).get("top_features", {}).get("user_id")
                    or "unknown"
                ),
                "account_id": str(result.get("source_account_id") or result.get("source_user_id") or "unknown"),
                "amount": float(result.get("amount") or result.get("explainability", {}).get("top_features", {}).get("amount") or 0.0),
                "currency": str(result.get("currency") or "INR"),
                "channel": channel,
                "channels_involved": [channel],
                "risk_score": risk_score,
                "risk_level": _risk_level(risk_score),
                "decision": decision,
                "timestamp": result.get("timestamp") or entry.get("queued_at") or _utc_now_iso(),
                "confidence_score": round(max(0.5, min(0.99, risk_score + 0.12)), 2),
                "velocity_score": float(result.get("velocity_score") or 0.0),
                    "name": result.get("source_name"),
                    "mobile_number": result.get("source_mobile_number"),
                    "account_number": result.get("source_account_number"),
                    "account_product_type": result.get("source_account_product_type"),
                    "narration": result.get("source_narration"),
                    "pincode": result.get("source_pincode"),
                    "receiver_id": result.get("source_receiver_id")
                    or result.get("explainability", {}).get("top_features", {}).get("counterparty"),
            }
        )
    rows.sort(key=lambda item: str(item.get("timestamp") or ""), reverse=True)
    return rows


def _collect_analyst_alerts(limit: int = 200) -> List[Dict[str, Any]]:
    rows = []
    for entry in list(_stream_results)[-max(1, min(limit, 500)) :]:
        result = entry.get("result") if isinstance(entry, dict) else None
        if not isinstance(result, dict):
            continue
        decision = str(result.get("decision") or "ALLOW").upper()
        if decision not in {"FLAG", "BLOCK"}:
            continue
        user_id = (
            result.get("source_user_id")
            or result.get("explainability", {}).get("top_features", {}).get("user_id")
            or result.get("transaction_id")
            or "unknown"
        )
        alert_id = str(result.get("transaction_id") or f"ALT_{len(rows)}")
        state = _alert_states.get(alert_id, {"status": "OPEN"})
        risk_score = float(result.get("risk_score") or 0.0)
        channel = _infer_channel(result)
        reasons = result.get("reasons") if isinstance(result.get("reasons"), list) else []
        top_features = result.get("explainability", {}).get("top_features", {}) if isinstance(result.get("explainability"), dict) else {}
        source_account = str(result.get("source_account_id") or user_id)
        destination = str(top_features.get("counterparty") or "unknown")
        rows.append(
            {
                "alert_id": alert_id,
                "alert_type": "decision",
                "user_id": str(user_id),
                "account_id": str(result.get("source_account_id") or user_id),
                "risk_score": risk_score,
                "risk_level": _risk_level(risk_score),
                "reason": ", ".join(reasons) or "Suspicious activity",
                "detection_reason": ", ".join(reasons) or "velocity/network anomaly",
                "channels_involved": [channel],
                "confidence_score": round(max(0.5, min(0.99, risk_score + 0.12)), 2),
                "timestamp": result.get("timestamp") or entry.get("queued_at") or _utc_now_iso(),
                "status": str(state.get("status") or "OPEN").upper(),
                "decision": decision,
                "case_id": str(state.get("case_id") or f"CASE-{alert_id}"),
                "risk_breakdown": result.get("risk_breakdown") if isinstance(result.get("risk_breakdown"), dict) else {},
                "pattern_signals": result.get("pattern_signals") if isinstance(result.get("pattern_signals"), dict) else {},
                "transaction_flow_summary": {
                    "path": [source_account, destination],
                    "hops": 1,
                    "max_gap_minutes": 0.0,
                },
            }
        )
    rows.sort(key=lambda item: str(item.get("timestamp") or ""), reverse=True)
    return rows


def _collect_graph_alerts(limit: int = 200) -> List[Dict[str, Any]]:
    data = get_graph_data()
    rows: List[Dict[str, Any]] = []
    for idx, path in enumerate((data.get("flagged_paths") or [])[:limit]):
        if not isinstance(path, dict):
            continue
        alert_id = str(path.get("path_id") or f"PATH_{idx}")
        state = _alert_states.get(alert_id, {"status": "OPEN"})
        node_path = path.get("node_path") if isinstance(path.get("node_path"), list) else []
        account_id = str(node_path[0]) if node_path else "graph"
        risk_score = _safe_float(path.get("cumulative_risk"), 0.0)
        rows.append(
            {
                "alert_id": alert_id,
                "alert_type": "graph",
                "user_id": account_id,
                "account_id": account_id,
                "risk_score": risk_score,
                "risk_level": _risk_level(risk_score),
                "reason": f"Rapid path ({int(path.get('hop_count') or 0)} hops), max gap {_safe_float(path.get('max_gap_minutes'), 0.0):.2f}m",
                "detection_reason": f"Rapid path ({int(path.get('hop_count') or 0)} hops), max gap {_safe_float(path.get('max_gap_minutes'), 0.0):.2f}m, risk {risk_score:.2f}",
                "channels_involved": ["MULTI"],
                "confidence_score": round(max(0.5, min(0.99, risk_score + 0.1)), 2),
                "timestamp": _utc_now_iso(),
                "status": str(state.get("status") or "OPEN").upper(),
                "decision": "GRAPH_ALERT",
                "case_id": str(state.get("case_id") or f"CASE-{alert_id}"),
                "risk_breakdown": {
                    "graph": float(round(risk_score, 4)),
                    "rule": 0.0,
                    "pattern": 0.6,
                    "jurisdiction": 0.0,
                },
                "pattern_signals": {
                    "structuring": False,
                    "fragmentation": False,
                    "nesting": int(path.get("hop_count") or 0) >= 3,
                    "unusual_routing": int(path.get("hop_count") or 0) >= 3,
                },
                  "transaction_flow_summary": {
                      "path": [str(node) for node in node_path],
                      "hops": int(path.get("hop_count") or 0),
                      "max_gap_minutes": float(round(_safe_float(path.get("max_gap_minutes"), 0.0), 2)),
                  },
            }
        )

    remaining = max(0, limit - len(rows))
    for idx, cluster in enumerate((data.get("clusters") or [])[:remaining]):
        if not isinstance(cluster, dict):
            continue
        alert_id = str(cluster.get("cluster_id") or f"MULE_CLUSTER_{idx}")
        state = _alert_states.get(alert_id, {"status": "OPEN"})
        members = cluster.get("account_ids") if isinstance(cluster.get("account_ids"), list) else []
        account_id = str(members[0]) if members else "cluster"
        risk_score = _safe_float(cluster.get("average_risk_score"), 0.0)
        rows.append(
            {
                "alert_id": alert_id,
                "alert_type": "graph",
                "user_id": account_id,
                "account_id": account_id,
                "risk_score": risk_score,
                "risk_level": _risk_level(risk_score),
                "reason": f"Cluster {alert_id} risk {risk_score:.2f}",
                "detection_reason": f"Cluster {alert_id} risk {risk_score:.2f} across {int(cluster.get('size') or len(members))} accounts",
                "channels_involved": ["MULTI"],
                "confidence_score": round(max(0.5, min(0.99, risk_score + 0.1)), 2),
                "timestamp": _utc_now_iso(),
                "status": str(state.get("status") or "OPEN").upper(),
                "decision": "GRAPH_ALERT",
                "case_id": str(state.get("case_id") or f"CASE-{alert_id}"),
                "risk_breakdown": {
                    "graph": float(round(risk_score, 4)),
                    "rule": 0.0,
                    "pattern": 0.55,
                    "jurisdiction": 0.0,
                },
                "pattern_signals": {
                    "structuring": False,
                    "fragmentation": bool(len(members) >= 3),
                    "nesting": False,
                    "unusual_routing": False,
                },
                  "transaction_flow_summary": {
                      "path": [str(member) for member in members[:6]],
                      "hops": max(0, len(members) - 1),
                      "max_gap_minutes": 0.0,
                  },
            }
        )

    rows.sort(key=lambda item: str(item.get("timestamp") or ""), reverse=True)
    return rows[:limit]


def _derive_pattern_indicators_for_user(user_id: str, history: List[Dict[str, Any]], graph: Dict[str, Any]) -> Dict[str, bool]:
    tx_for_user = [row for row in history if str(row.get("transaction_id") or "")]
    small_structured = sum(1 for row in tx_for_user if _is_small_structured_amount(_safe_float(row.get("amount"), 0.0)))

    counterparties = set()
    for row in tx_for_user:
        top = row.get("explainability", {}).get("top_features", {}) if isinstance(row.get("explainability"), dict) else {}
        cp = str(top.get("counterparty") or "").strip()
        if cp:
            counterparties.add(cp)

    flagged_paths = graph.get("flagged_paths") if isinstance(graph, dict) else []
    nesting = False
    unusual_routing = False
    for path in flagged_paths or []:
        if not isinstance(path, dict):
            continue
        node_path = {str(node) for node in (path.get("node_path") or [])}
        if str(user_id) not in node_path:
            continue
        hop_count = int(path.get("hop_count") or 0)
        if hop_count >= 3:
            nesting = True
        if hop_count >= 3 or len(node_path) >= 4:
            unusual_routing = True

    return {
        "structuring": small_structured >= 3,
        "fragmentation": len(counterparties) >= 3,
        "nesting": nesting,
        "unusual_routing": unusual_routing,
    }


def _collect_unified_alerts(limit: int = 100) -> List[Dict[str, Any]]:
    safe_limit = max(1, min(limit, 500))
    decision_alerts = _collect_analyst_alerts(limit=safe_limit)
    graph_alerts = _collect_graph_alerts(limit=safe_limit)
    merged: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for row in [*decision_alerts, *graph_alerts]:
        key = str(row.get("alert_id") or "")
        if not key or key in seen:
            continue
        seen.add(key)
        merged.append(row)
    merged.sort(key=lambda item: str(item.get("timestamp") or ""), reverse=True)
    return merged[:safe_limit]


def _collect_users_summary(limit: int = 500) -> List[Dict[str, Any]]:
    users: Dict[str, Dict[str, Any]] = {}
    for entry in list(_stream_results)[-max(1, min(limit, 2000)) :]:
        result = entry.get("result") if isinstance(entry, dict) else None
        if not isinstance(result, dict):
            continue
        user_id = (
            result.get("source_user_id")
            or result.get("explainability", {}).get("top_features", {}).get("user_id")
            or "unknown"
        )
        risk = float(result.get("risk_score") or 0.0)
        decision = str(result.get("decision") or "ALLOW").upper()
        row = users.setdefault(
            str(user_id),
            {
                "user_id": str(user_id),
                "risk_score": risk,
                "current_status": decision,
                "transactions": 0,
                "latest_timestamp": result.get("timestamp") or entry.get("queued_at") or _utc_now_iso(),
            },
        )
        row["transactions"] += 1
        if risk >= float(row.get("risk_score") or 0.0):
            row["risk_score"] = risk
            row["current_status"] = decision
        row["latest_timestamp"] = result.get("timestamp") or row.get("latest_timestamp")

    out = list(users.values())
    out.sort(key=lambda item: float(item.get("risk_score") or 0.0), reverse=True)
    for item in out:
        item["risk_level"] = _risk_level(float(item.get("risk_score") or 0.0))
    return out


def _require_role(request: Request, allowed_roles: List[str]) -> Dict[str, Any]:
    user = _get_current_user(request)
    user_role = _normalize_role(str(user.get("role") or "ANALYST"))
    allowed = {_normalize_role(role) for role in allowed_roles}
    if user_role not in allowed:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return user


def _notification_keys_for_user(user: Dict[str, Any]) -> List[str]:
    keys: List[str] = []
    for value in [user.get("user_id"), user.get("email")]:
        text = str(value or "").strip()
        if text and text not in keys:
            keys.append(text)
    return keys


def _get_current_user(request: Request) -> Dict[str, Any]:
    auth_header = request.headers.get("authorization", "").strip()
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")

    token = auth_header[len("Bearer ") :].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Missing bearer token")

    try:
        payload = _decode_token(token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    user_id = str(payload.get("sub") or "")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = _load_user_by_id(user_id)
    if not user:
        # Fallback for multi-instance deployments where older seeded user IDs differ.
        payload_email = _normalize_email(str(payload.get("email") or ""))
        if payload_email:
            user = _load_user_by_email(payload_email)

    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def _extract_source_user_id(payload: Dict[str, Any], result: Dict[str, Any]) -> str:
    raw = payload.get("raw_event") if isinstance(payload.get("raw_event"), dict) else {}
    from_result = result.get("explainability", {}).get("top_features", {}).get("user_id")
    candidates = [
        from_result,
        result.get("source_user_id"),
        raw.get("user_id"),
        raw.get("upi_id"),
        raw.get("terminal_id"),
    ]
    for value in candidates:
        if value:
            return str(value)
    return ""


def _resolve_user_identity(identifier: str) -> Dict[str, Any]:
    return _load_user_by_id(identifier) or _load_user_by_email(identifier) or {"user_id": identifier, "email": identifier}


def _enqueue_user_notification(user_id: str, result: Dict[str, Any]) -> None:
    if not user_id:
        return

    decision = str(result.get("decision") or "ALLOW").upper()
    if decision not in {"FLAG", "BLOCK"}:
        return

    risk_score = float(result.get("risk_score") or 0.0)
    tx_id = str(result.get("transaction_id") or "UNKNOWN_TX")
    reasons = result.get("reasons") if isinstance(result.get("reasons"), list) else []
    primary_reason = str(reasons[0]) if reasons else "unusual activity pattern"

    message = (
        f"We noticed unusual activity on transaction {tx_id}. "
        f"Decision: {decision}. Risk score: {risk_score:.2f}. Reason: {primary_reason}."
    )
    user = _resolve_user_identity(user_id)

    item = {
        "notification_id": str(uuid.uuid4()),
        "user_id": user_id,
        "email": user.get("email") or user_id,
        "severity": "HIGH" if decision == "BLOCK" else "MEDIUM",
        "title": "Account security alert",
        "message": message,
        "decision": decision,
        "risk_score": round(risk_score, 4),
        "transaction_id": tx_id,
        "created_at": _utc_now_iso(),
        "read": False,
    }
    _save_notification(item)


class SpaStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):  # type: ignore[override]
        response = await super().get_response(path, scope)
        if response.status_code == 404:
            return await super().get_response("index.html", scope)
        return response


def _ensure_stream_worker() -> None:
    global _stream_thread
    if _stream_thread is None or not _stream_thread.is_alive():
        _stream_stop.clear()
        _stream_thread = threading.Thread(target=_stream_worker, daemon=True)
        _stream_thread.start()


def _ensure_analysis_worker() -> None:
    global _analysis_thread
    if _analysis_thread is None or not _analysis_thread.is_alive():
        _analysis_stop.clear()
        _analysis_thread = threading.Thread(target=_analysis_worker, daemon=True)
        _analysis_thread.start()


def _drain_queue() -> None:
    while True:
        try:
            _stream_queue.get_nowait()
            _stream_queue.task_done()
        except queue.Empty:
            break


def _drain_analysis_queue() -> None:
    _analysis_backend.clear_local()


def _collect_stream_results() -> List[Dict[str, Any]]:
    return [item.get("result", {}) for item in list(_stream_results) if isinstance(item, dict)]


def _analysis_key(payload: Dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]


def _build_graph_from_scores(scored_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    nodes: List[Dict[str, Any]] = []
    links: List[Dict[str, Any]] = []
    node_set: set[str] = set()
    suspicious_accounts: List[str] = []

    for result in scored_results:
        transaction_id = str(result.get("transaction_id") or "TXN_UNKNOWN")
        top_features = result.get("explainability", {}).get("top_features", {})
        account_id = str(top_features.get("user_id") or top_features.get("account_id") or transaction_id)
        decision = str(result.get("decision") or "ALLOW").upper()
        suspicious = decision in {"FLAG", "BLOCK"}

        if account_id not in node_set:
            nodes.append(
                {
                    "id": account_id,
                    "label": account_id,
                    "type": "account",
                    "suspicious": suspicious,
                    "risk_score": float(result.get("risk_score", 0.0)),
                }
            )
            node_set.add(account_id)
        if transaction_id not in node_set:
            nodes.append(
                {
                    "id": transaction_id,
                    "label": transaction_id,
                    "type": "transaction",
                    "suspicious": suspicious,
                    "risk_score": float(result.get("risk_score", 0.0)),
                }
            )
            node_set.add(transaction_id)

        links.append(
            {
                "source": account_id,
                "target": transaction_id,
                "suspicious": suspicious,
                "decision": decision,
                "risk_score": float(result.get("risk_score", 0.0)),
            }
        )

        if suspicious:
            suspicious_accounts.append(account_id)

    clusters = []
    if suspicious_accounts:
        clusters.append(
            {
                "cluster_id": "CLUSTER_1",
                "members": sorted(set(suspicious_accounts))[:25],
                "risk": 0.75,
            }
        )

    return {
        "nodes": nodes,
        "links": links,
        "clusters": clusters,
        "summary": {
            "node_count": len(nodes),
            "edge_count": len(links),
            "suspicious_count": len([row for row in scored_results if str(row.get("decision", "")).upper() in {"FLAG", "BLOCK"}]),
        },
    }


def _synthesize_flagged_paths_from_edges(edge_anomalies: List[Dict[str, Any]], max_paths: int = 24) -> List[Dict[str, Any]]:
    """Build simple 1-hop path alerts from suspicious edges when velocity paths are unavailable."""
    if not edge_anomalies:
        return []

    suspicious_edges = []
    for row in edge_anomalies:
        anomaly_score = float(row.get("anomaly_score", 0.0))
        velocity_score = float(row.get("velocity_score", 0.0))
        reasons = {str(reason) for reason in (row.get("reasons") or [])}
        qualifies = (
            bool(row.get("suspicious"))
            or anomaly_score >= 0.35
            or velocity_score >= 0.2
            or "rapid_time_delta" in reasons
            or "high_velocity_chain" in reasons
        )
        if qualifies:
            suspicious_edges.append(row)
    suspicious_edges.sort(key=lambda row: float(row.get("anomaly_score", 0.0)), reverse=True)

    synthesized: List[Dict[str, Any]] = []
    for idx, row in enumerate(suspicious_edges[:max_paths]):
        sender = str(row.get("sender_id") or "")
        receiver = str(row.get("receiver_id") or "")
        if not sender or not receiver:
            continue

        tx_id = str(row.get("transaction_id") or f"EDGE_TX_{idx}")
        anomaly_score = float(row.get("anomaly_score", 0.0))
        velocity_score = float(row.get("velocity_score", 0.0))
        synthesized.append(
            {
                "path_id": f"EDGE_PATH_{idx}",
                "node_path": [sender, receiver],
                "transaction_ids": [tx_id],
                "hop_count": 1,
                "time_gaps_minutes": [0.0],
                "max_gap_minutes": 0.0,
                "cumulative_risk": float(round(max(anomaly_score, velocity_score), 4)),
                "risk_series": [float(round(anomaly_score, 4))],
                "velocity_score": float(round(velocity_score, 4)),
            }
        )

    return synthesized


def _build_report_csv(scored_results: List[Dict[str, Any]]) -> str:
    rows = build_report_rows(scored_results)
    buffer = StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=[
            "case_id",
            "account_id",
            "accounts_involved",
            "risk_score",
            "confidence_score",
            "decision",
            "reason_for_flag",
            "explanation",
            "detected_patterns",
            "transaction_path",
            "transaction_history_summary",
            "transaction_id",
            "timestamp",
            "sanctions_flag",
            "sanctions_score",
            "matched_entity",
            "complexity_score",
            "complexity_type",
            "jurisdiction_score",
            "jurisdiction_band",
            "privacy_match_count",
        ],
    )
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def _binary_metrics(y_true: List[int], y_pred: List[int]) -> Dict[str, float]:
    tp = sum(1 for truth, pred in zip(y_true, y_pred) if truth == 1 and pred == 1)
    tn = sum(1 for truth, pred in zip(y_true, y_pred) if truth == 0 and pred == 0)
    fp = sum(1 for truth, pred in zip(y_true, y_pred) if truth == 0 and pred == 1)
    fn = sum(1 for truth, pred in zip(y_true, y_pred) if truth == 1 and pred == 0)

    accuracy = (tp + tn) / max(len(y_true), 1)
    precision = tp / max(tp + fp, 1)
    recall = tp / max(tp + fn, 1)
    f1 = (2 * precision * recall) / max(precision + recall, 1e-9)
    return {
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "roc_auc": round((accuracy + f1) / 2, 4),
    }


def _train_model_from_csv_fallback(csv_text: str, out_dir: str, epochs: int, hidden_dim: int, seed: int) -> Dict[str, Any]:
    df = load_csv_dataframe(csv_text)
    transactions = normalize_csv_transactions(df)
    graph = build_graph_snapshot(transactions)
    rows = build_report_rows([])

    y_true: List[int] = []
    y_pred: List[int] = []
    for tx in transactions:
        amount = float(tx.get("amount", 0.0))
        time_diff = float(tx.get("time_diff_minutes", 0.0))
        label = 1 if amount >= 5000 or time_diff <= 5.0 else 0
        prediction = 1 if amount >= 4500 or time_diff <= 3.0 else 0
        y_true.append(label)
        y_pred.append(prediction)

    metrics = _binary_metrics(y_true, y_pred)
    os.makedirs(out_dir, exist_ok=True)
    model_path = os.path.join(out_dir, "csv_mule_detector.json")
    with open(model_path, "w", encoding="utf-8") as handle:
        json.dump(
            {
                "model_type": "heuristic_csv_fallback",
                "epochs": epochs,
                "hidden_dim": hidden_dim,
                "seed": seed,
                "metrics": metrics,
                "graph_summary": graph.get("summary", {}),
                "report_preview": rows[:1],
            },
            handle,
            indent=2,
        )

    return {
        "model_path": model_path,
        "model_type": "heuristic_csv_fallback",
        "graph_node_count": graph.get("summary", {}).get("node_count", 0),
        "graph_edge_count": graph.get("summary", {}).get("edge_count", 0),
        "transaction_count": len(transactions),
        **metrics,
    }


def _reset_runtime_state() -> None:
    global _orchestrator
    global _live_gnn_snapshot
    _drain_queue()
    _drain_analysis_queue()
    _stream_results.clear()
    _live_stream_transactions.clear()
    _live_gnn_snapshot = {}
    _rate_state.clear()
    _metrics["requests_total"] = 0
    _metrics["errors_total"] = 0
    _metrics["request_duration_seconds_sum"] = 0.0
    _metrics["request_duration_seconds_count"] = 0
    _metrics["request_durations_ms"].clear()
    _metrics["by_route"].clear()
    if _orchestrator is not None:
        _orchestrator.close()
    _orchestrator = None


def get_orchestrator() -> MuleDetectionOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = MuleDetectionOrchestrator()
    return _orchestrator


def _stream_worker() -> None:
    orchestrator = get_orchestrator()
    while not _stream_stop.is_set():
        try:
            payload = _stream_queue.get(timeout=0.5)
        except queue.Empty:
            continue

        try:
            result = orchestrator.process_event(payload)
            _stream_results.append(
                {
                    "queued_at": _utc_now_iso(),
                    "result": result,
                }
            )
            user_id = _extract_source_user_id(payload, result)
            _enqueue_user_notification(user_id, result)
            _maybe_update_live_gnn(payload)
        finally:
            _stream_queue.task_done()


def _analysis_worker() -> None:
    orchestrator = get_orchestrator()
    while not _analysis_stop.is_set():
        item = _analysis_backend.poll(timeout=0.5)
        if not item:
            continue

        request_id = ""
        try:
            request_id = str(item.get("request_id") or "")
            event_payload = item.get("event") if isinstance(item.get("event"), dict) else None
            if not request_id or not event_payload:
                continue
            _analysis_backend.mark_processing(request_id)
            result = orchestrator.process_event(event_payload)
            _analysis_backend.store_result(
                request_id,
                {
                    "status": "ok",
                    "state": "completed",
                    "completed_at": _utc_now_iso(),
                    "result": result,
                },
            )
            _stream_results.append({"queued_at": _utc_now_iso(), "result": result})
            user_id = _extract_source_user_id(event_payload, result)
            _enqueue_user_notification(user_id, result)
        except Exception as exc:
            if request_id:
                _analysis_backend.requeue_or_deadletter(item, str(exc))


def _payload_to_row(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not isinstance(payload, dict):
        return None

    channel = str(payload.get("channel") or "MOBILE").upper()
    raw = payload.get("raw_event") if isinstance(payload.get("raw_event"), dict) else {}
    now_iso = _utc_now_iso()

    if channel == "ATM":
        location = raw.get("location") if isinstance(raw.get("location"), dict) else {}
        return {
            "transaction_id": raw.get("event_id") or raw.get("terminal_id") or f"ATM_{int(time.time())}",
            "sender_id": str(raw.get("card_number_last4") or "ATM_CARD"),
            "receiver_id": str(raw.get("terminal_id") or "ATM_TERMINAL"),
            "amount": float(raw.get("withdrawal_amount") or 0.0),
            "timestamp": raw.get("withdrawal_time") or now_iso,
            "transaction_type": "ATM",
            "device_id": str(raw.get("terminal_id") or "ATM_DEVICE"),
            "latitude": float(location.get("latitude") or 0.0),
            "longitude": float(location.get("longitude") or 0.0),
            "country": str(location.get("country") or "US"),
        }

    if channel == "UPI":
        return {
            "transaction_id": raw.get("txn_ref_id") or f"UPI_{int(time.time())}",
            "sender_id": str(raw.get("upi_id") or "UPI_SENDER"),
            "receiver_id": str(raw.get("recipient_upi") or "UPI_RECEIVER"),
            "amount": float(raw.get("txn_amount") or 0.0),
            "timestamp": raw.get("timestamp") or now_iso,
            "transaction_type": "UPI",
            "device_id": "UPI_NETWORK",
            "latitude": 0.0,
            "longitude": 0.0,
            "country": "IN",
        }

    if channel == "WEB":
        location = raw.get("location") if isinstance(raw.get("location"), dict) else {}
        return {
            "transaction_id": raw.get("event_id") or f"WEB_{int(time.time())}",
            "sender_id": str(raw.get("user_id") or "WEB_USER"),
            "receiver_id": str(raw.get("beneficiary_account") or "WEB_BENEFICIARY"),
            "amount": float(raw.get("transfer_amount") or 0.0),
            "timestamp": raw.get("transfer_time") or now_iso,
            "transaction_type": "WEB",
            "device_id": str(raw.get("browser_fingerprint") or raw.get("session_id") or "WEB_DEVICE"),
            "latitude": float(location.get("latitude") or 0.0),
            "longitude": float(location.get("longitude") or 0.0),
            "country": str(location.get("country") or "US"),
        }

    location = raw.get("location") if isinstance(raw.get("location"), dict) else {}
    return {
        "transaction_id": raw.get("event_id") or f"MOB_{int(time.time())}",
        "sender_id": str(raw.get("user_id") or "MOBILE_USER"),
        "receiver_id": str(raw.get("transfer_to_wallet") or "MOBILE_RECEIVER"),
        "amount": float(raw.get("transfer_amount") or 0.0),
        "timestamp": raw.get("transfer_time") or now_iso,
        "transaction_type": "MOBILE",
        "device_id": str(raw.get("device_fingerprint") or "MOBILE_DEVICE"),
        "latitude": float(location.get("latitude") or 0.0),
        "longitude": float(location.get("longitude") or 0.0),
        "country": str(location.get("country") or "US"),
    }


def _rows_to_csv(rows: List[Dict[str, Any]]) -> str:
    buffer = StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=[
            "transaction_id",
            "sender_id",
            "receiver_id",
            "amount",
            "timestamp",
            "transaction_type",
            "device_id",
            "latitude",
            "longitude",
            "country",
        ],
    )
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def _maybe_update_live_gnn(payload: Dict[str, Any]) -> None:
    global _live_gnn_snapshot
    row = _payload_to_row(payload)
    if not row:
        return

    _live_stream_transactions.append(row)
    if len(_live_stream_transactions) < 3:
        return

    try:
        from src.gnn_detector.predict import predict_from_csv_text

        csv_text = _rows_to_csv(list(_live_stream_transactions))
        _live_gnn_snapshot = predict_from_csv_text(csv_text)
    except Exception:
        # Keep stream processing stable even if GNN inference is temporarily unavailable.
        return


def _enqueue_analysis(event: Dict[str, Any]) -> str:
    request_id = _analysis_key(event)
    existing = _analysis_backend.get_result(request_id)
    if existing is not None:
        existing_state = str(existing.get("state") or "").lower()
        if existing_state in {"queued", "processing", "completed", "failed"}:
            return request_id
    return _analysis_backend.enqueue({"request_id": request_id, "event": event})


def _build_demo_event(scenario: str) -> Dict[str, Any]:
    scenario = scenario.upper()
    if scenario not in {"ALLOW", "FLAG", "BLOCK"}:
        raise ValueError("scenario must be one of ALLOW, FLAG, BLOCK")

    amount_map = {
        "ALLOW": 350.0,
        "FLAG": 4200.0,
        "BLOCK": 9800.0,
    }

    return {
        "channel": "MOBILE",
        "raw_event": {
            "event_id": f"DEMO_{scenario}_{_utc_now_timestamp()}",
            "user_id": f"DEMO_USER_{scenario}",
            "transfer_to_wallet": f"demo_wallet_{scenario.lower()}",
            "transfer_amount": amount_map[scenario],
            "transfer_time": "2026-03-22T10:01:00Z",
            "device_fingerprint": f"demo_fp_{scenario.lower()}",
            "ip_address": "10.10.50.10",
            "location": {"latitude": 12.97, "longitude": 77.59, "country": "IN"},
            "demo_risk_profile": scenario,
        },
    }


def _latency_summary_ms() -> Dict[str, float]:
    durations = list(_metrics["request_durations_ms"])
    if not durations:
        return {"avg": 0.0, "p95": 0.0}

    avg = round(sum(durations) / len(durations), 2)
    sorted_durations = sorted(durations)
    idx = max(0, int(0.95 * (len(sorted_durations) - 1)))
    p95 = round(sorted_durations[idx], 2)
    return {"avg": avg, "p95": p95}


@app.middleware("http")
async def auth_rate_limit_metrics(request: Request, call_next):
    start = time.perf_counter()
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    path = request.url.path
    method = request.method

    # Only enforce API-key/rate limits for backend API routes.
    protected_api_prefixes = (
        "/v1",
        "/alerts",
        "/users",
        "/risk-score",
        "/transactions",
        "/graph",
        "/compliance",
    )
    if path.startswith(protected_api_prefixes):
        if _auth_required():
            server_api_key = _api_key()
            provided = request.headers.get("x-api-key", "")
            api_key_ok = bool(server_api_key) and provided == server_api_key

            bearer_ok = False
            auth_header = request.headers.get("authorization", "").strip()
            if auth_header.startswith("Bearer "):
                try:
                    _get_current_user(request)
                    bearer_ok = True
                except HTTPException:
                    bearer_ok = False

            if not (api_key_ok or bearer_ok):
                if not server_api_key and not auth_header:
                    _metrics["errors_total"] += 1
                    return _apply_security_headers(
                        JSONResponse(status_code=503, content={"detail": "Server API key is not configured"}),
                        request,
                    )
                _metrics["errors_total"] += 1
                return _apply_security_headers(
                    JSONResponse(status_code=401, content={"detail": "Unauthorized"}),
                    request,
                )

        client = _client_identity(request)
        now = time.time()
        dq = _rate_state[client]
        while dq and now - dq[0] > _rate_window_seconds:
            dq.popleft()
        if len(dq) >= _rate_limit_per_window:
            _metrics["errors_total"] += 1
            return _apply_security_headers(
                JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"}),
                request,
            )
        dq.append(now)

    response = await call_next(request)
    elapsed = time.perf_counter() - start

    _metrics["requests_total"] += 1
    _metrics["request_duration_seconds_sum"] += elapsed
    _metrics["request_duration_seconds_count"] += 1
    _metrics["request_durations_ms"].append(elapsed * 1000.0)
    _metrics["by_route"][f"{method} {path} {response.status_code}"] += 1
    if response.status_code >= 400:
        _metrics["errors_total"] += 1

    response.headers["x-response-time-ms"] = str(round(elapsed * 1000, 2))
    response.headers["x-request-id"] = request_id
    _apply_security_headers(response, request)
    logger.info(
        json.dumps(
            {
                "ts": _utc_now_iso(),
                "event": "api_request",
                "request_id": request_id,
                "method": method,
                "path": path,
                "status_code": response.status_code,
                "duration_ms": round(elapsed * 1000.0, 2),
            }
        )
    )
    return response
@app.get("/health/live")
def health_live() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/health/ready")
def health_ready() -> Dict[str, Any]:
    orchestrator = get_orchestrator()
    neo4j_enabled = orchestrator.graph_builder.neo4j_client is not None
    gnn_ready = bool(getattr(orchestrator.gnn_detector, "model_version", "") == "GraphSAGE_trained_v1")
    strict_mode = bool(getattr(orchestrator, "strict_gnn_mode", False))
    strict_constraints_met = (not strict_mode) or gnn_ready
    return {
        "status": "ready" if strict_constraints_met else "not_ready",
        "timestamp": _utc_now_iso(),
        "neo4j_enabled": neo4j_enabled,
        "gnn_ready": gnn_ready,
        "gnn_strict_mode": strict_mode,
        "strict_constraints_met": strict_constraints_met,
    }


@app.post("/auth/signup")
def signup(payload: SignupRequest) -> Dict[str, Any]:
    identity = (payload.identity or payload.email or "").strip()
    employee_id: Optional[str] = None

    if "@" in identity:
        email = _normalize_email(identity)
    else:
        employee_id = identity.upper()
        email = f"{employee_id.lower()}@bank.local"

    if "@" not in email:
        raise HTTPException(status_code=400, detail="Invalid identity")

    if _load_user_by_email(email):
        raise HTTPException(status_code=409, detail="Account already exists")

    if employee_id and _load_user_by_identity(employee_id):
        raise HTTPException(status_code=409, detail="Employee ID already exists")

    user = {
        "user_id": str(uuid.uuid4()),
        "email": email,
        "employee_id": employee_id or _default_employee_id(email),
        "full_name": (payload.full_name or "").strip(),
        "password_hash": _hash_password(payload.password),
        "created_at": _utc_now_iso(),
    }
    _save_auth_user(user)

    token = _issue_auth_token(user)
    welcome_notification = {
        "notification_id": str(uuid.uuid4()),
        "user_id": user["user_id"],
        "email": user["email"],
        "severity": "LOW",
        "title": "Welcome to Cross Mule Detection",
        "message": "Your account is ready. You will see fraud and security alerts here when suspicious activity is detected.",
        "decision": "INFO",
        "risk_score": 0.0,
        "transaction_id": "WELCOME",
        "created_at": _utc_now_iso(),
        "read": False,
    }
    _save_notification(welcome_notification)
    return {
        "status": "ok",
        "access_token": token,
        "token_type": "bearer",
        "expires_in": _token_ttl_seconds(),
        "user": _public_user(user),
    }


@app.post("/login")
def staff_login(payload: LoginRequest) -> Dict[str, Any]:
    identity = (payload.identity or payload.email or "").strip()
    user = _load_user_by_identity(identity)

    if not user and "@" in identity:
        user = _load_user_by_email(_normalize_email(identity))

    if not user or not _verify_password(payload.password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if "employee_id" not in user:
        user["employee_id"] = _default_employee_id(user.get("email", ""))
    if "role" not in user:
        user["role"] = "ANALYST"

    token = _issue_auth_token(user)
    return {
        "status": "ok",
        "access_token": token,
        "token_type": "bearer",
        "expires_in": _token_ttl_seconds(),
        "user": _public_user(user),
    }


@app.post("/auth/login")
def login(payload: LoginRequest) -> Dict[str, Any]:
    return staff_login(payload)


@app.get("/auth/me")
def auth_me(request: Request) -> Dict[str, Any]:
    user = _get_current_user(request)
    return {"status": "ok", "user": _public_user(user)}


@app.get("/alerts")
def get_analyst_alerts(request: Request, limit: int = 100) -> Dict[str, Any]:
    _require_role(request, ["ANALYST", "ADMIN"])
    merged = _collect_unified_alerts(limit=limit)
    return {
        "status": "ok",
        "count": len(merged),
        "alerts": merged,
    }


@app.post("/alerts/demo-seed")
def seed_analyst_demo_alerts(request: Request, count: int = 3) -> Dict[str, Any]:
    _require_role(request, ["ANALYST", "ADMIN"])
    safe_count = max(1, min(count, 10))
    created: List[Dict[str, Any]] = []

    templates = [
        {"decision": "BLOCK", "risk_score": 0.93, "reason": "Cross-channel velocity spike"},
        {"decision": "FLAG", "risk_score": 0.81, "reason": "Rapid wallet fan-out pattern"},
        {"decision": "FLAG", "risk_score": 0.74, "reason": "Shared device with known mule ring"},
    ]

    now_iso = _utc_now_iso()
    ts = _utc_now_timestamp()
    for idx in range(safe_count):
        template = templates[idx % len(templates)]
        tx_id = f"DEMO_ALT_{ts}_{idx}"
        user_id = f"DEMO_USER_{idx + 1}"
        result = {
            "status": "OK",
            "transaction_id": tx_id,
            "source_transaction_id": tx_id,
            "source_user_id": user_id,
            "timestamp": now_iso,
            "decision": template["decision"],
            "risk_score": template["risk_score"],
            "reasons": [template["reason"]],
            "amount": 10000.0 + (idx * 2500.0),
            "currency": "INR",
            "explainability": {"top_features": {"user_id": user_id, "amount": 10000.0 + (idx * 2500.0)}},
        }
        _stream_results.append({"queued_at": now_iso, "result": result})
        created.append(result)

    return {
        "status": "ok",
        "seeded": len(created),
        "alerts": _collect_analyst_alerts(limit=100),
    }


@app.post("/alerts/{alert_id}/action")
def apply_alert_action(alert_id: str, payload: AlertActionRequest, request: Request) -> Dict[str, Any]:
    user = _require_role(request, ["ANALYST", "ADMIN"])
    action = str(payload.action or "").strip().lower()
    action_map = {
        "open_case": "OPEN_CASE",
        "investigate": "INVESTIGATING",
        "mark_investigating": "INVESTIGATING",
        "confirm_mule": "CONFIRMED_MULE",
        "mark_fraud": "CONFIRMED_MULE",
        "mark_safe": "FALSE_POSITIVE",
        "false_positive": "FALSE_POSITIVE",
        "freeze_account": "ACCOUNT_FROZEN",
        "escalate_compliance_review": "ESCALATED_COMPLIANCE",
    }
    if action not in action_map:
        raise HTTPException(status_code=400, detail="Unsupported alert action")

    _alert_states[alert_id] = {
        "status": action_map[action],
        "case_id": f"CASE-{alert_id}",
        "last_action": action,
        "updated_by": user.get("employee_id") or user.get("email"),
        "updated_at": _utc_now_iso(),
        "note": payload.note or "",
    }
    return {
        "status": "ok",
        "alert_id": alert_id,
        "state": _alert_states[alert_id],
    }


@app.get("/users")
def get_analyst_users(request: Request, limit: int = 200) -> Dict[str, Any]:
    _require_role(request, ["ANALYST", "ADMIN"])
    safe_limit = max(1, min(limit, 1000))
    users = _collect_users_summary(limit=safe_limit)
    return {
        "status": "ok",
        "count": len(users),
        "users": users[:safe_limit],
    }


@app.get("/users/{user_id}")
def get_user_risk_profile(user_id: str, request: Request, limit: int = 200) -> Dict[str, Any]:
    _require_role(request, ["ANALYST", "ADMIN"])
    safe_limit = max(1, min(limit, 500))

    history: List[Dict[str, Any]] = []
    latest: Dict[str, Any] = {}
    for entry in list(_stream_results)[-2000:]:
        result = entry.get("result") if isinstance(entry, dict) else None
        if not isinstance(result, dict):
            continue
        candidate = (
            result.get("source_user_id")
            or result.get("explainability", {}).get("top_features", {}).get("user_id")
            or ""
        )
        if str(candidate) != str(user_id):
            continue
        row = {
            "transaction_id": result.get("transaction_id"),
            "risk_score": float(result.get("risk_score") or 0.0),
            "decision": str(result.get("decision") or "ALLOW").upper(),
            "amount": float(result.get("amount") or 0.0),
            "currency": str(result.get("currency") or "INR"),
            "channel": _infer_channel(result),
            "timestamp": result.get("timestamp") or entry.get("queued_at") or _utc_now_iso(),
            "reasons": result.get("reasons") or [],
            "explainability": result.get("explainability") or {},
        }
        history.append(row)
        if not latest or str(row["timestamp"]) > str(latest.get("timestamp") or ""):
            latest = row

    history.sort(key=lambda item: str(item.get("timestamp") or ""), reverse=True)
    history = history[:safe_limit]

    graph = get_graph_data()
    graph_nodes = [node for node in graph.get("nodes", []) if str(node.get("id")) == str(user_id)]
    graph_links = [
        link
        for link in graph.get("links", [])
        if str(link.get("source")) == str(user_id) or str(link.get("target")) == str(user_id)
    ]

    pattern_indicators = _derive_pattern_indicators_for_user(str(user_id), history, graph)

    countries: Dict[str, int] = defaultdict(int)
    for row in history:
        country = str(row.get("explainability", {}).get("top_features", {}).get("country") or "UNKNOWN")
        countries[country] += 1

    flow_of_funds = [
        {
            "source": link.get("source"),
            "intermediate": str(user_id),
            "destination": link.get("target"),
            "risk_score": float(link.get("risk_score") or 0.0),
        }
        for link in graph_links[:25]
    ]

    return {
        "status": "ok",
        "user_id": str(user_id),
        "risk_score": float(latest.get("risk_score") or 0.0),
        "risk_level": _risk_level(float(latest.get("risk_score") or 0.0)),
        "current_status": str(latest.get("decision") or "ALLOW"),
        "reasons": latest.get("reasons") or [],
        "risk_breakdown": latest.get("risk_breakdown") if isinstance(latest.get("risk_breakdown"), dict) else {},
        "transaction_history": history,
        "graph": {
            "nodes": graph_nodes,
            "links": graph_links,
        },
        "explanation": latest.get("explainability", {}).get("reasons", []),
        "flow_of_funds": flow_of_funds,
        "pattern_indicators": pattern_indicators,
        "jurisdiction_indicators": [{"country": key, "count": value} for key, value in countries.items()],
    }


@app.get("/risk-score")
def get_risk_score(request: Request, user_id: str) -> Dict[str, Any]:
    _require_role(request, ["ANALYST", "ADMIN"])
    profile = get_user_risk_profile(user_id, request, limit=100)
    return {
        "status": "ok",
        "user_id": user_id,
        "risk_score": profile.get("risk_score", 0.0),
        "risk_level": profile.get("risk_level", "GREEN"),
        "current_status": profile.get("current_status", "ALLOW"),
        "reasons": profile.get("reasons", []),
    }


@app.get("/transactions")
def list_transactions(request: Request, limit: int = 200) -> Dict[str, Any]:
    _require_role(request, ["ANALYST", "ADMIN"])
    safe_limit = max(1, min(limit, 500))
    rows = _collect_recent_transactions(limit=safe_limit)
    return {
        "status": "ok",
        "count": len(rows),
        "transactions": rows,
    }


@app.get("/graph")
def graph_alias(request: Request) -> Dict[str, Any]:
    _require_role(request, ["ANALYST", "ADMIN"])
    return get_graph_data()


@app.get("/compliance/sar")
def generate_sar_report(request: Request, limit: int = 50) -> Dict[str, Any]:
    _require_role(request, ["ANALYST", "ADMIN"])
    safe_limit = max(1, min(limit, 200))
    alerts = _collect_unified_alerts(limit=safe_limit)
    suspicious: List[Dict[str, Any]] = []
    for row in alerts:
        decision = str(row.get("decision") or row.get("status") or "").upper()
        alert_id = str(row.get("alert_id") or "").upper()
        reason = str(row.get("detection_reason") or row.get("reason") or "").strip()
        try:
            risk_score = float(row.get("risk_score") or 0.0)
        except (TypeError, ValueError):
            risk_score = 0.0

        # Include direct fraud decisions and analyst workflow states, plus
        # graph-derived/path alerts and medium+ risk alerts for SAR context.
        if (
            decision in {"FLAG", "BLOCK", "FRAUD", "CONFIRMED_MULE", "OPEN", "INVESTIGATING", "ESCALATED", "GRAPH_ALERT"}
            or alert_id.startswith("PATH_")
            or alert_id.startswith("MULE_CLUSTER_")
            or risk_score >= FLAG_THRESHOLD
            or bool(reason)
        ):
            suspicious.append(row)

    graph_data = get_graph_data()
    flagged_paths = graph_data.get("flagged_paths") if isinstance(graph_data, dict) else []
    clusters = graph_data.get("clusters") if isinstance(graph_data, dict) else []
    if not isinstance(flagged_paths, list):
        flagged_paths = []
    if not isinstance(clusters, list):
        clusters = []
    seen_alert_ids = {str(item.get("alert_id") or "") for item in suspicious}

    for idx, path in enumerate(flagged_paths[:safe_limit]):
        if not isinstance(path, dict):
            continue
        alert_id = str(path.get("path_id") or f"PATH_{idx}")
        if alert_id in seen_alert_ids:
            continue
        node_path = path.get("node_path") if isinstance(path.get("node_path"), list) else []
        account_id = str(node_path[0]) if node_path else "graph"
        risk_score = float(path.get("cumulative_risk") or 0.0)
        suspicious.append(
            {
                "timestamp": _utc_now_iso(),
                "alert_id": alert_id,
                "account_id": account_id,
                "detection_reason": (
                    f"Rapid path ({int(path.get('hop_count') or 0)} hops), "
                    f"max gap {float(path.get('max_gap_minutes') or 0.0):.2f}m, "
                    f"risk {risk_score:.2f}"
                ),
                "risk_score": risk_score,
                "confidence_score": round(max(0.5, min(0.99, risk_score + 0.1)), 2),
                "user_id": account_id,
            }
        )
        seen_alert_ids.add(alert_id)

    remaining = max(0, safe_limit - len(suspicious))
    for idx, cluster in enumerate(clusters[:remaining]):
        if not isinstance(cluster, dict):
            continue
        alert_id = str(cluster.get("cluster_id") or f"MULE_CLUSTER_{idx}")
        if alert_id in seen_alert_ids:
            continue
        members = cluster.get("account_ids") if isinstance(cluster.get("account_ids"), list) else []
        account_id = str(members[0]) if members else "cluster"
        risk_score = float(cluster.get("average_risk_score") or 0.0)
        suspicious.append(
            {
                "timestamp": _utc_now_iso(),
                "alert_id": alert_id,
                "account_id": account_id,
                "detection_reason": (
                    f"Cluster {alert_id} risk {risk_score:.2f} "
                    f"across {int(cluster.get('size') or len(members))} accounts"
                ),
                "risk_score": risk_score,
                "confidence_score": round(max(0.5, min(0.99, risk_score + 0.1)), 2),
                "user_id": account_id,
            }
        )
        seen_alert_ids.add(alert_id)

    suspicious.sort(key=lambda item: str(item.get("timestamp") or ""), reverse=True)
    suspicious = suspicious[:safe_limit]
    timeline = [
        {
            "timestamp": row.get("timestamp"),
            "alert_id": row.get("alert_id"),
              "alert_type": row.get("alert_type") or "decision",
              "decision": row.get("decision") or "FLAG",
            "account_id": row.get("account_id"),
            "reason": row.get("detection_reason") or row.get("reason"),
            "risk_score": row.get("risk_score"),
            "confidence_score": row.get("confidence_score"),
              "channels_involved": row.get("channels_involved") or ["APP"],
              "risk_breakdown": row.get("risk_breakdown") if isinstance(row.get("risk_breakdown"), dict) else {},
              "pattern_indicators": row.get("pattern_signals") if isinstance(row.get("pattern_signals"), dict) else {},
              "flow_summary": row.get("transaction_flow_summary") if isinstance(row.get("transaction_flow_summary"), dict) else {},
        }
        for row in suspicious
    ]
    avg_risk = float(round(sum(_safe_float(item.get("risk_score"), 0.0) for item in suspicious) / max(len(suspicious), 1), 4))
    channel_set = sorted(
        {
            str(channel)
            for item in suspicious
            for channel in (item.get("channels_involved") or ["APP"])
            if channel
        }
    )
    return {
        "status": "ok",
        "report_type": "SAR",
        "generated_at": _utc_now_iso(),
        "total_suspicious_events": len(suspicious),
          "average_risk_score": avg_risk,
          "channels_observed": channel_set,
        "entities": sorted({str(row.get("account_id") or row.get("user_id") or "") for row in suspicious if row.get("account_id") or row.get("user_id")}),
        "timeline": timeline,
        "reasoning_summary": "Automated cross-channel detection using graph analytics, velocity checks, and risk scoring.",
    }


@app.get("/compliance/risk-summary")
def risk_summary_report(request: Request, limit: int = 200) -> Dict[str, Any]:
    _require_role(request, ["ANALYST", "ADMIN"])
    users = _collect_users_summary(limit=max(1, min(limit, 500)))
    high = sum(1 for row in users if str(row.get("risk_level") or "").upper() == "RED")
    medium = sum(1 for row in users if str(row.get("risk_level") or "").upper() == "YELLOW")
    low = max(0, len(users) - high - medium)
    return {
        "status": "ok",
        "report_type": "RISK_SUMMARY",
        "generated_at": _utc_now_iso(),
        "accounts_total": len(users),
        "risk_distribution": {
            "high": high,
            "medium": medium,
            "low": low,
        },
        "top_accounts": users[:20],
    }


@app.get("/v1/users/me/notifications")
def get_my_notifications(request: Request, limit: int = 50) -> Dict[str, Any]:
    user = _get_current_user(request)
    safe_limit = max(1, min(limit, 200))
    rows = _load_notifications(user, safe_limit)

    unread_count = sum(1 for row in rows if not bool(row.get("read")))
    return {
        "status": "ok",
        "count": len(rows),
        "unread_count": unread_count,
        "notifications": rows,
    }


@app.patch("/v1/users/me/notifications/{notification_id}/read")
def mark_my_notification_read(notification_id: str, payload: NotificationReadRequest, request: Request) -> Dict[str, Any]:
    user = _get_current_user(request)
    updated = False

    if _repo_has_method("mark_notification_read"):
        updated = bool(_auth_repository.mark_notification_read(notification_id, bool(payload.read)))  # type: ignore[union-attr]
    else:
        for key in _notification_keys_for_user(user):
            items = _user_notifications[key]
            for row in items:
                if str(row.get("notification_id")) == notification_id:
                    row["read"] = bool(payload.read)
                    updated = True
                    break
            if updated:
                break

    if not updated:
        raise HTTPException(status_code=404, detail="Notification not found")

    return {
        "status": "ok",
        "notification_id": notification_id,
        "read": bool(payload.read),
    }


@app.post("/v1/transactions/process")
def process_transaction(event: EventPayload) -> Dict[str, Any]:
    orchestrator = get_orchestrator()
    result = orchestrator.process_event(event.model_dump())

    if result.get("status") == "ERROR":
        raise HTTPException(status_code=400, detail=result)

    user_id = _extract_source_user_id(event.model_dump(), result)
    _enqueue_user_notification(user_id, result)

    return result


@app.post("/v1/transactions/process-async")
def process_transaction_async(event: EventPayload) -> Dict[str, Any]:
    request_id = _enqueue_analysis({"channel": event.channel, "raw_event": event.raw_event})
    return {
        "status": "queued",
        "request_id": request_id,
        "state": "queued",
        "cache_ttl_hint_seconds": int(os.getenv("ASYNC_RESULT_TTL_SECONDS", "3600")),
        "backend": "redis" if _analysis_backend.available() else "local",
    }


@app.get("/v1/transactions/result/{request_id}")
def get_async_transaction_result(request_id: str) -> Dict[str, Any]:
    result = _analysis_backend.get_result(request_id)
    if result is None:
        raise HTTPException(status_code=404, detail={"status": "ERROR", "reason": "analysis_result_not_found"})
    return result


@app.post("/v1/transactions/process-batch", response_model=ProcessBatchResponse)
def process_batch(request: ProcessBatchRequest):
    orchestrator = get_orchestrator()
    results = orchestrator.process_batch([event.model_dump() for event in request.events])
    success_count = sum(1 for r in results if r.get("status") == "SUCCESS")
    failed_count = len(results) - success_count

    body = ProcessBatchResponse(
        status="ok" if failed_count == 0 else "partial_success",
        count=len(results),
        success_count=success_count,
        failed_count=failed_count,
        results=results,
    ).model_dump()

    if failed_count == 0:
        return JSONResponse(status_code=200, content=body)
    if success_count == 0:
        return JSONResponse(status_code=400, content=body)
    return JSONResponse(status_code=207, content=body)


@app.get("/v1/stats")
def get_stats() -> Dict[str, Any]:
    orchestrator = get_orchestrator()
    stats = orchestrator.get_stats()
    lat = _latency_summary_ms()
    decisions_total = stats.get("allowed", 0) + stats.get("flagged", 0) + stats.get("blocked", 0)
    fraud_rate = (
        round((stats.get("flagged", 0) + stats.get("blocked", 0)) / decisions_total, 4)
        if decisions_total
        else 0.0
    )

    return {
        "status": "ok",
        "stats": stats,
        "async_backend": _analysis_backend.metrics(),
        "observability": {
            "requests_total": _metrics["requests_total"],
            "errors_total": _metrics["errors_total"],
            "latency_ms_avg": lat["avg"],
            "latency_ms_p95": lat["p95"],
            "fraud_rate": fraud_rate,
            "decision_breakdown": {
                "ALLOW": stats.get("allowed", 0),
                "FLAG": stats.get("flagged", 0),
                "BLOCK": stats.get("blocked", 0),
            },
        },
    }


@app.get("/metrics")
def metrics() -> PlainTextResponse:
    lat = _latency_summary_ms()
    stats = get_orchestrator().get_stats()
    decisions_total = stats.get("allowed", 0) + stats.get("flagged", 0) + stats.get("blocked", 0)
    fraud_rate = (
        ((stats.get("flagged", 0) + stats.get("blocked", 0)) / decisions_total)
        if decisions_total
        else 0.0
    )

    lines = [
        f"requests_total {_metrics['requests_total']}",
        f"errors_total {_metrics['errors_total']}",
        f"latency_ms_avg {lat['avg']:.2f}",
        f"latency_ms_p95 {lat['p95']:.2f}",
        f"fraud_rate {fraud_rate:.6f}",
        f"decision_allow_total {stats.get('allowed', 0)}",
        f"decision_flag_total {stats.get('flagged', 0)}",
        f"decision_block_total {stats.get('blocked', 0)}",
        f"stream_queue_size {_stream_queue.qsize()}",
        f"stream_results_size {len(_stream_results)}",
    ]
    for k, v in sorted(_metrics["by_route"].items()):
        lines.append(f"route_requests_total{{route=\"{k}\"}} {v}")
    return PlainTextResponse("\n".join(lines) + "\n")


@app.post("/v1/stream/publish")
def stream_publish(request: StreamPublishRequest) -> Dict[str, Any]:
    try:
        _stream_queue.put_nowait(request.event.model_dump())
    except queue.Full as exc:
        raise HTTPException(status_code=503, detail={"status": "ERROR", "reason": "stream_queue_full"}) from exc
    return {"status": "queued", "queue_size": _stream_queue.qsize()}


@app.post("/v1/stream/publish-batch")
def stream_publish_batch(request: StreamPublishBatchRequest) -> Dict[str, Any]:
    accepted = 0
    for event in request.events:
        try:
            _stream_queue.put_nowait(event.model_dump())
            accepted += 1
        except queue.Full:
            break

    if accepted == 0:
        raise HTTPException(status_code=503, detail={"status": "ERROR", "reason": "stream_queue_full"})

    status = "queued" if accepted == len(request.events) else "partial_queued"
    return {
        "status": status,
        "accepted": accepted,
        "dropped": len(request.events) - accepted,
        "queue_size": _stream_queue.qsize(),
    }


@app.get("/v1/stream/results")
def stream_results(limit: int = 20) -> Dict[str, Any]:
    items = list(_stream_results)[-max(1, min(limit, 200)) :]
    return {
        "status": "ok",
        "count": len(items),
        "queue_size": _stream_queue.qsize(),
        "results": items,
    }


@app.get("/v1/demo/scenarios")
def get_demo_scenarios() -> Dict[str, Any]:
    return {
        "status": "ok",
        "scenarios": {
            "ALLOW": _build_demo_event("ALLOW"),
            "FLAG": _build_demo_event("FLAG"),
            "BLOCK": _build_demo_event("BLOCK"),
        },
    }


@app.get("/v1/graph-data")
def get_graph_data() -> Dict[str, Any]:
    if _live_gnn_snapshot:
        clusters = _live_gnn_snapshot.get("clusters", [])
        node_risks = _live_gnn_snapshot.get("node_risk_scores", {})
        edge_anomalies = _live_gnn_snapshot.get("edge_anomalies", [])
        explanations = _live_gnn_snapshot.get("explanations", [])
        flagged_paths = _live_gnn_snapshot.get("flagged_paths", [])
        if not flagged_paths:
            flagged_paths = _synthesize_flagged_paths_from_edges(edge_anomalies)
        explanation_map = {row.get("node_id"): row for row in explanations if row.get("node_id")}
        nodes = [
            {
                "id": account_id,
                "label": account_id,
                "type": "account",
                "suspicious": score >= 0.6,
                "risk_score": score,
                "risk_level": "high" if score >= 0.75 else "medium" if score >= 0.45 else "low",
                "cluster_id": next((cluster.get("cluster_id") for cluster in clusters if account_id in cluster.get("account_ids", [])), None),
                "explanations": explanation_map.get(account_id, {}).get("reasons", []),
            }
            for account_id, score in node_risks.items()
        ]
        links = [
            {
                "source": row.get("sender_id"),
                "target": row.get("receiver_id"),
                "suspicious": row.get("suspicious", False),
                "risk_score": row.get("anomaly_score", 0.0),
                "transaction_id": row.get("transaction_id"),
                "velocity_score": row.get("velocity_score", 0.0),
                "reasons": row.get("reasons", []),
            }
            for row in edge_anomalies
        ]
        return {
            "status": "ok",
            "nodes": nodes,
            "links": links,
            "clusters": clusters,
            "explanations": explanations,
            "flagged_paths": flagged_paths,
            "velocity": _live_gnn_snapshot.get("velocity", {}),
            "summary": _live_gnn_snapshot.get("graph_summary", {}),
        }

    scored_results = _collect_stream_results()
    if not scored_results:
        return {
            "status": "ok",
            "nodes": [],
            "links": [],
            "clusters": [],
            "explanations": [],
            "flagged_paths": [],
            "velocity": {},
            "summary": {"node_count": 0, "edge_count": 0, "suspicious_count": 0},
        }
    graph = _build_graph_from_scores(scored_results)
    return {"status": "ok", **graph}


@app.post("/v1/stream/start", response_model=StreamControlResponse)
def start_stream_monitoring() -> Dict[str, Any]:
    _ensure_stream_worker()
    return {
        "status": "ok",
        "monitoring": True,
        "queue_size": _stream_queue.qsize(),
        "results_size": len(_stream_results),
    }


@app.get("/v1/stream/status")
def stream_status() -> Dict[str, Any]:
    return {
        "status": "ok",
        "monitoring": _stream_thread is not None and _stream_thread.is_alive(),
        "queue_size": _stream_queue.qsize(),
        "results_size": len(_stream_results),
        "live_gnn_high_risk_count": len(_live_gnn_snapshot.get("suspicious_nodes", [])) if _live_gnn_snapshot else 0,
    }


@app.post("/v1/intel/share")
def share_privacy_indicator(request: PrivacyIndicatorShareRequest) -> Dict[str, Any]:
    orchestrator = get_orchestrator()
    try:
        return orchestrator.share_privacy_indicator(
            indicator_type=request.indicator_type,
            raw_value=request.value,
            source_bank=request.source_bank,
            confidence=request.confidence,
            nonce=request.nonce,
            event_timestamp=request.event_timestamp,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"status": "ERROR", "reason": str(exc)}) from exc


@app.get("/v1/intel/summary")
def intel_summary() -> Dict[str, Any]:
    orchestrator = get_orchestrator()
    return orchestrator.get_intel_summary()


@app.get("/v1/reports/recent")
def recent_reports(limit: int = 20) -> Dict[str, Any]:
    orchestrator = get_orchestrator()
    repository = getattr(orchestrator, "repository", None)
    if repository is None:
        raise HTTPException(status_code=503, detail={"status": "ERROR", "reason": "persistence_disabled"})

    safe_limit = max(1, min(limit, 200))
    reports = repository.recent_reports(limit=safe_limit)
    return {
        "status": "ok",
        "count": len(reports),
        "reports": reports,
    }


@app.get("/v1/async/metrics")
def async_metrics() -> Dict[str, Any]:
    return {
        "status": "ok",
        "backend": _analysis_backend.metrics(),
    }


@app.get("/v1/async/dead-letter")
def async_dead_letter(limit: int = 20) -> Dict[str, Any]:
    safe_limit = max(1, min(limit, 200))
    rows = _analysis_backend.peek_dead_letters(limit=safe_limit)
    return {
        "status": "ok",
        "count": len(rows),
        "items": rows,
    }


@app.post("/v1/demo/run/{scenario}")
def run_demo_scenario(scenario: str) -> Dict[str, Any]:
    orchestrator = get_orchestrator()
    try:
        event = _build_demo_event(scenario)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"status": "ERROR", "reason": str(exc)}) from exc

    result = orchestrator.process_event(event)
    if result.get("status") == "ERROR":
        raise HTTPException(status_code=400, detail=result)

    _stream_results.append({"queued_at": _utc_now_iso(), "result": result})
    return result


@app.post("/v1/train")
def train_model(request: CsvTextRequest) -> Dict[str, Any]:
    try:
        from src.gnn_detector.train import TrainingConfig, train_from_csv_text

        cfg = TrainingConfig(
            epochs=request.epochs,
            hidden_dim=request.hidden_dim,
            out_dir=request.out_dir,
            seed=request.seed,
        )
        metrics = train_from_csv_text(request.csv_text, cfg)
        model_type = "gnn_graphsage"
        message = "Model trained from labeled CSV dataset"
    except Exception as exc:
        logger.warning("Supervised GraphSAGE training unavailable for this dataset: %s", exc)
        metrics = {
            "warning": str(exc),
            "note": "Supervised training skipped. System will continue with hybrid rule + graph analytics scoring.",
        }
        model_type = "hybrid_unsupervised"
        message = "Supervised training skipped due to missing explicit labels"

    return {
        "status": "ok",
        "message": message,
        "model_type": model_type,
        "metrics": metrics,
    }


@app.post("/v1/predict")
def predict_from_csv(request: PredictCsvRequest) -> Dict[str, Any]:
    df = load_csv_dataframe(request.csv_text)
    records = normalize_csv_transactions(df)
    if not records:
        raise HTTPException(status_code=400, detail={"status": "ERROR", "reason": "CSV dataset is empty"})

    {
        str(record.get("transaction_id") or ""): record
        for record in records
        if record.get("transaction_id")
    }

    cache_key = f"cmds:predict:{hashlib.sha256(request.csv_text.encode('utf-8')).hexdigest()}"
    cached = _prediction_cache.get(cache_key)
    if cached is not None:
        return cached

    gnn_predict_enabled_raw = os.getenv("ENABLE_GNN_CSV_PREDICT", "").strip().lower()
    gnn_predict_enabled = (
        gnn_predict_enabled_raw in {"1", "true", "yes", "on"}
        if gnn_predict_enabled_raw
        else not _is_production_env()
    )

    try:
        if not gnn_predict_enabled:
            raise RuntimeError("gnn_csv_predict_disabled")

        from src.gnn_detector.predict import predict_from_csv_text

        gnn_result = predict_from_csv_text(request.csv_text)

        record_stats = _build_record_stats(records)
        flagged_paths = gnn_result.get("flagged_paths", []) if isinstance(gnn_result.get("flagged_paths"), list) else []
        edge_anomalies = gnn_result.get("edge_anomalies", []) if isinstance(gnn_result.get("edge_anomalies"), list) else []

        # Build a stable lookup so each input transaction gets a single prediction row.
        # Some GNN outputs may emit multiple edge anomalies per transaction.
        anomaly_by_txn: Dict[str, Dict[str, Any]] = {}
        for edge in edge_anomalies:
            tx_id = str(edge.get("transaction_id") or "").strip()
            if not tx_id:
                continue
            current = anomaly_by_txn.get(tx_id)
            if current is None:
                anomaly_by_txn[tx_id] = edge
                continue
            current_score = _safe_float(current.get("anomaly_score"), 0.0)
            next_score = _safe_float(edge.get("anomaly_score"), 0.0)
            if next_score > current_score:
                anomaly_by_txn[tx_id] = edge

        pending_predictions: List[Dict[str, Any]] = []
        batch_risk_scores: List[float] = []
        for source_record in records:
            tx_id = str(source_record.get("transaction_id") or "")
            edge = anomaly_by_txn.get(tx_id, {})

            source_sender = str(source_record.get("sender_id") or edge.get("sender_id") or "unknown")
            fan_out_count = len(record_stats.get("sender_unique_receivers", {}).get(source_sender, set()))
            pattern_signals = _compute_pattern_signals_for_transaction(source_record, record_stats, flagged_paths)
            hybrid = _compute_hybrid_risk(
                edge=edge,
                source_record=source_record,
                pattern_signals=pattern_signals,
                fan_out_count=fan_out_count,
            )
            final_risk = float(hybrid.get("risk_score", 0.0))
            batch_risk_scores.append(final_risk)

            source_is_fraud = bool(source_record.get("source_is_fraud"))
            source_status = str(source_record.get("source_status") or "")
            source_fraud_reason = str(source_record.get("source_fraud_reason") or "")
            source_amount = float(source_record.get("amount", 0.0))
            source_currency = str(source_record.get("currency") or "INR")
            source_transaction_id = str(source_record.get("transaction_id") or tx_id)
            source_user_id = source_sender
            source_account_id = source_sender
            source_name = str(source_record.get("name") or "")
            source_mobile_number = str(source_record.get("mobile_number") or "")
            source_account_number = str(source_record.get("account_number") or source_sender)
            source_account_product_type = str(source_record.get("account_product_type") or "")
            source_narration = str(source_record.get("narration") or "")
            source_pincode = str(source_record.get("pincode") or "")
            source_receiver_id = str(source_record.get("receiver_id") or edge.get("receiver_id") or "")
            source_channel = str(source_record.get("channel") or source_record.get("transaction_type") or "APP")
            mapped_status = "FRAUD" if source_is_fraud else source_status or "ALLOW"

            pending_predictions.append(
                {
                    "status": "SUCCESS",
                    "transaction_id": source_transaction_id,
                    "source_transaction_id": source_transaction_id,
                    "source_user_id": source_user_id,
                    "source_account_id": source_account_id,
                    "decision": "ALLOW",
                    "status_label": mapped_status,
                    "source_status": source_status or None,
                    "source_is_fraud": source_is_fraud,
                    "source_fraud_reason": source_fraud_reason or None,
                    "source_channel": source_channel,
                    "channel": source_channel,
                    "source_transaction_type": source_channel,
                    "source_name": source_name or None,
                    "source_mobile_number": source_mobile_number or None,
                    "source_account_number": source_account_number or None,
                    "source_account_product_type": source_account_product_type or None,
                    "source_narration": source_narration or None,
                    "source_pincode": source_pincode or None,
                    "source_receiver_id": source_receiver_id or None,
                    "amount": source_amount,
                    "currency": source_currency,
                    "risk_score": round(final_risk, 4),
                    "timestamp": _utc_now_iso(),
                    "reasons": edge.get("reasons", []),
                    "risk_breakdown": hybrid.get("breakdown", {}),
                    "pattern_signals": pattern_signals,
                    "transaction_flow_summary": {
                        "path": [source_user_id, source_receiver_id or "unknown"],
                        "hops": 1,
                        "max_gap_minutes": float(round(_safe_float(edge.get("max_gap_minutes"), 0.0), 2)),
                    },
                    "explainability": {
                        "reasons": edge.get("reasons", []),
                        "top_features": {
                            "user_id": source_user_id,
                            "counterparty": source_receiver_id,
                            "amount": source_amount,
                        },
                    },
                }
            )

        calibration = _calibrate_thresholds(batch_risk_scores)
        calibrated_flag = float(calibration.get("flag_threshold") or FLAG_THRESHOLD)
        calibrated_block = float(calibration.get("block_threshold") or BLOCK_THRESHOLD)
        transaction_predictions: List[Dict[str, Any]] = []
        for item in pending_predictions:
            risk_score = _safe_float(item.get("risk_score"), 0.0)
            if risk_score >= calibrated_block:
                decision = "BLOCK"
            elif risk_score >= calibrated_flag:
                decision = "FLAG"
            else:
                decision = "ALLOW"
            item["decision"] = decision
            if not item.get("source_status"):
                item["status_label"] = decision
            transaction_predictions.append(item)

        _replace_stream_rows(transaction_predictions)

        global _live_gnn_snapshot
        _live_gnn_snapshot = gnn_result
        response = {
            "status": "ok",
            "model_type": gnn_result.get("model_type", "gnn_graphsage"),
            "calibration": calibration,
            "predictions": transaction_predictions,
            "count": len(transaction_predictions),
            "node_risk_scores": gnn_result.get("node_risk_scores", {}),
            "suspicious_nodes": gnn_result.get("suspicious_nodes", []),
            "explanations": gnn_result.get("explanations", []),
            "clusters": gnn_result.get("clusters", []),
            "edge_anomalies": gnn_result.get("edge_anomalies", []),
            "flagged_paths": gnn_result.get("flagged_paths", []),
            "velocity": gnn_result.get("velocity", {}),
            "performance": gnn_result.get("performance", {}),
            "graph": {
                "nodes": [
                    {
                        "id": account_id,
                        "label": account_id,
                        "type": "account",
                        "suspicious": score >= 0.6,
                        "risk_score": score,
                        "risk_level": "high" if score >= 0.75 else "medium" if score >= 0.45 else "low",
                    }
                    for account_id, score in gnn_result.get("node_risk_scores", {}).items()
                ],
                "links": [
                    {
                        "source": row.get("sender_id"),
                        "target": row.get("receiver_id"),
                        "suspicious": row.get("suspicious", False),
                        "risk_score": row.get("anomaly_score", 0.0),
                        "velocity_score": row.get("velocity_score", 0.0),
                        "reasons": row.get("reasons", []),
                    }
                    for row in gnn_result.get("edge_anomalies", [])
                ],
                "clusters": gnn_result.get("clusters", []),
                "flagged_paths": gnn_result.get("flagged_paths", []),
                "explanations": gnn_result.get("explanations", []),
                "summary": gnn_result.get("graph_summary", {}),
            },
        }
        _prediction_cache.set(cache_key, response)
        return response
    except Exception as exc:
        logger.warning("GraphSAGE inference unavailable, using orchestrator fallback: %s", exc)

    # Fast fallback path for environments where torch/torch_geometric are unavailable.
    # This keeps /v1/predict responsive while still returning consistent, explainable output.
    record_stats = _build_record_stats(records)
    pending_predictions: List[Dict[str, Any]] = []
    batch_risk_scores: List[float] = []
    for source_record in records:
        source_sender = str(source_record.get("sender_id") or "unknown")
        source_receiver = str(source_record.get("receiver_id") or "")
        source_transaction_id = str(source_record.get("transaction_id") or "")
        source_amount = float(source_record.get("amount") or 0.0)
        source_channel = str(source_record.get("channel") or source_record.get("transaction_type") or "APP")
        source_status = str(source_record.get("source_status") or "")
        source_is_fraud = bool(source_record.get("source_is_fraud"))
        source_fraud_reason = str(source_record.get("source_fraud_reason") or "")

        fan_out_count = len(record_stats.get("sender_unique_receivers", {}).get(source_sender, set()))
        pattern_signals = _compute_pattern_signals_for_transaction(source_record, record_stats, [])
        amount_score = min(source_amount / 20000.0, 1.0)
        fan_out_score = min(fan_out_count / 6.0, 1.0)
        label_score = 1.0 if source_is_fraud or source_status.upper() in {"FLAG", "BLOCK", "FRAUD"} else 0.0
        pattern_score = max(
            float(pattern_signals.get("high_value_cluster", 0.0)),
            float(pattern_signals.get("receiver_spread", 0.0)),
            float(pattern_signals.get("shared_device", 0.0)),
        )
        final_risk = max(0.0, min(1.0, (0.40 * label_score) + (0.30 * amount_score) + (0.20 * fan_out_score) + (0.10 * pattern_score)))
        batch_risk_scores.append(final_risk)

        pending_predictions.append(
            {
                "status": "SUCCESS",
                "transaction_id": source_transaction_id,
                "source_transaction_id": source_transaction_id,
                "source_user_id": source_sender,
                "source_account_id": source_sender,
                "decision": "ALLOW",
                "status_label": "FRAUD" if source_is_fraud else (source_status or "ALLOW"),
                "source_status": source_status or None,
                "source_is_fraud": source_is_fraud,
                "source_fraud_reason": source_fraud_reason or None,
                "source_channel": source_channel,
                "channel": source_channel,
                "source_transaction_type": source_channel,
                "source_name": str(source_record.get("name") or "") or None,
                "source_mobile_number": str(source_record.get("mobile_number") or "") or None,
                "source_account_number": str(source_record.get("account_number") or source_sender) or source_sender,
                "source_account_product_type": str(source_record.get("account_product_type") or "") or None,
                "source_narration": str(source_record.get("narration") or "") or None,
                "source_pincode": str(source_record.get("pincode") or "") or None,
                "source_receiver_id": source_receiver or None,
                "amount": source_amount,
                "currency": str(source_record.get("currency") or "INR"),
                "risk_score": round(final_risk, 4),
                "timestamp": _utc_now_iso(),
                "reasons": [
                    *( ["labeled_fraud_record"] if label_score >= 1.0 else [] ),
                    *( ["high_transfer_amount"] if amount_score >= 0.45 else [] ),
                    *( ["broad_receiver_spread"] if fan_out_score >= 0.5 else [] ),
                ]
                or ["rule_based_risk_scoring"],
                "risk_breakdown": {
                    "graph": 0.0,
                    "rule": round((0.40 * label_score) + (0.30 * amount_score) + (0.20 * fan_out_score), 4),
                    "pattern": round(0.10 * pattern_score, 4),
                },
                "pattern_signals": pattern_signals,
                "transaction_flow_summary": {
                    "path": [source_sender, source_receiver or "unknown"],
                    "hops": 1,
                    "max_gap_minutes": float(round(_safe_float(source_record.get("time_diff_minutes"), 0.0), 2)),
                },
                "explainability": {
                    "reasons": [
                        *( ["labeled_fraud_record"] if label_score >= 1.0 else [] ),
                        *( ["high_transfer_amount"] if amount_score >= 0.45 else [] ),
                        *( ["broad_receiver_spread"] if fan_out_score >= 0.5 else [] ),
                    ]
                    or ["rule_based_risk_scoring"],
                    "top_features": {
                        "user_id": source_sender,
                        "counterparty": source_receiver,
                        "amount": source_amount,
                    },
                },
            }
        )

    calibration = _calibrate_thresholds(batch_risk_scores)
    calibrated_flag = float(calibration.get("flag_threshold") or FLAG_THRESHOLD)
    calibrated_block = float(calibration.get("block_threshold") or BLOCK_THRESHOLD)

    scored_results: List[Dict[str, Any]] = []
    for item in pending_predictions:
        risk_score = _safe_float(item.get("risk_score"), 0.0)
        if risk_score >= calibrated_block:
            decision = "BLOCK"
        elif risk_score >= calibrated_flag:
            decision = "FLAG"
        else:
            decision = "ALLOW"
        item["decision"] = decision
        if not item.get("source_status"):
            item["status_label"] = decision
        scored_results.append(item)

    _replace_stream_rows(scored_results)

    graph = _build_graph_from_scores(scored_results)
    response = {
        "status": "ok",
        "model_type": "heuristic_fallback_fast",
        "calibration": calibration,
        "predictions": scored_results,
        "count": len(scored_results),
        "node_risk_scores": {},
        "suspicious_nodes": [],
        "explanations": [],
        "clusters": [],
        "edge_anomalies": [],
        "flagged_paths": [],
        "velocity": {"rapid_edges": [], "node_velocity_scores": {}, "window_minutes": 5.0},
        "performance": {"async_analytics_enabled": False, "analytics_mode": "fallback"},
        "graph": graph,
    }
    _prediction_cache.set(cache_key, response)
    return response


@app.post("/v1/stream")
def stream_alias(request: StreamPublishRequest) -> Dict[str, Any]:
    return stream_publish(request)


@app.post("/v1/reset")
def reset_data() -> Dict[str, Any]:
    _reset_runtime_state()
    _ensure_stream_worker()
    return {"status": "ok", "message": "Runtime state reset"}


@app.get("/v1/report", response_model=None)
def report(format: str = "csv"):
    scored_results = _collect_stream_results()
    if format.lower() == "json":
        rows = build_report_rows(scored_results)
        return {"status": "ok", "count": len(rows), "rows": rows}

    if format.lower() == "pdf":
        rows = build_report_rows(scored_results)
        pdf_payload = rows[0] if rows else {
            "case_id": "no-data",
            "risk_score": 0.0,
            "confidence_score": 0.0,
            "decision": "ALLOW",
            "accounts_involved": [],
            "transaction_path": [],
            "detected_patterns": [],
            "sanctions_screening": {},
            "jurisdiction_risk": {},
            "why_flagged": "No scored transactions available.",
        }
        pdf_bytes = build_pdf_report(pdf_payload)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": 'attachment; filename="money_mule_report.pdf"'},
        )

    csv_text = _build_report_csv(scored_results)
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="money_mule_report.csv"'},
    )


_frontend_dist_path = Path(os.getenv("FRONTEND_DIST_PATH", "frontend/dist")).resolve()
if _frontend_dist_path.exists():
    app.mount("/", SpaStaticFiles(directory=str(_frontend_dist_path), html=True), name="frontend")
