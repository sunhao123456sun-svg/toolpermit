# ToolPermit

ToolPermit is a local-first permission policy and approval layer for MCP tool calls.

> Development status: v0.1.0 is under active implementation. The Phase 1 protocol and
> cross-platform feasibility gates have passed; the production package is not released yet.

English is the authoritative project language. A Chinese overview is available in
[README.zh-CN.md](README.zh-CN.md).

## Scope

The first release targets local, single-user MCP servers over `stdio`. It is not an operating
system sandbox and cannot protect calls that bypass its proxy.

## Development

```bash
python -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/python -m pytest
```

See [planning/PRODUCT_REQUIREMENTS.md](planning/PRODUCT_REQUIREMENTS.md) and
[planning/THREAT_MODEL.md](planning/THREAT_MODEL.md) for the approved product and security
boundaries.

