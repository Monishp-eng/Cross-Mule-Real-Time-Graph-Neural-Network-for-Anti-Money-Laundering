"""
Data Ingestion Service - Normalizes events from multiple channels
Converts disparate sources (Mobile, Web, ATM, UPI) to standard schema
"""

import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Channel(str, Enum):
    """Supported payment channels"""
    MOBILE = "MOBILE"
    WEB = "WEB"
    ATM = "ATM"
    UPI = "UPI"
    BANK = "BANK"


class AccountType(str, Enum):
    """Types of payment accounts"""
    WALLET = "WALLET"
    CARD = "CARD"
    BANK_ACCOUNT = "BANK_ACCOUNT"
    CRYPTO_WALLET = "CRYPTO_WALLET"


@dataclass
class Location:
    """Geographic information"""
    latitude: float
    longitude: float
    country: str
    city: Optional[str] = None
    
    def to_dict(self):
        return asdict(self)


@dataclass
class Account:
    """Normalized account representation"""
    account_id: str
    channel: Channel
    account_type: AccountType
    provider: str
    

@dataclass
class NormalizedTransaction:
    """Standard transaction schema across all channels"""
    event_id: str
    timestamp: datetime
    source_account_id: str
    dest_account_id: str
    amount: float
    currency: str
    channel: Channel
    device_id: str
    ip_address_hash: str
    location: Location
    status: str = "COMPLETED"
    
    def to_dict(self):
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "source_account_id": self.source_account_id,
            "dest_account_id": self.dest_account_id,
            "amount": self.amount,
            "currency": self.currency,
            "channel": self.channel.value,
            "device_id": self.device_id,
            "ip_address_hash": self.ip_address_hash,
            "location": self.location.to_dict(),
            "status": self.status
        }


class DataNormalizer:
    """
    Converts events from different channels to standard schema.
    
    Handles:
    - Mobile App events
    - Web portal events
    - ATM transactions
    - UPI transfers
    - Bank API events
    
    Performs:
    - PII hashing (phone, email, document IDs)
    - Data validation
    - Duplicate detection
    - Enrichment
    """
    
    def __init__(self):
        self.pii_cache = {}  # For consistent hashing
        
    def hash_pii(self, value: str) -> str:
        """Hash PII values consistently (same input → same hash)"""
        if not value:
            return None
        if value in self.pii_cache:
            return self.pii_cache[value]
        hash_val = hashlib.sha256(value.encode()).hexdigest()
        self.pii_cache[value] = hash_val
        return hash_val
    
    def normalize_mobile_event(self, raw_event: Dict) -> Optional[NormalizedTransaction]:
        """
        Normalize Mobile App event
        
        Example raw event:
        {
            "user_id": "MOBILE_USER_001",
            "app_version": "2.1.0",
            "transfer_to_wallet": "wallet_id_xyz",
            "transfer_amount": 1000,
            "transfer_time": "2024-03-23T14:35:00Z",
            "device_fingerprint": "device123",
            "ip_address": "192.168.1.1",
            "location": {"latitude": 40.7128, "longitude": -74.0060}
        }
        """
        try:
            timestamp = datetime.fromisoformat(
                raw_event["transfer_time"].replace("Z", "+00:00")
            )
            
            # Validate required fields
            if not all(k in raw_event for k in ["transfer_to_wallet", "transfer_amount"]):
                logger.warning(f"Missing required fields in mobile event: {raw_event}")
                return None
            
            normalized = NormalizedTransaction(
                event_id=f"MOB_{raw_event.get('event_id', 'unknown')}",
                timestamp=timestamp,
                source_account_id=f"ACC_MOBILE_{raw_event['user_id']}",
                dest_account_id=f"ACC_WALLET_{raw_event['transfer_to_wallet']}",
                amount=float(raw_event["transfer_amount"]),
                currency="USD",  # Assume USD for now
                channel=Channel.MOBILE,
                device_id=self.hash_pii(raw_event.get("device_fingerprint", "")),
                ip_address_hash=self.hash_pii(raw_event.get("ip_address", "")),
                location=Location(
                    latitude=raw_event["location"]["latitude"],
                    longitude=raw_event["location"]["longitude"],
                    country=raw_event["location"].get("country", "US")
                )
            )
            
            logger.info(f"Normalized mobile event: {normalized.event_id}")
            return normalized
            
        except KeyError as e:
            logger.error(f"Missing required field in mobile event: {e}")
            return None
        except Exception as e:
            logger.error(f"Error normalizing mobile event: {e}")
            return None
    
    def normalize_atm_event(self, raw_event: Dict) -> Optional[NormalizedTransaction]:
        """
        Normalize ATM withdrawal event
        
        Example raw event:
        {
            "terminal_id": "ATM_NYC_001",
            "card_number_last4": "1234",
            "withdrawal_amount": 500,
            "withdrawal_time": "2024-03-23T14:37:00Z",
            "location": {"latitude": 40.7201, "longitude": -74.0065, "city": "NYC"}
        }
        """
        try:
            timestamp = datetime.fromisoformat(
                raw_event["withdrawal_time"].replace("Z", "+00:00")
            )
            
            card_hash = self.hash_pii(raw_event.get("card_number_last4", ""))
            
            normalized = NormalizedTransaction(
                event_id=f"ATM_{raw_event.get('event_id', 'unknown')}",
                timestamp=timestamp,
                source_account_id=f"ACC_DEBIT_{card_hash[:10]}",
                dest_account_id=f"ACC_CASH_{raw_event['terminal_id']}",
                amount=float(raw_event["withdrawal_amount"]),
                currency="USD",
                channel=Channel.ATM,
                device_id=raw_event["terminal_id"],  # ATM terminal is "device"
                ip_address_hash="ATM_NETWORK",
                location=Location(
                    latitude=raw_event["location"]["latitude"],
                    longitude=raw_event["location"]["longitude"],
                    country=raw_event["location"].get("country", "US"),
                    city=raw_event["location"].get("city")
                )
            )
            
            logger.info(f"Normalized ATM event: {normalized.event_id}")
            return normalized
            
        except Exception as e:
            logger.error(f"Error normalizing ATM event: {e}")
            return None
    
    def normalize_upi_event(self, raw_event: Dict) -> Optional[NormalizedTransaction]:
        """
        Normalize UPI transfer event
        
        Example raw event:
        {
            "upi_id": "user@paytm",
            "recipient_upi": "merchant@okhdfcbank",
            "txn_amount": 2000,
            "txn_ref_id": "220399001089",
            "timestamp": "2024-03-23T14:35:00Z"
        }
        """
        try:
            timestamp = datetime.fromisoformat(
                raw_event["timestamp"].replace("Z", "+00:00")
            )
            
            normalized = NormalizedTransaction(
                event_id=f"UPI_{raw_event['txn_ref_id']}",
                timestamp=timestamp,
                source_account_id=f"ACC_UPI_{self.hash_pii(raw_event['upi_id'])}",
                dest_account_id=f"ACC_UPI_{self.hash_pii(raw_event['recipient_upi'])}",
                amount=float(raw_event["txn_amount"]),
                currency="INR",
                channel=Channel.UPI,
                device_id="UPI_NETWORK",
                ip_address_hash="UPI_NETWORK",
                location=Location(
                    latitude=0.0,
                    longitude=0.0,
                    country="IN"
                )
            )
            
            logger.info(f"Normalized UPI event: {normalized.event_id}")
            return normalized
            
        except Exception as e:
            logger.error(f"Error normalizing UPI event: {e}")
            return None

    def normalize_web_event(self, raw_event: Dict) -> Optional[NormalizedTransaction]:
        """
        Normalize Web banking transfer event.

        Example raw event:
        {
            "session_id": "WEB_SESS_001",
            "user_id": "WEB_USER_001",
            "beneficiary_account": "ACC_12345",
            "transfer_amount": 1500,
            "transfer_time": "2024-03-23T14:35:00Z",
            "ip_address": "203.0.113.45",
            "browser_fingerprint": "br_fp_001",
            "location": {"latitude": 51.5074, "longitude": -0.1278, "country": "UK"}
        }
        """
        try:
            timestamp = datetime.fromisoformat(
                raw_event["transfer_time"].replace("Z", "+00:00")
            )

            if not all(k in raw_event for k in ["user_id", "beneficiary_account", "transfer_amount"]):
                logger.warning(f"Missing required fields in web event: {raw_event}")
                return None

            browser_or_session = raw_event.get("browser_fingerprint") or raw_event.get("session_id", "")

            normalized = NormalizedTransaction(
                event_id=f"WEB_{raw_event.get('event_id', raw_event.get('session_id', 'unknown'))}",
                timestamp=timestamp,
                source_account_id=f"ACC_WEB_{raw_event['user_id']}",
                dest_account_id=f"ACC_BANK_{raw_event['beneficiary_account']}",
                amount=float(raw_event["transfer_amount"]),
                currency=raw_event.get("currency", "USD"),
                channel=Channel.WEB,
                device_id=self.hash_pii(browser_or_session),
                ip_address_hash=self.hash_pii(raw_event.get("ip_address", "")),
                location=Location(
                    latitude=raw_event["location"]["latitude"],
                    longitude=raw_event["location"]["longitude"],
                    country=raw_event["location"].get("country", "US"),
                    city=raw_event["location"].get("city")
                )
            )

            logger.info(f"Normalized web event: {normalized.event_id}")
            return normalized

        except Exception as e:
            logger.error(f"Error normalizing web event: {e}")
            return None
    
    def normalize_event(self, event: Dict) -> Optional[NormalizedTransaction]:
        """
        Main entry point. Routes to appropriate channel handler.
        """
        try:
            channel_str = event.get("channel", "").upper()
            
            if channel_str == "MOBILE":
                return self.normalize_mobile_event(event.get("raw_event", {}))
            elif channel_str == "WEB":
                return self.normalize_web_event(event.get("raw_event", {}))
            elif channel_str == "ATM":
                return self.normalize_atm_event(event.get("raw_event", {}))
            elif channel_str == "UPI":
                return self.normalize_upi_event(event.get("raw_event", {}))
            else:
                logger.warning(f"Unknown channel: {channel_str}")
                return None
                
        except Exception as e:
            logger.error(f"Error normalizing event: {e}")
            return None


class DataQualityValidator:
    """Validates normalized events for quality"""
    
    @staticmethod
    def validate(txn: NormalizedTransaction) -> tuple[bool, Optional[str]]:
        """
        Validate transaction data quality
        
        Returns: (is_valid, error_message)
        """
        # Check required fields
        if not txn.source_account_id or not txn.dest_account_id:
            return False, "Missing account IDs"
        
        # Check amount
        if txn.amount <= 0 or txn.amount > 1_000_000:
            return False, f"Invalid amount: {txn.amount}"
        
        # Check timestamp while handling both naive and timezone-aware datetimes.
        now = datetime.now(timezone.utc) if txn.timestamp.tzinfo else datetime.now()
        if txn.timestamp > now:
            return False, "Future timestamp"
        
        # Check location validity
        if not (-90 <= txn.location.latitude <= 90):
            return False, "Invalid latitude"
        if not (-180 <= txn.location.longitude <= 180):
            return False, "Invalid longitude"
        
        return True, None


# Example usage
if __name__ == "__main__":
    normalizer = DataNormalizer()
    validator = DataQualityValidator()
    
    # Example mobile event
    mobile_event = {
        "channel": "MOBILE",
        "raw_event": {
            "user_id": "USER_001",
            "transfer_to_wallet": "wallet_xyz",
            "transfer_amount": 1000,
            "transfer_time": "2024-03-23T14:35:00Z",
            "device_fingerprint": "fp123",
            "ip_address": "192.168.1.1",
            "location": {"latitude": 40.7128, "longitude": -74.0060, "country": "US"}
        }
    }
    
    normalized = normalizer.normalize_event(mobile_event)
    if normalized:
        is_valid, error = validator.validate(normalized)
        if is_valid:
            print("✓ Valid transaction:")
            print(json.dumps(normalized.to_dict(), indent=2, default=str))
        else:
            print(f"✗ Invalid: {error}")
