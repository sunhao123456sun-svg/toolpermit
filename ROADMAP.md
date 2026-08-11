# Roadmap

## v0.1 — local MCP `stdio` control plane

- Deterministic policy and one-time approvals.
- Redacted local audit, replay, and policy suggestion.
- Complete CLI and protected loopback UI.
- Reproducible PyPI/GitHub release pipeline.

## Candidates after v0.1

- Broader independent MCP client compatibility fixtures.
- Better audit querying and policy-diff ergonomics.
- Documented migration tooling as schemas evolve.
- Optional adapters for additional local protocols after separate threat-model review.

## Explicitly not committed

Remote/team UI, multi-tenant authorization, Streamable HTTP mediation, cloud storage, container
images, OS sandboxing, and LLM-based security decisions are not promised. They require separate
product and security decisions before implementation.
