# ADR-005: Local UI technology and distribution

> Status: Accepted for v0.1 after wheel packaging spike.

## Chinese summary

v0.1 不使用 React/Vite，而是在 Python Wheel 中打包少量原生 HTML、CSS 和 JavaScript。UI 只负责展示与调用本地 API，不能复制策略或审批业务逻辑。服务默认仅绑定回环地址，不开放 CORS，并实施 Host、Origin、CSRF、CSP 和 SameSite 防护。

## Context

The approval UI must be easy to install and must not create a second policy implementation or a large frontend supply chain. Phase 1 proved that package resources survive wheel build and clean installation.

## Decision

- Bundle framework-free HTML/CSS/JavaScript with `importlib.resources`.
- Serve the UI and API from one local Python application.
- Bind only to loopback in v0.1; non-loopback mode is unsupported rather than hidden behind a warning.
- Keep all policy, approval, and state-transition logic in shared application services.
- Use restrictive Content Security Policy, escaped DOM rendering, exact Host/Origin validation, no permissive CORS, SameSite cookies, and per-session CSRF tokens.
- Make approval controls keyboard accessible and never communicate decision state by color alone.
- CLI remains a complete alternative for core workflows.

## Consequences

- No Node build is needed for production distribution.
- UI features remain intentionally small; complex component ecosystems are deferred.
- Browser-security tests are release-blocking.
- Remote/team UI requires a new authentication and threat-model design.

## Verification

- Wheel clean-install asset test.
- Loopback and non-loopback refusal tests.
- Host, Origin, CORS, CSRF, CSP, escaping, and keyboard-flow tests.
- Manual rendered UI review before v0.1 release.

