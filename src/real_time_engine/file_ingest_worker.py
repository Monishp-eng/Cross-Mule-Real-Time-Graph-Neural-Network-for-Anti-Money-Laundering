"""Batch/file ingestion worker for processing transaction event files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

from src.orchestrator import MuleDetectionOrchestrator, load_events_from_file


def run_worker(input_file: str, output_file: str) -> Dict[str, Any]:
    orchestrator = MuleDetectionOrchestrator()
    events: List[Dict[str, Any]] = load_events_from_file(input_file)
    results = orchestrator.process_batch(events)

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(results, indent=2), encoding="utf-8")

    summary = {
        "status": "ok",
        "events": len(events),
        "output_file": str(output_path),
        "stats": orchestrator.get_stats(),
    }

    orchestrator.close()
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Process transaction events from a JSON file")
    parser.add_argument("--input", default="data/real_transactions.json", help="Path to input JSON array")
    parser.add_argument("--output", default="outputs/worker_results.json", help="Path to output results JSON")
    args = parser.parse_args()

    summary = run_worker(args.input, args.output)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
