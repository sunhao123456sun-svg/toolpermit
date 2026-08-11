# Phase 3 validation report

> Status: Passed  
> Validated commit: `899401fe33bed4d74c2b1f3847b02304d0d2c5b8`  
> Hosted evidence: [GitHub Actions run 31464435428](https://github.com/sunhao123456sun-svg/toolpermit/actions/runs/31464435428)

## Chinese executive summary

Phase 3 已完成发布候选仓库的文档、演示、治理与供应链准备。英文主文档、中文功能与快速上手、
策略/CLI/配置/安全/隐私/限制/故障排查文档均与实现核对；可抛弃目录演示在干净流程中完成
观察、建议、回放、导出和脱敏检查；Wheel 与源码包使用当前 PyPA Core Metadata 2.5 解析器
验证；GitHub Actions 在 Ubuntu、macOS、Windows 和 Python 3.11–3.13 上全部通过。

## Gate evidence

| Gate | Standard | Evidence | Result |
| --- | --- | --- | --- |
| Documentation | English authoritative docs and Chinese overview match v0.1 | README files, `docs/`, link/version validator | Pass |
| Safe demo | No credentials; writes remain in disposable directory | `examples/`, escape negative test, clean-room walkthrough | Pass |
| Governance | License, security, support, contribution, conduct, roadmap, issue/PR templates | Repository root and `.github/` | Pass |
| Packaging | Wheel contains UI; sdist contains docs/examples; metadata is valid | `scripts/check_distributions.py`, clean install | Pass |
| Supply chain | Separate least-privilege CI/TestPyPI/PyPI workflows; OIDC; pinned release actions | `.github/workflows/` and Actionlint 1.7.12 | Pass |
| Quality | Ruff, strict Pyright, coverage >= 70%, all tests | 36 tests, 70.42% reference coverage | Pass |
| Performance | Reproducible decision benchmark exists and baseline is recorded | median 20.432 µs on reference machine | Pass |
| Portability | Hosted matrix passes on supported OS/Python versions | GitHub Actions run linked above, 11/11 jobs | Pass |

## Packaging validator note

Core Metadata 2.5 was approved in September 2025. Twine 6.2.0 predates support and incorrectly
rejects it. The release gate therefore uses current PyPA `packaging.metadata.Metadata` validation,
plus explicit filename, version, license, Python requirement, Wheel asset, and sdist content checks.

## Phase 4 entry criteria

- All Phase 3 gates above are passed.
- Production publication remains disabled until the exact repository/PyPI ownership, protected
  environments, final commit, and user authorization are confirmed.
