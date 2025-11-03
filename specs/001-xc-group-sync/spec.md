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

### User Story 4 - Full membership synchronization (Priority: P1)

As an operator, the tool reconciles group membership completely with the CSV as the source of truth, adding missing users and removing users not listed in the CSV for each group.

**Why this priority**: Ensures complete parity between CSV and XC; prevents drift and maintains security posture by removing stale memberships.

**Independent Test**: For group A with members u1,u2 in XC; CSV lists only u1. Run sync and verify u2 is removed from group A. Then add u3 to CSV and verify u3 is added.

**Acceptance Scenarios**:

1. Given CSV lists u1 and XC group has u1,u2, When I run sync, Then u2 is removed from group A and summary shows updated=1.
2. Given CSV adds u3, When I run sync, Then u3 is added to group A and summary shows updated=1.

### Edge Cases

- Duplicate group_name rows in CSV → validation error and no apply.
- Invalid group names (unsupported characters/length) → skip with error, continue others; report failures.
- Users in CSV that don't exist in F5 XC → pre-validation detects missing users; skip affected groups with error, continue others; report failures.
- Malformed LDAP DNs in CSV (missing CN= or invalid escaping) → LDAP parser fails; skip row with error, continue others; report failures.
- API rate limits / transient 5xx → retry with backoff; stop after max attempts and report.
- Token expired during run → stop with clear error.
- Eventual consistency (newly created group not immediately listable) → brief retry on reads.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The tool MUST read the AD export CSV with columns: `User Name`, `Login ID`, `User Display Name`, `Email`, `Entitlement Attribute`, `Entitlement Display Name`, and other metadata fields.
- **FR-001a**: The tool MUST extract group names by parsing the CN (Common Name) from the `Entitlement Display Name` LDAP DN (e.g., "EADMIN_STD" from "CN=EADMIN_STD,OU=Groups,DC=example,DC=com").
- **FR-001b**: The tool MUST aggregate all users belonging to each group by grouping rows with the same extracted group name.
- **FR-002**: The tool MUST validate the CSV schema (required columns present) and fail fast if critical columns are missing.
- **FR-003**: The tool MUST authenticate to F5 XC using an API token (via `Authorization: APIToken <token>` header) and fail fast with a clear message on auth failure (401/403).
- **FR-004**: The tool MUST list existing user groups in the "system" namespace via `GET /api/web/custom/namespaces/system/user_groups` and compute the diff vs CSV.
- **FR-005**: The tool MUST create groups absent in XC via `POST /api/web/custom/namespaces/system/user_groups` with `name`, `display_name`, and `usernames` (user emails from CSV).
- **FR-006**: The tool MUST update existing groups when membership changes, using `PUT /api/web/custom/namespaces/system/user_groups/{name}` to replace the `usernames` array.
- **FR-006a**: The tool MUST be idempotent: a second run with unchanged CSV MUST produce zero changes (created=0, updated=0).
- **FR-007**: The tool MUST support a dry-run mode (`--dry-run` flag) that logs intended actions without performing create/update/delete operations.
- **FR-008**: The tool MUST produce a summary report including counts of: groups created, groups updated, groups deleted, groups skipped (no change), errors.
- **FR-009**: When cleanup mode is enabled (`--cleanup` flag), the tool MUST identify groups present in XC but absent from CSV and delete them via `DELETE /api/web/custom/namespaces/system/user_groups/{name}`.
- **FR-010**: The tool MUST pre-validate that all unique user emails from the CSV exist in F5 XC via `GET /api/web/custom/namespaces/system/user_roles` before performing group operations. The CSV is the authoritative source of truth.
- **FR-010a**: If users exist in F5 XC but are not present in the CSV, the tool MUST remove them from all XC user groups during sync operations (treating CSV as complete user roster).
- **FR-011**: The tool MUST implement retry with exponential backoff for transient API failures (5xx errors, rate limit 429) with configurable max retries (default: 3).
- **FR-012**: The tool MUST log errors with sufficient context (group name, operation, HTTP status, response message) without exposing API tokens in logs.
- **FR-013**: The tool MUST support configuration via CLI flags for: API base URL, auth token, dry-run, cleanup mode, logging level (debug/info/warn/error), max retries.
- **FR-014**: The tool MUST use HTTPS/TLS for all API calls (enforce certificate validation) and never print API tokens in logs or stdout.
- **FR-015**: Destructive operations (deleting groups via `--cleanup`) MUST be disabled by default and require explicit opt-in flag.
- **FR-016**: The tool MUST exit with status code 0 if all operations succeed; non-zero (1) if any operation fails or validation errors occur.
- **FR-017**: The tool MUST operate exclusively in the "system" namespace for all user group operations (hardcoded), as mandated by F5 XC API design. Multi-namespace support is out of scope.
- **FR-018**: The tool MUST set the `display_name` field for each user group to the extracted CN value (same as `name`), providing consistent human-readable group identifiers.
- **FR-019**: The tool MUST implement full membership synchronization: when updating groups, replace the entire `usernames` array with users from CSV. Users present in XC group but absent from CSV for that group MUST be removed (CSV is source of truth).
- **FR-020**: The tool MUST parse CSV files conforming to RFC 4180 format only (comma delimiter, double-quote escaping, CRLF line endings). Non-standard CSV formats are not supported.
- **FR-021**: The tool MUST use a proper LDAP DN parser library (e.g., `ldap3` for Python, `go-ldap` for Go) to extract CN from `Entitlement Display Name` LDAP DNs, and MUST validate extracted group names against F5 XC API naming constraints (length, allowed characters).

### Key Entities *(include if feature involves data)*

#### CSV Structure (Active Directory Export)

Based on the provided `User-Database.csv`, the input file contains:

**Available Columns**:
- `User Name`: AD username (e.g., "USER001")
- `Login ID`: Full LDAP DN (e.g., "CN=USER001,OU=Developers,OU=All Users,DC=example,DC=com")
- `User Display Name`: Full name (e.g., "Alice Anderson")
- `Email`: User email address (e.g., "alice.anderson@example.com")
- `Entitlement Attribute`: Always "memberOf" for group membership
- `Entitlement Display Name`: Group LDAP DN (e.g., "CN=EADMIN_STD,OU=Groups,DC=example,DC=com")
- Additional fields: Application Name, Job Title, Manager details, etc.

**Relevant Mapping for F5 XC**:
- **Group Name**: Extract CN from `Entitlement Display Name` (e.g., "EADMIN_STD" from "CN=EADMIN_STD,OU=Groups,DC=example,DC=com")
- **User Email**: Use `Email` column directly (F5 XC identifies users by email)
- **Group Display Name**: Set to extracted CN value (same as name)
- **Source of Truth**: CSV is authoritative; XC state will be reconciled to match CSV exactly (add missing groups/users, remove extras)

#### F5 XC API Data Model

**User Group Object** (`ves.io.schema.user_group`):
- `name` (string, required): Internal name/identifier (extracted group CN from LDAP DN)
- `display_name` (string, optional): Human-readable name
- `description` (string, optional): Descriptive text
- `usernames` (array of strings): List of user email addresses
- `namespace_roles` (array of objects): RBAC role assignments per namespace
- `namespace`: Always "system" for user groups

**API Endpoints**:
- Create: `POST /api/web/custom/namespaces/system/user_groups`
- Update: `PUT /api/web/custom/namespaces/system/user_groups/{name}`
- List: `GET /api/web/custom/namespaces/system/user_groups`
- Delete: `DELETE /api/web/custom/namespaces/system/user_groups/{name}`
- Add users to group: `PUT /api/web/custom/namespaces/system/users/group_add`
- Remove users from group: `PUT /api/web/custom/namespaces/system/users/group_remove`

**User Management** (`ves.io.schema.user`):
- Users identified by `email` (username field, e.g., "user1@company.com")
- User operations via `/api/web/custom/namespaces/system/user_roles`
- Users must exist in F5 XC before adding to groups

#### Entities

- **Group**: Identified by `name` (extracted CN); attributes: `display_name`, `description`, `usernames` (emails); namespace always "system".
- **User**: Identified by `email`; must exist in F5 XC tenant before group membership operations.
- **Configuration**: Parameters controlling auth, target namespace(s), modes (dry-run, cleanup, membership), CSV parsing, and logging.
- **Run Summary**: Counts of actions (created/updated/deleted/skipped/errors) and per-item outcomes for audit.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A CSV with 1,000 groups completes end-to-end in under 3 minutes; 5,000 groups completes in under 10 minutes.
- **SC-002**: Re-running with unchanged CSV results in zero changes (created=0, updated=0, deleted=0) in 100% of cases.
- **SC-003**: Dry-run output matches a subsequent apply run’s action set (within the same environment) with 100% parity.
- **SC-004**: On transient API errors, the tool retries up to the configured limit and succeeds without manual intervention in at least 95% of such cases.
- **SC-005**: Error rate during normal operation remains below 1% of total operations; all errors are logged with actionable messages.
- **SC-006**: Security compliance: no tokens are written to logs; all network calls use TLS.

---

## Clarifications *(session: 2025-11-03)*

### Session Context

This clarification session was initiated after examining the actual AD export CSV structure (`User-Database.csv`) and the F5 Distributed Cloud API documentation for user and user_group endpoints. The CSV contains LDAP-style data with group memberships expressed as `memberOf` attributes pointing to LDAP Distinguished Names (DNs).

### Outstanding Questions

#### Q1: User Existence Validation (FR-010)

**Context**: F5 XC API requires users to exist in the tenant before adding them to groups. The CSV contains user emails, but we don't know if these users are already provisioned in F5 XC.

**Question**: How should the tool handle users that don't exist in F5 XC?

**Options**:
1. **Pre-validate**: Query user existence via `GET /api/web/custom/namespaces/system/user_roles` for each unique email before group operations. Skip groups with non-existent users and log warnings.
2. **Optimistic add**: Attempt to add users to groups and handle 404 errors gracefully (log warning, continue with other groups).
3. **Auto-create users**: Create missing users via `POST /api/web/custom/namespaces/system/user_roles` with basic info from CSV (email, first_name, last_name, etc.).

**Recommendation**: Option 1 (pre-validate) - safer for initial release, prevents partial group membership.

**Impact**: Affects FR-010, error handling logic, and API call count.

---

#### Q2: Group Display Name Derivation (FR-018)

**Context**: The CSV has no explicit description column. F5 XC groups have both `name` (identifier) and `display_name` (human-readable). The `name` will be the extracted CN from the LDAP DN.

**Question**: What should populate the `display_name` field for user groups?

**Options**:
1. **Use CN value**: Set `display_name` = `name` (e.g., "EADMIN_STD")
2. **Derive from Application Name**: Use the `Application Name` column from CSV (e.g., "Active Directory")
3. **Construct from full DN**: Use full `Entitlement Display Name` (e.g., "CN=EADMIN_STD,OU=Groups,DC=example,DC=com")
4. **Custom prefix**: e.g., "AD Group: EADMIN_STD"
5. **Leave blank**: Omit `display_name` field (API allows optional)

**Recommendation**: Option 1 (use CN value) - simple, consistent, human-readable.

**Impact**: Affects FR-018, group creation payload structure.

---

#### Q3: Membership Removal Behavior (FR-019)

**Context**: When updating groups, the F5 XC API replaces the entire `usernames` array. If a user exists in the XC group but their row is missing from the CSV (e.g., user left company, entitlement revoked), should they be removed?

**Question**: Should membership updates remove users not present in the CSV for a given group?

**Options**:
1. **Full replacement (sync to CSV)**: Replace the entire `usernames` array with users from CSV. Users not in CSV are removed.
2. **Append-only**: Only add users from CSV that are missing; never remove existing users.
3. **Configurable via flag**: Default to append-only (`--membership-mode=append`), opt-in to full sync (`--membership-mode=sync`).

**Recommendation**: Option 3 (configurable) - Start with append-only as safe default; allow sync mode for environments needing strict parity.

**Impact**: Affects FR-006, FR-019, update operation logic, and dry-run reporting.

---

#### Q4: CSV Format Validation (FR-020)

**Context**: The provided CSV appears to be standard comma-delimited with double-quote escaping (RFC 4180).

**Question**: Should the tool support only standard CSV format, or also handle variations (semicolon delimiters, no quoting)?

**Options**:
1. **RFC 4180 only**: Comma delimiter, double-quote escaping, CRLF line endings.
2. **Auto-detect**: Try to detect delimiter and quoting style.
3. **Configurable delimiter**: Accept `--csv-delimiter` flag (default: comma).

**Recommendation**: Option 1 (RFC 4180 only) - Simple, predictable. AD exports are typically standard CSV.

**Impact**: Affects FR-001, FR-020, CSV parsing library choice.

---

#### Q5: Multi-Namespace Support (FR-017)

**Context**: Per F5 XC API documentation, all user groups are in the "system" namespace. The CSV has no namespace column.

**Question**: Is multi-namespace support needed for user groups?

**Options**:
1. **Single namespace (system)**: Hardcode `namespace: "system"` for all group operations.
2. **Defer to future**: Document as out-of-scope for v1; revisit if API behavior changes.

**Recommendation**: Option 1 - API design dictates system namespace for user groups. No multi-namespace needed.

**Impact**: Simplifies FR-017, configuration, and validation logic.

---

#### Q6: LDAP DN Parsing Edge Cases

**Context**: The tool must parse CNs from LDAP DNs like "CN=EADMIN_STD,OU=Groups,DC=example,DC=com". Some DNs may have special characters, escaping, or multiple CN components.

**Question**: How should the tool handle malformed or complex LDAP DNs?

**Options**:
1. **Strict parsing**: Use LDAP DN parser library (e.g., `ldap3` in Python, `go-ldap` in Go). Fail on malformed DNs with clear error.
2. **Simple regex**: Extract CN with regex `CN=([^,]+)`. Log warning if format unexpected.
3. **Validate against F5 XC naming rules**: After extraction, validate group name against XC constraints (length, allowed characters).

**Recommendation**: Option 1 + 3 - Use proper LDAP parser, then validate against XC API naming rules (see API docs for constraints).

**Impact**: Affects FR-001a, error handling, dependency choices.

---

### Resolved Answers

- **Q1: User Existence Validation** → Pre-validate users exist before adding to groups. CSV is the source of truth; users not in CSV should be removed from XC console.
- **Q2: Group Display Name Derivation** → Use extracted CN value (e.g., "EADMIN_STD")
- **Q3: Membership Removal Behavior** → Default to full sync mode (CSV as source of truth). If user membership is removed from group in CSV, remove user from XC group.
- **Q4: CSV Format Validation** → RFC 4180 only (standard comma-delimited)
- **Q5: Multi-Namespace Support** → Single "system" namespace (API constraint)
- **Q6: LDAP DN Parsing** → Use proper LDAP parser library + validate against XC naming rules
