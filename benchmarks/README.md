# Benchmarks

Run the policy decision microbenchmark from an installed development checkout:

```bash
.venv/bin/python benchmarks/benchmark_policy.py
```

It measures the complete pure `evaluate` call for a matched exact-tool + `path_under` rule,
including the policy digest currently produced for every decision. It excludes MCP framing,
subprocess I/O, SQLite persistence, approval waiting, UI polling, and upstream execution.

The output is versioned JSON and reports median/min/max microseconds per decision plus environment
details. This is a regression baseline, not a universal latency claim. CI runs a small smoke sample;
maintainers record a full sample during the final release audit.

## v0.1.0 release-candidate baseline

| Date | Environment | Trials × iterations | Median | Range |
| --- | --- | ---: | ---: | ---: |
| 2026-08-11 | macOS 14.5, arm64, CPython 3.12.13 | 7 × 20,000 | 20.432 µs | 19.865–20.521 µs |

The result is comfortably below one millisecond per in-process policy decision on this reference
machine. End-to-end latency is dominated by protocol, storage, approval, and upstream behavior and
must be measured separately for a deployment.
