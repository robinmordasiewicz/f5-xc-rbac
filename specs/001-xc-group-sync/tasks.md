# Tasks: XC Group Sync (Spec 001)

Input: Design documents from `specs/001-xc-group-sync/`
Prerequisites: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

Tests: Optional (not explicitly requested in spec). This plan focuses on implementation tasks.

Organization: Tasks are grouped by user story to enable independent implementation and testing of each story.

Format: `[ID] [P?] [Story] Description`

- [P]: Can run in parallel (different files, no dependencies)
- [Story]: US1, US2, US3, US4, US5 (from spec.md)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

Purpose: Project initialization and basic structure

- [ ] T001 Ensure Python packaging baseline is Python 3.12 in `pyproject.toml`
- [ ] T002 [P] Add LDAP DN parsing dependency `ldap3` to `[project.dependencies]` in `pyproject.toml`
- [ ] T003 [P] Confirm pre-commit hooks (Ruff/Black/Markdown/Shell) are installed and configured in `.pre-commit-config.yaml`

---

## Phase 2: Foundational (Blocking Prerequisites)

Purpose: Core infrastructure that MUST be complete before ANY user story can be implemented.

- [ ] T004 Create LDAP DN parsing utility `src/xc_rbac_sync/ldap_utils.py` using `ldap3.utils.dn.parse_dn` and validate CN against naming rules
- [ ] T005 [P] Implement XC API client with retries in `src/xc_rbac_sync/client.py` for endpoints from `specs/001-xc-group-sync/contracts/xc-iam.yaml`
- [ ] T006 [P] Add CLI options and environment loading for auth, tenant, dry-run, cleanup in `src/xc_rbac_sync/cli.py`
- [ ] T007 Implement CSV schema validation for required columns in `src/xc_rbac_sync/cli.py`
- [ ] T008 Configure logging levels and ensure secrets are never logged in `src/xc_rbac_sync/cli.py`

Checkpoint: Foundation ready — user story implementation can now begin in parallel

---

## Phase 3: User Story 1 — Idempotent sync from CSV (Priority: P1) 🎯 MVP

Goal: Sync groups from CSV into XC; repeated runs with identical CSV yield no changes. Support dry-run.

Independent Test: Provide CSV with groups A,B; dry-run shows planned actions, apply creates A,B; re-run shows created=0, updated=0, deleted=0, errors=0.

### Implementation for User Story 1

- [ ] T009 [US1] Aggregate CSV rows into group membership map in `src/xc_rbac_sync/cli.py`
- [ ] T010 [US1] Compute diff vs `GET /api/web/custom/namespaces/system/user_groups` in `src/xc_rbac_sync/cli.py`
- [ ] T011 [US1] Implement dry-run reporting of planned create/update with counts in `src/xc_rbac_sync/cli.py`
- [ ] T012 [US1] Create groups via `POST /api/web/custom/namespaces/system/user_groups` in `src/xc_rbac_sync/client.py`
- [ ] T013 [US1] Update groups with full `usernames` replacement via `PUT /api/web/custom/namespaces/system/user_groups/{name}` in `src/xc_rbac_sync/client.py`
- [ ] T014 [US1] Produce summary (created/updated/deleted/skipped/errors) and exit code in `src/xc_rbac_sync/cli.py`

Checkpoint: User Story 1 is fully functional and independently testable

---

## Phase 4: User Story 4 — Full membership synchronization (Priority: P1)

Goal: Replace group `usernames` entirely to match CSV; remove users not listed in CSV for that group.

Independent Test: For group A, XC has u1,u2; CSV lists u1 → after sync u2 is removed. Then CSV adds u3 → u3 is added.

### Implementation for User Story 4

- [ ] T015 [US4] Enforce full replacement of `usernames` during updates in `src/xc_rbac_sync/cli.py`
- [ ] T016 [US4] Validate extracted CN and skip invalid groups with clear error logging in `src/xc_rbac_sync/cli.py`

Checkpoint: Full membership reconciliation works as default behavior

---

## Phase 5: User Story 2 — Safe cleanup of extraneous groups (Priority: P2)

Goal: Optional cleanup to delete XC groups not present in CSV; safe by default with explicit opt-in.

Independent Test: With XC groups A,B,C and CSV A,B; dry-run with cleanup lists C for delete; apply with cleanup deletes C.

### Implementation for User Story 2

- [ ] T017 [US2] Add `--cleanup` flag and compute delete candidates in `src/xc_rbac_sync/cli.py`
- [ ] T018 [US2] Delete groups via `DELETE /api/web/custom/namespaces/system/user_groups/{name}` in `src/xc_rbac_sync/client.py`

Checkpoint: Cleanup mode works with clear dry-run vs apply semantics

---

## Phase 6: User Story 3 — Authentication and early failure (Priority: P3)

Goal: Detect auth issues early and fail fast with clear messaging.

Independent Test: Run with invalid token; tool exits before any changes with auth error and non-zero status.

### Implementation for User Story 3

- [ ] T019 [US3] Preflight `GET /api/web/custom/namespaces/system/user_groups` to validate auth in `src/xc_rbac_sync/cli.py`
- [ ] T020 [US3] Ensure secrets masked; no tokens printed in logs in `src/xc_rbac_sync/cli.py`

Checkpoint: Authentication failures are detected early with clear messages

---

## Phase 7: User Story 5 — Setup and CI integration (Priority: P2)

Goal: Bootstrap local `.env`, derive tenant, split p12 to PEM, and configure GitHub Actions with secrets.

Independent Test: Single `.p12` in `~/Downloads` named `mytenant-api.p12` → `.env` created with TENANT_ID=mytenant, PEM files exist, secrets created, workflow runs on `main` and `workflow_dispatch`.

### Implementation for User Story 5

- [ ] T021 [US5] Implement setup script `scripts/setup_xc_credentials.sh` (derive TENANT_ID, split p12 to PEM, write `.env`)
- [ ] T022 [P] [US5] Create workflow `.github/workflows/xc-group-sync.yml` to decode secrets and run sync
- [ ] T023 [US5] Document CI secrets and setup steps in `specs/001-xc-group-sync/quickstart.md`

Checkpoint: One-command setup and CI pipeline are in place

---

## Phase N: Polish & Cross-Cutting

- [ ] T024 [P] Update README.md with usage and dry-run examples in `README.md`
- [ ] T025 Add performance knobs (max retries, backoff) and document in `specs/001-xc-group-sync/quickstart.md`
- [ ] T026 Security review: verify no secrets are logged and HTTPS validation is enforced across `src/xc_rbac_sync/*`

---

## Dependencies & Execution Order

Phase Dependencies
- Setup (Phase 1): No dependencies — can start immediately
- Foundational (Phase 2): Depends on Setup completion — BLOCKS all stories
- User Stories (Phase 3+): Depend on Phase 2 completion; then proceed by priority (P1 → P2 → P3)
- Polish (Final): After desired user stories are complete

User Story Dependencies
- US1 (P1): Starts after Foundational — no other story deps
- US4 (P1): Starts after US1 core diff/update flow exists
- US2 (P2): Independent; can start after Foundational
- US3 (P3): Independent; can start after Foundational
- US5 (P2): Independent; can start after Foundational

Within Each User Story
- Models/Utilities → Client/Services → CLI behavior → Reporting
- Dry-run before apply paths
- Summary/reporting before exit codes

Parallel Opportunities
- [P] tasks in Setup and Foundational can run concurrently
- Different user stories can proceed in parallel post-Foundational
- For US5, workflow and docs tasks marked [P] can run in parallel

---

## Implementation Strategy

MVP First (US1 Only)
1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: US1 (MVP)
4. Stop and validate: Dry-run and apply produce expected summaries

Incremental Delivery
1. Add US4 (full membership sync)
2. Add US2 (cleanup)
3. Add US3 (auth fail-fast)
4. Add US5 (setup + CI)

Notes
- [P] tasks = different files, no dependencies
- [Story] label ensures traceability to spec.md
- Each story should be independently deliverable and testable
