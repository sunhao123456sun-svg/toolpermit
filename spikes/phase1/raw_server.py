"""Minimal JSON-RPC line server used to prove pre-forward cancellation."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> None:
    log_path = Path(sys.argv[1])
    for line in sys.stdin.buffer:
        message = json.loads(line)
        method = message.get("method", "")
        with log_path.open("a", encoding="utf-8") as log:
            log.write(f"{method}\n")
        if "id" not in message:
            continue
        response = {
            "jsonrpc": "2.0",
            "id": message["id"],
            "result": {"content": [{"type": "text", "text": "executed"}]},
        }
        sys.stdout.write(json.dumps(response, separators=(",", ":")) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()

