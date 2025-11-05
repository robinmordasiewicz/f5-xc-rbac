# Data Model

This feature defines policy and CI workflow behavior; it does not introduce persistent domain entities.

## Policy Artifacts

- .pre-commit-config.yaml: Hook definitions (formatting, linting, security, policy gates)
- .secrets.baseline: detect-secrets baseline (tracked)
- .github/workflows/pre-commit.yml: CI workflow mirroring pre-commit checks (PR-blocking)

No schema-managed data or database changes are required.
