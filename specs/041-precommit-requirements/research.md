# Research: Pre-commit enforcement and CI parity

## Decisions

- Decision: Enforce local+CI parity; CI blocks merges on any failure
  - Rationale: Prevents local bypass, ensures consistent enforcement, simplifies support.
  - Alternatives: Local-only (risk of drift); CI-only (slower feedback, more churn).

- Decision: Toolchain
  - Rationale: Aligns with current repo hooks and Python 3.12; widely adopted, fast.
  - Alternatives: Flake8 instead of Ruff (overlap, less integrated); custom scripts (maintenance burden).

### Formatting

- Black (24.10.0) and shfmt (3.12.0-2), EditorConfig checker, EoF/trailing whitespace, LF endings

### Linting

- Ruff (0.6.0), ShellCheck (0.11.0), PyMarkdown (0.9.33), YAML/JSON structure checks

### Security

- detect-secrets (v1.5.0 baseline), Bandit (MEDIUM+ fail), pip-audit (HIGH/CRITICAL fail)

### Policy & Governance

- Commit-msg gate (#N), no commits to main, branch regex, PR template with Closes #N
- Pin versions, quarterly updates, mirror hooks in CI (`pre-commit run --all-files`)

## Open Questions (resolved)

- CI parity vs local-only: choose parity (block merges)

## References

- Internal: .pre-commit-config.yaml, .specify/memory/constitution.md
- External: Upstream tool docs (no changes required)
