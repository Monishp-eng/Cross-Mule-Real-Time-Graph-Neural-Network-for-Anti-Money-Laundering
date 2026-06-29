import os
import csv
import json
import requests
import random
from datetime import datetime, timedelta

def generate_story_dataset():
    transactions = []
    base_time = datetime.utcnow() - timedelta(hours=1)
    
    # 1. Hacked account sends $500 to 50 mules
    for i in range(1, 51):
        mule_id = f"MULE_{i:03d}"
        transactions.append({
            "transaction_id": f"TXN_VICT_{i:03d}",
            "sender_id": "HACKED_CORP_ACC",
            "receiver_id": mule_id,
            "amount": 500.0,
            "timestamp": (base_time + timedelta(seconds=i*5)).isoformat() + "Z",
            "transaction_type": "WEB",
            "currency": "INR",
            "channel": "WEB"
        })
        
    # 2. Mules forward $450 to 5 Managers
    for i in range(1, 51):
        mule_id = f"MULE_{i:03d}"
        manager_id = f"MANAGER_{(i % 5) + 1:02d}"
        transactions.append({
            "transaction_id": f"TXN_MULE_{i:03d}",
            "sender_id": mule_id,
            "receiver_id": manager_id,
            "amount": 450.0,
            "timestamp": (base_time + timedelta(minutes=5, seconds=i*7)).isoformat() + "Z",
            "transaction_type": "UPI",
            "currency": "INR",
            "channel": "UPI"
        })
        
    # 3. Managers forward money to offshore crypto
    for i in range(1, 6):
        manager_id = f"MANAGER_{i:02d}"
        transactions.append({
            "transaction_id": f"TXN_MGR_{i:02d}",
            "sender_id": manager_id,
            "receiver_id": "OFFSHORE_CRYPTO",
            "amount": 4500.0,
            "timestamp": (base_time + timedelta(minutes=15, seconds=i*30)).isoformat() + "Z",
            "transaction_type": "WIRE",
            "currency": "INR",
            "channel": "API"
        })
        
    # Add a few completely normal transactions to show contrast
    transactions.append({
        "transaction_id": "TXN_NORM_1",
        "sender_id": "ALICE_STUDENT",
        "receiver_id": "STARBUCKS",
        "amount": 5.0,
        "timestamp": (base_time + timedelta(minutes=1)).isoformat() + "Z",
        "transaction_type": "POS",
        "currency": "INR",
        "channel": "POS"
    })
    transactions.append({
        "transaction_id": "TXN_NORM_2",
        "sender_id": "BOB_WORKER",
        "receiver_id": "LANDLORD",
        "amount": 1200.0,
        "timestamp": (base_time + timedelta(minutes=2)).isoformat() + "Z",
        "transaction_type": "UPI",
        "currency": "INR",
        "channel": "UPI"
    })
        
    # Save to CSV
    csv_file = "story_dataset.csv"
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=transactions[0].keys())
        writer.writeheader()
        writer.writerows(transactions)
        
    print(f"Generated {len(transactions)} transactions in {csv_file}")
    return csv_file, transactions

def upload_dataset(csv_file):
    print(f"Uploading {csv_file} to backend...")
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        csv_content = f.read()
        
    headers = {
        "x-api-key": "test-api-key",
        "Content-Type": "application/json"
    }
    payload = {
        "csv_text": csv_content
    }
    
    try:
        response = requests.post("http://127.0.0.1:8000/v1/predict", json=payload, headers=headers, timeout=60)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("Upload Successful!")
            res_data = response.json()
            print(f"Predictions: {len(res_data.get('predictions', []))}")
            print(f"Flagged Paths: {len(res_data.get('flagged_paths', []))}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Failed to upload: {e}")

if __name__ == "__main__":
    csv_file, _ = generate_story_dataset()
    upload_dataset(csv_file)
