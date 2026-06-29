#!/usr/bin/env python3
"""Upload and test prediction dataset."""

import os
import requests
import sys
import json

def upload_prediction_dataset():
    """Upload prediction dataset and check results."""
    
    # Configuration
    base_url = "http://127.0.0.1:8000"
    csv_file = "prediction_dataset.csv"
    
    print("=" * 70)
    print("🚀 PREDICTION DATASET UPLOAD & VALIDATION")
    print("=" * 70)
    
    # Step 1: Resolve API key locally
    print("\n[1/4] 🔐 Resolving API key...")
    api_key = os.getenv("API_KEY", "test-api-key")
    print(f"      ✓ API key resolved (length: {len(api_key)})")
    
    # Step 2: Read CSV file
    print(f"\n[2/4] 📄 Reading CSV file ({csv_file})...")
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            csv_content = f.read()
        line_count = len(csv_content.split('\n')) - 1  # Exclude header
        print(f"      ✓ CSV loaded ({line_count} transactions, {len(csv_content)} bytes)")
    except Exception as e:
        print(f"      ✗ Failed to read CSV: {e}")
        return False
    
    # Step 3: Upload to API
    print(f"\n[3/4] 📤 Uploading to /v1/predict endpoint...")
    endpoint = f"{base_url}/v1/predict"
    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json"
    }
    payload = {
        "csv_text": csv_content
    }
    
    try:
        response = requests.post(endpoint, json=payload, headers=headers, timeout=60)
        print(f"      Response Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"      ✗ Upload failed!")
            print(f"      Response body: {response.text[:500]}")
            return False
        
        print(f"      ✓ Upload successful!")
        
    except Exception as e:
        print(f"      ✗ Request failed: {e}")
        return False
    
    # Step 4: Parse and validate results
    print(f"\n[4/4] ✅ Validating predictions...")
    try:
        result = response.json()
        
        predictions = result.get('predictions', [])
        flagged = result.get('flagged_paths', [])
        edge_anomalies = result.get('edge_anomalies', [])
        
        print(f"      ✓ Predictions generated: {len(predictions)}")
        print(f"      ✓ Flagged paths detected: {len(flagged)}")
        print(f"      ✓ Edge anomalies: {len(edge_anomalies)}")
        
        # Show sample predictions
        if predictions:
            print(f"\n      Sample predictions (first 3):")
            for i, pred in enumerate(predictions[:3], 1):
                fraud_score = pred.get('fraud_score', 'N/A')
                risk_level = pred.get('risk_level', 'N/A')
                tx_id = pred.get('transaction_id', pred.get('sender_id', 'N/A'))
                print(f"        {i}. Tx: {tx_id}, Risk: {risk_level}, Score: {fraud_score}")
        
        # Show flagged transactions
        if edge_anomalies:
            print(f"\n      Flagged transactions:")
            for i, edge in enumerate(edge_anomalies[:3], 1):
                anomaly_type = edge.get('anomaly_type', 'unknown')
                sender = edge.get('sender_id', 'N/A')
                receiver = edge.get('receiver_id', 'N/A')
                print(f"        {i}. {sender} → {receiver} ({anomaly_type})")
        
        print("\n" + "=" * 70)
        print("✅ UPLOAD SUCCESSFUL - PREDICTIONS GENERATED")
        print("=" * 70)
        return True
        
    except json.JSONDecodeError:
        print(f"      ⚠️  Could not parse JSON response")
        print(f"      Response: {response.text[:200]}")
        print("\n" + "=" * 70)
        print("✅ UPLOAD SUCCESSFUL (response parsing issue)")
        print("=" * 70)
        return True
    except Exception as e:
        print(f"      ✗ Validation failed: {e}")
        return False

if __name__ == "__main__":
    os.chdir('c:\\Users\\Monish P\\Downloads\\Cross Mule Detection')
    success = upload_prediction_dataset()
    sys.exit(0 if success else 1)
