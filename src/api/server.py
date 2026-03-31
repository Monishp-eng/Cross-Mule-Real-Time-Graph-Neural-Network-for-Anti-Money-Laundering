"""FastAPI backend for mule detection orchestration."""

from __future__ import annotations

import os
import queue
import threading
import time
import json
import logging
from collections import defaultdict, deque
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field, model_validator

from src.orchestrator import MuleDetectionOrchestrator

logger = logging.getLogger(__name__)


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


app = FastAPI(
    title="Cross-Channel Mule Detection API",
    version="1.0.0",
    description="API layer for transaction scoring and mule detection",
)

_orchestrator: Optional[MuleDetectionOrchestrator] = None
_stream_queue: queue.Queue = queue.Queue(maxsize=5000)
_stream_results: deque = deque(maxlen=1000)
_stream_stop = threading.Event()
_stream_thread: Optional[threading.Thread] = None

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


def _auth_required() -> bool:
    return os.getenv("AUTH_REQUIRED", "false").lower() in {"1", "true", "yes"}


def _api_key() -> str:
    return os.getenv("API_KEY", "hackathon-demo-key")


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
                    "queued_at": datetime.utcnow().isoformat() + "Z",
                    "result": result,
                }
            )
        finally:
            _stream_queue.task_done()


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
            "event_id": f"DEMO_{scenario}_{int(datetime.utcnow().timestamp())}",
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

    # Skip auth/rate-limit for docs and health.
    exempt_prefixes = ("/docs", "/redoc", "/openapi.json", "/health", "/metrics")
    if not path.startswith(exempt_prefixes):
        if _auth_required():
            provided = request.headers.get("x-api-key", "")
            if provided != _api_key():
                _metrics["errors_total"] += 1
                return JSONResponse(status_code=401, content={"detail": "Unauthorized"})

        client = request.client.host if request.client else "unknown"
        now = time.time()
        dq = _rate_state[client]
        while dq and now - dq[0] > _rate_window_seconds:
            dq.popleft()
        if len(dq) >= _rate_limit_per_window:
            _metrics["errors_total"] += 1
            return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})
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
    logger.info(
        json.dumps(
            {
                "ts": datetime.utcnow().isoformat() + "Z",
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


@app.on_event("startup")
def startup_event() -> None:
    global _stream_thread
    _stream_stop.clear()
    if _stream_thread is None or not _stream_thread.is_alive():
        _stream_thread = threading.Thread(target=_stream_worker, daemon=True)
        _stream_thread.start()


@app.get("/health/live")
def health_live() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/health/ready")
def health_ready() -> Dict[str, Any]:
    orchestrator = get_orchestrator()
    neo4j_enabled = orchestrator.graph_builder.neo4j_client is not None
    return {
        "status": "ready",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "neo4j_enabled": neo4j_enabled,
    }


@app.post("/v1/transactions/process")
def process_transaction(event: EventPayload) -> Dict[str, Any]:
    orchestrator = get_orchestrator()
    result = orchestrator.process_event(event.model_dump())

    if result.get("status") == "ERROR":
        raise HTTPException(status_code=400, detail=result)

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


@app.post("/v1/intel/share")
def share_privacy_indicator(request: PrivacyIndicatorShareRequest) -> Dict[str, Any]:
    orchestrator = get_orchestrator()
    try:
        return orchestrator.share_privacy_indicator(
            indicator_type=request.indicator_type,
            raw_value=request.value,
            source_bank=request.source_bank,
            confidence=request.confidence,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"status": "ERROR", "reason": str(exc)}) from exc


@app.get("/v1/intel/summary")
def intel_summary() -> Dict[str, Any]:
    orchestrator = get_orchestrator()
    return orchestrator.get_intel_summary()


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
    return result


@app.on_event("shutdown")
def shutdown_event() -> None:
    global _stream_thread
    _stream_stop.set()
    if _stream_thread and _stream_thread.is_alive():
        _stream_thread.join(timeout=2)
    _stream_thread = None

    global _orchestrator
    if _orchestrator is not None:
        _orchestrator.close()
        _orchestrator = None
