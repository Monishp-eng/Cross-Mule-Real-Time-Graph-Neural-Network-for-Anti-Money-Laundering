from __future__ import annotations

import argparse
import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib import error, request


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _post_json(url: str, payload: Dict[str, Any], timeout: float = 30.0) -> Tuple[int, Dict[str, Any]]:
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, json.loads(raw) if raw else {}
    except error.HTTPError as exc:
        raw = exc.read().decode("utf-8") if exc.fp else ""
        try:
            payload = json.loads(raw) if raw else {}
        except Exception:
            payload = {"raw": raw}
        return exc.code, payload


def _read_csv_rows(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def _extract_numeric(rows: List[Dict[str, str]], field: str) -> List[float]:
    out: List[float] = []
    for row in rows:
        val = row.get(field)
        if val is None or val == "":
            continue
        try:
            out.append(float(val))
        except Exception:
            continue
    return out


def _hist(values: List[float], bins: int = 10) -> List[float]:
    if not values:
        return [0.0] * bins
    lo = min(values)
    hi = max(values)
    if hi == lo:
        arr = [0.0] * bins
        arr[-1] = 1.0
        return arr
    width = (hi - lo) / bins
    counts = [0] * bins
    for v in values:
        idx = int((v - lo) / width)
        if idx >= bins:
            idx = bins - 1
        counts[idx] += 1
    total = sum(counts) or 1
    return [c / total for c in counts]


def _psi(baseline: List[float], current: List[float], bins: int = 10) -> float:
    eps = 1e-8
    hb = _hist(baseline, bins=bins)
    hc = _hist(current, bins=bins)
    score = 0.0
    for b, c in zip(hb, hc):
        b = max(b, eps)
        c = max(c, eps)
        score += (c - b) * math.log(c / b)
    return float(score)


def _labels_from_rows(rows: List[Dict[str, str]]) -> Tuple[List[int], str]:
    label_fields = ["label", "is_fraud", "is_mule", "target"]
    for field in label_fields:
        if rows and field in rows[0]:
            labels: List[int] = []
            for row in rows:
                raw = str(row.get(field, "0")).strip().lower()
                labels.append(1 if raw in {"1", "true", "yes", "fraud", "mule"} else 0)
            return labels, f"dataset:{field}"

    # Fallback proxy label for governance smoke evidence when explicit labels are absent.
    labels = []
    for row in rows:
        try:
            amount = float(row.get("amount") or 0.0)
        except Exception:
            amount = 0.0
        labels.append(1 if amount >= 5000 else 0)
    return labels, "proxy:amount>=5000"


def _brier(y_true: List[int], y_prob: List[float]) -> float:
    n = max(1, min(len(y_true), len(y_prob)))
    return float(sum((y_prob[i] - y_true[i]) ** 2 for i in range(n)) / n)


def _ece(y_true: List[int], y_prob: List[float], bins: int = 10) -> float:
    n = max(1, min(len(y_true), len(y_prob)))
    if n == 0:
        return 0.0
    bucket_totals = [0] * bins
    bucket_true = [0.0] * bins
    bucket_conf = [0.0] * bins

    for i in range(n):
        p = max(0.0, min(1.0, y_prob[i]))
        idx = min(bins - 1, int(p * bins))
        bucket_totals[idx] += 1
        bucket_true[idx] += y_true[i]
        bucket_conf[idx] += p

    ece_sum = 0.0
    for i in range(bins):
        count = bucket_totals[i]
        if count == 0:
            continue
        acc = bucket_true[i] / count
        conf = bucket_conf[i] / count
        ece_sum += (count / n) * abs(acc - conf)
    return float(ece_sum)


def _extract_prediction_scores(predict_response: Dict[str, Any]) -> Dict[str, float]:
    out: Dict[str, float] = {}
    preds = predict_response.get("predictions", [])
    if isinstance(preds, list):
        for row in preds:
            if not isinstance(row, dict):
                continue
            txid = str(row.get("transaction_id") or "")
            if not txid:
                continue
            try:
                out[txid] = float(row.get("risk_score", 0.0))
            except Exception:
                out[txid] = 0.0
    return out


def _write_markdown(path: Path, report: Dict[str, Any]) -> None:
    drift = report["drift"]
    calib = report["calibration"]
    rb = report["rollback_test"]
    lines = [
        "# Model Governance Evidence",
        "",
        f"Generated: {report['generated_at']}",
        f"Model type: {report['model_metadata'].get('model_type')}",
        f"Label source: {calib['label_source']}",
        "",
        "## Drift",
        f"- PSI amount: {drift['psi_amount']}",
        f"- PSI latitude: {drift['psi_latitude']}",
        f"- PSI longitude: {drift['psi_longitude']}",
        f"- Drift alert: {drift['alert']}",
        "",
        "## Calibration",
        f"- Brier score: {calib['brier_score']}",
        f"- ECE: {calib['ece']}",
        f"- Samples: {calib['sample_count']}",
        "",
        "## Rollback Test",
        f"- Triggered: {rb['triggered']}",
        f"- Reasons: {', '.join(rb['reasons']) if rb['reasons'] else 'none'}",
        f"- Recommendation: {rb['recommendation']}",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate drift/calibration/rollback governance artifacts.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--baseline-csv", default="data/sample_transactions.csv")
    parser.add_argument("--current-csv", default="data/sample_transactions.csv")
    parser.add_argument("--psi-warn", type=float, default=0.10)
    parser.add_argument("--psi-alert", type=float, default=0.25)
    parser.add_argument("--ece-threshold", type=float, default=0.08)
    parser.add_argument("--brier-threshold", type=float, default=0.20)
    parser.add_argument("--out-dir", default="artifacts/evidence")
    args = parser.parse_args()

    baseline_path = Path(args.baseline_csv)
    current_path = Path(args.current_csv)
    baseline_rows = _read_csv_rows(baseline_path)
    current_rows = _read_csv_rows(current_path)

    baseline_csv_text = baseline_path.read_text(encoding="utf-8")
    current_csv_text = current_path.read_text(encoding="utf-8")

    status_b, pred_b = _post_json(f"{args.base_url}/v1/predict", {"csv_text": baseline_csv_text})
    status_c, pred_c = _post_json(f"{args.base_url}/v1/predict", {"csv_text": current_csv_text})
    if status_b != 200 or status_c != 200:
        raise RuntimeError(f"Prediction endpoint failed: baseline_status={status_b}, current_status={status_c}")

    psi_amount = _psi(_extract_numeric(baseline_rows, "amount"), _extract_numeric(current_rows, "amount"))
    psi_lat = _psi(_extract_numeric(baseline_rows, "latitude"), _extract_numeric(current_rows, "latitude"))
    psi_lon = _psi(_extract_numeric(baseline_rows, "longitude"), _extract_numeric(current_rows, "longitude"))
    max_psi = max(psi_amount, psi_lat, psi_lon)

    labels, label_source = _labels_from_rows(current_rows)
    scores_by_tx = _extract_prediction_scores(pred_c)
    probs: List[float] = []
    ordered_labels: List[int] = []
    for row, y in zip(current_rows, labels):
        txid = str(row.get("transaction_id") or "")
        if txid and txid in scores_by_tx:
            probs.append(scores_by_tx[txid])
            ordered_labels.append(y)

    brier = _brier(ordered_labels, probs)
    ece = _ece(ordered_labels, probs)

    rollback_reasons: List[str] = []
    if max_psi >= args.psi_alert:
        rollback_reasons.append("feature_drift_alert")
    if ece > args.ece_threshold:
        rollback_reasons.append("calibration_ece_exceeded")
    if brier > args.brier_threshold:
        rollback_reasons.append("calibration_brier_exceeded")
    if pred_c.get("model_type") != "gnn_graphsage":
        rollback_reasons.append("non_gnn_model_response")

    rollback_triggered = len(rollback_reasons) > 0

    report = {
        "generated_at": _now_iso(),
        "base_url": args.base_url,
        "model_metadata": {
            "model_type": pred_c.get("model_type"),
            "model_path": pred_c.get("model_path"),
            "count": pred_c.get("count"),
        },
        "thresholds": {
            "psi_warn": args.psi_warn,
            "psi_alert": args.psi_alert,
            "ece_threshold": args.ece_threshold,
            "brier_threshold": args.brier_threshold,
        },
        "drift": {
            "psi_amount": round(psi_amount, 6),
            "psi_latitude": round(psi_lat, 6),
            "psi_longitude": round(psi_lon, 6),
            "max_psi": round(max_psi, 6),
            "alert": max_psi >= args.psi_alert,
            "warn": (max_psi >= args.psi_warn) and (max_psi < args.psi_alert),
        },
        "calibration": {
            "label_source": label_source,
            "sample_count": len(probs),
            "brier_score": round(brier, 6),
            "ece": round(ece, 6),
        },
        "rollback_test": {
            "triggered": rollback_triggered,
            "reasons": rollback_reasons,
            "recommendation": "rollback_to_last_stable" if rollback_triggered else "keep_current_model",
        },
    }

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    json_path = out_dir / f"model_governance_evidence_{stamp}.json"
    md_path = out_dir / f"model_governance_evidence_{stamp}.md"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    _write_markdown(md_path, report)

    print(json.dumps({"status": "ok", "json": str(json_path), "markdown": str(md_path)}, indent=2))


if __name__ == "__main__":
    main()
