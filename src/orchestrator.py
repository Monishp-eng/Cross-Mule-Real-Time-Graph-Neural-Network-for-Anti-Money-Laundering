# Main Orchestration Script

"""
Integration orchestrator - ties all modules together for end-to-end processing.

Flow: Raw Event → Normalize → Graph Update → Risk Scoring → GNN Detection → Decision
"""

import json
import logging
import os
import hashlib
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional, List, Tuple

from dotenv import load_dotenv
from neo4j import GraphDatabase
from neo4j.exceptions import ClientError

# Import modules
from src.data_ingestion.normalizer import DataNormalizer, DataQualityValidator
from src.graph_builder.graph_builder import GraphBuilder
from src.risk_scoring.risk_scorer import RiskScorer
from src.gnn_detector.gnn_detector import SimpleGNNDetector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Neo4jClient:
    """Thin Neo4j client wrapper exposing a single execute method."""

    def __init__(self, uri: str, username: str, password: str, database: str = "neo4j"):
        self.database = database
        self.driver = GraphDatabase.driver(uri, auth=(username, password))

    def verify(self) -> None:
        self.driver.verify_connectivity()

    def execute(self, query: str, params: Optional[Dict] = None) -> None:
        try:
            with self.driver.session(database=self.database) as session:
                session.run(query, params or {})
        except ClientError as exc:
            code = getattr(exc, "code", "")
            if code == "Neo.ClientError.Database.DatabaseNotFound":
                logger.warning(
                    f"Database '{self.database}' not found, retrying with Neo4j default database."
                )
                with self.driver.session() as session:
                    session.run(query, params or {})
            else:
                raise

    def query(self, query: str, params: Optional[Dict] = None) -> List[Dict]:
        """Execute a read query and return records as dictionaries."""
        try:
            with self.driver.session(database=self.database) as session:
                result = session.run(query, params or {})
                return [record.data() for record in result]
        except ClientError as exc:
            code = getattr(exc, "code", "")
            if code == "Neo.ClientError.Database.DatabaseNotFound":
                logger.warning(
                    f"Database '{self.database}' not found, retrying read query with Neo4j default database."
                )
                with self.driver.session() as session:
                    result = session.run(query, params or {})
                    return [record.data() for record in result]
            raise

    def close(self) -> None:
        self.driver.close()


class MuleDetectionOrchestrator:
    """
    Main orchestrator for end-to-end mule detection pipeline.
    
    Pipeline:
    1. Ingest events from multiple channels
    2. Normalize to standard schema
    3. Validate data quality
    4. Update graph database
    5. Compute risk scores
    6. Run GNN detection
    7. Make decision (ALLOW/FLAG/BLOCK)
    8. Generate alerts & cases
    """
    
    def __init__(self, neo4j_client=None):
        load_dotenv()

        if neo4j_client is None:
            neo4j_client = self._build_neo4j_client_from_env()

        self.normalizer = DataNormalizer()
        self.validator = DataQualityValidator()
        self.graph_builder = GraphBuilder(neo4j_client)
        self.risk_scorer = RiskScorer()
        self.gnn_detector = SimpleGNNDetector()

        self.ml_weight = max(0.0, min(1.0, float(os.getenv("HYBRID_ML_WEIGHT", "0.65"))))
        self.rule_weight = 1.0 - self.ml_weight
        self.pattern_boost_weight = max(0.0, min(0.5, float(os.getenv("PATTERN_BOOST_WEIGHT", "0.20"))))

        # In-memory, privacy-safe indicator index for hackathon/demo usage.
        self._intel_indicators: Dict[str, Dict[str, Any]] = {}
        
        self.stats = {
            "ingested": 0,
            "normalized": 0,
            "valid": 0,
            "graph_updated": 0,
            "duplicates": 0,
            "degraded": 0,
            "intel_hits": 0,
            "allowed": 0,
            "flagged": 0,
            "blocked": 0
        }

    @staticmethod
    def _utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _append_trace(trace_steps: List[Dict], step: str, started_at: float) -> None:
        trace_steps.append(
            {
                "step": step,
                "duration_ms": round((time.perf_counter() - started_at) * 1000.0, 2),
            }
        )

    @staticmethod
    def _top_reasons(risk_result, mule_result: Dict, enhanced_signals: Optional[Dict[str, float]] = None) -> List[str]:
        reasons: List[str] = []
        contrib = risk_result.factor_contributions

        if contrib.get("velocity", 0) >= 0.12:
            reasons.append("high_velocity_pattern")
        if contrib.get("account_diversity", 0) >= 0.09:
            reasons.append("high_counterparty_diversity")
        if contrib.get("geographic_inconsistency", 0) >= 0.12:
            reasons.append("geo_anomaly_detected")
        if contrib.get("structuring_pattern", 0) >= 0.08:
            reasons.append("possible_structuring_pattern")
        if contrib.get("account_age", 0) >= 0.07:
            reasons.append("new_account_risk")
        if contrib.get("device_count", 0) >= 0.06:
            reasons.append("multi_device_risk")

        mule_prob = float(mule_result.get("mule_probability", 0.0))
        if mule_prob >= 0.75:
            reasons.append("gnn_detected_high_risk_graph_pattern")
        elif mule_prob >= 0.55:
            reasons.append("gnn_detected_moderate_graph_anomaly")

        if enhanced_signals:
            if enhanced_signals.get("fragmentation_score", 0.0) >= 0.6:
                reasons.append("fragmentation_pattern_detected")
            if enhanced_signals.get("nesting_score", 0.0) >= 0.6:
                reasons.append("nested_fund_flow_detected")
            if enhanced_signals.get("routing_complexity_score", 0.0) >= 0.55:
                reasons.append("unusual_routing_complexity")
            if enhanced_signals.get("sanctions_behavior_score", 0.0) >= 0.65:
                reasons.append("behavior_based_sanctions_signal")
            if enhanced_signals.get("intel_signal_score", 0.0) > 0.0:
                reasons.append("peer_bank_privacy_signal_match")

        return reasons[:8]

    @staticmethod
    def _hash_value(value: str) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    def share_privacy_indicator(self, indicator_type: str, raw_value: str, source_bank: str = "BANK_LOCAL", confidence: float = 0.7) -> Dict[str, Any]:
        indicator = (indicator_type or "").strip().lower()
        value = (raw_value or "").strip().lower()
        if not indicator or not value:
            raise ValueError("indicator_type and value are required")

        hashed_value = self._hash_value(f"{indicator}:{value}")
        record = self._intel_indicators.get(hashed_value)
        if record is None:
            record = {
                "indicator_type": indicator,
                "hashed_value": hashed_value,
                "source_banks": set(),
                "first_seen": self._utc_now_iso(),
                "last_seen": self._utc_now_iso(),
                "confidence": max(0.0, min(1.0, float(confidence))),
                "sightings": 0,
            }
            self._intel_indicators[hashed_value] = record

        record["source_banks"].add(source_bank or "BANK_LOCAL")
        record["last_seen"] = self._utc_now_iso()
        record["confidence"] = max(record["confidence"], max(0.0, min(1.0, float(confidence))))
        record["sightings"] += 1

        return {
            "status": "ok",
            "indicator_type": indicator,
            "hashed_value": hashed_value,
            "source_bank_count": len(record["source_banks"]),
            "sightings": record["sightings"],
            "confidence": round(record["confidence"], 4),
        }

    def _evaluate_privacy_signals(self, normalized, raw_payload: Dict[str, Any]) -> Tuple[float, List[str], int]:
        candidates: List[Tuple[str, str]] = [
            ("device", str(getattr(normalized, "device_id", ""))),
            ("destination_account", str(getattr(normalized, "dest_account_id", ""))),
            ("source_account", str(getattr(normalized, "source_account_id", ""))),
            ("ip", str(raw_payload.get("ip_address", ""))),
        ]

        matched: List[str] = []
        confidence_acc = 0.0
        for indicator_type, value in candidates:
            val = (value or "").strip().lower()
            if not val:
                continue
            key = self._hash_value(f"{indicator_type}:{val}")
            rec = self._intel_indicators.get(key)
            if rec:
                matched.append(indicator_type)
                confidence_acc += float(rec.get("confidence", 0.7))

        if not matched:
            return 0.0, [], 0

        score = min(0.9, (0.2 * len(set(matched))) + (0.2 * confidence_acc))
        return round(score, 4), sorted(set(matched)), len(matched)

    @staticmethod
    def _fragmentation_score(amounts: List[float]) -> float:
        if not amounts:
            return 0.0
        count = len(amounts)
        total = float(sum(amounts))
        if count < 4 or total < 5000:
            return 0.0
        near_small = sum(1 for a in amounts if 300 <= a <= 2500)
        ratio = near_small / max(count, 1)
        score = min(1.0, (ratio * 0.7) + (min(count, 20) / 20.0) * 0.3)
        return round(score, 4)

    @staticmethod
    def _nesting_score(raw_payload: Dict[str, Any], connected_accounts: List[Dict]) -> float:
        hops = int(raw_payload.get("routing_hops", 1) or 1)
        intermediates = raw_payload.get("intermediate_accounts", [])
        intermediate_count = len(intermediates) if isinstance(intermediates, list) else 0
        graph_proxy = min(len(connected_accounts), 20) / 20.0
        score = min(1.0, (max(hops - 1, 0) / 4.0) * 0.5 + (intermediate_count / 6.0) * 0.3 + graph_proxy * 0.2)
        return round(score, 4)

    @staticmethod
    def _routing_complexity_score(target_countries: List[str], unique_counterparties: int, connected_accounts: List[Dict]) -> float:
        jurisdiction_spread = min(len(set(target_countries or [])), 4) / 4.0
        counterparty_pressure = min(unique_counterparties, 40) / 40.0
        graph_complexity = min(len(connected_accounts), 20) / 20.0
        score = min(1.0, 0.4 * counterparty_pressure + 0.35 * jurisdiction_spread + 0.25 * graph_complexity)
        return round(score, 4)

    @staticmethod
    def _sanctions_behavior_score(target_countries: List[str], mule_prob: float, velocity_score: float, routing_complexity_score: float) -> float:
        high_risk_countries = {"KP", "IR", "SY", "CU", "RU"}
        country_signal = 1.0 if any(c in high_risk_countries for c in (target_countries or [])) else 0.2
        score = min(1.0, 0.35 * country_signal + 0.30 * mule_prob + 0.20 * velocity_score + 0.15 * routing_complexity_score)
        return round(score, 4)

    def get_intel_summary(self) -> Dict[str, Any]:
        total_sightings = sum(int(v.get("sightings", 0)) for v in self._intel_indicators.values())
        high_conf = sum(1 for v in self._intel_indicators.values() if float(v.get("confidence", 0.0)) >= 0.8)
        return {
            "status": "ok",
            "indicator_count": len(self._intel_indicators),
            "total_sightings": total_sightings,
            "high_confidence_indicators": high_conf,
        }

    @staticmethod
    def _confidence_score(final_risk: float, ml_score: float, rule_score: float, rule_conf: float, ml_conf: float) -> float:
        boundary_distance = min(abs(final_risk - 0.35), abs(final_risk - 0.70)) / 0.35
        agreement = 1.0 - abs(ml_score - rule_score)
        model_conf = min(rule_conf, ml_conf)
        combined = (0.35 * max(0.0, min(1.0, boundary_distance))) + (0.35 * agreement) + (0.30 * model_conf)
        return round(max(0.0, min(1.0, combined)), 4)

    @classmethod
    def _build_compliance_report(
        cls,
        transaction_id: str,
        trace_id: str,
        decision: str,
        risk_score: float,
        reasons: List[str],
        confidence_score: float,
        model_version: str,
    ) -> Dict:
        timestamp = cls._utc_now_iso()
        report_seed = f"{transaction_id}|{trace_id}|{decision}|{risk_score:.6f}|{timestamp}"
        report_id = "RPT-" + hashlib.sha1(report_seed.encode("utf-8")).hexdigest()[:12].upper()
        return {
            "schema_version": "1.0",
            "report_id": report_id,
            "timestamp": timestamp,
            "trace_id": trace_id,
            "decision": decision,
            "risk_score": round(risk_score, 4),
            "confidence_score": confidence_score,
            "reasons": reasons,
            "model_version": model_version,
        }

    @staticmethod
    def _demo_profile_overrides(profile: str, normalized_amount: float) -> Dict:
        """Provide deterministic scoring inputs for hackathon demo scenarios."""
        p = (profile or "").upper()
        if p == "BLOCK":
            return {
                "current_txn_count_1h": 70,
                "unique_counterparties": 35,
                "amounts": [9800, 9900, 9950, 9700, 10000, normalized_amount],
                "account_age_days": 1,
                "device_count": 12,
                "target_countries": ["KP", "IR"],
            }
        if p == "FLAG":
            return {
                "current_txn_count_1h": 18,
                "unique_counterparties": 12,
                "amounts": [4200, 4300, 4100, normalized_amount],
                "account_age_days": 5,
                "device_count": 5,
                "target_countries": ["CN"],
            }
        return {
            "current_txn_count_1h": 3,
            "unique_counterparties": 3,
            "amounts": [normalized_amount],
            "account_age_days": 120,
            "device_count": 1,
            "target_countries": ["US"],
        }

    @staticmethod
    def _build_neo4j_client_from_env() -> Optional[Neo4jClient]:
        """Initialize Neo4j client from environment variables if credentials are set."""
        uri = os.getenv("NEO4J_URI", "").strip()
        username = os.getenv("NEO4J_USERNAME", "").strip()
        password = os.getenv("NEO4J_PASSWORD", "").strip()
        database = os.getenv("NEO4J_DATABASE", "neo4j").strip() or "neo4j"

        if not uri or not username or not password or "<your-password>" in password:
            logger.warning("NEO4J credentials are missing or placeholders are in use. Running without Neo4j persistence.")
            return None

        try:
            client = Neo4jClient(uri=uri, username=username, password=password, database=database)
            client.verify()
            logger.info("Connected to Neo4j successfully.")
            return client
        except Exception as exc:
            logger.error(f"Neo4j connection failed: {exc}")
            return None
    
    def process_event(self, raw_event: Dict) -> Dict:
        """
        Process a single raw event through the full pipeline.
        
        Returns: Decision result with risk scores
        """
        try:
            trace_id = str(uuid.uuid4())
            pipeline_started = time.perf_counter()
            trace_steps: List[Dict] = []
            self.stats["ingested"] += 1
            
            # Step 1: Normalize
            t0 = time.perf_counter()
            normalized = self.normalizer.normalize_event(raw_event)
            self._append_trace(trace_steps, "normalize", t0)
            if not normalized:
                logger.warning(f"Failed to normalize event: {raw_event}")
                return {
                    "status": "ERROR",
                    "trace_id": trace_id,
                    "reason": "normalization_failed",
                    "trace": trace_steps,
                }
            self.stats["normalized"] += 1
            
            # Step 2: Validate data quality
            t0 = time.perf_counter()
            is_valid, error_msg = self.validator.validate(normalized)
            self._append_trace(trace_steps, "validate", t0)
            if not is_valid:
                logger.warning(f"Data quality check failed: {error_msg}")
                return {
                    "status": "ERROR",
                    "trace_id": trace_id,
                    "reason": f"validation_failed: {error_msg}",
                    "trace": trace_steps,
                }
            self.stats["valid"] += 1
            
            # Step 3: Update graph
            t0 = time.perf_counter()
            normalized_dict = normalized.to_dict()
            graph_persist_enabled = self.graph_builder.neo4j_client is not None
            degraded_mode = not graph_persist_enabled
            if degraded_mode:
                self.stats["degraded"] += 1

            is_duplicate = self.graph_builder.transaction_exists(normalized.event_id)
            if is_duplicate:
                self.stats["duplicates"] += 1

            graph_success = True
            if not is_duplicate:
                graph_success = self.graph_builder.ingest_transaction(normalized_dict)

            if graph_success and graph_persist_enabled and not is_duplicate:
                self.stats["graph_updated"] += 1
            self._append_trace(trace_steps, "graph_update", t0)
            
            # Step 4: Compute risk score
            t0 = time.perf_counter()
            connected_accounts = self.graph_builder.get_connected_accounts(
                normalized.source_account_id,
                limit=20,
            )

            activity = self.graph_builder.get_account_activity(normalized.source_account_id)
            unique_counterparties = max(
                1,
                int(activity.get("unique_counterparties", 1)),
                len(connected_accounts),
            )

            raw_payload = raw_event.get("raw_event", {}) if isinstance(raw_event, dict) else {}
            demo_profile = str(raw_payload.get("demo_risk_profile", "")).upper() if isinstance(raw_payload, dict) else ""
            if demo_profile:
                overrides = self._demo_profile_overrides(demo_profile, normalized.amount)
            else:
                recent_amounts = activity.get("recent_amounts", [])
                txn_count_1h = int(activity.get("txn_count_1h", 1)) + 1
                inferred_device_count = 1 + int(len(connected_accounts) / 4)
                target_countries = [normalized.location.country]

                if normalized.amount >= 250000:
                    txn_count_1h = max(txn_count_1h, 25)
                    inferred_device_count = max(inferred_device_count, 5)

                overrides = {
                    "current_txn_count_1h": txn_count_1h,
                    "unique_counterparties": unique_counterparties,
                    "amounts": (recent_amounts[-10:] + [normalized.amount]) if recent_amounts else [normalized.amount],
                    "account_age_days": 2,
                    "device_count": inferred_device_count,
                    "target_countries": target_countries,
                }

            source_account_data = {
                "account_id": normalized.source_account_id,
                "account_age_days": overrides["account_age_days"],
                "velocity_score": 0.7,
                "balance": 5000,
                "txn_count_24h": int(activity.get("txn_count_24h", 1)),
                "unique_counterparties": unique_counterparties,
                "device_count": overrides["device_count"],
                "avg_amount": float(activity.get("avg_amount", normalized.amount) or normalized.amount),
                "structuring_score": 0.2,
                "is_new": overrides["account_age_days"] <= 7,
                "has_high_velocity": overrides["current_txn_count_1h"] > 15
            }
            
            risk_result = self.risk_scorer.score_transaction(
                current_txn_count_1h=overrides["current_txn_count_1h"],
                unique_counterparties=overrides["unique_counterparties"],
                locations_24h=[],
                time_gaps_minutes=[],
                amounts=overrides["amounts"],
                account_age_days=overrides["account_age_days"],
                device_count=overrides["device_count"],
                target_countries=overrides["target_countries"],
            )
            self._append_trace(trace_steps, "rule_score", t0)
            
            # Step 5: GNN Detection
            t0 = time.perf_counter()
            mule_result = self.gnn_detector.detect_mule_ring(
                anchor_account=source_account_data,
                connected_accounts=connected_accounts,
                transaction_graph={}
            )
            self._append_trace(trace_steps, "gnn_score", t0)
            
            # Step 6: Combined decision
            rule_score = float(risk_result.overall_score)
            ml_score = float(mule_result["mule_probability"])
            combined_risk = (self.ml_weight * ml_score) + (self.rule_weight * rule_score)

            # Deterministic hackathon demo behavior when explicit demo profile is provided.
            if demo_profile == "ALLOW":
                combined_risk = min(combined_risk, 0.20)
            elif demo_profile == "FLAG":
                combined_risk = max(0.45, min(combined_risk, 0.65))
            elif demo_profile == "BLOCK":
                combined_risk = max(0.82, combined_risk)
            
            t0 = time.perf_counter()
            if combined_risk >= 0.70:
                decision = "BLOCK"
                self.stats["blocked"] += 1
            elif combined_risk >= 0.35:
                decision = "FLAG"
                self.stats["flagged"] += 1
            else:
                decision = "ALLOW"
                self.stats["allowed"] += 1
            self._append_trace(trace_steps, "decision", t0)

            t0 = time.perf_counter()
            fragmentation_score = self._fragmentation_score(overrides.get("amounts", []))
            nesting_score = self._nesting_score(raw_payload if isinstance(raw_payload, dict) else {}, connected_accounts)
            routing_complexity_score = self._routing_complexity_score(
                overrides.get("target_countries", []),
                overrides.get("unique_counterparties", unique_counterparties),
                connected_accounts,
            )
            sanctions_behavior_score = self._sanctions_behavior_score(
                overrides.get("target_countries", []),
                ml_score,
                float(risk_result.factor_contributions.get("velocity", 0.0)),
                routing_complexity_score,
            )
            intel_signal_score, matched_indicators, intel_match_count = self._evaluate_privacy_signals(
                normalized,
                raw_payload if isinstance(raw_payload, dict) else {},
            )
            if intel_match_count > 0:
                self.stats["intel_hits"] += intel_match_count

            pattern_signal_score = round(
                min(
                    1.0,
                    (0.30 * fragmentation_score)
                    + (0.30 * nesting_score)
                    + (0.20 * routing_complexity_score)
                    + (0.20 * sanctions_behavior_score),
                ),
                4,
            )
            enhanced_signals = {
                "fragmentation_score": fragmentation_score,
                "nesting_score": nesting_score,
                "routing_complexity_score": routing_complexity_score,
                "sanctions_behavior_score": sanctions_behavior_score,
                "intel_signal_score": intel_signal_score,
                "pattern_signal_score": pattern_signal_score,
            }
            combined_risk = min(1.0, combined_risk + (self.pattern_boost_weight * pattern_signal_score) + (0.10 * intel_signal_score))
            self._append_trace(trace_steps, "advanced_patterns", t0)

            reasons = self._top_reasons(risk_result, mule_result, enhanced_signals=enhanced_signals)
            confidence_score = self._confidence_score(
                final_risk=combined_risk,
                ml_score=ml_score,
                rule_score=rule_score,
                rule_conf=float(risk_result.confidence),
                ml_conf=float(mule_result.get("confidence", 0.5)),
            )
            model_version = mule_result.get("model_version", "unknown")
            compliance_report = self._build_compliance_report(
                transaction_id=normalized.event_id,
                trace_id=trace_id,
                decision=decision,
                risk_score=combined_risk,
                reasons=reasons,
                confidence_score=confidence_score,
                model_version=model_version,
            )
            self._append_trace(trace_steps, "reporting", t0)

            total_latency_ms = round((time.perf_counter() - pipeline_started) * 1000.0, 2)
            
            result = {
                "status": "SUCCESS",
                "transaction_id": normalized.event_id,
                "trace_id": trace_id,
                "decision": decision,
                "risk_score": round(combined_risk, 4),
                "score_breakdown": {
                    "ml_score": round(ml_score, 4),
                    "rule_score": round(rule_score, 4),
                    "final_risk": round(combined_risk, 4),
                    "ml_impact": round(combined_risk - rule_score, 4),
                    "weights": {
                        "ml_weight": round(self.ml_weight, 2),
                        "rule_weight": round(self.rule_weight, 2),
                    },
                },
                "ml_score": round(ml_score, 4),
                "rule_score": round(rule_score, 4),
                "confidence": confidence_score,
                "confidence_score": confidence_score,
                "duplicate": is_duplicate,
                "degraded_mode": degraded_mode,
                "gnn_model_version": model_version,
                "risk_factors": {
                    "velocity": risk_result.factor_contributions.get("velocity", 0),
                    "account_diversity": risk_result.factor_contributions.get("account_diversity", 0),
                    "geographic_inconsistency": risk_result.factor_contributions.get("geographic_inconsistency", 0),
                    "structuring": risk_result.factor_contributions.get("structuring_pattern", 0),
                    "account_age": risk_result.factor_contributions.get("account_age", 0),
                    "device_count": risk_result.factor_contributions.get("device_count", 0),
                    "mule_probability": ml_score,
                    "fragmentation_score": fragmentation_score,
                    "nesting_score": nesting_score,
                    "routing_complexity_score": routing_complexity_score,
                    "sanctions_behavior_score": sanctions_behavior_score,
                    "intel_signal_score": intel_signal_score,
                    "pattern_signal_score": pattern_signal_score,
                },
                "explainability": {
                    "reasons": reasons,
                    "top_features": {
                        "current_txn_count_1h": overrides["current_txn_count_1h"],
                        "unique_counterparties": overrides["unique_counterparties"],
                        "device_count": overrides["device_count"],
                        "target_countries": overrides["target_countries"],
                        "intel_matches": matched_indicators,
                    },
                },
                "privacy_safe_intelligence": {
                    "matched_indicator_types": matched_indicators,
                    "match_count": intel_match_count,
                    "intel_signal_score": intel_signal_score,
                },
                "reasons": reasons,
                "model": {
                    "name": "GraphSAGEHybrid",
                    "version": model_version,
                },
                "compliance_report": compliance_report,
                "trace": trace_steps,
                "latency_ms": total_latency_ms,
                "timestamp": self._utc_now_iso(),
            }
            
            logger.info(
                json.dumps(
                    {
                        "event": "transaction_scored",
                        "trace_id": trace_id,
                        "transaction_id": normalized.event_id,
                        "decision": decision,
                        "risk_score": round(combined_risk, 4),
                        "ml_score": round(ml_score, 4),
                        "rule_score": round(rule_score, 4),
                        "latency_ms": total_latency_ms,
                        "degraded_mode": degraded_mode,
                        "duplicate": is_duplicate,
                    }
                )
            )
            return result
            
        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            return {"status": "ERROR", "reason": str(e)}
    
    def process_batch(self, events: list) -> list:
        """Process multiple events, return results"""
        results = []
        for event in events:
            result = self.process_event(event)
            results.append(result)
        return results
    
    def get_stats(self) -> Dict:
        """Return processing statistics"""
        return self.stats

    def close(self) -> None:
        """Release resources held by the orchestrator."""
        neo4j_client = getattr(self.graph_builder, "neo4j_client", None)
        if neo4j_client and hasattr(neo4j_client, "close"):
            neo4j_client.close()


def load_events_from_file(file_path: str) -> List[Dict]:
    """Load transaction events from a JSON file."""
    with open(file_path, "r", encoding="utf-8") as fp:
        data = json.load(fp)
    if not isinstance(data, list):
        raise ValueError("Transaction data file must contain a JSON array")
    return data


# Example usage
if __name__ == "__main__":
    orchestrator = MuleDetectionOrchestrator()

    transactions_file = os.getenv("TRANSACTIONS_FILE", "data/real_transactions.json")
    if os.path.exists(transactions_file):
        events = load_events_from_file(transactions_file)
        logger.info(f"Loaded {len(events)} real transaction events from {transactions_file}")
    else:
        logger.warning(f"Transaction file not found: {transactions_file}. Using fallback sample events.")
        events = [
            {
                "channel": "MOBILE",
                "raw_event": {
                    "event_id": "MOB_REAL_001",
                    "user_id": "MOBILE_USER_011",
                    "transfer_to_wallet": "wallet_alpha_882",
                    "transfer_amount": 2450.25,
                    "transfer_time": "2026-03-23T09:35:00Z",
                    "device_fingerprint": "fp_dev_9f3a1",
                    "ip_address": "49.36.112.10",
                    "location": {"latitude": 12.9716, "longitude": 77.5946, "country": "IN"}
                }
            },
            {
                "channel": "ATM",
                "raw_event": {
                    "event_id": "ATM_REAL_001",
                    "terminal_id": "ATM_BLR_044",
                    "card_number_last4": "8841",
                    "withdrawal_amount": 1900,
                    "withdrawal_time": "2026-03-23T09:41:00Z",
                    "location": {"latitude": 12.9352, "longitude": 77.6245, "country": "IN"}
                }
            },
            {
                "channel": "UPI",
                "raw_event": {
                    "event_id": "UPI_REAL_001",
                    "payer_vpa": "user011@okaxis",
                    "payee_vpa": "merchant728@icici",
                    "amount": 4999,
                    "transaction_time": "2026-03-23T09:43:30Z",
                    "status": "SUCCESS"
                }
            }
        ]
    
    # Process batch
    results = orchestrator.process_batch(events)
    
    # Print results
    print("Pipeline Results:")
    print(json.dumps(results, indent=2, default=str))
    print(f"\nStatistics: {orchestrator.get_stats()}")
