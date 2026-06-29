"""Sanctions screening helpers with exact, alias, and fuzzy matching."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class SanctionsEntity:
    entity_name: str
    aliases: List[str]
    entity_type: str = "individual"
    countries: List[str] | None = None
    source: str = "mock-watchlist"


def _normalize_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (value or "").strip().lower()).strip()


def _default_watchlist() -> List[SanctionsEntity]:
    return [
        SanctionsEntity("John A. Doe", ["John Doe", "J Doe", "Jonathan Doe"], "individual", ["US"]),
        SanctionsEntity("Global Mule Holdings", ["GMH", "Global Mule Ltd", "Mule Hub LLC"], "entity", ["AE", "HK"]),
        SanctionsEntity("North Star Trading", ["NST", "NorthStar Trade", "North Star Trade LLC"], "entity", ["TR", "CY"]),
        SanctionsEntity("A. Rahman", ["Ahmed Rahman", "A Rahman", "Rahman, A"], "individual", ["AE", "PK"]),
    ]


def load_watchlist(path: Optional[str] = None) -> List[SanctionsEntity]:
    watchlist_path = path or os.getenv("SANCTIONS_WATCHLIST_PATH", "data/sanctions_watchlist.json")
    file_path = Path(watchlist_path)
    if not file_path.exists():
        return _default_watchlist()

    try:
        with file_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, list):
            return _default_watchlist()
        entities: List[SanctionsEntity] = []
        for item in data:
            if not isinstance(item, dict):
                continue
            entities.append(
                SanctionsEntity(
                    entity_name=str(item.get("entity_name") or item.get("name") or "Unknown"),
                    aliases=[str(alias) for alias in item.get("aliases", []) if alias],
                    entity_type=str(item.get("entity_type") or "individual"),
                    countries=[str(code).upper() for code in item.get("countries", []) if code],
                    source=str(item.get("source") or "mock-watchlist"),
                )
            )
        return entities or _default_watchlist()
    except Exception:
        return _default_watchlist()


def candidate_strings(raw_payload: Dict[str, Any], normalized: Any = None) -> List[str]:
    candidates: List[str] = []

    keys = (
        "user_name",
        "full_name",
        "account_name",
        "beneficiary_name",
        "recipient_name",
        "sender_name",
        "counterparty_name",
        "destination_name",
        "merchant_name",
        "display_name",
        "upi_id",
        "recipient_upi",
        "beneficiary_account",
        "transfer_to_wallet",
        "source_account_id",
        "dest_account_id",
        "user_id",
    )

    for key in keys:
        value = raw_payload.get(key)
        if isinstance(value, str) and value.strip():
            candidates.append(value.strip())

    if normalized is not None:
        for attr in ("source_account_id", "dest_account_id", "event_id"):
            value = getattr(normalized, attr, None)
            if isinstance(value, str) and value.strip():
                candidates.append(value.strip())

    seen: set[str] = set()
    unique_candidates: List[str] = []
    for candidate in candidates:
        normalized_candidate = candidate.lower()
        if normalized_candidate not in seen:
            seen.add(normalized_candidate)
            unique_candidates.append(candidate)
    return unique_candidates


class SanctionsScreeningEngine:
    def __init__(self, watchlist_path: Optional[str] = None):
        self.watchlist = load_watchlist(watchlist_path)

    @staticmethod
    def _best_match(candidate: str, entity: SanctionsEntity) -> Dict[str, Any]:
        normalized_candidate = _normalize_text(candidate)
        normalized_entity = _normalize_text(entity.entity_name)
        exact_match = normalized_candidate == normalized_entity
        exact_alias_match = any(_normalize_text(alias) == normalized_candidate for alias in entity.aliases)

        alias_scores = [SequenceMatcher(None, normalized_candidate, _normalize_text(alias)).ratio() for alias in entity.aliases]
        name_score = SequenceMatcher(None, normalized_candidate, normalized_entity).ratio()
        fuzzy_score = max([name_score, *alias_scores] if alias_scores else [name_score])

        static_score = 0.0
        if exact_match:
            static_score = 1.0
        elif exact_alias_match:
            static_score = 0.95
        elif fuzzy_score >= 0.86:
            static_score = round(fuzzy_score, 4)

        return {
            "static_score": static_score,
            "fuzzy_score": round(fuzzy_score, 4),
            "exact_match": exact_match,
            "exact_alias_match": exact_alias_match,
        }

    def screen(
        self,
        raw_payload: Dict[str, Any],
        normalized: Any = None,
        behavioral_risk: float = 0.0,
        country_risk: float = 0.0,
    ) -> Dict[str, Any]:
        candidates = candidate_strings(raw_payload, normalized)
        best: Dict[str, Any] = {
            "sanctions_flag": False,
            "sanctions_score": 0.0,
            "matched_entity": None,
            "matched_candidate": None,
            "match_type": None,
            "matched_alias": None,
            "evidence": [],
        }

        for candidate in candidates:
            for entity in self.watchlist:
                match = self._best_match(candidate, entity)
                static_score = float(match["static_score"])
                if static_score <= 0.0:
                    continue

                combined_score = min(1.0, (0.75 * static_score) + (0.15 * max(0.0, behavioral_risk)) + (0.10 * max(0.0, country_risk)))
                if combined_score >= best["sanctions_score"]:
                    best = {
                        "sanctions_flag": combined_score >= 0.6 or static_score >= 0.95,
                        "sanctions_score": round(combined_score, 4),
                        "matched_entity": entity.entity_name,
                        "matched_candidate": candidate,
                        "match_type": "exact" if match["exact_match"] else "alias" if match["exact_alias_match"] else "fuzzy",
                        "matched_alias": candidate if match["exact_alias_match"] else None,
                        "evidence": [
                            {
                                "candidate": candidate,
                                "watchlist_entity": entity.entity_name,
                                "static_score": static_score,
                                "fuzzy_score": match["fuzzy_score"],
                                "countries": entity.countries or [],
                            }
                        ],
                    }

        return best

