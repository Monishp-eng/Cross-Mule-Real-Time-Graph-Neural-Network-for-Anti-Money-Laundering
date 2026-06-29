"""
Risk Scoring Engine - Computes composite risk scores from transaction features
"""

from dataclasses import dataclass
from typing import Dict, Optional
import math
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class RiskFactors:
    """Individual risk scoring components"""
    velocity_score: float           # Transaction frequency anomaly
    account_diversity: float        # # of linked accounts
    geographic_inconsistency: float # Possible geography
    structuring_pattern: float      # Amount fragmentation
    account_age: float              # Fresh accounts
    device_count: float             # Device diversity
    jurisdiction_risk: float        # Target country risk


@dataclass
class RiskResult:
    """Final risk score with breakdown"""
    overall_score: float            # 0-1
    confidence: float               # 0-1 confidence in score
    category: str                   # LOW, MEDIUM, HIGH
    factors: RiskFactors
    factor_contributions: Dict[str, float]
    recommendation: str             # ALLOW, FLAG, BLOCK, ESCALATE


class RiskScorer:
    """
    Computes transaction and user risk scores using multiple factors.
    
    Each factor is scored 0-1, then combined with weights to produce
    overall risk score.
    
    Risk Categories:
    - LOW: 0.0-0.3 → ALLOW
    - MEDIUM: 0.3-0.7 → FLAG
    - HIGH: 0.7-1.0 → BLOCK
    """
    
    # Reference baselines (would be computed from historical data)
    BASELINE_HOURLY_TXN_COUNT = 5
    BASELINE_ACCOUNT_COUNT = 3
    JURISDICTION_RISK_SCORES = {
        "US": 0.1,
        "UK": 0.1,
        "CN": 0.8,  # High risk
        "KP": 0.95, # North Korea - very high
        "IR": 0.9,  # Iran - very high
    }
    
    # Component weights (must sum to 1.0)
    WEIGHTS = {
        "velocity": 0.25,
        "account_diversity": 0.20,
        "geographic_inconsistency": 0.20,
        "structuring_pattern": 0.15,
        "account_age": 0.10,
        "device_count": 0.10
    }
    
    def __init__(self):
        # Verify weights sum to 1.0
        total_weight = sum(self.WEIGHTS.values())
        if not math.isclose(total_weight, 1.0):
            raise ValueError(f"Weights must sum to 1.0, got {total_weight}")
    
    def compute_velocity_score(
        self,
        current_txn_count_1h: int,
        baseline_txn_count: Optional[int] = None
    ) -> float:
        """
        Score based on transaction velocity.
        
        Compares current activity to user baseline.
        High velocity = higher score.
        
        Args:
            current_txn_count_1h: Transactions in last hour
            baseline_txn_count: User's typical hourly rate (default: 5)
        
        Returns: 0-1 score
        """
        if baseline_txn_count is None:
            baseline_txn_count = self.BASELINE_HOURLY_TXN_COUNT
        
        # Avoid division by zero
        if baseline_txn_count == 0:
            baseline_txn_count = 1
        
        # Ratio of current to baseline
        ratio = current_txn_count_1h / (baseline_txn_count + 0.1)
        
        # Normalize to 0-1 scale (around 18x baseline saturates at 1.0).
        # This keeps baseline traffic low-risk while making 10x baseline high-risk.
        score = min(ratio / 18.0, 1.0)
        
        logger.debug(f"Velocity: {current_txn_count_1h} txns vs {baseline_txn_count} baseline → {score:.2f}")
        return score
    
    def compute_account_diversity_score(
        self,
        unique_counterparties: int,
        baseline_diversity: Optional[int] = None
    ) -> float:
        """
        Score based on account diversity.
        
        How many different accounts is user interacting with?
        Mules interact with many accounts (outbound hubs).
        
        Args:
            unique_counterparties: # of unique accounts contacted
            baseline_diversity: User's typical diversity (default: 3)
        
        Returns: 0-1 score
        """
        if baseline_diversity is None:
            baseline_diversity = self.BASELINE_ACCOUNT_COUNT
        
        # Mule pattern: interacting with 50+ accounts
        # Normal user: 5-10 accounts
        # Score: 50 accounts / 50 cap = 1.0
        
        score = min(unique_counterparties / 50.0, 1.0)
        
        logger.debug(f"Account diversity: {unique_counterparties} accounts → {score:.2f}")
        return score
    
    def compute_geographic_inconsistency_score(
        self,
        locations_24h: list,
        time_gaps_minutes: list
    ) -> float:
        """
        Score based on geographic inconsistencies.
        
        Detects impossible geography (e.g., NYC then Tokyo in 30 mins).
        
        Args:
            locations_24h: List of (latitude, longitude, timestamp) tuples
            time_gaps_minutes: List of time differences between locations
        
        Returns: 0-1 score (1.0 = impossible geography)
        """
        if len(locations_24h) < 2:
            return 0.0
        
        # Check for impossible travel (rough check)
        # Airplane speed ~ 500 mph = 8.33 miles/minute
        # Max reasonable distance in time_gap = time_gap_min * 8.33 miles
        
        impossible_travel_detected = False
        for i in range(len(locations_24h) - 1):
            lat1, lon1, _ = locations_24h[i]
            lat2, lon2, _ = locations_24h[i + 1]
            
            # Simple distance formula (Haversine would be more accurate)
            distance_miles = math.sqrt((lat2 - lat1)**2 + (lon2 - lon1)**2) * 69
            
            time_gap_minutes = time_gaps_minutes[i]
            max_distance = time_gap_minutes * 8.33  # Airplane speed
            
            if distance_miles > max_distance:
                impossible_travel_detected = True
                logger.debug(f"Impossible travel: {distance_miles} miles in {time_gap_minutes} min")
                break
        
        score = 0.95 if impossible_travel_detected else 0.1
        
        logger.debug(f"Geographic inconsistency: {score:.2f}")
        return score
    
    def compute_structuring_score(
        self,
        amounts: list,
        threshold: float = 10000
    ) -> float:
        """
        Score based on structuring pattern.
        
        Structuring = Multiple small transfers just below threshold
        to evade detection.
        
        Args:
            amounts: List of transaction amounts
            threshold: Reporting threshold (default: $10k)
        
        Returns: 0-1 score
        """
        if not amounts:
            return 0.0
        
        # Pattern 1: many transactions concentrated just below reporting threshold.
        near_threshold = sum(1 for a in amounts if threshold * 0.8 <= a < threshold)

        # Pattern 2: repeated near-identical amounts over many transfers.
        mean_amt = sum(amounts) / len(amounts)
        variance = sum((a - mean_amt) ** 2 for a in amounts) / len(amounts)
        std_dev = math.sqrt(variance)
        coeff_var = (std_dev / mean_amt) if mean_amt > 0 else 1.0
        repeated_pattern = len(amounts) >= 8 and mean_amt > 500 and coeff_var < 0.06

        if len(amounts) >= 5 and near_threshold >= len(amounts) * 0.8:
            score = 0.88  # Classic threshold structuring
        elif repeated_pattern:
            score = 0.75  # Repeated, tightly clustered transfers
        elif len(amounts) >= 10 and near_threshold >= len(amounts) * 0.4:
            score = 0.5  # Partial structuring pattern
        else:
            score = 0.1  # Normal pattern
        
        logger.debug(f"Structuring: {len(amounts)} txns, {near_threshold} near threshold, cv={coeff_var:.3f} → {score:.2f}")
        return score
    
    def compute_account_age_score(self, account_age_days: int) -> float:
        """
        Score based on account age.
        
        Fresh accounts higher risk (typical mule pattern).
        Score decays over 30 days.
        
        Args:
            account_age_days: Days since account creation
        
        Returns: 0-1 score
        """
        # 0 days old = 1.0 (highest risk)
        # 7 days old = 0.77
        # 30 days old = 0.0 (baseline)
        
        score = max(0.0, 1.0 - (account_age_days / 30.0))
        
        logger.debug(f"Account age: {account_age_days} days → {score:.2f}")
        return score
    
    def compute_device_count_score(self, device_count: int) -> float:
        """
        Score based on device diversity.
        
        Mules use multiple devices/IPs to hide tracks.
        
        Args:
            device_count: Number of unique devices/IPs
        
        Returns: 0-1 score
        """
        # 1 device = 0.0
        # 10 devices = 1.0
        # 15+ devices = 1.0
        
        score = min(device_count / 10.0, 1.0)
        
        logger.debug(f"Device count: {device_count} → {score:.2f}")
        return score
    
    def compute_jurisdiction_risk_score(self, target_countries: list) -> float:
        """
        Score based on target countries.
        
        High-risk countries (FATF grey list, sanctioned) = higher score.
        
        Args:
            target_countries: List of ISO country codes
        
        Returns: 0-1 score (max risk across countries)
        """
        if not target_countries:
            return 0.1
        
        # Take max risk score for any country
        max_risk = max(
            self.JURISDICTION_RISK_SCORES.get(country, 0.3) 
            for country in target_countries
        )
        
        logger.debug(f"Jurisdiction risk: {target_countries} → {max_risk:.2f}")
        return max_risk
    
    def score_transaction(
        self,
        current_txn_count_1h: int,
        unique_counterparties: int,
        locations_24h: list,
        time_gaps_minutes: list,
        amounts: list,
        account_age_days: int,
        device_count: int,
        target_countries: list
    ) -> RiskResult:
        """
        Compute composite risk score.
        
        Returns: RiskResult with overall score, confidence, and breakdown
        """
        
        # Compute individual factor scores
        factors = RiskFactors(
            velocity_score=self.compute_velocity_score(current_txn_count_1h),
            account_diversity=self.compute_account_diversity_score(unique_counterparties),
            geographic_inconsistency=self.compute_geographic_inconsistency_score(locations_24h, time_gaps_minutes),
            structuring_pattern=self.compute_structuring_score(amounts),
            account_age=self.compute_account_age_score(account_age_days),
            device_count=self.compute_device_count_score(device_count),
            jurisdiction_risk=self.compute_jurisdiction_risk_score(target_countries),
        )
        
        # Weighted combination
        factor_contributions = {
            "velocity": factors.velocity_score * self.WEIGHTS["velocity"],
            "account_diversity": factors.account_diversity * self.WEIGHTS["account_diversity"],
            "geographic_inconsistency": factors.geographic_inconsistency * self.WEIGHTS["geographic_inconsistency"],
            "structuring_pattern": factors.structuring_pattern * self.WEIGHTS["structuring_pattern"],
            "account_age": factors.account_age * self.WEIGHTS["account_age"],
            "device_count": factors.device_count * self.WEIGHTS["device_count"]
        }
        
        overall_score = sum(factor_contributions.values())
        
        # Jurisdiction adjustment: keep behavioral risk dominant and use country risk as a light prior.
        jurisdiction_score = self.compute_jurisdiction_risk_score(target_countries)
        overall_score = (overall_score * 0.9) + (jurisdiction_score * 0.1)
        
        overall_score = min(overall_score, 1.0)
        
        # Determine category and recommendation
        if overall_score < 0.3:
            category = "LOW"
            recommendation = "ALLOW"
            confidence = 0.95
        elif overall_score < 0.7:
            category = "MEDIUM"
            recommendation = "FLAG"
            confidence = 0.85
        else:
            category = "HIGH"
            recommendation = "BLOCK"
            confidence = 0.90
        
        return RiskResult(
            overall_score=overall_score,
            confidence=confidence,
            category=category,
            factors=factors,
            factor_contributions=factor_contributions,
            recommendation=recommendation
        )


# Example usage
if __name__ == "__main__":
    scorer = RiskScorer()
    
    # Sample mule-like transaction
    result = scorer.score_transaction(
        current_txn_count_1h=50,
        unique_counterparties=38,
        locations_24h=[(40.7, -74.0, 0), (35.6, 139.7, 120)],  # NYC → Tokyo
        time_gaps_minutes=[120],
        amounts=[950, 980, 1000, 1050],  # Structuring pattern
        account_age_days=2,
        device_count=15,
        target_countries=["US", "CN"]
    )
    
    print(f"Overall Risk Score: {result.overall_score:.2f} ({result.category})")
    print(f"Confidence: {result.confidence:.2f}")
    print(f"Recommendation: {result.recommendation}")
    print("\nFactor Breakdown:")
    for factor, contrib in result.factor_contributions.items():
        print(f"  {factor}: {contrib:.3f}")
