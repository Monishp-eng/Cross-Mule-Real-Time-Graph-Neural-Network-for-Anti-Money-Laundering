"""Transaction complexity detection for mule-style behaviors."""

from __future__ import annotations

from typing import Any, Dict, List


class TransactionComplexityDetector:
    def detect(
        self,
        *,
        current_txn_count_1h: int,
        unique_counterparties: int,
        connected_accounts: List[Dict[str, Any]],
        amounts: List[float],
        routing_hops: int = 1,
        time_diff_minutes: float = 0.0,
        inbound_count: int = 0,
        outbound_count: int = 0,
    ) -> Dict[str, Any]:
        fan_out = min(1.0, (max(outbound_count, unique_counterparties) / 12.0) + (current_txn_count_1h / 30.0))
        fan_in = min(1.0, (inbound_count / 12.0) + (len(connected_accounts) / 20.0))
        nesting = min(1.0, max(0, routing_hops - 1) / 4.0 + len(connected_accounts) / 30.0)
        burst = min(1.0, (current_txn_count_1h / 20.0) + (1.0 if time_diff_minutes <= 2.0 else 0.0))

        complexity_type = max(
            [("fan-out", fan_out), ("fan-in", fan_in), ("nesting", nesting), ("burst", burst)],
            key=lambda item: item[1],
        )[0]

        structure = 0.0
        if amounts:
            near_threshold = sum(1 for amount in amounts if 300 <= amount <= 2500 or 9000 <= amount < 10000)
            structure = min(1.0, near_threshold / max(len(amounts), 1))

        complexity_score = min(100.0, round(((0.35 * fan_out) + (0.25 * fan_in) + (0.20 * nesting) + (0.20 * burst) + (0.10 * structure)) * 100.0, 2))

        return {
            "complexity_score": complexity_score,
            "complexity_type": complexity_type,
            "fan_out_score": round(fan_out, 4),
            "fan_in_score": round(fan_in, 4),
            "nesting_score": round(nesting, 4),
            "burst_score": round(burst, 4),
            "structuring_overlap": round(structure, 4),
        }

