# Feature Specification: User Lifecycle Management with CSV Synchronization

**Feature Branch**: `059-user-lifecycle`
**Created**: 2025-11-10
**Status**: Draft
**Input**: User description: "Implement full user lifecycle management with CSV-based synchronization including user create/update/delete operations, enhanced CSV parsing for user attributes (display name, active status), state-based reconciliation treating CSV as source of truth, configurable deletion flags, dry-run support, and detailed summary reporting - replicating SCIM-like idempotent synchronization behavior using F5 XC custom user_roles API"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Synchronize New Users from CSV (Priority: P1)

When a new user appears in the Active Directory CSV export, the system administrator needs to create that user in F5 Distributed Cloud with complete profile information including their name, email, active status, and group memberships.

**Why this priority**: Core functionality - without user creation, no synchronization can happen. This is the foundation for all other user management operations.

**Independent Test**: Can be fully tested by providing a CSV with new users, running the sync tool, and verifying users are created in F5 XC with correct attributes (first name, last name, email, active status).

**Acceptance Scenarios**:

1. **Given** a CSV file contains a user "Alice Anderson" with email "alice@example.com" and Employee Status "A", **When** synchronization runs, **Then** a user is created in F5 XC with first_name="Alice", last_name="Anderson", email="alice@example.com", active=true
2. **Given** a CSV file contains a user "John Paul Smith" with Employee Status "I" (inactive), **When** synchronization runs, **Then** a user is created with first_name="John Paul", last_name="Smith", active=false
3. **Given** a CSV file contains a user with single name "Madonna", **When** synchronization runs, **Then** a user is created with first_name="Madonna", last_name="" (empty)
4. **Given** a user already exists in F5 XC, **When** synchronization runs again with the same CSV, **Then** no duplicate user is created (idempotent)

---

### User Story 2 - Update Existing User Attributes (Priority: P1)

When an existing user's information changes in Active Directory (name change, status change), the system administrator needs to update that user's profile in F5 Distributed Cloud to match the current CSV data.

**Why this priority**: Critical for maintaining data accuracy - users change names (marriage, legal changes), and active status changes frequently (terminations, leaves of absence).

**Independent Test**: Can be tested by creating a user, then running sync with modified CSV data (different name or status), and verifying the user's attributes are updated in F5 XC.

**Acceptance Scenarios**:

1. **Given** user "Alice Anderson" exists in F5 XC, **When** CSV shows her name as "Alice Smith" (married name), **Then** user's first_name and last_name are updated to "Alice" and "Smith"
2. **Given** user with active=true exists, **When** CSV shows Employee Status changed to "T" (terminated), **Then** user's active status is set to false
3. **Given** user attributes match CSV exactly, **When** synchronization runs, **Then** no update API call is made (idempotent - no unnecessary updates)
4. **Given** user exists with multiple attribute changes, **When** synchronization runs, **Then** all changed attributes are updated in a single operation

---

### User Story 3 - Remove Users Not in CSV (Priority: P2)

When a user is removed from Active Directory (termination, transfer), the system administrator needs to optionally delete that user from F5 Distributed Cloud to maintain clean user lists and security compliance.

**Why this priority**: Important for security and compliance, but lower priority than create/update because it's optional (controlled by --delete-users flag) and can be deferred.

**Independent Test**: Can be tested by removing a user from the CSV, running sync with --delete-users flag, and verifying the user is removed from F5 XC. Can also test that without the flag, users are not deleted.

**Acceptance Scenarios**:

1. **Given** user "charlie@example.com" exists in F5 XC but not in CSV, **When** sync runs with --delete-users flag, **Then** user is deleted from F5 XC
2. **Given** user "charlie@example.com" exists in F5 XC but not in CSV, **When** sync runs WITHOUT --delete-users flag, **Then** user is NOT deleted (safe default)
3. **Given** --delete-users flag is enabled, **When** dry-run mode is active, **Then** deletion is logged but not executed
4. **Given** user deletion fails due to API error, **When** sync completes, **Then** error is logged and sync continues with other users

---

### User Story 4 - Parse Enhanced CSV User Attributes (Priority: P1)

When the CSV export contains user profile data in Active Directory format, the system administrator needs to extract and transform this data into F5 XC user attributes, specifically parsing display names into first/last names and mapping employee status codes to active booleans.

**Why this priority**: Foundation for P1 stories - without correct parsing, user data will be incomplete or incorrect.

**Independent Test**: Can be tested by providing CSV with various name formats and status codes, verifying parsed data structure matches expected User objects before any API calls.

**Acceptance Scenarios**:

1. **Given** CSV contains "User Display Name" column with "Alice Anderson", **When** CSV is parsed, **Then** first_name="Alice" and last_name="Anderson"
2. **Given** CSV contains "User Display Name" with "John Paul Smith", **When** CSV is parsed, **Then** first_name="John Paul" and last_name="Smith"
3. **Given** CSV contains "Employee Status" column with "A", **When** CSV is parsed, **Then** active=true
4. **Given** CSV contains "Employee Status" with any value other than "A" (e.g., "I", "T", "L"), **When** CSV is parsed, **Then** active=false
5. **Given** CSV missing required columns ("Email", "Entitlement Display Name", "User Display Name", "Employee Status"), **When** CSV is parsed, **Then** clear error message identifies missing columns

---

### User Story 5 - Preview Changes with Dry-Run Mode (Priority: P2)

Before applying potentially destructive changes (especially deletions), the system administrator needs to preview what actions will be taken without actually executing them, to validate the synchronization logic and prevent accidental data loss.

**Why this priority**: Important safety feature, but not blocking - users can manually review carefully. Increases confidence and reduces risk.

**Independent Test**: Can be tested by running sync with --dry-run flag, verifying that logs show planned actions (create/update/delete) but no actual API calls are made to F5 XC.

**Acceptance Scenarios**:

1. **Given** CSV contains new user "alice@example.com", **When** sync runs with --dry-run, **Then** log shows "Would create user: alice@example.com" but user is NOT created
2. **Given** user needs attribute update, **When** dry-run executes, **Then** log shows "Would update user: bob@example.com (name changed)" but no update occurs
3. **Given** user should be deleted, **When** dry-run with --delete-users executes, **Then** log shows "Would delete user: charlie@example.com" but user remains
4. **Given** dry-run completes, **When** reviewing output, **Then** summary report shows counts of planned creates/updates/deletes

---

### User Story 6 - View Detailed Synchronization Summary (Priority: P3)

After synchronization completes, the system administrator needs a comprehensive summary report showing what actions were taken, how many users were affected, execution time, and any errors encountered, to verify success and troubleshoot issues.

**Why this priority**: Nice-to-have for operational visibility - sync can work without detailed reporting, but it improves troubleshooting and confidence.

**Independent Test**: Can be tested by running sync with various scenarios (new users, updates, errors) and verifying summary report shows accurate counts and error details.

**Acceptance Scenarios**:

1. **Given** sync creates 5 users, updates 3, deletes 2, **When** sync completes, **Then** summary shows "Users: Created: 5, Updated: 3, Deleted: 2"
2. **Given** sync encounters 2 API errors, **When** sync completes, **Then** summary shows "Errors: 2" with details of which users failed and why
3. **Given** sync processes large CSV, **When** sync completes, **Then** summary shows total execution time (e.g., "Duration: 00:05:23")
4. **Given** sync has no changes (all users match), **When** sync completes, **Then** summary shows "Users: Unchanged: 1,245" with no errors

---

### Edge Cases

- What happens when CSV contains duplicate email addresses? (First occurrence processed, duplicates logged as warnings)
- What happens when CSV has malformed LDAP DNs that cannot be parsed? (Row skipped with warning, sync continues)
- What happens when F5 XC API is unreachable during sync? (Retry logic with exponential backoff up to 3 attempts, then fail with clear error)
- What happens when a user exists in F5 XC with different email case (Alice@example.com vs alice@example.com)? (Email comparison is case-insensitive)
- What happens when CSV file is empty or has only headers? (Sync completes successfully with zero operations, warning logged)
- What happens when --delete-users would delete all users because CSV is corrupt/incomplete? (No automatic safeguard - dry-run recommended before destructive operations)
- What happens when display name has trailing/leading spaces? (Spaces are trimmed before parsing)
- What happens when Employee Status column has unexpected values (e.g., null, empty string)? (Treated as inactive - active=false, logged as warning)
- What happens when sync is interrupted mid-execution? (Partial state - some users created/updated, others not; re-running sync will be idempotent and complete remaining work)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST parse CSV files with columns: Email, Entitlement Display Name, User Display Name, Employee Status
- **FR-002**: System MUST extract first name and last name from "User Display Name" column using rule: last space-separated word = last name, remaining words = first name
- **FR-003**: System MUST map "Employee Status" column value "A" to active=true, all other values to active=false
- **FR-004**: System MUST create users in F5 XC that exist in CSV but not in F5 XC, including email, first_name, last_name, display_name, and active status
- **FR-005**: System MUST update existing F5 XC users when CSV attributes (first_name, last_name, active status) differ from current values
- **FR-006**: System MUST compare current user attributes with desired CSV attributes before updating to ensure idempotency (no unnecessary update API calls)
- **FR-007**: System MUST support optional user deletion via --delete-users CLI flag, deleting F5 XC users that do not exist in CSV
- **FR-008**: System MUST default to NOT deleting users unless --delete-users flag is explicitly provided (safe default)
- **FR-009**: System MUST support dry-run mode via --dry-run CLI flag that logs planned actions without executing API calls
- **FR-010**: System MUST generate detailed logs for each user operation: create, update, delete, skip (unchanged)
- **FR-011**: System MUST generate summary report at end of sync showing counts: users created, updated, deleted, unchanged, errors encountered
- **FR-012**: System MUST be idempotent - running sync multiple times with same CSV produces same end state without errors or duplicate operations
- **FR-013**: System MUST handle CSV parsing errors gracefully, logging which rows failed and why, continuing with remaining valid rows
- **FR-014**: System MUST retry transient API errors (429, 5xx) with exponential backoff up to 3 attempts before failing
- **FR-015**: System MUST validate that required CSV columns exist before processing any rows
- **FR-016**: System MUST trim whitespace from display names before parsing to handle formatting inconsistencies
- **FR-017**: System MUST perform case-insensitive email matching when comparing CSV users with F5 XC users
- **FR-018**: System MUST log execution duration in summary report
- **FR-019**: System MUST continue processing remaining users if individual user operations fail, collecting all errors for summary report
- **FR-020**: System MUST use F5 XC custom user_roles API endpoint (/api/web/custom/namespaces/system/user_roles) for all user operations

### Key Entities

- **User**: Represents a person with access to F5 Distributed Cloud
  - Attributes: email (unique identifier), first name, last name, display name, active status (boolean indicating if user can access system)
  - Derived from CSV columns: Email, User Display Name (parsed), Employee Status (mapped to active boolean)
  - Lifecycle: Created when in CSV but not in F5 XC, updated when attributes change, optionally deleted when not in CSV

- **CSV Record**: A row in the Active Directory export file
  - Attributes: Email, User Display Name, Employee Status, Entitlement Display Name (for group memberships)
  - Source of truth: CSV file is authoritative - F5 XC should match CSV exactly after sync

- **Synchronization Operation**: An action taken to reconcile F5 XC state with CSV state
  - Types: Create (new user), Update (attribute change), Delete (user removed), Skip (no change)
  - Each operation logged with user identifier and action details

- **Synchronization Summary**: Aggregate statistics from a sync execution
  - Metrics: counts of creates/updates/deletes/unchanged, error count, execution duration
  - Output: Displayed to user at end of sync for verification

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Administrators can synchronize 1,000 user records from CSV to F5 XC in under 5 minutes
- **SC-002**: Running synchronization twice with identical CSV produces zero operations on second run (100% idempotent)
- **SC-003**: 100% of users with Employee Status "A" in CSV have active=true in F5 XC after sync
- **SC-004**: 100% of users with display name "FirstName LastName" format have correctly parsed first_name and last_name in F5 XC
- **SC-005**: Dry-run mode executes without making any API calls to F5 XC (verified by API monitoring)
- **SC-006**: Summary report accuracy: reported counts match actual F5 XC state changes within 1% margin
- **SC-007**: Synchronization completes successfully even when 10% of users encounter API errors (graceful degradation)
- **SC-008**: Administrators can identify which users failed and why from error logs within 30 seconds
- **SC-009**: Zero users are deleted when --delete-users flag is NOT provided, regardless of CSV content
- **SC-010**: 100% of CSV parsing errors include row number and specific field that failed validation

### Assumptions

- CSV file is UTF-8 encoded with header row containing exact column names: "Email", "User Display Name", "Employee Status", "Entitlement Display Name"
- CSV is comma-delimited with double-quote text qualifiers
- Email addresses in CSV are valid and unique within the file
- F5 XC API credentials (certificate or token) are configured and valid before sync execution
- Network connectivity to F5 XC API is available during sync execution
- Active Directory export process produces consistent CSV format (column order may vary but names are exact)
- F5 XC user_roles API accepts user objects with fields: email, username (same as email), display_name, first_name, last_name, active
- Administrator has appropriate permissions in F5 XC to create/update/delete users via API
- CSV represents complete snapshot of desired user state (not incremental changes)
- Display names in CSV follow Western naming convention (space-separated words with last word as surname)

### Existing Functionality (Preserved)

This feature **enhances** the existing F5 XC user and group synchronization tool with user lifecycle management. The following existing capabilities are preserved and not modified by this feature:

- **F5 XC API credential management** - Certificate-based and token-based authentication (already implemented via `./scripts/setup_xc_credentials.sh` and CLI)
- **Group synchronization** - Creating, updating, and deleting groups based on CSV (existing `GroupSyncService`)
- **LDAP DN parsing** - Extracting group CNs from LDAP Distinguished Names (existing `ldap_utils.py`)
- **Retry logic and error handling** - Exponential backoff for API failures (existing `XCClient` with tenacity)
- **CLI framework** - Click-based command structure with dry-run, log-level, timeout options (existing `cli.py`)
- **Environment configuration** - Loading credentials from `secrets/.env` and environment variables (existing dotenv integration)

### Out of Scope

This feature focuses specifically on **user lifecycle management**. The following are explicitly out of scope for this enhancement:

- Generating or exporting CSV from Active Directory (CSV file must be provided by external process - no change from existing behavior)
- Role assignments and permissions management (roles managed separately in F5 XC - not part of user sync)
- User authentication or password management (F5 XC handles authentication separately - users log in via SSO/SAML)
- Multi-tenancy or cross-namespace operations (operates in "system" namespace only - same as existing group sync)
- Conflict resolution for concurrent edits (last write wins - no locking mechanism, same as existing behavior)
- Backup or rollback of user changes (no automated recovery from failed sync - users can re-run with previous CSV)
- Advanced CSV validation (email format, data type validation happens at F5 XC API layer - same as existing)
- Performance optimization beyond retry logic (no caching, batching, or parallel API calls in initial implementation)
- Configuration file support (environment variables and CLI flags only - consistent with existing tool)
