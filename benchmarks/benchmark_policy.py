"""Reproducible microbenchmark for in-process policy decision overhead."""

from __future__ import annotations

import argparse
import json
import platform
import statistics
import time

from toolpermit.canonical import schema_fingerprint
from toolpermit.domain.models import ToolCall
from toolpermit.policy import evaluate, parse_policy


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", type=int, default=20_000)
    parser.add_argument("--trials", type=int, default=7)
    return parser.parse_args()


def main() -> int:
    values = _arguments()
    if values.iterations < 1 or values.trials < 1:
        raise SystemExit("iterations and trials must be positive")
    policy = parse_policy(
        """
version: 1
default: deny
rules:
  - id: allow-contained-read
    action: allow
    explanation: Benchmark exact and path matching.
    match:
      tool: filesystem.read_file
      arguments:
        path:
          path_under: /safe/project
"""
    )
    call = ToolCall(
        event_id="benchmark-event",
        run_id="benchmark-run",
        connection_id="benchmark-connection",
        request_id=1,
        tool_name="filesystem.read_file",
        schema_fingerprint=schema_fingerprint({"type": "object"}),
        arguments={"path": "/safe/project/docs/readme.md"},
    )
    for _ in range(1_000):
        evaluate(call, policy)
    samples: list[float] = []
    for _ in range(values.trials):
        started = time.perf_counter_ns()
        for _ in range(values.iterations):
            evaluate(call, policy)
        elapsed = time.perf_counter_ns() - started
        samples.append(elapsed / values.iterations / 1_000)
    payload = {
        "schema_version": 1,
        "benchmark": "policy-evaluate-matched-path-under",
        "iterations_per_trial": values.iterations,
        "trials": values.trials,
        "median_microseconds_per_decision": round(statistics.median(samples), 3),
        "min_microseconds_per_decision": round(min(samples), 3),
        "max_microseconds_per_decision": round(max(samples), 3),
        "python": platform.python_version(),
        "platform": platform.platform(),
    }
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
