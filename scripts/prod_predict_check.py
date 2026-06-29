import json
import os
import subprocess
import time
from pathlib import Path

import requests


def get_api_key() -> str:
    raw = subprocess.check_output(
        [
            "gcloud",
            "run",
            "services",
            "describe",
            "cross-mule-detection",
            "--region",
            "us-central1",
            "--format=json",
        ],
        text=True,
    )
    payload = json.loads(raw)
    env = (
        payload.get("spec", {})
        .get("template", {})
        .get("spec", {})
        .get("containers", [{}])[0]
        .get("env", [])
    )
    return next((row.get("value", "") for row in env if row.get("name") == "API_KEY"), "")


def main() -> None:
    url = "https://cross-mule-detection-86346703988.us-central1.run.app"
    api_key = os.getenv("API_KEY", "") or get_api_key()
    if not api_key:
        raise RuntimeError("API_KEY not found in Cloud Run service env")

    csv_text = Path("data/sample_transactions_full.csv").read_text(encoding="utf-8")
    headers = {"x-api-key": api_key, "Content-Type": "application/json"}
    payload = {"csv_text": csv_text}

    for idx in (1, 2):
        start = time.perf_counter()
        response = requests.post(url + "/v1/predict", headers=headers, json=payload, timeout=180)
        elapsed = time.perf_counter() - start
        response.raise_for_status()
        body = response.json()
        preds = body.get("predictions", [])
        users = {
            str(item.get("source_user_id") or "").strip()
            for item in preds
            if str(item.get("source_user_id") or "").strip()
        }
        has_unknown = any(user.lower() == "unknown" for user in users)
        print(
            f"run_{idx}_seconds={elapsed:.3f} count={body.get('count')} "
            f"pred_len={len(preds)} unknown={has_unknown} users={len(users)}"
        )


if __name__ == "__main__":
    main()
