# Tasks: User Lifecycle Management with CSV Synchronization

**Feature**: 059-user-lifecycle
**Input**: Design documents from `/specs/059-user-lifecycle/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/user_sync_api.md, quickstart.md

**Tests**: Following TDD approach as specified in quickstart.md - tests are written FIRST before implementation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing. Note that User Stories 1, 2, and 4 are tightly coupled (all P1 priority, all needed for core sync functionality), so they will be implemented together as the MVP.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

Single project structure (from plan.md):
- Source: `src/xc_rbac_sync/`
- Tests: `tests/unit/`, `tests/integration/`
- Scripts: `scripts/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure - no code changes needed, existing infrastructure is sufficient

- [ ] T001 Verify existing project structure matches plan.md requirements
- [ ] T002 Verify existing dependencies (click, pydantic, requests, tenacity, ldap3, python-dotenv) are installed
- [ ] T003 [P] Verify existing linting and formatting tools (black, ruff, mypy) are configured
- [ ] T004 [P] Run existing test suite to establish baseline (`pytest`)

**Checkpoint**: Existing project infrastructure validated - ready for new feature development

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core utilities and protocols that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 [P] Create `parse_display_name()` function in src/xc_rbac_sync/user_utils.py
- [ ] T006 [P] Create `parse_active_status()` function in src/xc_rbac_sync/user_utils.py
- [ ] T007 [P] Create unit tests for `parse_display_name()` in tests/unit/test_user_utils.py
- [ ] T008 [P] Create unit tests for `parse_active_status()` in tests/unit/test_user_utils.py
- [ ] T009 Add User model to src/xc_rbac_sync/models.py with EmailStr validation
- [ ] T010 Add UserSyncStats dataclass to src/xc_rbac_sync/user_sync_service.py
- [ ] T011 Add UserRepository protocol to src/xc_rbac_sync/protocols.py
- [ ] T012 Create unit tests for User model in tests/unit/test_models.py
- [ ] T013 Run foundational tests to verify utility functions and models (`pytest tests/unit/test_user_utils.py tests/unit/test_models.py`)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: Core User Sync - US1, US2, US4 Combined (Priority: P1) 🎯 MVP

**Goal**: Implement complete user synchronization workflow: parse CSV with enhanced attributes (US4), create new users (US1), and update existing users (US2). These three stories are tightly coupled and form the minimum viable product.

**Independent Test**:
1. Create CSV with test users (new and existing with changes)
2. Run `xc-group-sync sync --csv test.csv --dry-run`
3. Verify: Dry-run logs show correct creates and updates
4. Run `xc-group-sync sync --csv test.csv`
5. Verify: Users created/updated in F5 XC match CSV exactly
6. Run sync again with same CSV
7. Verify: Idempotent - no changes on second run (all unchanged)

### Tests for US1, US2, US4 (TDD - Write FIRST)

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T014 [P] [US4] Unit test: CSV parsing with valid data in tests/unit/test_user_sync_service.py
- [ ] T015 [P] [US4] Unit test: CSV parsing with missing required columns in tests/unit/test_user_sync_service.py
- [ ] T016 [P] [US4] Unit test: CSV parsing with name variations (single name, multiple names, whitespace) in tests/unit/test_user_sync_service.py
- [ ] T017 [P] [US4] Unit test: CSV parsing with status mapping (A → True, others → False) in tests/unit/test_user_sync_service.py
- [ ] T018 [P] [US4] Unit test: CSV parsing with pipe-separated group DNs in tests/unit/test_user_sync_service.py
- [ ] T019 [P] [US1] Unit test: sync_users creates new user when not in F5 XC in tests/unit/test_user_sync_service.py
- [ ] T020 [P] [US2] Unit test: sync_users updates user when attributes differ in tests/unit/test_user_sync_service.py
- [ ] T021 [P] [US2] Unit test: sync_users skips unchanged users (idempotency) in tests/unit/test_user_sync_service.py
- [ ] T022 [P] [US1] [US2] Integration test: Full sync workflow (parse → fetch → reconcile) in tests/integration/test_user_sync_integration.py
- [ ] T023 [P] [US2] Integration test: Idempotency - running sync twice produces no changes on second run in tests/integration/test_user_sync_integration.py

### Implementation for US1, US2, US4

**XCClient Extensions** (API operations for user CRUD):

- [ ] T024 [P] [US1] Add `list_users()` alias method to XCClient in src/xc_rbac_sync/client.py
- [ ] T025 [P] [US2] Add `update_user()` method to XCClient in src/xc_rbac_sync/client.py with tenacity retry
- [ ] T026 [P] [US1] [US2] Add `get_user()` method to XCClient in src/xc_rbac_sync/client.py with tenacity retry
- [ ] T027 [P] [US1] Unit test: XCClient.create_user success in tests/unit/test_client.py
- [ ] T028 [P] [US2] Unit test: XCClient.update_user success and retry on 429 in tests/unit/test_client.py
- [ ] T029 [P] [US1] [US2] Unit test: XCClient.get_user success in tests/unit/test_client.py

**UserSyncService** (Business logic for sync):

- [ ] T030 [US4] Implement `parse_csv_to_users()` in UserSyncService in src/xc_rbac_sync/user_sync_service.py
- [ ] T031 [US1] [US2] Implement `fetch_existing_users()` in UserSyncService in src/xc_rbac_sync/user_sync_service.py
- [ ] T032 [US1] [US2] Implement `sync_users()` reconciliation logic in UserSyncService in src/xc_rbac_sync/user_sync_service.py
- [ ] T033 [US1] Implement `_create_user()` helper method in UserSyncService in src/xc_rbac_sync/user_sync_service.py
- [ ] T034 [US2] Implement `_update_user()` helper method in UserSyncService in src/xc_rbac_sync/user_sync_service.py
- [ ] T035 [US2] Implement `_user_needs_update()` comparison logic in UserSyncService in src/xc_rbac_sync/user_sync_service.py
- [ ] T036 [US1] [US2] Add error handling and stats collection to all user operations in src/xc_rbac_sync/user_sync_service.py

**CLI Integration**:

- [ ] T037 [US1] [US2] [US4] Integrate UserSyncService into CLI sync command in src/xc_rbac_sync/cli.py
- [ ] T038 [US1] [US2] [US4] Add user sync summary output to CLI in src/xc_rbac_sync/cli.py
- [ ] T039 [US1] [US2] [US4] Unit test: CLI sync command with user CSV in tests/unit/test_cli.py

**Validation**:

- [ ] T040 [US1] [US2] [US4] Run all unit tests for MVP features (`pytest tests/unit/`)
- [ ] T041 [US1] [US2] [US4] Run integration tests for full sync workflow (`pytest tests/integration/`)
- [ ] T042 [US1] [US2] [US4] Manual validation: Create test CSV and run sync with --dry-run
- [ ] T043 [US1] [US2] [US4] Manual validation: Execute sync and verify users created/updated in F5 XC
- [ ] T044 [US1] [US2] [US4] Manual validation: Run sync again and verify idempotency (no changes)

**Checkpoint**: At this point, core user sync (create, update, parse CSV) is fully functional. Users can synchronize CSV to F5 XC with create/update operations. This is the MVP.

---

## Phase 4: User Story 3 - Remove Users Not in CSV (Priority: P2)

**Goal**: Add optional user deletion capability with explicit flag for safety

**Independent Test**:
1. Create CSV without a user that exists in F5 XC
2. Run `xc-group-sync sync --csv test.csv --dry-run` (WITHOUT --delete-users)
3. Verify: No deletion logged (safe default)
4. Run `xc-group-sync sync --csv test.csv --delete-users --dry-run`
5. Verify: Dry-run logs show user would be deleted
6. Run `xc-group-sync sync --csv test.csv --delete-users`
7. Verify: User deleted from F5 XC

### Tests for US3 (TDD - Write FIRST)

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T045 [P] [US3] Unit test: sync_users deletes user when --delete-users=True in tests/unit/test_user_sync_service.py
- [ ] T046 [P] [US3] Unit test: sync_users preserves user when --delete-users=False in tests/unit/test_user_sync_service.py
- [ ] T047 [P] [US3] Unit test: XCClient.delete_user success in tests/unit/test_client.py
- [ ] T048 [P] [US3] Unit test: XCClient.delete_user handles 404 (already deleted) in tests/unit/test_client.py
- [ ] T049 [P] [US3] Integration test: User deletion with --delete-users flag in tests/integration/test_user_sync_integration.py

### Implementation for US3

- [ ] T050 [P] [US3] Add `delete_user()` method to XCClient in src/xc_rbac_sync/client.py with tenacity retry (not for 404)
- [ ] T051 [US3] Implement `_delete_user()` helper method in UserSyncService in src/xc_rbac_sync/user_sync_service.py
- [ ] T052 [US3] Add deletion logic to `sync_users()` based on delete_users flag in src/xc_rbac_sync/user_sync_service.py
- [ ] T053 [US3] Add `--delete-users` flag to CLI sync command in src/xc_rbac_sync/cli.py
- [ ] T054 [US3] Update CLI to pass delete_users flag to UserSyncService in src/xc_rbac_sync/cli.py
- [ ] T055 [US3] Unit test: CLI sync command with --delete-users flag in tests/unit/test_cli.py

**Validation**:

- [ ] T056 [US3] Run all tests for user deletion (`pytest tests/unit/test_user_sync_service.py::*delete* tests/unit/test_client.py::*delete*`)
- [ ] T057 [US3] Manual validation: Test --delete-users flag with dry-run
- [ ] T058 [US3] Manual validation: Execute deletion and verify user removed from F5 XC

**Checkpoint**: User deletion capability added with explicit flag. Users can now clean up terminated users safely.

---

## Phase 5: User Story 5 - Preview Changes with Dry-Run Mode (Priority: P2)

**Goal**: Enhance existing dry-run mode to work with user operations

**Independent Test**:
1. Create CSV with mix of new users, updates, and deletions
2. Run `xc-group-sync sync --csv test.csv --delete-users --dry-run`
3. Verify: All operations logged with "Would create/update/delete" prefix
4. Verify: No actual API calls made to F5 XC
5. Verify: Summary shows planned operation counts

### Tests for US5 (TDD - Write FIRST)

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T059 [P] [US5] Unit test: dry_run logs creates without executing in tests/unit/test_user_sync_service.py
- [ ] T060 [P] [US5] Unit test: dry_run logs updates without executing in tests/unit/test_user_sync_service.py
- [ ] T061 [P] [US5] Unit test: dry_run logs deletes without executing in tests/unit/test_user_sync_service.py
- [ ] T062 [P] [US5] Unit test: dry_run shows correct summary counts in tests/unit/test_user_sync_service.py

### Implementation for US5

- [ ] T063 [P] [US5] Add dry_run logic to `_create_user()` helper in src/xc_rbac_sync/user_sync_service.py
- [ ] T064 [P] [US5] Add dry_run logic to `_update_user()` helper in src/xc_rbac_sync/user_sync_service.py
- [ ] T065 [P] [US5] Add dry_run logic to `_delete_user()` helper in src/xc_rbac_sync/user_sync_service.py
- [ ] T066 [US5] Ensure dry_run flag is passed through from CLI to UserSyncService in src/xc_rbac_sync/cli.py
- [ ] T067 [US5] Add dry_run indicators to CLI output in src/xc_rbac_sync/cli.py

**Validation**:

- [ ] T068 [US5] Run all dry-run tests (`pytest tests/unit/test_user_sync_service.py::*dry_run*`)
- [ ] T069 [US5] Manual validation: Run sync with --dry-run and verify no F5 XC changes
- [ ] T070 [US5] Manual validation: Verify dry-run summary matches actual operations

**Checkpoint**: Dry-run mode fully functional for user operations. Users can safely preview all changes before execution.

---

## Phase 6: User Story 6 - View Detailed Synchronization Summary (Priority: P3)

**Goal**: Provide comprehensive summary reporting with execution time and error details

**Independent Test**:
1. Run sync with mix of successful and failed operations
2. Verify summary shows: created, updated, deleted, unchanged, error counts
3. Verify execution time is displayed
4. Verify error details include user email and error message

### Tests for US6 (TDD - Write FIRST)

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T071 [P] [US6] Unit test: UserSyncStats.summary() generates correct format in tests/unit/test_user_sync_service.py
- [ ] T072 [P] [US6] Unit test: UserSyncStats.has_errors() detects errors in tests/unit/test_user_sync_service.py
- [ ] T073 [P] [US6] Unit test: Error details collected for failed operations in tests/unit/test_user_sync_service.py
- [ ] T074 [P] [US6] Integration test: Full sync summary with errors in tests/integration/test_user_sync_integration.py

### Implementation for US6

- [ ] T075 [US6] Ensure UserSyncStats.summary() returns formatted string in src/xc_rbac_sync/user_sync_service.py
- [ ] T076 [US6] Ensure error_details collection in all operation helpers in src/xc_rbac_sync/user_sync_service.py
- [ ] T077 [US6] Add execution time tracking to sync workflow in src/xc_rbac_sync/cli.py
- [ ] T078 [US6] Display detailed error list in CLI output if errors exist in src/xc_rbac_sync/cli.py
- [ ] T079 [US6] Add execution time to CLI summary output in src/xc_rbac_sync/cli.py

**Validation**:

- [ ] T080 [US6] Run all summary tests (`pytest tests/unit/test_user_sync_service.py::*summary* tests/unit/test_user_sync_service.py::*error*`)
- [ ] T081 [US6] Manual validation: Run sync and verify summary format
- [ ] T082 [US6] Manual validation: Trigger errors and verify error details in output

**Checkpoint**: Comprehensive summary reporting complete. Users have full visibility into sync operations and errors.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Quality improvements and documentation

- [ ] T083 [P] Run full test suite with coverage (`pytest --cov=src/xc_rbac_sync --cov-report=html`)
- [ ] T084 [P] Verify 80%+ test coverage for all new code (user_sync_service.py, user_utils.py)
- [ ] T085 [P] Run type checking with mypy (`mypy src/`)
- [ ] T086 [P] Run linting with ruff (`ruff check src/`)
- [ ] T087 [P] Run formatting with black (`black src/ tests/`)
- [ ] T088 [P] Add docstrings to all public methods (Google style)
- [ ] T089 Code review: Verify protocol pattern consistency with GroupSyncService
- [ ] T090 Code review: Verify error handling follows existing patterns
- [ ] T091 [P] Update test fixtures in tests/conftest.py with user-specific fixtures
- [ ] T092 Manual end-to-end test following quickstart.md user guide
- [ ] T093 Performance validation: Sync 1,000 users in under 5 minutes
- [ ] T094 Security review: Verify no sensitive data logged (email OK, no passwords)
- [ ] T095 Backwards compatibility check: Verify existing group sync still works

**Checkpoint**: Feature complete, quality validated, ready for production

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **Core Sync - US1, US2, US4 (Phase 3)**: Depends on Foundational phase completion - MVP MUST be complete first
- **User Deletion - US3 (Phase 4)**: Depends on Core Sync (Phase 3) completion
- **Dry-Run - US5 (Phase 5)**: Depends on Core Sync (Phase 3) and User Deletion (Phase 4) completion
- **Summary - US6 (Phase 6)**: Can run in parallel with US3, US5 (different concerns)
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

**CRITICAL MVP Path** (must be completed first):
1. **Phase 2: Foundational** - BLOCKS everything
2. **Phase 3: US1 + US2 + US4** - Core sync (tightly coupled, forms MVP)

**Post-MVP Features** (can proceed after Phase 3):
3. **Phase 4: US3** - User deletion (depends on core sync)
4. **Phase 5: US5** - Dry-run (depends on US3 for delete dry-run)
5. **Phase 6: US6** - Summary (independent, can run parallel with US3/US5)

### Within Each User Story

- Tests MUST be written and FAIL before implementation (TDD)
- Models before services
- Services before CLI integration
- Unit tests before integration tests
- Manual validation after automated tests pass

### Parallel Opportunities

**Phase 1 (Setup)**: All 4 tasks can run in parallel

**Phase 2 (Foundational)**:
- T005, T006 can run in parallel (different functions)
- T007, T008 can run in parallel (different test files)
- T009, T010, T011 can run in parallel (different files)
- T012 runs after T009 (same file)

**Phase 3 (Core Sync - MVP)**:
- All test tasks T014-T023 can run in parallel (different test files)
- XCClient extensions T024-T029 can run in parallel (different methods)
- UserSyncService tasks must be sequential (same file, dependencies)

**Phase 4 (User Deletion)**:
- All test tasks T045-T049 can run in parallel
- Implementation tasks T050-T051 can run in parallel

**Phase 5 (Dry-Run)**:
- All test tasks T059-T062 can run in parallel
- Implementation tasks T063-T065 can run in parallel

**Phase 6 (Summary)**:
- All test tasks T071-T074 can run in parallel
- Implementation tasks mostly sequential (same files)

**Phase 7 (Polish)**:
- All quality checks T083-T087 can run in parallel

---

## Parallel Example: Core Sync MVP (Phase 3)

```bash
# Launch all tests together (TDD - write FIRST):
Task T014: "Unit test: CSV parsing with valid data"
Task T015: "Unit test: CSV parsing with missing columns"
Task T016: "Unit test: CSV parsing with name variations"
Task T017: "Unit test: CSV parsing with status mapping"
Task T018: "Unit test: CSV parsing with group DNs"
Task T019: "Unit test: sync_users creates new user"
Task T020: "Unit test: sync_users updates user"
Task T021: "Unit test: sync_users skips unchanged"
Task T022: "Integration test: Full sync workflow"
Task T023: "Integration test: Idempotency"

# Launch all XCClient extensions together (after tests written):
Task T024: "Add list_users() to XCClient"
Task T025: "Add update_user() to XCClient"
Task T026: "Add get_user() to XCClient"
Task T027: "Unit test: create_user success"
Task T028: "Unit test: update_user success and retry"
Task T029: "Unit test: get_user success"
```

---

## Implementation Strategy

### MVP First (Phases 1-3 Only)

1. Complete Phase 1: Setup validation (5 minutes)
2. Complete Phase 2: Foundational - utility functions and models (2-4 hours)
3. Complete Phase 3: Core Sync - US1, US2, US4 (8-12 hours)
4. **STOP and VALIDATE**: Test core sync independently
5. Deploy/demo MVP (create + update users from CSV)

**MVP Deliverable**: Users can synchronize CSV to F5 XC with create and update operations. Idempotent, safe, production-ready.

### Incremental Delivery

1. **Foundation** (Phases 1-2) → Utilities and models ready (4 hours)
2. **MVP** (Phase 3) → Core sync functional (12 hours) → Deploy
3. **Deletion** (Phase 4) → Add --delete-users capability (4 hours) → Deploy
4. **Safety** (Phase 5) → Enhance dry-run for deletions (2 hours) → Deploy
5. **Observability** (Phase 6) → Detailed summaries (2 hours) → Deploy
6. **Quality** (Phase 7) → Polish and harden (4 hours) → Final release

**Total Estimate**: 28-32 hours for complete feature

### Parallel Team Strategy

With 2 developers:

1. **Both**: Complete Setup + Foundational together (4 hours)
2. **After Foundational**:
   - Developer A: Phase 3 (Core Sync MVP) → Phase 4 (User Deletion)
   - Developer B: Phase 6 (Summary) → Phase 5 (Dry-Run)
3. **Both**: Phase 7 (Polish) together (2 hours)

**Parallel Completion**: ~16-20 hours with 2 developers

---

## Notes

- [P] tasks = different files, no dependencies - can run in parallel
- [Story] label maps task to specific user story for traceability
- US1, US2, US4 are tightly coupled and form the MVP (core sync functionality)
- Each phase includes TDD approach: write failing tests FIRST, then implement
- Tests written before implementation ensure correctness and design validation
- Verify tests fail before implementing (red → green → refactor)
- Commit after each logical group of tasks (e.g., after all tests pass for a phase)
- Stop at any checkpoint to validate independently
- 80%+ test coverage required for all new code
- Follow existing patterns: GroupSyncService, Protocol-based DI, Pydantic models
- Manual validation after each phase ensures quality before proceeding

---

## Task Count Summary

- **Total Tasks**: 95 tasks
- **Phase 1 (Setup)**: 4 tasks
- **Phase 2 (Foundational)**: 9 tasks (BLOCKS all stories)
- **Phase 3 (US1+US2+US4 - MVP)**: 31 tasks (core functionality)
- **Phase 4 (US3 - Deletion)**: 14 tasks
- **Phase 5 (US5 - Dry-Run)**: 13 tasks
- **Phase 6 (US6 - Summary)**: 11 tasks
- **Phase 7 (Polish)**: 13 tasks

**Parallel Opportunities**: 47 tasks marked [P] can run concurrently

**MVP Scope**: Phases 1-3 (44 tasks) deliver core user sync functionality

**Independent Tests**: Each user story phase includes independent test criteria for validation
