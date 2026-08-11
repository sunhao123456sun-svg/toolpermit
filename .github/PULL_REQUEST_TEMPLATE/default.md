## Summary

Describe the user-visible change and why it belongs in the current scope.

## Verification

- [ ] Tests cover success and relevant unsafe/failure paths.
- [ ] Ruff, strict Pyright, coverage, and release checks pass locally.
- [ ] Cross-platform behavior is unchanged or explicitly tested.
- [ ] English docs are updated; Chinese overview is updated when advertised behavior changes.

## Security and compatibility

- [ ] I considered proxy bypass, canonicalization, approval races, redaction, browser security, and
      upstream side effects as applicable.
- [ ] Policy/event/database/JSON contracts and migration impact are documented.
- [ ] This change adds no telemetry, real credentials, or sensitive fixtures.

## Release note

Provide one concise changelog line, or explain why none is needed.
