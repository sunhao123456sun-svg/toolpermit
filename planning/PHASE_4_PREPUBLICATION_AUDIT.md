# Phase 4 pre-publication audit

> Status: Passed for private `main` integration; public release requires owner authorization  
> Audited commit: `e3fa7e7eccf49734a3a7cbd7d5e8b6673d90104a`  
> Hosted evidence: [GitHub Actions run 31465302088](https://github.com/sunhao123456sun-svg/toolpermit/actions/runs/31465302088)

## Chinese executive summary

v0.1.0 发布候选的代码、文档、演示、数据边界、浏览器防护、依赖、工作流、构建包和跨平台
兼容性已完成最终审计。当前可以安全合并到私有 `main`。公开仓库、创建 PyPI/TestPyPI 项目、
配置 Trusted Publisher、创建发布标签和上传包都属于尚未执行的外部发布动作，必须由项目所有者
明确确认后再进行。

## Final audit evidence

| Area | Evidence | Result |
| --- | --- | --- |
| Functional and negative tests | 36 tests; cancellation race repeated 20 times; deny/expiry/digest/redaction/path-escape tests | Pass |
| Coverage | 72.56% reference coverage; enforced minimum 70% | Pass |
| Static quality | Ruff and strict Pyright | Pass |
| Static security | Bandit scan of `src/` | Pass, no findings |
| Dependency security | `pip-audit` after Pytest 9 / pytest-asyncio 1 upgrade | Pass, no known vulnerabilities |
| Secret hygiene | Repository credential/private-key pattern scan | Pass, no matches outside intentional test/planning fixtures |
| Workflow syntax | Actionlint 1.7.12 | Pass |
| Build metadata | PyPA `packaging` Core Metadata 2.5 validation | Pass |
| Distribution contents | Wheel UI assets, license, sdist docs/examples/screenshot | Pass |
| Clean installation | CLI init/config and bundled UI from a fresh Wheel environment | Pass |
| Clean-room product flow | observe, inspect, suggest, replay, export, secret absence | Pass |
| Performance | matched policy median 20.432 µs on the recorded reference machine | Pass |
| Hosted portability | Ubuntu/macOS/Windows × Python 3.11–3.13, quality, package | Pass, 11/11 jobs |

## Release service state checked on 2026-08-11

- `https://pypi.org/pypi/toolpermit/json`: HTTP 404.
- `https://test.pypi.org/pypi/toolpermit/json`: HTTP 404.
- GitHub repository remains private, as explicitly requested.
- GitHub Free rejected private-repository branch protection with HTTP 403; protection can be enabled
  after the repository becomes public, before a production tag is created.
- Protected `testpypi` and `pypi` environments and exact Trusted Publishers are not configured yet.

A 404 is evidence that no public project currently resolves at the name; it is not a reservation.
Name and ownership must be checked again at the moment of publication.

## Required owner-authorized publication sequence

1. Make the GitHub repository public.
2. Enable `main` protection, required CI checks, conversation resolution, no force-push/deletion,
   and private vulnerability reporting/security features available to public repositories.
3. Create protected `testpypi` and `pypi` environments with manual approval.
4. Configure exact pending Trusted Publishers for this owner/repository/workflow/environment.
5. Recheck PyPI/TestPyPI name state and run the TestPyPI rehearsal from reviewed `main`.
6. Set the changelog release date, run the final checks, create annotated tag `v0.1.0`, and approve
   the production `pypi` environment.
7. Verify PyPI install, GitHub Release files/checksums/provenance, and the contained demo.

No item in this sequence is implied by general development authorization; publication requires an
explicit final owner decision.
