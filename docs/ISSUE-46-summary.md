Issue: #46 — Audit: pre-commit & CI changes (2025-11-05)

Summary

This document references Issue #46 and provides a short summary of the edits made to harden pre-commit, CI, and related documentation on 2025-11-05.

What changed

- Added a PR-blocking `pre-commit` enforcement job in CI and a `pre-commit` config with multiple hooks (Black, Ruff, ShellCheck, shfmt, detect-secrets, Bandit, pip-audit, actionlint, jscpd).
- Introduced a `bandit-local` wrapper to limit Bandit scans to `src/` and avoid scanning `.venv` or vendored packages.
- Added a `pip-audit` step compatible with `pyproject.toml` in CI.
- Lowered noise by narrowing jscpd scope and adding Node setup in CI for jscpd usage.
- Moved `no-commit-to-branch` hook to commit-only stage to avoid failing `pre-commit run --all-files` runs in CI.
- Updated `.github/copilot-instructions.md` with safe CLI patterns (heredoc, `--body-file`, single-quoted bodies) to avoid zsh/basename/backtick substitution issues.

Files of interest

- `.pre-commit-config.yaml` — hook additions/edits including `bandit-local` and commit-stage adjustments.
- `.github/workflows/pre-commit.yml` — CI job setup that runs the `pre-commit` suite (Python 3.12 + Node 20 configured).
- `.github/copilot-instructions.md` — safe CLI/heredoc guidance updated.
- `specs/041-precommit-requirements/` — spec and plan docs that motivated the changes.

Rationale & follow-ups

- Keep `pre-commit` as the single source of truth for local and CI checks.
- Limit scanner scope to actionable source files to reduce noise.
- Consider adjusting CI to run only pre-commit hook-stage pre-commit (e.g., add `--hook-stage pre-commit`) to avoid accidentally invoking commit-only hooks in CI.
- Consider adding a small dry-run pre-commit validation step in CI (or `pre-commit try-repo`) to detect config problems earlier.

This file was created automatically to reference Issue #46 and provide a short, human-friendly summary for the repository history.

Refs: Issue #46
