# Releasing

This is the maintainer runbook. A release is built once by GitHub Actions and the same artifacts are
promoted to PyPI and GitHub Releases. Do not rebuild and upload from a workstation.

## One-time setup

1. Protect `main` with required CI checks and pull-request review.
2. Create protected GitHub environments named `testpypi` and `pypi`; require a manual reviewer for
   production.
3. Register exact PyPI Trusted Publishers for owner `sunhao123456sun-svg`, repository `toolpermit`,
   workflow `release.yml`, environment `pypi`; use the corresponding TestPyPI configuration for
   `testpypi.yml`/`testpypi`.
4. Enable private vulnerability reporting, secret scanning/push protection where available, and
   Dependabot.

Trusted Publishing uses short-lived OIDC credentials; no long-lived PyPI token belongs in GitHub.

## Release candidate gate

- Update version in `pyproject.toml` and `src/toolpermit/__init__.py` together.
- Move changelog notes from Unreleased and set the release date.
- Run `python scripts/check_release.py` and the full local CI commands.
- Build both distributions and run `python scripts/check_distributions.py dist`; this validator uses
  the current PyPA metadata parser and verifies release-critical package contents.
- Merge a reviewed release PR only after every required check passes.
- Run the TestPyPI workflow against the exact commit and install the uploaded wheel in a clean
  Python 3.11+ environment.
- Confirm package/repository ownership and Trusted Publisher fields immediately before production.

## Production

Create and push an annotated `vX.Y.Z` tag pointing at the reviewed `main` commit. `release.yml`
validates tag/version equality, tests, builds once, verifies metadata, publishes with OIDC, and then
creates the GitHub Release from those same files. The protected `pypi` environment is the final
human approval boundary.

## Post-release

Install from PyPI into a new environment, run `toolpermit --version`, complete the contained demo,
confirm the GitHub/PyPI metadata and attestations, and record any follow-up issue. Never overwrite a
published version. Yank only when leaving the file available would cause material harm, and publish
a corrected version promptly.

The expanded checklist and incident procedure are in
[planning/RELEASE_PLAN.md](../planning/RELEASE_PLAN.md).
