#!/usr/bin/env python3
"""Convert team-provided transaction CSV into Cross Mule Detection upload format.

Expected team fields (case-insensitive aliases supported):
- Narration
- Pincode
- Mobile Number
- Name
- Account Number
- Account Product Type

Output schema (required by backend upload flow):
transaction_id,sender_id,receiver_id,amount,timestamp,transaction_type,device_id,latitude,longitude,country

Optional labels also passed-through when present:
is_fraud,status,fraud_reason,currency
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List


REQUIRED_OUTPUT_COLUMNS: List[str] = [
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
]

OPTIONAL_OUTPUT_COLUMNS: List[str] = [
    "is_fraud",
    "status",
    "fraud_reason",
    "currency",
    "narration",
    "pincode",
    "mobile_number",
    "name",
    "account_number",
    "account_product_type",
]


ALIASES: Dict[str, Iterable[str]] = {
    "transaction_id": ("transaction_id", "txn_id", "txn_ref_id", "event_id"),
    "sender_id": ("sender_id", "account_number", "from_account", "source_account", "account no", "account"),
    "receiver_id": ("receiver_id", "beneficiary_account", "to_account", "dest_account", "counterparty_account"),
    "amount": ("amount", "txn_amount", "transfer_amount", "withdrawal_amount"),
    "timestamp": ("timestamp", "transaction_time", "time", "transfer_time", "withdrawal_time"),
    "transaction_type": ("transaction_type", "channel", "txn_channel"),
    "device_id": ("device_id", "mobile_number", "mobile no", "phone", "device", "device_fingerprint"),
    "latitude": ("latitude", "lat"),
    "longitude": ("longitude", "lon", "lng"),
    "country": ("country", "country_code"),
    "is_fraud": ("is_fraud",),
    "status": ("status",),
    "fraud_reason": ("fraud_reason", "reason"),
    "currency": ("currency",),
    "narration": ("narration", "description", "remarks"),
    "pincode": ("pincode", "pin_code", "zip", "postal_code"),
    "mobile_number": ("mobile_number", "mobile", "mobile no", "phone", "phone_number"),
    "name": ("name", "customer_name", "account_name"),
    "account_number": ("account_number", "account", "account no"),
    "account_product_type": ("account_product_type", "account_product", "product_type", "account type"),
}

VALID_TYPES = {"MOBILE", "WEB", "ATM", "UPI"}


def norm(key: str) -> str:
    return " ".join(str(key).strip().lower().replace("_", " ").split())


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def pick(row: Dict[str, str], target: str) -> str:
    aliases = ALIASES.get(target, (target,))
    for candidate in aliases:
        value = row.get(norm(candidate), "")
        if str(value).strip() != "":
            return str(value).strip()
    return ""


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert team CSV to CMD upload schema")
    parser.add_argument("--input", required=True, help="Path to source CSV")
    parser.add_argument("--output", required=True, help="Path to converted CSV")
    parser.add_argument("--default-receiver", default="UNKNOWN_RECEIVER", help="Fallback receiver_id")
    parser.add_argument("--default-country", default="IN", help="Fallback country code")
    parser.add_argument("--default-lat", default="12.9716", help="Fallback latitude")
    parser.add_argument("--default-lon", default="77.5946", help="Fallback longitude")
    parser.add_argument("--default-type", default="MOBILE", choices=sorted(VALID_TYPES), help="Fallback transaction_type")
    parser.add_argument("--default-currency", default="INR", help="Fallback currency")
    args = parser.parse_args()

    in_path = Path(args.input)
    out_path = Path(args.output)

    if not in_path.exists():
        raise FileNotFoundError(f"Input file not found: {in_path}")

    with in_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError("Input CSV has no header")

        normalized_rows: List[Dict[str, str]] = []
        for idx, raw in enumerate(reader, start=1):
            row = {norm(k): (v if v is not None else "") for k, v in raw.items()}

            tx_id = pick(row, "transaction_id") or f"TXN_{idx}"
            sender_id = pick(row, "sender_id") or f"ACC_{idx}"
            receiver_id = pick(row, "receiver_id") or args.default_receiver
            amount = pick(row, "amount") or "0"
            timestamp = pick(row, "timestamp") or iso_now()
            tx_type = (pick(row, "transaction_type") or args.default_type).upper()
            if tx_type not in VALID_TYPES:
                tx_type = args.default_type

            device_id = pick(row, "device_id") or f"DEV_{idx}"
            latitude = pick(row, "latitude") or args.default_lat
            longitude = pick(row, "longitude") or args.default_lon
            country = (pick(row, "country") or args.default_country).upper()

            normalized: Dict[str, str] = {
                "transaction_id": tx_id,
                "sender_id": sender_id,
                "receiver_id": receiver_id,
                "amount": amount,
                "timestamp": timestamp,
                "transaction_type": tx_type,
                "device_id": device_id,
                "latitude": latitude,
                "longitude": longitude,
                "country": country,
                "is_fraud": pick(row, "is_fraud"),
                "status": pick(row, "status"),
                "fraud_reason": pick(row, "fraud_reason"),
                "currency": pick(row, "currency") or args.default_currency,
                "narration": pick(row, "narration"),
                "pincode": pick(row, "pincode"),
                "mobile_number": pick(row, "mobile_number"),
                "name": pick(row, "name"),
                "account_number": pick(row, "account_number") or sender_id,
                "account_product_type": pick(row, "account_product_type"),
            }
            normalized_rows.append(normalized)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = REQUIRED_OUTPUT_COLUMNS + OPTIONAL_OUTPUT_COLUMNS
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(normalized_rows)

    print(f"Converted {len(normalized_rows)} rows -> {out_path}")


if __name__ == "__main__":
    main()
