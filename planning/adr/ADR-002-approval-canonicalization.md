# ADR-002: Approval canonicalization and digest

> Status: Accepted for v0.1 design; production test vectors required before implementation gate closes.

## Chinese summary

审批必须绑定“准确的工具调用”，不能只绑定工具名。ToolPermit 将使用带版本号的类型化二进制规范编码，再以带域分隔的 SHA-256 计算摘要。编码保留字符串原样、不做 Unicode 归一化，拒绝 NaN/Infinity，并将工具名、Schema 指纹、参数、连接关联和策略摘要全部纳入。

## Context

JSON text has multiple equivalent encodings, and generic JSON serializers have difficult cross-language number rules. Approval needs stable binding to ToolPermit's parsed value, not to whitespace or object insertion order. The scheme must also make accidental cross-purpose digest reuse impossible.

## Decision

Define `TP-CANONICAL-V1`, a small type-tagged encoding for JSON-compatible values:

- Null, booleans, integers, finite binary64 floats, strings, arrays, and string-keyed objects have distinct type markers.
- Strings are UTF-8 with explicit byte lengths and no Unicode normalization.
- Integers use a sign plus canonical base-10 magnitude.
- Floats use big-endian IEEE-754 binary64 bytes; NaN and infinities are rejected.
- Arrays preserve order and include element count.
- Object keys are sorted by their UTF-8 byte representation; duplicate keys are rejected during JSON parsing.
- The encoding version is part of the input.

The approval request includes:

- Tool name.
- Tool-schema fingerprint.
- Canonical arguments.
- ToolPermit run ID and connection ID.
- Active policy digest.
- Approval expiry and purpose where relevant.

Digest formula:

```text
SHA-256("toolpermit/approval/v1\0" || TP-CANONICAL-V1(request))
```

The stored audit event contains the digest but never relies on it as secret encryption.

## Consequences

- No canonical-JSON dependency is required.
- Cross-language adapters must implement published vectors exactly.
- `1`, `1.0`, `0.0`, and `-0.0` remain distinguishable parsed values.
- Changing any bound field creates a new approval request.
- A future encoding requires a new version/domain; old digests are never reinterpreted.

## Verification

- Golden byte/digest vectors checked into the repository.
- Property tests for object order independence and field binding.
- Rejection tests for duplicate keys and non-finite floats.
- Cross-platform vector tests in CI.

