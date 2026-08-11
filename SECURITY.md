# Security policy

## Supported versions

Before the first public release, only the current `main` branch receives security fixes. After
v0.1.0, the latest released minor line is supported. Pre-1.0 compatibility may change, but security
fixes and required migration steps will be documented.

## Report a vulnerability

Do not open a public issue for a suspected vulnerability. Use GitHub's private vulnerability
reporting for this repository: **Security → Advisories → Report a vulnerability**. Include affected
versions, prerequisites, impact, reproduction steps, and any suggested mitigation. Remove real
credentials and personal data from the report.

The maintainer will acknowledge a report as soon as practical, validate scope, coordinate a fix and
release, and credit the reporter if requested. There is no bug bounty program and no guaranteed
response SLA for this volunteer project.

## Security boundary

ToolPermit mediates supported MCP calls that pass through its proxy. It is not an OS sandbox, cannot
see bypass traffic, and cannot undo a completed action. See [docs/security.md](docs/security.md),
[docs/limitations.md](docs/limitations.md), and the detailed
[threat model](planning/THREAT_MODEL.md).
