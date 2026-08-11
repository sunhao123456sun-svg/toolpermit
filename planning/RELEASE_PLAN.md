# Release Plan

> Target: First public release v0.1.0  
> Distribution: GitHub Release and PyPI  
> Status: Proposed

## Chinese executive summary

发布不是“把代码推到 GitHub”这一个动作，而是一条受保护、可重复、能够撤回的供应链。v0.1.0 采用 SemVer 预稳定版本、GitHub 保护分支、Pull Request 强制检查、TestPyPI 演练、PyPI Trusted Publishing、GitHub Release 和构建来源证明。发布包必须由同一个受保护的 GitHub Actions 工作流构建并上传，禁止维护者在本机重新构建另一个版本手工上传。

如果发布后发现安全或数据完整性问题，优先停止推荐该版本、发布安全公告并尽快修复；只有在包本身无法安全使用时才考虑 PyPI yank。任何版本都不能覆盖上传。

## Release principles

1. Build once, promote the same artifacts.
2. Use short-lived OIDC credentials, not stored PyPI API tokens.
3. Release only from a reviewed commit that passed required checks.
4. Keep release permissions separate from normal CI permissions.
5. Make supported behavior, limitations, and migration notes visible.
6. Never overwrite or silently replace a published artifact.
7. Treat documentation, translation, and examples as release artifacts.

## Versioning

Use Semantic Versioning:

- `0.x.y`: public but compatibility may change with documented migration notes.
- Patch: backwards-compatible defect and security fixes within a minor line.
- Minor: new functionality or intentional pre-1.0 compatibility changes.
- `1.0.0`: considered only after policy schema, event schema, CLI, and storage compatibility commitments are proven.

Additional rules:

- Policy and event schemas have their own explicit integer versions.
- Database migrations are monotonic and tested in both fresh and upgrade paths.
- CLI output intended for machines is versioned JSON; human text is not a stable API.
- Deprecations must identify a removal target where practical.

## Branching and change workflow

- `main` is always releasable.
- Work occurs on short-lived `feat/`, `fix/`, `docs/`, or `chore/` branches.
- Every change reaches `main` through a Pull Request.
- Squash merge is the default to keep one intentional changelog unit per PR.
- PR titles follow Conventional Commit-style categories for release-note automation.
- Direct pushes and force pushes to `main` are disabled.

## Repository protection

Configure a GitHub ruleset for `main`:

- Require a Pull Request.
- Require required status checks.
- Require the branch to be up to date before merge where practical.
- Block force pushes and deletion.
- Require conversation resolution.
- Apply protections to administrators where the account/repository plan permits.
- Require signed commits only if the contributor experience and bot support are verified; do not enable it as an untested checkbox.

## Required Pull Request checks

### Python quality

- Formatting check.
- Ruff lint.
- Pyright type check.
- Unit and property-based tests.
- Coverage thresholds.

### Compatibility

- Supported Python matrix.
- Ubuntu, macOS, and Windows integration tests.
- MCP fixture protocol tests.
- Frontend build/test when UI paths change.

### Packaging and docs

- Build sdist and wheel.
- Install wheel into a clean environment and run smoke test.
- Validate package metadata and included files.
- Build documentation and check internal links.
- Validate README rendering and language links.

### Security and supply chain

- CodeQL.
- Dependency review.
- Secret scanning/push protection through repository settings.
- Dependency lock consistency.
- License allowlist/report.
- Workflow static analysis where practical.

## GitHub files before public launch

- `README.md` and `README.zh-CN.md`.
- `LICENSE`.
- `SECURITY.md`.
- `CONTRIBUTING.md`.
- `CODE_OF_CONDUCT.md`.
- `SUPPORT.md`.
- `CHANGELOG.md`.
- `ROADMAP.md`.
- Issue forms for bugs, features, and questions.
- PR template with tests, docs, threat-model, and compatibility checkboxes.
- `dependabot.yml`.
- `CODEOWNERS` once ownership is meaningful.

## CI workflow separation

### `ci.yml`

- Trigger: pull requests and pushes to `main`.
- Permissions: read-only by default.
- No production credentials or publishing.
- Runs quality, test, compatibility, package, and docs checks.

### `security.yml` / CodeQL

- Trigger: Pull Requests, pushes, and schedule.
- Uses minimal documented permissions.
- Uploads security results only.

### `docs.yml`

- Builds previews for reviewed branches where safe.
- Production docs deploy only from `main` or a release tag.
- Never executes untrusted documentation code with release permissions.

### `release.yml`

- Trigger: an intentional version tag or protected manual dispatch tied to an exact commit.
- Requires the protected `pypi` GitHub Environment and manual approval.
- Builds sdist/wheel once in an isolated job.
- Runs package inspection and clean-install smoke tests.
- Publishes the same downloaded artifacts to PyPI through Trusted Publishing.
- Creates GitHub artifact attestations and the GitHub Release.
- Does not run arbitrary scripts from untrusted Pull Requests.

## Release automation choice

Recommended initial option: Release Please or a similarly reviewable release PR that:

- Calculates the next version from merged PR titles/labels.
- Updates `CHANGELOG.md` and package version metadata.
- Opens a normal reviewable PR.
- Creates a tag/release only after the release PR is merged.

If automation becomes confusing, prefer a documented manual release PR over custom opaque scripts.

## Environments

### TestPyPI

- Used for release rehearsals.
- Trusted Publisher scoped to the exact repository and workflow.
- Clean-install test uses the uploaded package, not the workspace.

### PyPI production

- Protected GitHub Environment named `pypi`.
- Manual approval required.
- OIDC `id-token: write` granted only to the publish job.
- No long-lived PyPI API token stored in GitHub.

### Documentation hosting

- Initially GitHub Pages if MkDocs is chosen.
- Production deploy restricted to `main` or release tags.
- Documentation version banner matches the latest release.

## Pre-release stages

### Internal alpha

- Version examples: `0.1.0a1`.
- Purpose: validate packaging and core workflow.
- No compatibility promise.

### Public beta or release candidate

- Version examples: `0.1.0b1` or `0.1.0rc1`.
- Purpose: clean-room installation, compatibility, security, and documentation feedback.
- Feature freeze except release-blocking changes.

### Stable pre-1.0 release

- Version: `0.1.0`.
- Full published scope and supported-version policy apply.

## Release checklist

### Scope and product

- [ ] All v0.1 release gates in [MVP_SCOPE.md](MVP_SCOPE.md) pass.
- [ ] Deferred features are not accidentally documented as supported.
- [ ] Known limitations are visible from the README.
- [ ] Demo completes in a clean disposable directory.

### Security

- [ ] Threat model reconciled with implementation.
- [ ] No unresolved critical/high security issue in supported scope.
- [ ] Deny, expiry, alteration, replay, and fail-closed tests pass.
- [ ] Secret fixtures are absent from logs, database, exports, and artifacts.
- [ ] Security reporting and supported-version policy are live.

### Compatibility and data

- [ ] CI passes on all supported OS/Python combinations.
- [ ] Two target MCP clients complete the documented path.
- [ ] Fresh database and every supported migration path pass.
- [ ] Policy/event schema versions are correct.

### Documentation and languages

- [ ] English README and docs match the release.
- [ ] Chinese overview and quickstart show the same commands/version.
- [ ] All links and code snippets are checked.
- [ ] Screenshots/GIF contain no secrets or personal paths.

### Distribution

- [ ] Name and package ownership reverified.
- [ ] sdist/wheel contents inspected.
- [ ] TestPyPI rehearsal installed successfully.
- [ ] Release notes reviewed.
- [ ] PyPI environment approval completed.
- [ ] GitHub Release, checksums/provenance, and PyPI files match.

## Release notes template

```markdown
## ToolPermit vX.Y.Z

### Highlights
### Security-relevant changes
### Added
### Changed
### Fixed
### Compatibility and migrations
### Known limitations
### Contributors
### Verification
```

## Post-release verification

Within the release session:

1. Install from PyPI into a new environment.
2. Run `toolpermit --version` and the packaged smoke demo.
3. Confirm README/PyPI/GitHub links and metadata.
4. Verify artifact provenance where supported.
5. Confirm documentation shows the released version.
6. Open a tracking issue for any non-blocking follow-up found during verification.

## Incident and rollback procedure

### Documentation-only defect

- Correct through a normal PR and redeploy docs.

### Functional regression without security/data risk

- Publish a patch release; do not replace existing files.
- Document workaround and affected versions.

### Security or data-integrity issue

- Use private GitHub Security Advisory workflow.
- Reproduce and assess supported versions.
- Prepare fix, tests, advisory, and patch release privately where possible.
- Publish coordinated advisory and fixed release.
- Yank a PyPI version only when discouraging new installation is justified; explain why.

### Compromised release workflow or credential

- Disable publishing environment/workflow.
- Revoke or remove affected trust configuration.
- Audit tags, releases, package files, and workflow changes.
- Communicate verified affected artifacts and recovery steps.

## Supported-version policy proposal

Before 1.0:

- Latest minor line: bug and security fixes.
- Previous minor line: security fixes for a short, explicitly documented overlap when feasible.
- Pre-releases: best effort only.

Do not promise backports until maintainer capacity supports them.

## References

- GitHub community health files: <https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/creating-a-default-community-health-file>
- GitHub protected branches: <https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/managing-a-branch-protection-rule>
- PyPI Trusted Publishing: <https://docs.pypi.org/trusted-publishers/>
- Python package publishing with GitHub Actions: <https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/>
- GitHub artifact attestations: <https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations/use-artifact-attestations>
