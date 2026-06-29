#!/usr/bin/env python3
"""Upload prediction dataset to the Cross Mule Detection API."""

import csv
import io
import json
import sys
import requests
from typing import Optional

# Prediction dataset with all required fields
PREDICTION_DATA = [
    {
        "Narration": "UPI transfer to vendor",
        "Pincode": "560001",
        "Mobile Number": "9876543210",
        "Name": "Ravi Kumar",
        "Account Number": "ACC001",
        "Account Product Type": "SAVINGS",
        "receiver_id": "ACC090",
        "amount": 1250.00,
        "timestamp": "2026-04-05T08:00:00Z",
        "transaction_type": "UPI",
        "currency": "INR"
    },
    {
        "Narration": "NEFT outward transfer",
        "Pincode": "560001",
        "Mobile Number": "9876543210",
        "Name": "Ravi Kumar",
        "Account Number": "ACC001",
        "Account Product Type": "SAVINGS",
        "receiver_id": "ACC200",
        "amount": 9800.00,
        "timestamp": "2026-04-05T08:15:00Z",
        "transaction_type": "WEB",
        "currency": "INR"
    },
    {
        "Narration": "ATM cash withdrawal",
        "Pincode": "400001",
        "Mobile Number": "9988776655",
        "Name": "Anita Shah",
        "Account Number": "ACC300",
        "Account Product Type": "CURRENT",
        "receiver_id": "ATM001",
        "amount": 15000.00,
        "timestamp": "2026-04-05T08:30:00Z",
        "transaction_type": "ATM",
        "currency": "INR"
    },
    {
        "Narration": "Online shopping payment",
        "Pincode": "110001",
        "Mobile Number": "8765432109",
        "Name": "Priya Sharma",
        "Account Number": "ACC002",
        "Account Product Type": "SAVINGS",
        "receiver_id": "ACC091",
        "amount": 3450.00,
        "timestamp": "2026-04-05T08:45:00Z",
        "transaction_type": "WEB",
        "currency": "INR"
    },
    {
        "Narration": "Multiple rapid transfers",
        "Pincode": "560002",
        "Mobile Number": "9123456789",
        "Name": "Vikram Singh",
        "Account Number": "ACC400",
        "Account Product Type": "CURRENT",
        "receiver_id": "ACC101",
        "amount": 50000.00,
        "timestamp": "2026-04-05T09:00:00Z",
        "transaction_type": "UPI",
        "currency": "INR"
    },
    {
        "Narration": "International wire transfer",
        "Pincode": "220001",
        "Mobile Number": "7654321098",
        "Name": "Deepak Patel",
        "Account Number": "ACC500",
        "Account Product Type": "CURRENT",
        "receiver_id": "INT_ACC001",
        "amount": 75000.00,
        "timestamp": "2026-04-05T09:15:00Z",
        "transaction_type": "WEB",
        "currency": "INR"
    },
    {
        "Narration": "Bill payment utility",
        "Pincode": "560003",
        "Mobile Number": "9999888877",
        "Name": "Sneha Reddy",
        "Account Number": "ACC600",
        "Account Product Type": "SAVINGS",
        "receiver_id": "UTIL_ACC01",
        "amount": 2100.00,
        "timestamp": "2026-04-05T09:30:00Z",
        "transaction_type": "UPI",
        "currency": "INR"
    },
    {
        "Narration": "Cash deposit at branch",
        "Pincode": "400002",
        "Mobile Number": "8888777766",
        "Name": "Rajesh Gupta",
        "Account Number": "ACC700",
        "Account Product Type": "SAVINGS",
        "receiver_id": "ACC102",
        "amount": 25000.00,
        "timestamp": "2026-04-05T09:45:00Z",
        "transaction_type": "ATM",
        "currency": "INR"
    },
    {
        "Narration": "Cross-border payment",
        "Pincode": "110002",
        "Mobile Number": "7777666655",
        "Name": "Neha Kapoor",
        "Account Number": "ACC800",
        "Account Product Type": "CURRENT",
        "receiver_id": "INTL_02",
        "amount": 120000.00,
        "timestamp": "2026-04-05T10:00:00Z",
        "transaction_type": "WEB",
        "currency": "INR"
    },
    {
        "Narration": "High-value mobile transfer",
        "Pincode": "560004",
        "Mobile Number": "6666555544",
        "Name": "Amit Kumar",
        "Account Number": "ACC900",
        "Account Product Type": "SAVINGS",
        "receiver_id": "ACC103",
        "amount": 500000.00,
        "timestamp": "2026-04-05T10:15:00Z",
        "transaction_type": "MOBILE",
        "currency": "INR"
    },
    {
        "Narration": "Regular vendor payment",
        "Pincode": "220002",
        "Mobile Number": "5555444433",
        "Name": "Sanjana Das",
        "Account Number": "ACC010",
        "Account Product Type": "CURRENT",
        "receiver_id": "ACC104",
        "amount": 8500.00,
        "timestamp": "2026-04-05T10:30:00Z",
        "transaction_type": "UPI",
        "currency": "INR"
    },
    {
        "Narration": "ATM bulk withdrawal",
        "Pincode": "400003",
        "Mobile Number": "4444333322",
        "Name": "Mahesh Verma",
        "Account Number": "ACC020",
        "Account Product Type": "SAVINGS",
        "receiver_id": "ATM002",
        "amount": 45000.00,
        "timestamp": "2026-04-05T10:45:00Z",
        "transaction_type": "ATM",
        "currency": "INR"
    },
    {
        "Narration": "Same-day multiple payments",
        "Pincode": "110003",
        "Mobile Number": "3333222211",
        "Name": "Priyanka Singh",
        "Account Number": "ACC030",
        "Account Product Type": "CURRENT",
        "receiver_id": "ACC105",
        "amount": 5600.00,
        "timestamp": "2026-04-05T11:00:00Z",
        "transaction_type": "WEB",
        "currency": "INR"
    },
    {
        "Narration": "Suspicious chained transfer",
        "Pincode": "560005",
        "Mobile Number": "2222111100",
        "Name": "Karan Malhotra",
        "Account Number": "ACC040",
        "Account Product Type": "SAVINGS",
        "receiver_id": "ACC106",
        "amount": 80000.00,
        "timestamp": "2026-04-05T11:15:00Z",
        "transaction_type": "UPI",
        "currency": "INR"
    },
    {
        "Narration": "Peer-to-peer money transfer",
        "Pincode": "400004",
        "Mobile Number": "1111000099",
        "Name": "Divya Nair",
        "Account Number": "ACC050",
        "Account Product Type": "SAVINGS",
        "receiver_id": "ACC107",
        "amount": 12000.00,
        "timestamp": "2026-04-05T11:30:00Z",
        "transaction_type": "MOBILE",
        "currency": "INR"
    },
    {
        "Narration": "Regular salary deposit",
        "Pincode": "560006",
        "Mobile Number": "9876543209",
        "Name": "Vishnu Reddy",
        "Account Number": "ACC111",
        "Account Product Type": "SAVINGS",
        "receiver_id": "ACC200",
        "amount": 35000.00,
        "timestamp": "2026-04-05T11:45:00Z",
        "transaction_type": "WEB",
        "currency": "INR"
    },
    {
        "Narration": "Mobile top-up payment",
        "Pincode": "400005",
        "Mobile Number": "8765432198",
        "Name": "Sharika Desai",
        "Account Number": "ACC121",
        "Account Product Type": "CURRENT",
        "receiver_id": "MOBILE_OP",
        "amount": 399.00,
        "timestamp": "2026-04-05T12:00:00Z",
        "transaction_type": "UPI",
        "currency": "INR"
    },
    {
        "Narration": "Insurance premium payment",
        "Pincode": "220003",
        "Mobile Number": "7654321087",
        "Name": "Arjun Nair",
        "Account Number": "ACC131",
        "Account Product Type": "SAVINGS",
        "receiver_id": "INS_ACC01",
        "amount": 5000.00,
        "timestamp": "2026-04-05T12:15:00Z",
        "transaction_type": "WEB",
        "currency": "INR"
    }
]

def upload_transactions(base_url: str, api_key: str) -> bool:
    """Upload transactions via CSV prediction endpoint."""
    endpoint = f"{base_url}/v1/predict"
    
    print(f"📤 Uploading {len(PREDICTION_DATA)} prediction transactions...")
    print(f"   Endpoint: {endpoint}")
    
    # Convert to CSV format
    csv_content = _convert_to_csv(PREDICTION_DATA)
    
    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json"
    }
    
    payload = {
        "csv_text": csv_content
    }
    
    print(f"   CSV Size: {len(csv_content)} bytes")
    print(f"   Sample CSV (first 200 chars):\n{csv_content[:200]}\n")
    
    try:
        response = requests.post(endpoint, json=payload, headers=headers, timeout=60)
        
        print(f"\n📊 Response Status: {response.status_code}")
        
        if response.status_code in [200, 201, 202]:
            try:
                result = response.json()
                print(f"   Predictions Generated: {len(result.get('predictions', []))} records")
                print(f"   Flagged Transactions: {len(result.get('flagged_paths', []))} paths")
                print("\n✅ Prediction upload successful!")
                return True
            except json.JSONDecodeError:
                print(f"   Response: {response.text[:300]}")
                print("\n✅ Prediction upload successful!")
                return True
        else:
            print(f"   Error Response: {response.text[:300]}")
            print(f"\n❌ Upload failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"\n❌ Error uploading transactions: {e}")
        import traceback
        traceback.print_exc()
        return False

def _convert_to_csv(data: list) -> str:
    """Convert list of dicts to CSV string."""
    if not data:
        return ""
    
    import io
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=data[0].keys())
    writer.writeheader()
    writer.writerows(data)
    return output.getvalue()

def main():
    """Main entry point."""
    import argparse
    import os
    
    parser = argparse.ArgumentParser(description="Upload prediction dataset to Cross Mule Detection API")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="API base URL")
    parser.add_argument("--api-key", help="API key for authentication")
    
    args = parser.parse_args()
    
    # Resolve API key
    api_key = args.api_key or os.getenv("API_KEY")
    
    if not api_key:
        api_key = "test-api-key"
        print("⚠️  No API key provided, using test key")
    
    print("=" * 60)
    print("🔍 PREDICTION DATASET UPLOAD")
    print("=" * 60)
    print(f"API Base URL: {args.base_url}")
    print(f"API Key: {'*' * (len(api_key) - 4) + api_key[-4:] if len(api_key) > 4 else '****'}")
    print("=" * 60 + "\n")
    
    success = upload_transactions(args.base_url, api_key)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
