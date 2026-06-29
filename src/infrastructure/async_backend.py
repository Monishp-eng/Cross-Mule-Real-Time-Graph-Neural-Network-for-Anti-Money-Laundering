"""Redis-backed task queue and cache helpers.

This module provides an equivalent to Celery-style async processing using Redis
if available, with a safe in-process fallback for local development.
"""

from __future__ import annotations

import json
import os
import queue
import threading
import time
import uuid
from collections import deque
from dataclasses import dataclass
from typing import Any, Dict, Optional

try:  # pragma: no cover - optional dependency
    import redis
except Exception:  # pragma: no cover
    redis = None


def _default_ttl() -> int:
    return max(60, int(os.getenv("REDIS_CACHE_TTL_SECONDS", "3600")))


def _redis_url() -> str:
    return os.getenv("REDIS_URL", "redis://localhost:6379/0")


def _json_dumps(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, separators=(",", ":"), default=str)


def _json_loads(payload: str | bytes | None) -> Optional[Dict[str, Any]]:
    if payload is None:
        return None
    if isinstance(payload, bytes):
        payload = payload.decode("utf-8")
    try:
        return json.loads(payload)
    except Exception:
        return None


@dataclass
class AsyncTaskState:
    request_id: str
    state: str
    created_at: str
    updated_at: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class RedisCache:
    def __init__(self, client: Any | None = None, ttl_seconds: Optional[int] = None):
        self.ttl_seconds = ttl_seconds or _default_ttl()
        self.client = client or self._build_client()

    @staticmethod
    def _build_client():
        if redis is None:
            return None
        try:
            return redis.Redis.from_url(_redis_url(), decode_responses=True)
        except Exception:
            return None

    def available(self) -> bool:
        return self.client is not None

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        if self.client is None:
            return None
        try:
            return _json_loads(self.client.get(key))
        except Exception:
            # Redis connection failed or unavailable - return None (cache miss)
            return None

    def set(self, key: str, value: Dict[str, Any], ttl_seconds: Optional[int] = None) -> None:
        if self.client is None:
            return
        try:
            self.client.setex(key, ttl_seconds or self.ttl_seconds, _json_dumps(value))
        except Exception:
            # Redis connection failed or unavailable - skip caching silently
            pass

    def delete(self, key: str) -> None:
        if self.client is None:
            return
        self.client.delete(key)


class RedisTaskQueue:
    def __init__(self, client: Any | None = None, queue_name: str = "cmds:analysis:queue"):
        self.queue_name = queue_name
        self.dead_letter_queue_name = os.getenv("ANALYSIS_DLQ_NAME", "cmds:analysis:dlq")
        self.max_retries = max(0, int(os.getenv("ANALYSIS_MAX_RETRIES", "3")))
        self.client = client or self._build_client()
        self._local_queue: queue.Queue = queue.Queue()
        self._local_dlq: deque = deque(maxlen=2000)
        self._local_results: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    @staticmethod
    def _build_client():
        if redis is None:
            return None
        try:
            return redis.Redis.from_url(_redis_url(), decode_responses=True)
        except Exception:
            return None

    def available(self) -> bool:
        return self.client is not None

    def enqueue(self, payload: Dict[str, Any]) -> str:
        request_id = str(payload.get("request_id") or uuid.uuid4())
        payload = {
            **payload,
            "request_id": request_id,
            "attempt": int(payload.get("attempt", 0)),
            "state": "queued",
            "queued_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        if self.client is not None:
            self.client.lpush(self.queue_name, _json_dumps(payload))
        else:
            self._local_queue.put(payload)
        self.set_state(request_id, {"state": "queued", "queued_at": payload["queued_at"], "attempt": payload["attempt"]})
        return request_id

    def set_state(self, request_id: str, payload: Dict[str, Any], ttl_seconds: Optional[int] = None) -> None:
        state_payload = {"request_id": request_id, **payload}
        if self.client is not None:
            self.client.setex(f"cmds:analysis:state:{request_id}", ttl_seconds or _default_ttl(), _json_dumps(state_payload))
        else:
            self._local_results[request_id] = state_payload

    def poll(self, timeout: float = 1.0) -> Optional[Dict[str, Any]]:
        if self.client is not None:
            try:
                item = self.client.brpop(self.queue_name, timeout=timeout)
            except Exception:
                return None
            if not item:
                return None
            _, raw = item
            return _json_loads(raw)

        try:
            return self._local_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def mark_processing(self, request_id: str, ttl_seconds: Optional[int] = None) -> None:
        self.set_state(request_id, {"state": "processing", "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}, ttl_seconds=ttl_seconds)

    def store_result(self, request_id: str, result: Dict[str, Any], ttl_seconds: Optional[int] = None) -> None:
        payload = {
            "request_id": request_id,
            "state": result.get("state", "completed"),
            "completed_at": result.get("completed_at") or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "result": result,
        }
        if self.client is not None:
            ttl = ttl_seconds or _default_ttl()
            self.client.setex(f"cmds:analysis:result:{request_id}", ttl, _json_dumps(payload))
            self.client.setex(f"cmds:analysis:state:{request_id}", ttl, _json_dumps({"request_id": request_id, "state": payload["state"], "completed_at": payload["completed_at"]}))
        else:
            with self._lock:
                self._local_results[request_id] = payload

    def store_failure(self, request_id: str, error: str, ttl_seconds: Optional[int] = None) -> None:
        payload = {"request_id": request_id, "state": "failed", "error": error, "completed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        if self.client is not None:
            ttl = ttl_seconds or _default_ttl()
            self.client.setex(f"cmds:analysis:result:{request_id}", ttl, _json_dumps(payload))
            self.client.setex(f"cmds:analysis:state:{request_id}", ttl, _json_dumps(payload))
        else:
            with self._lock:
                self._local_results[request_id] = payload

    def requeue_or_deadletter(self, payload: Dict[str, Any], error: str, ttl_seconds: Optional[int] = None) -> str:
        request_id = str(payload.get("request_id") or "")
        if not request_id:
            return "dropped"

        next_attempt = int(payload.get("attempt", 0)) + 1
        if next_attempt <= self.max_retries:
            retry_payload = {
                **payload,
                "attempt": next_attempt,
                "state": "queued",
                "last_error": error,
                "queued_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
            if self.client is not None:
                self.client.lpush(self.queue_name, _json_dumps(retry_payload))
            else:
                self._local_queue.put(retry_payload)
            self.set_state(
                request_id,
                {
                    "state": "queued",
                    "attempt": next_attempt,
                    "last_error": error,
                    "queued_at": retry_payload["queued_at"],
                },
                ttl_seconds=ttl_seconds,
            )
            return "requeued"

        dlq_payload = {
            **payload,
            "attempt": next_attempt,
            "state": "dead_lettered",
            "error": error,
            "dead_lettered_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        if self.client is not None:
            self.client.lpush(self.dead_letter_queue_name, _json_dumps(dlq_payload))
        else:
            with self._lock:
                self._local_dlq.appendleft(dlq_payload)

        self.store_failure(request_id, error, ttl_seconds=ttl_seconds)
        return "dead_lettered"

    def get_result(self, request_id: str) -> Optional[Dict[str, Any]]:
        if self.client is not None:
            result = _json_loads(self.client.get(f"cmds:analysis:result:{request_id}"))
            if result is not None:
                return result
            return _json_loads(self.client.get(f"cmds:analysis:state:{request_id}"))
        with self._lock:
            return self._local_results.get(request_id)

    def clear_local(self) -> None:
        with self._lock:
            self._local_results.clear()
            while not self._local_queue.empty():
                try:
                    self._local_queue.get_nowait()
                except queue.Empty:
                    break
            self._local_dlq.clear()

    def dead_letter_size(self) -> int:
        if self.client is not None:
            try:
                return int(self.client.llen(self.dead_letter_queue_name))
            except Exception:
                return 0
        with self._lock:
            return len(self._local_dlq)

    def peek_dead_letters(self, limit: int = 20) -> list[Dict[str, Any]]:
        safe_limit = max(1, min(limit, 200))
        if self.client is not None:
            try:
                rows = self.client.lrange(self.dead_letter_queue_name, 0, safe_limit - 1)
                return [row for row in (_json_loads(raw) for raw in rows) if isinstance(row, dict)]
            except Exception:
                return []
        with self._lock:
            return list(self._local_dlq)[:safe_limit]

    def queue_size(self) -> int:
        if self.client is not None:
            try:
                return int(self.client.llen(self.queue_name))
            except Exception:
                return 0
        return self._local_queue.qsize()

    def metrics(self) -> Dict[str, Any]:
        return {
            "redis_enabled": self.client is not None,
            "queue_size": self.queue_size(),
            "dead_letter_queue_size": self.dead_letter_size(),
            "max_retries": self.max_retries,
        }

