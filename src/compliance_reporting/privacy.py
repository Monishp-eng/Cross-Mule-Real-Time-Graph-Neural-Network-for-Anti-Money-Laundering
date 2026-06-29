"""Privacy-safe intelligence sharing helpers."""

from __future__ import annotations

import hashlib
import os
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List


def hash_entity_id(entity_type: str, raw_value: str, salt: str | None = None) -> str:
    seed = f"{entity_type}:{raw_value}:{salt or os.getenv('INTEL_HASH_SALT', 'demo-salt')}"
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()


@dataclass
class ReplayProtectionStore:
    ttl_seconds: int = 3600
    _seen: Dict[str, float] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def _purge(self) -> None:
        cutoff = time.time() - self.ttl_seconds
        stale = [nonce for nonce, created_at in self._seen.items() if created_at < cutoff]
        for nonce in stale:
            self._seen.pop(nonce, None)

    def register(self, nonce: str, event_timestamp: str | None = None) -> bool:
        key = f"{nonce}:{event_timestamp or ''}"
        with self._lock:
            self._purge()
            if key in self._seen:
                return False
            self._seen[key] = time.time()
            return True


class PrivacyIntelManager:
    def __init__(self, ttl_seconds: int = 3600):
        self.replay_guard = ReplayProtectionStore(ttl_seconds=ttl_seconds)

    @staticmethod
    def hash_entity_id(entity_type: str, raw_value: str) -> str:
        return hash_entity_id(entity_type, raw_value)

    def share_indicator(
        self,
        *,
        indicator_type: str,
        value: str,
        source_bank: str,
        confidence: float,
        nonce: str | None = None,
        event_timestamp: str | None = None,
    ) -> Dict[str, Any]:
        replay_detected = False
        if nonce:
            replay_detected = not self.replay_guard.register(nonce, event_timestamp)

        return {
            "hashed_entity_id": self.hash_entity_id(indicator_type, value),
            "replay_detected": replay_detected,
            "timestamp": event_timestamp or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "source_bank": source_bank,
            "confidence": round(max(0.0, min(1.0, confidence)), 4),
        }

    @staticmethod
    def simulate_federated_embedding_exchange(local_embedding: List[float], peer_embeddings: List[List[float]]) -> Dict[str, Any]:
        vectors = [local_embedding] + [embedding for embedding in peer_embeddings if embedding]
        if not vectors:
            return {"status": "ok", "shared_embedding": [], "peer_count": 0}

        max_len = max(len(vector) for vector in vectors)
        normalized = []
        for vector in vectors:
            padded = list(vector) + [0.0] * (max_len - len(vector))
            normalized.append(padded)

        aggregated = [round(sum(values) / len(values), 6) for values in zip(*normalized)]
        return {
            "status": "ok",
            "shared_embedding": aggregated,
            "peer_count": max(0, len(vectors) - 1),
        }

