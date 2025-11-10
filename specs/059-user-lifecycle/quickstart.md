# Quickstart Guide: User Lifecycle Management

**Feature**: 059-user-lifecycle
**Date**: 2025-11-10
**Audience**: Developers implementing this feature, Users adopting user sync

## For Developers

### Prerequisites

- **Python**: 3.9+ installed (3.12 recommended)
- **Git**: Repository cloned and feature branch checked out
- **Environment**: Existing F5 XC credentials configured (via `scripts/setup_xc_credentials.sh`)
- **Dependencies**: Installed via `pip install -e .` or `pip install -r requirements.txt`
- **Tools**: `pytest`, `ruff`, `black`, `mypy` for development

### Development Environment Setup

```bash
# 1. Activate project with Serena (if using Serena MCP)
# Already done: f5-xc-rbac project activated

# 2. Checkout feature branch
git checkout 059-user-lifecycle

# 3. Install dependencies
pip install -e .

# 4. Run existing tests to ensure baseline
pytest

# Expected: All tests pass (baseline established)
```

### Implementation Sequence (TDD Approach)

#### Phase 1: Data Models and Utilities

**Step 1.1: User Model** (`src/xc_rbac_sync/models.py`)

```python
# Add to models.py alongside existing Group model
from pydantic import BaseModel, Field, EmailStr
from typing import List

class User(BaseModel):
    """User data model for F5 XC synchronization."""
    email: EmailStr
    username: str = Field(default="")
    display_name: str
    first_name: str
    last_name: str
    active: bool = True
    groups: List[str] = Field(default_factory=list)

    def __post_init__(self):
        """Set username to email if not provided."""
        if not self.username:
            self.username = self.email
```

**Test First**: Create `tests/unit/test_models.py` (or extend existing)

```python
import pytest
from xc_rbac_sync.models import User

def test_user_email_validation():
    """Test email validation with Pydantic EmailStr."""
    user = User(
        email="alice@example.com",
        display_name="Alice Anderson",
        first_name="Alice",
        last_name="Anderson"
    )
    assert user.email == "alice@example.com"

    with pytest.raises(ValueError):
        User(email="invalid-email", display_name="Test", first_name="T", last_name="U")

def test_user_username_defaults_to_email():
    """Test username defaults to email if not provided."""
    user = User(
        email="bob@example.com",
        display_name="Bob Smith",
        first_name="Bob",
        last_name="Smith"
    )
    assert user.username == "bob@example.com"
```

**Step 1.2: Utility Functions** (`src/xc_rbac_sync/user_utils.py`)

```python
# Create new file: user_utils.py

def parse_display_name(display_name: str) -> tuple[str, str]:
    """Parse display name into (first_name, last_name)."""
    trimmed = display_name.strip()
    if not trimmed:
        return ("", "")

    parts = trimmed.split()
    if len(parts) == 1:
        return (parts[0], "")

    first_name = " ".join(parts[:-1])
    last_name = parts[-1]
    return (first_name, last_name)


def parse_active_status(employee_status: str) -> bool:
    """Map employee status code to active boolean."""
    return employee_status.strip().upper() == "A"
```

**Test First**: Create `tests/unit/test_user_utils.py`

```python
import pytest
from xc_rbac_sync.user_utils import parse_display_name, parse_active_status

class TestParseDisplayName:
    def test_two_word_name(self):
        assert parse_display_name("Alice Anderson") == ("Alice", "Anderson")

    def test_three_word_name(self):
        assert parse_display_name("John Paul Smith") == ("John Paul", "Smith")

    def test_single_name(self):
        assert parse_display_name("Madonna") == ("Madonna", "")

    def test_whitespace_trimming(self):
        assert parse_display_name("  Alice  Anderson  ") == ("Alice", "Anderson")

    def test_empty_string(self):
        assert parse_display_name("") == ("", "")

class TestParseActiveStatus:
    def test_active_uppercase(self):
        assert parse_active_status("A") is True

    def test_active_lowercase(self):
        assert parse_active_status("a") is True

    def test_inactive_status(self):
        assert parse_active_status("I") is False

    def test_terminated_status(self):
        assert parse_active_status("T") is False

    def test_whitespace_handling(self):
        assert parse_active_status("  A  ") is True
```

#### Phase 2: API Client Extensions

**Step 2.1: XCClient Extensions** (`src/xc_rbac_sync/client.py`)

Add methods to existing `XCClient` class:

```python
# Add to existing XCClient class

def list_users(self, namespace: str = "system") -> Dict[str, Any]:
    """Alias for list_user_roles for naming consistency."""
    return self.list_user_roles(namespace)

@retry(
    wait=wait_exponential(multiplier=1, min=1, max=10),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type((requests.exceptions.HTTPError,))
)
def update_user(
    self,
    email: str,
    user: Dict[str, Any],
    namespace: str = "system"
) -> Dict[str, Any]:
    """Update existing user via PUT."""
    url = f"{self.base_url}/api/web/custom/namespaces/{namespace}/user_roles/{email}"
    response = self.session.put(url, json=user)
    response.raise_for_status()
    return response.json()

# Similar implementation for delete_user and get_user
# (Follow same pattern as existing create_user)
```

**Test First**: Extend `tests/unit/test_client.py`

```python
import pytest
from unittest.mock import Mock, patch
from xc_rbac_sync.client import XCClient

class TestXCClientUserOperations:
    @patch("requests.Session.put")
    def test_update_user_success(self, mock_put):
        mock_put.return_value.json.return_value = {"email": "alice@example.com"}
        mock_put.return_value.status_code = 200

        client = XCClient(...)
        result = client.update_user("alice@example.com", {"email": "alice@example.com"})

        assert result["email"] == "alice@example.com"
        mock_put.assert_called_once()

    # Add tests for delete_user, get_user, retry logic, etc.
```

#### Phase 3: UserSyncService Implementation

**Step 3.1: UserRepository Protocol** (`src/xc_rbac_sync/protocols.py`)

```python
# Add to existing protocols.py

from typing import Protocol, Dict, Any

class UserRepository(Protocol):
    """Protocol for user management operations."""

    def list_users(self, namespace: str = "system") -> Dict[str, Any]: ...
    def create_user(self, user: Dict[str, Any], namespace: str = "system") -> Dict[str, Any]: ...
    def update_user(self, email: str, user: Dict[str, Any], namespace: str = "system") -> Dict[str, Any]: ...
    def delete_user(self, email: str, namespace: str = "system") -> None: ...
    def get_user(self, email: str, namespace: str = "system") -> Dict[str, Any]: ...
```

**Step 3.2: UserSyncService** (`src/xc_rbac_sync/user_sync_service.py`)

Create new file following `sync_service.py` pattern:

```python
# Mirror GroupSyncService structure

import csv
import logging
from typing import List, Dict
from dataclasses import dataclass, field
from xc_rbac_sync.models import User
from xc_rbac_sync.protocols import UserRepository
from xc_rbac_sync.user_utils import parse_display_name, parse_active_status
from xc_rbac_sync.ldap_utils import extract_cn

logger = logging.getLogger(__name__)

@dataclass
class UserSyncStats:
    created: int = 0
    updated: int = 0
    deleted: int = 0
    unchanged: int = 0
    errors: int = 0
    error_details: List[Dict[str, str]] = field(default_factory=list)

    def summary(self) -> str:
        return f"Users: created={self.created}, updated={self.updated}, deleted={self.deleted}, unchanged={self.unchanged}, errors={self.errors}"

    def has_errors(self) -> bool:
        return self.errors > 0

class UserSyncService:
    def __init__(self, repository: UserRepository, retry_wait=None, retry_stop=None):
        self.repository = repository
        # Store retry configs if needed

    def parse_csv_to_users(self, csv_path: str) -> List[User]:
        """Parse CSV to User objects."""
        users = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            # Validate required columns
            required = {"Email", "User Display Name", "Employee Status", "Entitlement Display Name"}
            if not required.issubset(reader.fieldnames):
                raise ValueError(f"Missing required columns: {required - set(reader.fieldnames)}")

            for row in reader:
                try:
                    email = row["Email"].strip().lower()
                    display_name = row["User Display Name"].strip()
                    first_name, last_name = parse_display_name(display_name)
                    active = parse_active_status(row["Employee Status"])

                    # Parse groups from pipe-separated LDAP DNs
                    groups = []
                    entitlements = row["Entitlement Display Name"].strip()
                    if entitlements:
                        for dn in entitlements.split("|"):
                            cn = extract_cn(dn.strip())
                            if cn:
                                groups.append(cn)

                    user = User(
                        email=email,
                        username=email,
                        display_name=display_name,
                        first_name=first_name,
                        last_name=last_name,
                        active=active,
                        groups=groups
                    )
                    users.append(user)

                except Exception as e:
                    logger.warning(f"Skipping invalid row for {row.get('Email', 'unknown')}: {e}")

        return users

    def fetch_existing_users(self) -> Dict[str, Dict]:
        """Fetch users from F5 XC, return email -> user_data map."""
        result = self.repository.list_users()
        # Transform to lowercase email keys
        return {email.lower(): data for email, data in result.items()}

    def sync_users(
        self,
        planned_users: List[User],
        existing_users: Dict[str, Dict],
        dry_run: bool = False,
        delete_users: bool = False
    ) -> UserSyncStats:
        """Reconcile users with F5 XC."""
        stats = UserSyncStats()

        # Build maps
        desired_map = {u.email.lower(): u for u in planned_users}
        current_map = {email.lower(): data for email, data in existing_users.items()}

        # Create or update
        for email, desired_user in desired_map.items():
            if email not in current_map:
                self._create_user(desired_user, dry_run, stats)
            else:
                current = current_map[email]
                if self._user_needs_update(current, desired_user):
                    self._update_user(desired_user, dry_run, stats)
                else:
                    stats.unchanged += 1

        # Delete orphaned users
        if delete_users:
            for email in current_map:
                if email not in desired_map:
                    self._delete_user(email, dry_run, stats)

        return stats

    def _create_user(self, user: User, dry_run: bool, stats: UserSyncStats):
        """Create user (helper method)."""
        try:
            if dry_run:
                logger.info(f"Would create user: {user.email}")
            else:
                self.repository.create_user(user.dict())
                logger.info(f"Created user: {user.email}")
            stats.created += 1
        except Exception as e:
            logger.error(f"Failed to create user {user.email}: {e}")
            stats.errors += 1
            stats.error_details.append({"email": user.email, "operation": "create", "error": str(e)})

    # Implement _update_user, _delete_user, _user_needs_update similarly
```

**Test First**: Create `tests/unit/test_user_sync_service.py`

```python
import pytest
from unittest.mock import Mock
from xc_rbac_sync.user_sync_service import UserSyncService, UserSyncStats
from xc_rbac_sync.models import User

class TestUserSyncService:
    def test_parse_csv_to_users_valid(self, tmp_path):
        """Test CSV parsing with valid data."""
        csv_content = """Email,User Display Name,Employee Status,Entitlement Display Name
alice@example.com,Alice Anderson,A,CN=EADMIN_STD,OU=Groups,DC=example,DC=com
bob@example.com,Bob Smith,I,CN=DEVELOPERS,OU=Groups,DC=example,DC=com"""

        csv_file = tmp_path / "test.csv"
        csv_file.write_text(csv_content)

        mock_repo = Mock()
        service = UserSyncService(mock_repo)
        users = service.parse_csv_to_users(str(csv_file))

        assert len(users) == 2
        assert users[0].email == "alice@example.com"
        assert users[0].first_name == "Alice"
        assert users[0].last_name == "Anderson"
        assert users[0].active is True
        assert "EADMIN_STD" in users[0].groups

    def test_sync_users_creates_new(self):
        """Test user creation when not in F5 XC."""
        mock_repo = Mock()
        service = UserSyncService(mock_repo)

        planned = [User(email="alice@example.com", display_name="Alice", first_name="Alice", last_name="A")]
        existing = {}

        stats = service.sync_users(planned, existing, dry_run=False, delete_users=False)

        assert stats.created == 1
        assert stats.unchanged == 0
        mock_repo.create_user.assert_called_once()

    # Add tests for update, delete, idempotency, dry-run, etc.
```

#### Phase 4: CLI Integration

**Step 4.1: Extend CLI** (`src/xc_rbac_sync/cli.py`)

```python
# Add --delete-users flag to existing sync command

@click.command()
@click.option("--csv", required=True, help="Path to CSV file")
@click.option("--dry-run", is_flag=True, help="Preview changes without executing")
@click.option("--delete-users", is_flag=True, help="Delete F5 XC users not in CSV")
# ... existing options ...
def sync(csv: str, dry_run: bool, delete_users: bool, ...):
    """Synchronize users and groups from CSV to F5 XC."""

    # Existing group sync logic (preserved)
    group_service = GroupSyncService(...)
    # ... existing code ...

    # NEW: User sync logic
    user_service = UserSyncService(repository=client)

    # Parse CSV for users
    planned_users = user_service.parse_csv_to_users(csv)
    existing_users = user_service.fetch_existing_users()

    # Sync users
    user_stats = user_service.sync_users(
        planned_users=planned_users,
        existing_users=existing_users,
        dry_run=dry_run,
        delete_users=delete_users
    )

    # Display summary
    click.echo(f"\n{user_stats.summary()}")
    if user_stats.has_errors():
        click.echo(f"\nErrors encountered:")
        for error in user_stats.error_details:
            click.echo(f"  - {error['email']}: {error['error']}")
```

**Test**: Extend `tests/unit/test_cli.py`

```python
from click.testing import CliRunner
from xc_rbac_sync.cli import cli

def test_sync_with_delete_users_flag():
    """Test sync command with --delete-users flag."""
    runner = CliRunner()
    result = runner.invoke(cli, ["sync", "--csv", "test.csv", "--delete-users", "--dry-run"])

    assert result.exit_code == 0
    assert "Would delete" in result.output  # dry-run should log deletions
```

#### Phase 5: Integration Testing

**Step 5.1: End-to-End Test** (`tests/integration/test_user_sync_integration.py`)

```python
import pytest
from unittest.mock import Mock
from xc_rbac_sync.user_sync_service import UserSyncService

class TestUserSyncIntegration:
    def test_full_sync_workflow(self, tmp_path):
        """Test complete sync: parse CSV → fetch existing → reconcile → report."""
        # Create test CSV
        csv_content = """Email,User Display Name,Employee Status,Entitlement Display Name
alice@example.com,Alice Anderson,A,CN=GROUP1,OU=Groups,DC=example,DC=com"""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text(csv_content)

        # Mock F5 XC API
        mock_repo = Mock()
        mock_repo.list_users.return_value = {}
        mock_repo.create_user.return_value = {"email": "alice@example.com"}

        # Execute sync
        service = UserSyncService(mock_repo)
        planned = service.parse_csv_to_users(str(csv_file))
        existing = service.fetch_existing_users()
        stats = service.sync_users(planned, existing, dry_run=False, delete_users=False)

        # Verify
        assert stats.created == 1
        assert stats.errors == 0
        mock_repo.create_user.assert_called_once()

    def test_idempotency(self, tmp_path):
        """Test running sync twice with same CSV produces no changes on second run."""
        # First run: create user
        # Second run: no changes (unchanged=1, created=0)
        # Implementation left as exercise
        ...
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_user_utils.py

# Run with coverage
pytest --cov=src/xc_rbac_sync --cov-report=html

# Expected coverage: 80%+ for user-specific code
```

### Pre-Commit Checklist

Before committing:

1. ✅ All tests pass: `pytest`
2. ✅ Type checking: `mypy src/`
3. ✅ Linting: `ruff check src/`
4. ✅ Formatting: `black src/`
5. ✅ Coverage: `pytest --cov` (80%+ for new code)
6. ✅ Documentation: Docstrings added (Google style)

### Development Tips

- **Follow Existing Patterns**: Mirror `GroupSyncService` structure for consistency
- **TDD Approach**: Write tests first, then implementation
- **Incremental Commits**: Commit after each phase (models → utils → client → service → CLI)
- **Dry-Run Testing**: Always test with `--dry-run` before executing real sync
- **Error Logging**: Use `logger.error()` with context (email, operation, error)

---

## For Users

### Prerequisites

- **F5 XC Credentials**: Configured via `scripts/setup_xc_credentials.sh`
- **CSV File**: Active Directory export with required columns
- **Python Environment**: Tool installed and accessible via `xc-group-sync` command

### CSV Format Requirements

Your CSV must contain these columns (exact names):

- **Email**: User email address (unique identifier)
- **User Display Name**: Full name (e.g., "Alice Anderson")
- **Employee Status**: Active status code ("A" = active, others = inactive)
- **Entitlement Display Name**: Pipe-separated LDAP DNs for group memberships

**Example CSV**:

```csv
Email,User Display Name,Employee Status,Entitlement Display Name
alice@example.com,Alice Anderson,A,CN=EADMIN_STD,OU=Groups,DC=example,DC=com|CN=DEVELOPERS,OU=Groups,DC=example,DC=com
bob@example.com,Bob Smith,I,CN=READONLY,OU=Groups,DC=example,DC=com
charlie@example.com,Charlie Jones,T,
```

### Basic Usage

#### 1. Preview Changes (Recommended First Step)

```bash
# Dry-run to see what would happen (no changes made)
xc-group-sync sync-users --csv users.csv --dry-run

# Output:
# Users planned from CSV: 1067
#  - Active: 1066, Inactive: 1
# Existing users in F5 XC: 1066
#
# [DRY-RUN] Would create user: alice@example.com
# [DRY-RUN] Would update user: bob@example.com
#
# Users: created=1, updated=1, deleted=0, unchanged=1065, errors=0
# Execution time: 2.34 seconds
#
# User sync complete.
```

#### 2. Sync Users (Create and Update Only)

```bash
# Sync users without deletions (safe default)
xc-group-sync sync-users --csv users.csv

# Output:
# Users planned from CSV: 1067
#  - Active: 1066, Inactive: 1
# Existing users in F5 XC: 1066
#
# Created user: alice@example.com
# Updated user: bob@example.com
#
# Users: created=1, updated=1, deleted=0, unchanged=1065, errors=0
# Execution time: 4.56 seconds
#
# User sync complete.
```

#### 3. Sync Users with Deletions (Use with Caution)

```bash
# Preview deletions first (ALWAYS recommended)
xc-group-sync sync-users --csv users.csv --delete-users --dry-run

# Output:
# Users planned from CSV: 1066
#  - Active: 1066, Inactive: 0
# Existing users in F5 XC: 1067
#
# [DRY-RUN] Would delete user: charlie@example.com
#
# Users: created=0, updated=0, deleted=1, unchanged=1066, errors=0
# Execution time: 2.12 seconds
#
# User sync complete.

# Execute deletions (only if dry-run output is correct)
xc-group-sync sync-users --csv users.csv --delete-users

# Output:
# Users planned from CSV: 1066
#  - Active: 1066, Inactive: 0
# Existing users in F5 XC: 1067
#
# Deleted user: charlie@example.com
#
# Users: created=0, updated=0, deleted=1, unchanged=1066, errors=0
# Execution time: 3.78 seconds
#
# User sync complete.
```

### Common Workflows

#### Initial Bulk User Import

```bash
# 1. Export users from Active Directory to CSV
# 2. Preview import
xc-group-sync sync-users --csv initial_users.csv --dry-run

# 3. Execute import
xc-group-sync sync-users --csv initial_users.csv

# Expected: All users created, no errors
```

#### Regular Synchronization (Daily/Weekly)

```bash
# 1. Export updated CSV from Active Directory
# 2. Preview changes
xc-group-sync sync-users --csv daily_sync.csv --dry-run

# 3. Execute sync (create/update only, no deletions)
xc-group-sync sync-users --csv daily_sync.csv

# Expected: New users created, changed users updated, no deletions
```

#### User Cleanup (Terminations)

```bash
# 1. Export current active users from Active Directory
# 2. Preview deletions (CRITICAL: verify output carefully)
xc-group-sync sync-users --csv active_users.csv --delete-users --dry-run

# 3. Review dry-run output: ensure only terminated users are listed for deletion
# 4. Execute cleanup (only if dry-run is correct)
xc-group-sync sync-users --csv active_users.csv --delete-users

# Expected: Terminated users deleted, active users unchanged
```

### Troubleshooting

#### Error: "Missing required columns"

**Problem**: CSV is missing required columns.

**Solution**: Ensure CSV has exact column names (case-sensitive):
- Email
- User Display Name
- Employee Status
- Entitlement Display Name

#### Error: "Failed to create user: 409 Conflict"

**Problem**: User already exists in F5 XC.

**Solution**: This is normal on re-runs. User will be updated instead. If persists, check for duplicate emails in CSV.

#### Warning: "Skipping invalid row for unknown@example.com"

**Problem**: Row has invalid data (malformed email, missing display name, etc.).

**Solution**: Check CSV for data quality issues. Sync continues with remaining valid rows.

#### Error: "Rate limit exceeded (429)"

**Problem**: Too many API requests to F5 XC.

**Solution**: Tool automatically retries with backoff. If persists, reduce CSV size or wait and retry.

### Safety Best Practices

1. **Always Dry-Run First**: Never execute `--delete-users` without previewing with `--dry-run`
2. **Verify CSV Accuracy**: Ensure CSV export is complete and accurate before sync
3. **Incremental Changes**: Test with small CSV subsets before full sync
4. **Backup Strategy**: No automated backup - ensure you can regenerate CSV if needed
5. **Monitor Summary**: Always review sync summary for unexpected counts or errors

### Performance Expectations

| Operation | Expected Time |
|-----------|---------------|
| 1,000 users sync | < 5 minutes |
| CSV parsing (10,000 rows) | < 5 seconds |
| Dry-run overhead | < 10% vs actual sync |
| Idempotent re-run | < 30 seconds (all unchanged) |

### Support and Feedback

- **Issues**: Report bugs or issues via GitHub issue tracker
- **Documentation**: See `/specs/059-user-lifecycle/` for detailed specifications
- **Examples**: Sample CSV templates available in repository
