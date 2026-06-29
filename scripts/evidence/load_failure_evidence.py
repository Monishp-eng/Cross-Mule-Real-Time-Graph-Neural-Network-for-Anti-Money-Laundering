from __future__ import annotations

import argparse
import json
import math
import random
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple
from urllib import error, request


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _post_json(url: str, payload: Dict[str, Any], timeout: float = 10.0) -> Tuple[int, Dict[str, Any], float]:
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    started = time.perf_counter()
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            elapsed_ms = (time.perf_counter() - started) * 1000.0
            raw = resp.read().decode("utf-8")
            parsed = json.loads(raw) if raw else {}
            return resp.status, parsed, elapsed_ms
    except error.HTTPError as exc:
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        raw = exc.read().decode("utf-8") if exc.fp else ""
        try:
            parsed = json.loads(raw) if raw else {}
        except Exception:
            parsed = {"raw": raw}
        return exc.code, parsed, elapsed_ms
    except TimeoutError:
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        return 599, {"error": "timeout"}, elapsed_ms
    except Exception as exc:
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        return 598, {"error": str(exc)}, elapsed_ms


def _get_json(url: str, timeout: float = 10.0) -> Tuple[int, Dict[str, Any], float]:
    req = request.Request(url, method="GET")
    started = time.perf_counter()
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            elapsed_ms = (time.perf_counter() - started) * 1000.0
            raw = resp.read().decode("utf-8")
            parsed = json.loads(raw) if raw else {}
            return resp.status, parsed, elapsed_ms
    except error.HTTPError as exc:
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        raw = exc.read().decode("utf-8") if exc.fp else ""
        try:
            parsed = json.loads(raw) if raw else {}
        except Exception:
            parsed = {"raw": raw}
        return exc.code, parsed, elapsed_ms
    except TimeoutError:
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        return 599, {"error": "timeout"}, elapsed_ms
    except Exception as exc:
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        return 598, {"error": str(exc)}, elapsed_ms


def _make_mobile_event(idx: int, invalid: bool = False) -> Dict[str, Any]:
    if invalid:
        return {"channel": "MOBILE", "raw_event": {"event_id": f"FAULT_{idx}"}}

    amount = round(random.uniform(100, 9500), 2)
    return {
        "channel": "MOBILE",
        "raw_event": {
            "event_id": f"LOAD_{idx}_{int(time.time() * 1000)}",
            "user_id": f"USER_{idx % 500}",
            "transfer_to_wallet": f"WALLET_{(idx * 7) % 1000}",
            "transfer_amount": amount,
            "transfer_time": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "device_fingerprint": f"DEV_{idx % 120}",
            "ip_address": f"10.0.{idx % 255}.{(idx * 3) % 255}",
            "location": {"latitude": 12.97 + (idx % 10) * 0.001, "longitude": 77.59 + (idx % 10) * 0.001, "country": "IN"},
        },
    }


def _percentile(values: List[float], pct: float) -> float:
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    idx = int(math.ceil((pct / 100.0) * len(sorted_vals))) - 1
    idx = max(0, min(idx, len(sorted_vals) - 1))
    return float(sorted_vals[idx])


def _run_phase(base_url: str, total: int, concurrency: int, invalid_ratio: float) -> Dict[str, Any]:
    url = f"{base_url}/v1/transactions/process"
    latencies_ok: List[float] = []
    latencies_all: List[float] = []
    status_counts: Dict[str, int] = {}

    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = []
        for idx in range(total):
            invalid = random.random() < invalid_ratio
            payload = _make_mobile_event(idx, invalid=invalid)
            futures.append(pool.submit(_post_json, url, payload))

        for fut in as_completed(futures):
            status, _, elapsed_ms = fut.result()
            latencies_all.append(elapsed_ms)
            key = str(status)
            status_counts[key] = status_counts.get(key, 0) + 1
            if 200 <= status < 300:
                latencies_ok.append(elapsed_ms)

    elapsed = time.perf_counter() - started
    success_count = sum(v for k, v in status_counts.items() if k.startswith("2"))
    error_count = total - success_count

    return {
        "requests": total,
        "duration_seconds": round(elapsed, 4),
        "throughput_rps": round((total / elapsed) if elapsed > 0 else 0.0, 4),
        "success_count": success_count,
        "error_count": error_count,
        "status_counts": status_counts,
        "latency_ms": {
            "avg_ok": round(statistics.mean(latencies_ok), 4) if latencies_ok else 0.0,
            "p95_ok": round(_percentile(latencies_ok, 95), 4),
            "p99_ok": round(_percentile(latencies_ok, 99), 4),
            "avg_all": round(statistics.mean(latencies_all), 4) if latencies_all else 0.0,
        },
    }


def _measure_recovery(base_url: str, probe_interval_seconds: float, max_wait_seconds: float) -> Dict[str, Any]:
    url = f"{base_url}/v1/transactions/process"
    start = time.perf_counter()
    consecutive_success = 0
    first_success_at = None

    while (time.perf_counter() - start) <= max_wait_seconds:
        status, _, _ = _post_json(url, _make_mobile_event(random.randint(1, 1_000_000), invalid=False), timeout=10.0)
        if 200 <= status < 300:
            consecutive_success += 1
            if first_success_at is None:
                first_success_at = time.perf_counter()
            if consecutive_success >= 5:
                stable_at = time.perf_counter()
                return {
                    "recovered": True,
                    "first_success_seconds": round((first_success_at - start), 4) if first_success_at else None,
                    "stable_recovery_seconds": round((stable_at - start), 4),
                }
        else:
            consecutive_success = 0
        time.sleep(probe_interval_seconds)

    return {
        "recovered": False,
        "first_success_seconds": None,
        "stable_recovery_seconds": None,
    }


def _write_markdown(path: Path, report: Dict[str, Any]) -> None:
    b = report["baseline_phase"]
    f = report["fault_phase"]
    r = report["recovery"]
    p = report.get("preflight", {})
    lines = [
        "# Load & Failure Evidence",
        "",
        f"Generated: {report['generated_at']}",
        f"Base URL: {report['base_url']}",
        "",
        "## Preflight",
        f"- Reachable: {p.get('reachable')}",
        f"- Startup wait (s): {p.get('startup_wait_seconds')}",
        f"- Health timeout (s): {p.get('health_timeout_seconds')}",
        f"- Attempts captured: {len(p.get('attempts', []))}",
        "",
        "## Baseline",
        f"- Requests: {b['requests']}",
        f"- Throughput (RPS): {b['throughput_rps']}",
        f"- p95 latency (ms): {b['latency_ms']['p95_ok']}",
        f"- p99 latency (ms): {b['latency_ms']['p99_ok']}",
        f"- Success count: {b['success_count']}",
        f"- Error count: {b['error_count']}",
        "",
        "## Under Fault",
        f"- Requests: {f['requests']}",
        f"- Throughput (RPS): {f['throughput_rps']}",
        f"- p95 latency (ms): {f['latency_ms']['p95_ok']}",
        f"- p99 latency (ms): {f['latency_ms']['p99_ok']}",
        f"- Success count: {f['success_count']}",
        f"- Error count: {f['error_count']}",
        f"- Status counts: {json.dumps(f['status_counts'])}",
        "",
        "## Recovery",
        f"- Recovered: {r['recovered']}",
        f"- First success after fault (s): {r['first_success_seconds']}",
        f"- Stable recovery (5 consecutive successes) (s): {r['stable_recovery_seconds']}",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate load/failure evidence artifacts with p95/p99 and recovery timing.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--baseline-requests", type=int, default=300)
    parser.add_argument("--fault-requests", type=int, default=300)
    parser.add_argument("--concurrency", type=int, default=30)
    parser.add_argument("--fault-invalid-ratio", type=float, default=0.35)
    parser.add_argument("--probe-interval", type=float, default=0.25)
    parser.add_argument("--max-recovery-wait", type=float, default=30.0)
    parser.add_argument("--health-timeout", type=float, default=5.0)
    parser.add_argument("--startup-wait", type=float, default=20.0)
    parser.add_argument("--startup-probe-interval", type=float, default=1.0)
    parser.add_argument("--out-dir", default="artifacts/evidence")
    args = parser.parse_args()

    random.seed(42)

    preflight_attempts: List[Dict[str, Any]] = []
    reachable = False
    preflight_started = time.perf_counter()
    while (time.perf_counter() - preflight_started) <= max(0.0, args.startup_wait):
        for endpoint in ("/health/live", "/health/ready"):
            status, payload, elapsed_ms = _get_json(f"{args.base_url}{endpoint}", timeout=args.health_timeout)
            preflight_attempts.append(
                {
                    "endpoint": endpoint,
                    "status": status,
                    "payload": payload,
                    "elapsed_ms": round(elapsed_ms, 4),
                    "checked_at": _now_iso(),
                }
            )
            if status == 200:
                reachable = True
                break
        if reachable:
            break
        time.sleep(max(0.1, args.startup_probe_interval))

    if reachable:
        baseline = _run_phase(args.base_url, args.baseline_requests, args.concurrency, invalid_ratio=0.0)
        fault = _run_phase(args.base_url, args.fault_requests, args.concurrency, invalid_ratio=max(0.0, min(1.0, args.fault_invalid_ratio)))
        recovery = _measure_recovery(args.base_url, args.probe_interval, args.max_recovery_wait)
    else:
        baseline = {
            "requests": 0,
            "duration_seconds": 0.0,
            "throughput_rps": 0.0,
            "success_count": 0,
            "error_count": 0,
            "status_counts": {},
            "latency_ms": {"avg_ok": 0.0, "p95_ok": 0.0, "p99_ok": 0.0, "avg_all": 0.0},
        }
        fault = {
            "requests": 0,
            "duration_seconds": 0.0,
            "throughput_rps": 0.0,
            "success_count": 0,
            "error_count": 0,
            "status_counts": {},
            "latency_ms": {"avg_ok": 0.0, "p95_ok": 0.0, "p99_ok": 0.0, "avg_all": 0.0},
        }
        recovery = {
            "recovered": False,
            "first_success_seconds": None,
            "stable_recovery_seconds": None,
            "note": "API unreachable during startup preflight window; phases skipped",
        }

    report = {
        "generated_at": _now_iso(),
        "base_url": args.base_url,
        "preflight": {
            "reachable": reachable,
            "startup_wait_seconds": args.startup_wait,
            "health_timeout_seconds": args.health_timeout,
            "attempts": preflight_attempts,
        },
        "baseline_phase": baseline,
        "fault_phase": fault,
        "recovery": recovery,
        "slo_assessment": {
            "p95_under_100ms": baseline["latency_ms"]["p95_ok"] < 100.0,
            "p99_under_150ms": baseline["latency_ms"]["p99_ok"] < 150.0,
            "recovery_under_10s": bool(recovery["stable_recovery_seconds"] is not None and recovery["stable_recovery_seconds"] <= 10.0),
        },
    }

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    json_path = out_dir / f"load_failure_evidence_{stamp}.json"
    md_path = out_dir / f"load_failure_evidence_{stamp}.md"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    _write_markdown(md_path, report)

    final_status = "ok" if reachable else "degraded"
    print(json.dumps({"status": final_status, "json": str(json_path), "markdown": str(md_path)}, indent=2))


if __name__ == "__main__":
    main()
