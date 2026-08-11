# ADR-006: Audit minimization and redaction

> Status: Accepted for v0.1 after Phase 1 persistence spike.

## Chinese summary

ToolPermit 只在内存中保留执行所需的原始请求；写入 SQLite、结构化日志或导出文件之前必须先脱敏。默认不保存 Prompt 和完整工具返回内容。脱敏值使用明确的结构化哨兵，回放遇到依赖该值的规则时返回 `indeterminate`，不能把未知误判为匹配或不匹配。

## Context

Tool arguments and results may contain credentials or personal data. Masking only in the UI leaves raw values in databases, backups, logs, and exports. Irreversible redaction reduces replay fidelity, so uncertainty must be explicit.

## Decision

- Keep the exact execution request in memory only for evaluation/forwarding.
- Apply redaction before audit storage, structured logging, and export.
- Redact configured sensitive keys and maintained high-confidence credential patterns.
- Represent redacted values as a versioned structural sentinel, not a recoverable hash or encrypted copy.
- Store tool-result metadata by default, not full result content.
- Do not store model prompts/messages in v0.1.
- Record which fields were redacted and which rule caused redaction without retaining originals.
- Replay returns `indeterminate` when a matcher needs an unavailable redacted value.
- Effective-configuration output masks secrets.
- Debug mode does not bypass redaction.
- Provide explicit retention, deletion, and JSONL export commands.

## Consequences

- Some historical calls cannot be fully replayed; reports must count and explain indeterminate decisions.
- Secret-shape detection is defense in depth, not a complete DLP guarantee.
- Users can add key/pattern rules but cannot reveal a value ToolPermit never stored.
- Database backups inherit the same redacted-only data contract.

## Verification

- Raw secret fixtures absent from SQLite bytes, logs, and JSONL exports.
- Nested key/value redaction tests.
- Replay indeterminate tests.
- Result-content default-minimization tests.

