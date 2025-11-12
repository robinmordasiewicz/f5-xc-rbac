# Data Model: User Lifecycle Management

**Feature**: 059-user-lifecycle
**Date**: 2025-11-10

## Overview

This document defines the data structures for user lifecycle management in the F5 XC RBAC sync tool. All models follow Pydantic validation patterns consistent with the existing codebase.

## Core Entities

### User

Represents a person with access to F5 Distributed Cloud.

**Location**: `src/xc_rbac_sync/models.py`

**Schema**:

```python
from pydantic import BaseModel, Field, EmailStr
from typing import List

class User(BaseModel):
    """User data model for F5 XC synchronization.

    Attributes:
        email: User's email address (unique identifier, primary key)
        username: Username for F5 XC (typically same as email)
        display_name: Full name as shown in UI (from CSV "User Display Name")
        first_name: Given name (parsed from display_name)
        last_name: Family name (parsed from display_name)
        active: Whether user can access system (from CSV "Employee Status")
        groups: List of group names user belongs to (for coordination with group sync)
    """
    email: EmailStr
    username: str = Field(default="")  # Defaults to email if not provided
    display_name: str
    first_name: str
    last_name: str
    active: bool = True
    groups: List[str] = Field(default_factory=list)

    def __post_init__(self):
        """Set username to email if not provided."""
        if not self.username:
            self.username = self.email
```text
**Field Descriptions**:

| Field | Type | Required | Source | Description |
|-------|------|----------|--------|-------------|
| email | EmailStr | Yes | CSV "Email" | Unique identifier, validated email format |
| username | str | No | Defaults to email | F5 XC username (same as email for consistency) |
| display_name | str | Yes | CSV "User Display Name" | Full name (e.g., "Alice Anderson") |
| first_name | str | Yes | Parsed from display_name | Given name (e.g., "Alice") |
| last_name | str | Yes | Parsed from display_name | Family name (e.g., "Anderson") |
| active | bool | No (default: True) | CSV "Employee Status" | True if user can access F5 XC |
| groups | List[str] | No (default: []) | CSV "Entitlement Display Name" | Group names (CNs extracted from LDAP DNs) |

**Validation Rules**:

- `email`: Must be valid email format (enforced by Pydantic EmailStr)
- `display_name`: Non-empty string required (for name parsing)
- `first_name`, `last_name`: Can be empty (handles single-name case)
- `active`: Boolean (defaults to True if not provided)
- `groups`: List of strings (can be empty, order preserved)

**Example**:

```python
user = User(
    email="alice.anderson@example.com",
    username="alice.anderson@example.com",
    display_name="Alice Anderson",
    first_name="Alice",
    last_name="Anderson",
    active=True,
    groups=["EADMIN_STD", "DEVELOPERS"]
)
```text
---

### UserSyncStats

Tracks synchronization statistics for user operations.

**Location**: `src/xc_rbac_sync/user_sync_service.py`

**Schema**:

```python
from dataclasses import dataclass, field
from typing import List, Dict

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
```text
**Field Descriptions**:

| Field | Type | Description |
|-------|------|-------------|
| created | int | Count of users created in F5 XC during sync |
| updated | int | Count of users updated in F5 XC during sync |
| deleted | int | Count of users deleted from F5 XC during sync |
| unchanged | int | Count of users that already matched desired state |
| errors | int | Total error count (failed creates + updates + deletes) |
| error_details | List[Dict] | List of {email, operation, error} for troubleshooting |

**Example**:

```python
stats = UserSyncStats(
    created=45,
    updated=123,
    deleted=12,
    unchanged=1065,
    errors=3,
    error_details=[
        {"email": "alice@example.com", "operation": "create", "error": "409 Conflict"},
        {"email": "bob@example.com", "operation": "update", "error": "400 Bad Request"},
        {"email": "charlie@example.com", "operation": "delete", "error": "500 Internal Server Error"}
    ]
)
```text
---

### CSV Record (Conceptual Model)

Represents a row in the Active Directory CSV export.

**Source**: External CSV file (not a Python class)

**Structure**:

```csv
"User Name","Login ID","User Display Name","Cof Account Type","Application Name","Entitlement Attribute","Entitlement Display Name","Related Application","Sox","Job Level","Job Title","Created Date","Account Locker","Employee Status","Email","Cost Center","Finc Level 4","Manager EID","Manager Name","Manager Email"
"USER001","CN=USER001,OU=Users,DC=example,DC=com","Alice Anderson","User","Active Directory","memberOf","CN=EADMIN_STD,OU=Groups,DC=example,DC=com|CN=DEVELOPERS,OU=Groups,DC=example,DC=com","Example App","true","50","Lead Software Engineer","2025-09-23 00:00:00","0","A","alice.anderson@example.com","IT Infrastructure","Network Engineering","MGR001","David Wilson","David.Wilson@example.com"
```text
**Used Columns** (for user sync):

| Column Name | Usage | Parsing Logic |
|-------------|-------|---------------|
| Email | User.email | Direct copy (lowercase for comparison) |
| User Display Name | User.display_name, first_name, last_name | Parse with `parse_display_name()` |
| Employee Status | User.active | Map with `parse_active_status()` ("A" → True, else → False) |
| Entitlement Display Name | User.groups | Split on `|`, extract CN from each LDAP DN |

**Unused Columns** (informational only, not synced):

- User Name, Login ID, Cof Account Type, Application Name, etc. (metadata not needed for F5 XC user sync)

---

## Utility Functions

### parse_display_name

Parses full name into first and last name components.

**Location**: `src/xc_rbac_sync/user_utils.py`

**Signature**:

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
    """
```text
### parse_active_status

Maps employee status code to active boolean.

**Location**: `src/xc_rbac_sync/user_utils.py`

**Signature**:

```python
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
    """
```text
---

## Entity Relationships

```text
CSV Record (source of truth)
    ↓ (parsed by)
User (Python object)
    ↓ (synchronized to)
F5 XC user_role (API resource)
    ↓ (belongs to)
Group (existing entity, preserved)
```text
**Relationships**:

- **CSV → User**: One-to-one mapping (one CSV row creates one User object)
- **User → user_role**: One-to-one (User object synced to F5 XC API resource)
- **User → Group**: Many-to-many (User.groups references Group.name, coordination only)

**No Foreign Keys**: CSV and F5 XC API are external systems. Relationships maintained through email (User) and name (Group) matching.

---

## State Transitions

```text
New User in CSV → Create in F5 XC
Existing User, attributes changed → Update in F5 XC
Existing User, attributes match → Skip (no operation)
User removed from CSV (with --delete-users flag) → Delete from F5 XC
User removed from CSV (without flag) → Orphaned in F5 XC (no operation)
```text
**Idempotency Guarantee**: Running sync multiple times with same CSV produces same end state.

---

## Validation Rules Summary

| Entity | Field | Validation |
|--------|-------|------------|
| User | email | EmailStr (Pydantic validates format) |
| User | display_name | Non-empty string |
| User | first_name | String (can be empty) |
| User | last_name | String (can be empty) |
| User | active | Boolean |
| User | groups | List of strings |
| UserSyncStats | created | Non-negative integer |
| UserSyncStats | updated | Non-negative integer |
| UserSyncStats | deleted | Non-negative integer |
| UserSyncStats | unchanged | Non-negative integer |
| UserSyncStats | errors | Non-negative integer |

---

## Data Flow

```text

1. CSV File

    ↓ (read)

2. Raw CSV Rows (dict per row)

    ↓ (parse with parse_display_name, parse_active_status)

3. User Objects (Pydantic validated)

    ↓ (convert to dict for API)

4. F5 XC API Payload

    ↓ (POST/PUT/DELETE)

5. F5 XC user_role Resources

    ↓ (track operations)

6. UserSyncStats (summary)
```text
**Error Handling**: Validation errors at step 3 logged and skipped. API errors at step 5 collected in UserSyncStats.error_details.

---

## Comparison with Existing Group Model

| Aspect | Group (existing) | User (new) |
|--------|------------------|------------|
| Identifier | name (string, validated pattern) | email (EmailStr) |
| Validation | Pydantic with StringConstraints | Pydantic with EmailStr |
| Optional fields | description, roles | username (defaults to email) |
| Lists | users (List[str]), roles (List[str]) | groups (List[str]) |
| Source | CSV "Entitlement Display Name" | CSV "Email", "User Display Name", "Employee Status" |

**Consistency**: Both use Pydantic BaseModel, both have list fields for relationships, both use simple types (str, bool, List[str]).

---

## Testing Considerations

**Unit Tests** (test data models):

- Pydantic validation (valid/invalid emails, etc.)
- Name parsing edge cases (single name, multiple names, whitespace)
- Status mapping edge cases (various codes, case sensitivity)
- Stats summary generation and error tracking

**Integration Tests** (test with mock F5 XC API):

- CSV parsing to User objects
- User reconciliation logic (create, update, delete, skip)
- Error handling and partial failures
- Idempotency (running sync twice)

**Test Fixtures**:

```python
@pytest.fixture
def sample_user():
    return User(
        email="test@example.com",
        username="test@example.com",
        display_name="Test User",
        first_name="Test",
        last_name="User",
        active=True,
        groups=["GROUP1", "GROUP2"]
    )
```text
