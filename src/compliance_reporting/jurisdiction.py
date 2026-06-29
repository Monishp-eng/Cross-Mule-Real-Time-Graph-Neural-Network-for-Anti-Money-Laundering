"""Jurisdiction risk scoring with structured country tiers."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List


DEFAULT_COUNTRY_RISK_TABLE = {
    "US": {"tier": "low", "score": 0.10},
    "UK": {"tier": "low", "score": 0.12},
    "IN": {"tier": "low", "score": 0.18},
    "AE": {"tier": "medium", "score": 0.42},
    "SG": {"tier": "medium", "score": 0.38},
    "CN": {"tier": "high", "score": 0.80},
    "TR": {"tier": "high", "score": 0.74},
    "IR": {"tier": "high", "score": 0.95},
    "KP": {"tier": "high", "score": 0.98},
    "SY": {"tier": "high", "score": 0.96},
    "CU": {"tier": "high", "score": 0.92},
    "RU": {"tier": "high", "score": 0.75},
}


def load_country_risk_table(path: str | None = None) -> Dict[str, Dict[str, Any]]:
    risk_path = path or os.getenv("COUNTRY_RISK_TABLE_PATH", "data/country_risk_table.json")
    file_path = Path(risk_path)
    if not file_path.exists():
        return DEFAULT_COUNTRY_RISK_TABLE
    try:
        with file_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, dict):
            return DEFAULT_COUNTRY_RISK_TABLE
        return {str(k).upper(): v for k, v in data.items() if isinstance(v, dict)} or DEFAULT_COUNTRY_RISK_TABLE
    except Exception:
        return DEFAULT_COUNTRY_RISK_TABLE


class JurisdictionRiskEngine:
    def __init__(self, table_path: str | None = None):
        self.table = load_country_risk_table(table_path)

    def _country_score(self, country: str) -> float:
        record = self.table.get(str(country or "US").upper(), {"tier": "medium", "score": 0.30})
        return float(record.get("score", 0.30))

    def score(self, origin_country: str, destination_countries: List[str], repeated_high_risk_routing: int = 0) -> Dict[str, Any]:
        origin = str(origin_country or "US").upper()
        destinations = [str(country).upper() for country in destination_countries if country]
        destination_scores = [self._country_score(country) for country in destinations] or [0.0]

        origin_score = self._country_score(origin)
        destination_score = max(destination_scores)
        cross_border = any(country != origin for country in destinations)
        cross_border_boost = 0.10 if cross_border else 0.0
        repeat_boost = min(0.20, max(0, repeated_high_risk_routing) * 0.05)

        jurisdiction_score = min(1.0, max(origin_score, destination_score) + cross_border_boost + repeat_boost)
        risk_band = "HIGH" if jurisdiction_score >= 0.7 else "MEDIUM" if jurisdiction_score >= 0.35 else "LOW"

        return {
            "jurisdiction_score": round(jurisdiction_score, 4),
            "risk_band": risk_band,
            "origin_country": origin,
            "origin_risk": round(origin_score, 4),
            "destination_countries": destinations,
            "destination_risk": round(destination_score, 4),
            "cross_border": cross_border,
            "repeated_high_risk_routing": repeated_high_risk_routing,
        }

