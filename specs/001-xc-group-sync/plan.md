# Implementation Plan: XC Group Sync (Spec 001)

**Branch**: `001-xc_user_group_sync-plan` | **Date**: 2025-11-04 | **Spec**: `specs/001-xc_user_group_sync/spec.md`
**Input**: Feature specification from `specs/001-xc_user_group_sync/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Automate synchronization of Active Directory groups to F5 Distributed Cloud (XC) IAM user groups. The tool ingests a CSV export, extracts group names from LDAP DNs, validates users, and performs idempotent create/update/delete against XC in the `system` namespace. Authentication supports API token or client certificate (P12 or split PEM), with P12 preferred when both are present. Robust retry and full membership reconciliation are required.

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: Python 3.12
**Primary Dependencies**: requests, click, pydantic, python-dotenv, tenacity
**Storage**: N/A (reads CSV files)
**Testing**: pytest
**Target Platform**: macOS/Linux (also GitHub Actions Ubuntu runner)
**Project Type**: single project (src + tests)
**Performance Goals**: Process 10k rows in < 60s (network dependent)
**Constraints**: Pre-commit completes < 2 min; no plaintext secrets in code
**Scale/Scope**: CSVs up to ~100k rows; groups up to API limits (assumed 128-char names)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Issue-First: PASS → https://github.com/robinmordasiewicz/f5-xc-user-group-sync/issues/12
- Quality Gates: PRE-COMMIT in place (Markdown, Shell, EditorConfig). Python linters (ruff/black) NOT configured → NEEDS FOLLOW-UP (proposal in next steps).
- Review Required: Will open PR from feature branch.
- Clean History: Will squash-and-merge, delete branch.
- Test-Driven: Tests planned; initial scaffold to include pytest but implementation TBD.

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
src/
├── xc_user_group_sync/
│   ├── __init__.py
│   ├── cli.py
│   ├── client.py
│   └── models.py

tests/
├── unit/
└── integration/
```text
#### Structure Decision

Single-project layout for a CLI tool. Code under `src/xc_user_group_sync`, tests under `tests/`.

## Complexity Tracking

> Fill ONLY if Constitution Check has violations that must be justified

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
