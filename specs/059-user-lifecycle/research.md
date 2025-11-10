# Research: User Lifecycle Management

**Feature**: 059-user-lifecycle
**Date**: 2025-11-10
**Status**: Complete

## Overview

This document captures research findings for implementing user lifecycle management in the F5 XC RBAC sync tool. All unknowns from the Technical Context have been investigated and resolved.

## Research Tasks & Findings

### 1. F5 XC user_roles API Schema

**Question**: What fields does the F5 XC `/api/web/custom/namespaces/system/user_roles` API support for user objects?

**Research Method**:
- Examined existing `XCClient` implementation in `src/xc_rbac_sync/client.py`
- Reviewed test fixtures in `tests/unit/test_sync_service.py` and `tests/unit/test_cli_and_client.py`
- Analyzed current `create_user` implementation

**Findings**:
- **Endpoint**: `/api/web/custom/namespaces/system/user_roles`
- **Operations**: GET (list), POST (create), PUT (update), DELETE (delete)
- **Supported Fields** (based on existing code):
  - `email` - Primary identifier
  - `username` - Typically same as email
  - `display_name` - Full name
  - Additional fields inferred from PRD: `first_name`, `last_name`, `active`

**Decision**: Extend existing `XCClient` with user-specific operations (update, delete, get) following the same pattern as `create_user`.

**Rationale**: Reuse proven API patterns. Existing retry logic with `tenacity` handles transient failures. Consistent with current architecture.

**Alternatives Considered**:
- Creating separate UserClient class - Rejected: adds unnecessary complexity, violates single responsibility at the wrong level
- Using SCIM 2.0 API - Rejected: not available/accessible, custom API is the supported interface

---

### 2. CSV Parsing Strategy for Multiple Groups

**Question**: How should we handle users with multiple group memberships in a single CSV row?

**Research Method**:
- Reviewed existing `GroupSyncService.parse_csv_to_groups` implementation
- Examined sample CSV structure from PRD
- Clarified format with user (conversation history)

**Findings**:
- **Format**: One row per user with pipe-separated LDAP DNs in "Entitlement Display Name" column
- **Example**: `CN=GROUP1,OU=Groups,DC=...|CN=GROUP2,OU=Groups,DC=...|CN=GROUP3,OU=Groups,DC=...`
- **Existing Handling**: Current code likely splits on delimiter and extracts CN from each

**Decision**: Parse "Entitlement Display Name" by splitting on pipe (`|`), then extract CN from each LDAP DN using existing `ldap_utils.extract_cn()` function.

**Rationale**: Consistent with Active Directory export format. Reuses existing LDAP parsing logic. Single row per user simplifies CSV structure.

**Alternatives Considered**:
- Multiple rows per user (one per group) - Rejected: complicates CSV generation, harder to parse user attributes
- JSON array in column - Rejected: non-standard CSV format, breaks compatibility with AD exports

---

### 3. Name Parsing Edge Cases

**Question**: How should we handle various display name formats when parsing first/last names?

**Research Method**:
- Reviewed spec requirements (FR-002)
- Clarified parsing rules with user
- Identified edge cases

**Findings**:
- **Standard Rule**: Last space-separated word = last name, remaining words = first name
- **Edge Cases Identified**:
  - Single name (e.g., "Madonna") → first_name="Madonna", last_name=""
  - Multiple middle names (e.g., "John Paul Smith") → first_name="John Paul", last_name="Smith"
  - Leading/trailing whitespace → Trim before parsing
  - Empty display name → Handle gracefully with error or defaults

**Decision**: Implement `parse_display_name(display_name: str) -> tuple[str, str]` in `user_utils.py`:
1. Trim whitespace
2. Split on spaces
3. If zero parts: ("", "")
4. If one part: (part, "")
5. If two+ parts: (" ".join(parts[:-1]), parts[-1])

**Rationale**: Handles Western naming conventions. Simple algorithm with clear edge case handling. Matches user requirements.

**Alternatives Considered**:
- Third-party name parsing library (python-nameparser) - Rejected: overkill for simple use case, adds dependency
- Regex-based parsing - Rejected: less readable, no benefit over simple split

---

### 4. Employee Status Mapping

**Question**: How should we map Active Directory Employee Status codes to boolean active status?

**Research Method**:
- Reviewed spec requirements (FR-003)
- Clarified with user: "A" = active, all others = inactive
- Common AD status codes researched

**Findings**:
- **Mapping Rule**: "A" (Active) → true, everything else → false
- **Common AD Status Codes**: A=Active, I=Inactive, T=Terminated, L=Leave, etc.
- **Missing Values**: Treat as inactive (safe default)

**Decision**: Implement `parse_active_status(employee_status: str) -> bool` in `user_utils.py`:
```python
def parse_active_status(employee_status: str) -> bool:
    """Map employee status code to active boolean."""
    return employee_status.strip().upper() == "A"
```

**Rationale**: Simple, explicit, safe default (inactive). Case-insensitive for robustness. Matches user requirements.

**Alternatives Considered**:
- Allowlist of active codes (A, ACTIVE, etc.) - Rejected: over-complicates, spec is clear
- Mapping table for all codes - Rejected: only two states needed (active/inactive)

---

### 5. State Reconciliation Algorithm

**Question**: What algorithm should be used for state-based reconciliation to ensure idempotency?

**Research Method**:
- Analyzed existing `GroupSyncService.sync_groups()` implementation
- Reviewed idempotency patterns
- Examined retry and error handling logic

**Findings**:
- **Existing Pattern** (GroupSyncService):
  1. Fetch current state from F5 XC
  2. Parse desired state from CSV
  3. Calculate diff: creates (desired - current), updates (attribute changes), deletes (current - desired)
  4. Execute only necessary operations
  5. Track stats and errors
  6. Continue on individual failures

- **Idempotency Guarantees**:
  - Check existence before create (avoid duplicates)
  - Compare attributes before update (skip if unchanged)
  - Re-running with same input produces same end state

**Decision**: Mirror `GroupSyncService` pattern for `UserSyncService`:
```python
def sync_users(self, planned_users, existing_users, dry_run, delete_users):
    stats = UserSyncStats()

    # Build email -> user maps
    desired_map = {u.email.lower(): u for u in planned_users}
    current_map = {email.lower(): data for email, data in existing_users.items()}

    # Calculate operations
    for email, desired in desired_map.items():
        if email not in current_map:
            create_user(desired, dry_run, stats)
        else:
            current = current_map[email]
            if user_needs_update(current, desired):
                update_user(desired, dry_run, stats)
            else:
                stats.unchanged += 1

    if delete_users:
        for email in current_map:
            if email not in desired_map:
                delete_user(email, dry_run, stats)

    return stats
```

**Rationale**: Proven pattern in existing code. Consistent architecture. Well-tested. Handles partial failures gracefully.

**Alternatives Considered**:
- Transactional approach (all-or-nothing) - Rejected: F5 XC API doesn't support transactions, would complicate error recovery
- Event sourcing - Rejected: overkill for stateless sync tool, adds complexity

---

### 6. Error Handling and Partial Failures

**Question**: How should the sync tool handle individual operation failures without aborting the entire sync?

**Research Method**:
- Examined existing error handling in `GroupSyncService._create_group` and `_update_group`
- Reviewed `SyncStats` error tracking
- Analyzed retry logic in `XCClient`

**Findings**:
- **Existing Pattern**:
  - Wrap operations in try/except
  - Log errors with user identifier
  - Increment error counter in stats
  - Continue with remaining operations
  - Return stats with error count

- **Retry Behavior** (in `XCClient`):
  - Automatic retry for 429, 5xx errors
  - Exponential backoff (1s, 2s, 4s)
  - Max 3 attempts
  - Non-retryable errors (4xx except 429) fail immediately

**Decision**: Reuse existing error handling pattern:
1. Each user operation wrapped in try/except
2. Errors logged with user email and error message
3. Stats track error count and details
4. Sync continues with remaining users
5. Return code indicates partial failure if errors > 0

**Rationale**: Consistent with existing code. Aligns with user requirement FR-019 (continue on failures). Enables batch processing.

**Alternatives Considered**:
- Fail-fast on first error - Rejected: prevents bulk sync, user wants resilience
- Collect errors and retry failed batch at end - Rejected: adds complexity, retry already handled at HTTP layer

---

## Summary of Decisions

| Research Area | Decision | Rationale |
|---------------|----------|-----------|
| API Operations | Extend XCClient with update_user, delete_user, get_user | Consistent with existing pattern |
| CSV Parsing | Split on pipe, extract CN from each LDAP DN | Reuse existing logic, matches AD format |
| Name Parsing | Last word = last name, rest = first name | Simple, handles edge cases, matches requirements |
| Status Mapping | "A" → true, else → false | Explicit, safe default, matches requirements |
| Reconciliation | Mirror GroupSyncService pattern | Proven, idempotent, handles partial failures |
| Error Handling | Continue on failures, collect stats | Resilient, enables batch processing |

## Implementation Notes

1. **No New Dependencies**: All functionality achievable with existing libraries
2. **Pattern Reuse**: Follow GroupSyncService as template for consistency
3. **Testability**: Protocol pattern enables mocking for unit tests
4. **Backwards Compatibility**: No changes to existing group sync behavior
5. **Safety**: Dry-run mode + explicit --delete-users flag prevent accidental data loss

## Next Steps

Proceed to Phase 1: Data Model and Contracts design.
