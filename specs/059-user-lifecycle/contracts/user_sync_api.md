# API Contract: User Synchronization Service

**Feature**: 059-user-lifecycle
**Date**: 2025-11-10
**Status**: Design Phase

## Overview

This document defines the API contracts for user lifecycle management in the F5 XC user and group synchronization tool. All contracts follow Protocol-based dependency injection patterns consistent with the existing `GroupRepository` and `GroupSyncService` architecture.

## Protocol Definitions

### UserRepository Protocol

**Location**: `src/xc_user_group_sync/protocols.py`

**Purpose**: Abstraction for user management operations, enabling dependency injection and testability.

```python
from typing import Protocol, Dict, Any

class UserRepository(Protocol):
    """Protocol for user management operations against F5 XC API.

    This protocol defines the contract for user CRUD operations,
    allowing different implementations (production XCClient, test mocks)
    to be used interchangeably.
    """

    def list_users(self, namespace: str = "system") -> Dict[str, Any]:
        """List all users with roles from F5 XC.

        Args:
            namespace: F5 XC namespace (default: "system")

        Returns:
            Dictionary mapping email addresses to user data:
            {
                "alice@example.com": {
                    "email": "alice@example.com",
                    "username": "alice@example.com",
                    "display_name": "Alice Anderson",
                    "first_name": "Alice",
                    "last_name": "Anderson",
                    "active": true,
                    "groups": ["EADMIN_STD", "DEVELOPERS"]
                },
                ...
            }

        Raises:
            requests.exceptions.RequestException: On API communication failure
            ValueError: On invalid response format
        """
        ...

    def create_user(
        self,
        user: Dict[str, Any],
        namespace: str = "system"
    ) -> Dict[str, Any]:
        """Create new user in F5 XC.

        Args:
            user: User data dictionary with keys:
              - email (required): User email address
              - username (optional): Defaults to email if not provided
              - display_name (required): Full name
              - first_name (required): Given name
              - last_name (required): Family name
              - active (optional): Boolean, defaults to True
              - groups (optional): List of group names
            namespace: F5 XC namespace (default: "system")

        Returns:
            Created user data as returned by F5 XC API

        Raises:
            requests.exceptions.HTTPError: On 4xx/5xx responses
            requests.exceptions.RequestException: On network failures
            ValueError: On invalid user data format

        Notes:
          - Automatically retries 429 and 5xx errors with exponential backoff
          - Maximum 3 retry attempts via tenacity decorator
        """
        ...

    def update_user(
        self,
        email: str,
        user: Dict[str, Any],
        namespace: str = "system"
    ) -> Dict[str, Any]:
        """Update existing user in F5 XC.

        Args:
            email: User email address (primary identifier)
            user: Updated user data (same structure as create_user)
            namespace: F5 XC namespace (default: "system")

        Returns:
            Updated user data as returned by F5 XC API

        Raises:
            requests.exceptions.HTTPError: On 4xx/5xx responses (404 if user not found)
            requests.exceptions.RequestException: On network failures
            ValueError: On invalid user data format

        Notes:
          - Email is used as unique identifier for user lookup
          - Partial updates not supported - full user object required
          - Automatically retries 429 and 5xx errors
        """
        ...

    def delete_user(
        self,
        email: str,
        namespace: str = "system"
    ) -> None:
        """Delete user from F5 XC.

        Args:
            email: User email address (primary identifier)
            namespace: F5 XC namespace (default: "system")

        Returns:
            None on successful deletion

        Raises:
            requests.exceptions.HTTPError: On 4xx/5xx responses (404 if user not found)
            requests.exceptions.RequestException: On network failures

        Notes:
          - Deletion is permanent and cannot be undone
          - Automatically retries 429 and 5xx errors
          - 404 errors are NOT retried (user already deleted)
        """
        ...

    def get_user(
        self,
        email: str,
        namespace: str = "system"
    ) -> Dict[str, Any]:
        """Get single user by email from F5 XC.

        Args:
            email: User email address (primary identifier)
            namespace: F5 XC namespace (default: "system")

        Returns:
            User data dictionary (same structure as list_users values)

        Raises:
            requests.exceptions.HTTPError: On 4xx/5xx responses (404 if user not found)
            requests.exceptions.RequestException: On network failures

        Notes:
          - Primarily used for individual user lookups
          - For bulk operations, prefer list_users() for efficiency
        """
        ...
```text
---

## Service Layer Contract

### UserSyncService Class

**Location**: `src/xc_user_group_sync/user_sync_service.py`

**Purpose**: Business logic for user lifecycle management with state-based reconciliation.

```python
from typing import List, Dict, Protocol
from dataclasses import dataclass, field
from xc_user_group_sync.models import User
from xc_user_group_sync.protocols import UserRepository

@dataclass
class UserSyncStats:
    """Statistics from user synchronization operation.

    Attributes:
        created: Number of users created in F5 XC
        updated: Number of users updated in F5 XC
        deleted: Number of users deleted from F5 XC
        unchanged: Number of users that matched and required no changes
        errors: Total number of errors encountered
        error_details: List of error dictionaries with user and error info
    """
    created: int = 0
    updated: int = 0
    deleted: int = 0
    unchanged: int = 0
    errors: int = 0
    error_details: List[Dict[str, str]] = field(default_factory=list)

    def summary(self) -> str:
        """Generate human-readable summary."""
        return (
            f"Users: created={self.created}, updated={self.updated}, "
            f"deleted={self.deleted}, unchanged={self.unchanged}, "
            f"errors={self.errors}"
        )

    def has_errors(self) -> bool:
        """Check if any errors occurred."""
        return self.errors > 0

class UserSyncService:
    """Service for synchronizing users between CSV and F5 XC.

    This service implements state-based reconciliation, treating CSV
    as the source of truth and synchronizing F5 XC to match.

    Attributes:
        repository: UserRepository implementation for F5 XC API operations
        retry_wait: Retry wait strategy (from tenacity, optional)
        retry_stop: Retry stop strategy (from tenacity, optional)
    """

    def __init__(
        self,
        repository: UserRepository,
        retry_wait=None,
        retry_stop=None
    ):
        """Initialize with user repository.

        Args:
            repository: UserRepository implementation (typically XCClient)
            retry_wait: tenacity wait strategy for retries (optional)
            retry_stop: tenacity stop strategy for retries (optional)

        Example:
            >>> from tenacity import wait_exponential, stop_after_attempt
            >>> client = XCClient(...)
            >>> service = UserSyncService(
            ...     repository=client,
            ...     retry_wait=wait_exponential(multiplier=1, min=1, max=10),
            ...     retry_stop=stop_after_attempt(3)
            ... )
        """
        ...

    def parse_csv_to_users(self, csv_path: str) -> List[User]:
        """Parse CSV file to User objects with enhanced attributes.

        Args:
            csv_path: Absolute path to CSV file

        Returns:
            List of User objects parsed from CSV

        Raises:
            FileNotFoundError: If CSV file doesn't exist
            ValueError: If required CSV columns are missing
            csv.Error: On CSV parsing failures

        Behavior:
          1. Validate required columns exist: "Email", "User Display Name",
            "Employee Status", "Entitlement Display Name"
          2. For each row:
            - Extract email (required)
            - Parse display_name to first_name and last_name
            - Map employee status to active boolean ("A" → True, else → False)
            - Extract group CNs from pipe-separated LDAP DNs
            - Create User object with Pydantic validation
          3. Skip rows with validation errors (log warnings)
          4. Return list of valid User objects

        CSV Column Mapping:
          - "Email" → User.email
          - "User Display Name" → User.display_name, first_name, last_name (parsed)
          - "Employee Status" → User.active (mapped: "A" → True, else → False)
          - "Entitlement Display Name" → User.groups (pipe-separated LDAP DNs → CNs)

        Example:
            >>> service.parse_csv_to_users("users.csv")
            [
                User(email="alice@example.com", first_name="Alice", ...),
                User(email="bob@example.com", first_name="Bob", ...)
            ]

        Notes:
          - Email comparison is case-insensitive (lowercased for consistency)
          - Duplicate emails: first occurrence kept, duplicates logged as warnings
          - Missing required columns: raises ValueError immediately
          - Malformed rows: logged and skipped, sync continues
        """
        ...

    def fetch_existing_users(self) -> Dict[str, Dict]:
        """Fetch users from F5 XC, return email -> user_data map.

        Returns:
            Dictionary mapping lowercase email to user data:
            {
                "alice@example.com": {
                    "email": "alice@example.com",
                    "username": "alice@example.com",
                    "display_name": "Alice Anderson",
                    "first_name": "Alice",
                    "last_name": "Anderson",
                    "active": True,
                    "groups": ["EADMIN_STD"]
                },
                ...
            }

        Raises:
            requests.exceptions.RequestException: On API failures

        Notes:

            - Calls repository.list_users() to fetch from F5 XC
            - Lowercases email keys for case-insensitive comparison
            - Returns empty dict if no users exist (not an error)

        """
        ...

    def sync_users(
        self,
        planned_users: List[User],
        existing_users: Dict[str, Dict],
        dry_run: bool = False,
        delete_users: bool = False
    ) -> UserSyncStats:
        """Reconcile users with F5 XC using state-based synchronization.

        Args:
            planned_users: Desired user state from CSV
            existing_users: Current user state from F5 XC (from fetch_existing_users)
            dry_run: If True, log operations without executing (default: False)
            delete_users: If True, delete F5 XC users not in CSV (default: False)

        Returns:
            UserSyncStats with operation counts and error details

        Algorithm:
          1. Build email -> user maps (lowercase emails for comparison)
          2. For each desired user:
            a. If not in F5 XC → CREATE
            b. If in F5 XC but attributes differ → UPDATE
            c. If in F5 XC and attributes match → SKIP (unchanged)
          3. If delete_users=True:
            For each F5 XC user not in desired state → DELETE
          4. Collect stats and errors for summary report

        Idempotency Guarantee:

            - Running multiple times with same CSV produces same end state
            - No unnecessary API calls (skip unchanged users)
            - Safe to re-run after partial failures

        Error Handling:

            - Individual operation failures logged and collected
            - Sync continues with remaining users (no fail-fast)
            - All errors reported in UserSyncStats.error_details

        Dry-Run Behavior:

            - All operations logged with "Would create/update/delete" prefix
            - No API calls executed to F5 XC
            - Stats reflect planned operations, not actual

        Example:
            >>> stats = service.sync_users(
            ...     planned_users=csv_users,
            ...     existing_users=xc_users,
            ...     dry_run=True,
            ...     delete_users=False
            ... )
            >>> print(stats.summary())
            Users: created=5, updated=3, deleted=0, unchanged=1065, errors=0

        Notes:

            - Attribute comparison is deep (all fields checked)
            - Group list order matters for comparison
            - Email is primary identifier (case-insensitive)
            - delete_users=False is safe default (no accidental deletions)

        """
        ...
```text

---

## Utility Functions Contract

### User Parsing Utilities

**Location**: `src/xc_user_group_sync/user_utils.py`

```python
def parse_display_name(display_name: str) -> tuple[str, str]:
    """Parse display name into (first_name, last_name).

    Args:
        display_name: Full name from CSV (e.g., "Alice Anderson")

    Returns:
        Tuple of (first_name, last_name)

    Rules:

        - Last space-separated word → last_name
        - Remaining words → first_name
        - Whitespace trimmed before parsing

    Examples:
        >>> parse_display_name("Alice Anderson")
        ('Alice', 'Anderson')
        >>> parse_display_name("John Paul Smith")
        ('John Paul', 'Smith')
        >>> parse_display_name("Madonna")
        ('Madonna', '')
        >>> parse_display_name("  Alice  Anderson  ")
        ('Alice', 'Anderson')

    Edge Cases:

        - Empty string → ('', '')
        - Single name → (name, '')
        - Multiple spaces → normalized to single space

    """
    ...

def parse_active_status(employee_status: str) -> bool:
    """Map employee status code to active boolean.

    Args:
        employee_status: Status code from CSV (e.g., "A", "I", "T")

    Returns:
        True if status is "A" (Active), False otherwise

    Rules:

        - "A" (case-insensitive) → True
        - All other values → False
        - Whitespace trimmed before comparison

    Examples:
        >>> parse_active_status("A")
        True
        >>> parse_active_status("a")  # case-insensitive
        True
        >>> parse_active_status("I")  # Inactive
        False
        >>> parse_active_status("T")  # Terminated
        False
        >>> parse_active_status("  A  ")  # with whitespace
        True

    Notes:

        - Safe default: unknown codes treated as inactive
        - Common AD codes: A=Active, I=Inactive, T=Terminated, L=Leave

    """
    ...
```text

---

## XCClient Extensions Contract

### Extended API Client

**Location**: `src/xc_user_group_sync/client.py`

**Modifications**: Add user-specific methods to existing `XCClient` class.

```python
class XCClient:
    """F5 XC API client with user and group operations.

    Existing methods preserved:

        - list_user_roles(): List users (existing, now aliased by list_users)
        - create_user(): Create user (existing)
        - list_groups(): List groups
        - create_group(): Create group
        - update_group(): Update group
        - delete_group(): Delete group

    New methods for user lifecycle:

        - list_users(): Alias for list_user_roles (consistent naming)
        - update_user(): Update existing user
        - delete_user(): Delete user
        - get_user(): Get single user by email

    """

    # EXISTING METHODS (preserved)

    def list_user_roles(self, namespace: str = "system") -> Dict[str, Any]:
        """List users via user_roles API (existing implementation)."""
        ...

    def create_user(self, user: Dict[str, Any], namespace: str = "system") -> Dict[str, Any]:
        """Create user (existing implementation with tenacity retry)."""
        ...

    # NEW METHODS (to be added)

    def list_users(self, namespace: str = "system") -> Dict[str, Any]:
        """List users (alias for list_user_roles for naming consistency).

        Returns:
            Same as list_user_roles()

        Notes:

            - Simple alias to maintain consistent naming with other repositories
            - Existing code using list_user_roles() continues to work

        """
        return self.list_user_roles(namespace)

    def update_user(
        self,
        email: str,
        user: Dict[str, Any],
        namespace: str = "system"
    ) -> Dict[str, Any]:
        """Update user via PUT to user_roles/{email}.

        Implementation:

            - Endpoint: PUT /api/web/custom/namespaces/{namespace}/user_roles/{email}
            - Headers: Same as create_user (cert auth)
            - Body: Full user object (same structure as create_user)
            - Retry: Same tenacity decorator as create_user

        Returns:
            Updated user data from F5 XC API response

        Raises:
            requests.exceptions.HTTPError: On 4xx/5xx responses

        Notes:

            - Email in URL must be URL-encoded
            - Requires full user object (partial updates not supported)
            - Automatically retries 429 and 5xx with exponential backoff

        """
        ...

    def delete_user(
        self,
        email: str,
        namespace: str = "system"
    ) -> None:
        """Delete user via DELETE to user_roles/{email}.

        Implementation:

            - Endpoint: DELETE /api/web/custom/namespaces/{namespace}/user_roles/{email}
            - Headers: Same as create_user (cert auth)
            - Body: None
            - Retry: Same tenacity decorator as create_user (but NOT for 404)

        Returns:
            None on successful deletion

        Raises:
            requests.exceptions.HTTPError: On 4xx/5xx responses

        Notes:

            - 404 errors should NOT be retried (user already deleted)
            - Deletion is permanent and irreversible
            - Automatically retries 429 and 5xx (except 404)

        """
        ...

    def get_user(
        self,
        email: str,
        namespace: str = "system"
    ) -> Dict[str, Any]:
        """Get user via GET to user_roles/{email}.

        Implementation:

            - Endpoint: GET /api/web/custom/namespaces/{namespace}/user_roles/{email}
            - Headers: Same as create_user (cert auth)
            - Retry: Same tenacity decorator as create_user

        Returns:
            User data dictionary

        Raises:
            requests.exceptions.HTTPError: On 4xx/5xx responses (404 if not found)

        Notes:

            - Used for individual user lookups
            - For bulk operations, prefer list_users() for efficiency
            - Automatically retries 429 and 5xx

        """
        ...
```text

---

## CLI Contract Extensions

### Command-Line Interface

**Location**: `src/xc_user_group_sync/cli.py`

**Modifications**: Add `--delete-users` flag to existing `sync` command.

```python
@click.command()
@click.option("--csv", required=True, help="Path to CSV file")
@click.option("--dry-run", is_flag=True, help="Preview changes without executing")
@click.option("--delete-users", is_flag=True, help="Delete F5 XC users not in CSV (default: False)")

# ... existing options ...

def sync(csv: str, dry_run: bool, delete_users: bool, ...):
    """Synchronize users and groups from CSV to F5 XC.

    New Behavior:

        - Parses CSV for both users and groups (existing + new)
        - Syncs users if CSV contains user columns
        - Syncs groups (existing behavior preserved)
        - Displays combined summary with user and group stats

    Flags:

        --delete-users: Enable deletion of F5 XC users not in CSV

                        (default: False for safety)
                        Recommended: Always test with --dry-run first

    Example:

        # Preview user sync with deletions

        xc-group-sync sync --csv users.csv --delete-users --dry-run

        # Execute user sync with deletions

        xc-group-sync sync --csv users.csv --delete-users

        # Sync users without deletions (safe default)

        xc-group-sync sync --csv users.csv
    """
    ...
```text
---

## Testing Contracts

### Unit Test Requirements

**Location**: `tests/unit/test_user_sync_service.py`

**Coverage Requirements**: 80%+ coverage for all user-specific code

```python
class TestUserSyncService:
    """Unit tests for UserSyncService."""

    def test_parse_csv_to_users_valid(self):
        """Test CSV parsing with valid data."""
        ...

    def test_parse_csv_to_users_missing_columns(self):
        """Test CSV parsing raises ValueError on missing required columns."""
        ...

    def test_parse_display_name_variations(self):
        """Test name parsing edge cases (single name, multiple names, whitespace)."""
        ...

    def test_parse_active_status_mapping(self):
        """Test employee status mapping (A → True, others → False)."""
        ...

    def test_sync_users_creates_new(self):
        """Test user creation when not in F5 XC."""
        ...

    def test_sync_users_updates_changed(self):
        """Test user update when attributes differ."""
        ...

    def test_sync_users_skips_unchanged(self):
        """Test no operation when user matches (idempotency)."""
        ...

    def test_sync_users_deletes_with_flag(self):
        """Test user deletion when --delete-users=True."""
        ...

    def test_sync_users_preserves_without_flag(self):
        """Test no deletion when --delete-users=False."""
        ...

    def test_sync_users_dry_run(self):
        """Test dry-run logs operations without executing."""
        ...

    def test_sync_users_continues_on_errors(self):
        """Test sync continues with remaining users after individual failures."""
        ...
```text

**Location**: `tests/unit/test_client.py`

```python
class TestXCClientUserOperations:
    """Unit tests for XCClient user-specific methods."""

    def test_update_user_success(self):
        """Test successful user update."""
        ...

    def test_update_user_retry_on_429(self):
        """Test retry logic on rate limit."""
        ...

    def test_delete_user_success(self):
        """Test successful user deletion."""
        ...

    def test_delete_user_404_not_retried(self):
        """Test 404 errors not retried (user already deleted)."""
        ...

    def test_get_user_success(self):
        """Test successful user retrieval."""
        ...
```text

### Integration Test Requirements

**Location**: `tests/integration/test_user_sync_integration.py`

```python
class TestUserSyncIntegration:
    """End-to-end integration tests with mock F5 XC API."""

    def test_full_sync_workflow(self):
        """Test complete sync: parse CSV → fetch existing → reconcile → report."""
        ...

    def test_idempotency(self):
        """Test running sync twice with same CSV produces no changes on second run."""
        ...

    def test_partial_failure_handling(self):
        """Test sync completes with partial failures, reports errors."""
        ...
```text
---

## Error Handling Standards

### Expected Exception Types

| Operation | Error Type | Retry? | User Action |
|-----------|-----------|--------|-------------|
| CSV parsing | `FileNotFoundError` | No | Check CSV path |
| CSV validation | `ValueError` | No | Fix CSV format |
| API 429 (rate limit) | `HTTPError` | Yes (3x) | Wait for retry |
| API 5xx (server error) | `HTTPError` | Yes (3x) | Check F5 XC status |
| API 404 (not found) | `HTTPError` | No* | Expected for deletes |
| API 4xx (client error) | `HTTPError` | No | Fix request data |
| Network timeout | `RequestException` | Yes (3x) | Check connectivity |

*404 on delete operations is treated as success (already deleted)

### Error Logging Format

```python

# Individual operation error

logger.error(
    f"Failed to {operation} user {email}: {error_message}",
    extra={"email": email, "operation": operation, "error": str(error)}
)

# Summary error collection

stats.error_details.append({
    "email": email,
    "operation": operation,
    "error": str(error)
})
```text

---

## Performance Characteristics

### Expected Performance

| Metric | Target | Measurement |
|--------|--------|-------------|
| Sync 1,000 users | < 5 minutes | End-to-end sync time |
| CSV parsing | < 5 seconds | parse_csv_to_users() |
| API call latency | < 2 seconds | Per operation (create/update/delete) |
| Dry-run overhead | < 10% | vs actual sync |
| Idempotent re-run | < 30 seconds | All users unchanged |

### Rate Limiting Strategy

- **Max concurrent requests**: 5 (conservative, F5 XC default)
- **Retry backoff**: Exponential (1s, 2s, 4s)
- **Max retries**: 3 attempts
- **Non-retryable errors**: 4xx (except 429)

---

## Version Compatibility

### API Version

- **F5 XC API**: `/api/web/custom/namespaces/system/user_roles`
- **API Version**: Unversioned custom endpoint (stable)
- **Authentication**: Certificate-based (existing mechanism)

### Python Compatibility

- **Minimum**: Python 3.9
- **Recommended**: Python 3.12
- **Type Hints**: Full type annotations (PEP 484)

---

## Security Considerations

### Credential Handling

- Use existing certificate-based authentication (preserved)
- No password storage (F5 XC handles authentication separately)
- Environment variables for sensitive data (`secrets/.env`)

### Data Validation

- Pydantic EmailStr validation for email format
- LDAP DN parsing with validation (existing `ldap_utils`)
- No SQL injection risk (no database operations)
- No XSS risk (CLI tool, no web output)

### Deletion Safety

- Explicit `--delete-users` flag required
- Dry-run mode for validation before destructive operations
- No bulk deletion safeguards (user responsibility with dry-run)

---

## Backwards Compatibility

### Preserved Functionality

All existing features remain unchanged:

- Group synchronization (`GroupSyncService`)
- LDAP DN parsing (`ldap_utils`)
- F5 XC API client (`XCClient.list_user_roles`, `create_user`)
- CLI structure and existing flags
- Credential management (`setup_xc_credentials.sh`)

### Migration Path

No migration needed - pure enhancement:

1. Existing users continue with group sync only
2. New users adopt user sync by adding user columns to CSV
3. No breaking changes to existing CSV format or CLI usage
