# Implementation Plan: Comprehensive pre-commit requirements with CI parity

**Branch**: `41-precommit-requirements` | **Date**: 2025-11-05 | **Spec**: specs/041-precommit-requirements/spec.md
**Input**: Feature specification from `/specs/041-precommit-requirements/spec.md`

Note: Driving Issue: https://github.com/robinmordasiewicz/f5-xc-rbac/issues/41

## Summary

Implement comprehensive, enforceable pre-commit requirements (formatting, linting, security) and mirror them in CI as PR-blocking checks to guarantee parity and prevent bypass. Tools: Black, Ruff, ShellCheck, shfmt, PyMarkdown, EditorConfig Checker, YAML/JSON checks, detect-secrets (baseline), Bandit, pip-audit. Policy gates: block commits to main, branch/commit-msg enforcement, pin hook versions and update quarterly.

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: pre-commit; Black 24.10.0; Ruff v0.6.0; ShellCheck v0.11.0; shfmt v3.12.0-2; PyMarkdown v0.9.33; editorconfig-checker 3.4.1; detect-secrets v1.5.0; Bandit 1.7.9; pip-audit v2.7.3; actionlint v1.7.4
**Storage**: N/A
**Testing**: pytest
**Target Platform**: GitHub Actions (CI), macOS/Linux dev machines
**Project Type**: Single Python project (src/, tests/)
**Performance Goals**: CI lint job completes in < 2 minutes; local pre-commit average < 30s warm cache
**Constraints**: No secrets in VCS; .gitignore secrets/; reproducible hooks; hooks run read-only in CI (no auto-fix)
**Scale/Scope**: Small repo; single CLI/tooling project

## Constitution Check

Gate statuses derived from `.specify/memory/constitution.md`:

- Issue-First: PASS (Issue #41 exists and referenced)
- Branch naming regex `^[0-9]+-[a-z0-9-]+$`: PASS (41-precommit-requirements)
- Branch number equals Issue number: RESOLVED (branch uses 41)
- Commit-msg gate: PRESENT (local hook scripts); CI policy gate: ADDED (pre-commit workflow)
- No commits to main: PRESENT (pre-commit config)
- PR template linking: PRESENT

Decision: Proceed with Phase 0/1 planning; branch/spec renaming performed in this change. CI parity MUST be implemented in this feature.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```text
### Source Code (repository root)

<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
# [REMOVE IF UNUSED] Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# [REMOVE IF UNUSED] Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# [REMOVE IF UNUSED] Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure: feature modules, UI flows, platform tests]
```text
**Structure Decision**: Single Python project with pre-commit and CI policy. Documentation under `specs/041-precommit-requirements/` aligned with Issue #41.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Branch/spec numbering mismatch (resolved) | N/A | N/A |
