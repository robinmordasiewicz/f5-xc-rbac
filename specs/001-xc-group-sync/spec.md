# Feature Specification: Sync AD Groups to F5 XC IAM

**Feature Branch**: `001-xc-group-sync`  
**Created**: 2025-11-03  
**Status**: Draft  
**Input**: User description: "Automate synchronization of AD group list from CSV into F5 XC IAM via API with idempotent create/update/delete, optional cleanup, dry-run, and detailed logging."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Run idempotent sync from CSV (Priority: P1)

As an operator, I can run the sync with a CSV of group names so that XC groups are created or updated and repeated runs make no further changes when nothing has changed.

**Why this priority**: This is the core value: reliably reflecting CSV state in XC and enabling configuration-as-code.

**Independent Test**: Provide a CSV with 3 groups; run dry-run (no changes), then apply. Re-run with identical CSV and verify no additional changes are reported or applied.

**Acceptance Scenarios**:

1. Given a CSV with groups A,B, When I run in apply mode, Then groups A,B exist with correct descriptions and summary shows created=2, updated=0, deleted=0, errors=0.
2. Given no changes in CSV, When I run again, Then summary shows created=0, updated=0, deleted=0, errors=0.

---

### User Story 2 - Safe cleanup of extraneous groups (Priority: P2)

As an operator, I can enable a cleanup mode that removes groups in XC not present in the CSV, with explicit confirmation or a flag for automation.

**Why this priority**: Ensures drift correction and keeps XC clean while preventing accidental deletions.

**Independent Test**: With CSV listing A,B and XC containing A,B,C, run dry-run with cleanup=true to see C flagged for deletion; then run apply with cleanup=true and confirm C is deleted.

**Acceptance Scenarios**:

1. Given XC contains group C not in CSV, When I run in dry-run with cleanup, Then the report lists C under delete_candidates and no deletion occurs.
2. Given delete flag is enabled, When I run apply with cleanup, Then group C is deleted and summary reflects deleted=1.

---

### User Story 3 - Authentication and early failure (Priority: P3)

As an operator, I authenticate with an API token (or certificate) and the tool fails fast with a clear message if authentication or permissions are insufficient.

**Why this priority**: Prevents wasted time and avoids partial runs; improves supportability and security.

**Independent Test**: Run with an invalid/expired token and verify the tool exits quickly with a clear error and exit code != 0.

**Acceptance Scenarios**:

1. Given an invalid token, When I start a sync, Then the tool exits before any changes with an "authentication failed" message.
2. Given missing permissions, When I attempt to create a group, Then the tool logs a permission error and exits non-zero.

---

### User Story 4 - Optional membership reconciliation (Priority: P3)

As an operator, when the CSV includes an optional members column, I can reconcile group membership (add missing users, remove extras) according to configuration.

**Why this priority**: Enables complete group parity with source of truth where needed.

**Independent Test**: For group A with members u1; CSV lists u1; add u2 to CSV and run; verify u2 is added. Remove u1 in CSV and, if removals are enabled, verify u1 is removed.

**Acceptance Scenarios**:

1. Given CSV lists u1 and XC has none, When I run, Then u1 is added to group A (if membership sync enabled).
2. Given CSV removes u1, When I run with membership removals enabled, Then u1 is removed from group A.

### Edge Cases

- Duplicate group_name rows in CSV → validation error and no apply.
- Invalid group names (unsupported characters/length) → skip with error, continue others; report failures.
- API rate limits / transient 5xx → retry with backoff; stop after max attempts and report.
- Token expired during run → stop with clear error.
- Eventual consistency (newly created group not immediately listable) → brief retry on reads.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The tool MUST read a CSV with at least the column group_name; optional columns include description, members (semicolon-separated), namespace.
- **FR-002**: The tool MUST validate the CSV schema and reject duplicates for group_name before making API calls.
- **FR-003**: The tool MUST authenticate to F5 XC using an API token (or certificate) and fail fast with a clear message on auth failure.
- **FR-004**: The tool MUST list existing user groups in the target namespace(s) and compute the diff vs CSV to determine create/update/no-op (and optional delete).
- **FR-005**: The tool MUST create groups absent in XC and optionally update descriptions for existing groups when changed.
- **FR-006**: The tool MUST be idempotent: a second run with unchanged CSV MUST produce zero changes.
- **FR-007**: The tool MUST support a dry-run mode that logs intended actions without performing them.
- **FR-008**: The tool MUST produce a summary report including counts of created, updated, deleted, skipped, and errors.
- **FR-009**: When cleanup mode is enabled, the tool MUST identify and (on apply) delete groups present in XC but absent from CSV, with explicit confirmation or a non-interactive flag.
- **FR-010**: The tool SHOULD support optional membership reconciliation when a members column is present: add missing users and, if configured, remove extra users.
- **FR-011**: The tool MUST implement retry with backoff for transient API failures and respect rate limits.
- **FR-012**: The tool MUST log errors with sufficient context (group name, operation, status) without exposing secrets.
- **FR-013**: The tool MUST support configuration via CLI flags and/or config file for base URL, auth, namespace(s), mode, dry-run, logging level, and cleanup behavior.
- **FR-014**: The tool MUST use HTTPS/TLS for all API calls and avoid printing sensitive tokens.
- **FR-015**: Destructive operations (deleting groups or removing members) MUST be disabled by default and require explicit opt-in.
- **FR-016**: The tool SHOULD exit with non-zero status if any operation fails; zero if all succeed.
- **FR-017**: The tool SHOULD support multi-namespace processing when requested (iterate per namespace field or config).

Unclear items (explicitly limited):

- **FR-018**: Membership reconciliation scope [NEEDS CLARIFICATION: Is membership sync included in initial release or behind a flag for later?]
- **FR-019**: Cleanup default behavior [NEEDS CLARIFICATION: Should cleanup be entirely disabled by default with no prompts, or allowed with confirmation on interactive runs?]
- **FR-020**: CSV members delimiter [NEEDS CLARIFICATION: Confirm semicolon (;) as default delimiter for members or prefer comma with quoted cells?]

### Key Entities *(include if feature involves data)*

- **Group**: Identified by name; attributes include description; may include members (user emails); belongs to a namespace.
- **User**: Identified by email; may be added to groups when membership reconciliation is enabled.
- **Configuration**: Parameters controlling auth, namespace(s), modes (dry-run, cleanup, membership), and logging.
- **Run Summary**: Counts of actions (created/updated/deleted/skipped/errors) and per-item outcomes for audit.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A CSV with 1,000 groups completes end-to-end in under 3 minutes; 5,000 groups completes in under 10 minutes.
- **SC-002**: Re-running with unchanged CSV results in zero changes (created=0, updated=0, deleted=0) in 100% of cases.
- **SC-003**: Dry-run output matches a subsequent apply run’s action set (within the same environment) with 100% parity.
- **SC-004**: On transient API errors, the tool retries up to the configured limit and succeeds without manual intervention in at least 95% of such cases.
- **SC-005**: Error rate during normal operation remains below 1% of total operations; all errors are logged with actionable messages.
- **SC-006**: Security compliance: no tokens are written to logs; all network calls use TLS.
