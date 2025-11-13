"""User synchronization service for F5 Distributed Cloud.

This module provides business logic for synchronizing users between CSV files
and F5 Distributed Cloud, treating CSV as the source of truth.
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List, Set

from xc_user_group_sync.models import User
from xc_user_group_sync.protocols import UserRepository

logger = logging.getLogger(__name__)


def validate_email_format(email: str) -> bool:
    """Validate email format using simple RFC-compliant pattern.

    Args:
        email: Email address to validate

    Returns:
        True if email format is valid, False otherwise
    """
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


@dataclass
class CSVValidationResult:
    """Result of CSV parsing with validation warnings.

    Attributes:
        users: List of successfully parsed User objects
        total_count: Total number of users in CSV
        active_count: Number of active users
        inactive_count: Number of inactive users
        duplicate_emails: Map of duplicate emails to their row numbers
        invalid_emails: List of (email, row_number) tuples with invalid format
        users_without_groups: Number of users with no group assignments
        users_without_names: Number of users with missing display names
        unique_groups: Set of unique group names found across all users
    """

    users: List[User]
    total_count: int
    active_count: int
    inactive_count: int
    duplicate_emails: Dict[str, List[int]] = field(default_factory=dict)
    invalid_emails: List[tuple[str, int]] = field(default_factory=list)
    users_without_groups: int = 0
    users_without_names: int = 0
    unique_groups: Set[str] = field(default_factory=set)

    def has_warnings(self) -> bool:
        """Check if any validation warnings were found."""
        return (
            len(self.duplicate_emails) > 0
            or len(self.invalid_emails) > 0
            or self.users_without_groups > 0
            or self.users_without_names > 0
        )


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
    """

    def __init__(self, repository: UserRepository, retry_wait=None, retry_stop=None):
        """Initialize with user repository.

        Args:
            repository: UserRepository implementation (typically XCClient)
            retry_wait: tenacity wait strategy for retries (optional)
            retry_stop: tenacity stop strategy for retries (optional)
        """
        self.repository = repository
        self.retry_wait = retry_wait
        self.retry_stop = retry_stop

    def parse_csv_to_users(self, csv_path: str) -> CSVValidationResult:
        """Parse CSV file to User objects with validation warnings.

        Args:
            csv_path: Absolute path to CSV file

        Returns:
            CSVValidationResult with parsed users and validation warnings

        Raises:
            FileNotFoundError: If CSV file doesn't exist
            ValueError: If required CSV columns are missing
        """
        import csv
        from pathlib import Path

        from xc_user_group_sync.ldap_utils import extract_cn
        from xc_user_group_sync.user_utils import (
            parse_active_status,
            parse_display_name,
        )

        csv_file = Path(csv_path)
        if not csv_file.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        users = []
        email_tracker: Dict[str, List[int]] = {}  # Track emails for duplicates
        invalid_emails: List[tuple[str, int]] = []
        users_without_groups = 0
        users_without_names = 0
        unique_groups: Set[str] = set()

        required_columns = {
            "Email",
            "User Display Name",
            "Employee Status",
            "Entitlement Display Name",
        }

        with csv_file.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            # Validate required columns
            if not reader.fieldnames:
                raise ValueError("CSV file is empty or has no header row")

            missing_columns = required_columns - set(reader.fieldnames)
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")

            for row_num, row in enumerate(reader, start=2):  # start=2 for header row
                try:
                    email = row["Email"].strip()
                    if not email:
                        logger.warning(f"Row {row_num}: Empty email, skipping")
                        continue

                    # Track email for duplicate detection (case-insensitive)
                    email_lower = email.lower()
                    if email_lower in email_tracker:
                        email_tracker[email_lower].append(row_num)
                    else:
                        email_tracker[email_lower] = [row_num]

                    # Validate email format
                    if not validate_email_format(email):
                        invalid_emails.append((email, row_num))
                        logger.warning(f"Row {row_num}: Invalid email format: {email}")

                    display_name = row["User Display Name"].strip()
                    first_name, last_name = parse_display_name(display_name)

                    # Track users without display names
                    if not display_name:
                        users_without_names += 1

                    active = parse_active_status(row["Employee Status"])

                    # Parse pipe-separated LDAP DNs and extract CNs
                    groups = []
                    entitlements = row["Entitlement Display Name"].strip()
                    if entitlements:
                        dn_list = [dn.strip() for dn in entitlements.split("|")]
                        for dn in dn_list:
                            if dn:
                                cn = extract_cn(dn)
                                if cn:
                                    groups.append(cn)
                                    unique_groups.add(cn)

                    # Track users without group assignments
                    if not groups:
                        users_without_groups += 1

                    user = User(
                        email=email,
                        display_name=display_name,
                        first_name=first_name,
                        last_name=last_name,
                        active=active,
                        groups=groups,
                    )
                    users.append(user)

                except Exception as e:
                    logger.error(f"Row {row_num}: Failed to parse user - {e}")
                    raise ValueError(f"Row {row_num}: {e}") from e

        logger.info(f"Parsed {len(users)} users from {csv_path}")

        # Identify duplicate emails (only those that appear more than once)
        duplicate_emails = {
            email: rows for email, rows in email_tracker.items() if len(rows) > 1
        }

        # Count active/inactive users
        active_count = sum(1 for u in users if u.active)
        inactive_count = len(users) - active_count

        return CSVValidationResult(
            users=users,
            total_count=len(users),
            active_count=active_count,
            inactive_count=inactive_count,
            duplicate_emails=duplicate_emails,
            invalid_emails=invalid_emails,
            users_without_groups=users_without_groups,
            users_without_names=users_without_names,
            unique_groups=unique_groups,
        )

    def fetch_existing_users(self) -> Dict[str, Dict]:
        """Fetch users from F5 XC, return email -> user_data map.

        Returns:
            Dictionary mapping lowercase email to user data
        """
        response = self.repository.list_users()
        users_map = {}

        if "items" in response:
            for user_data in response["items"]:
                email = user_data.get("email", "").lower()
                if email:
                    users_map[email] = user_data

        logger.info(f"Fetched {len(users_map)} existing users from F5 XC")
        return users_map

    def sync_users(
        self,
        planned_users: List[User],
        existing_users: Dict[str, Dict],
        dry_run: bool = False,
        delete_users: bool = False,
    ) -> UserSyncStats:
        """Reconcile users with F5 XC using state-based synchronization.

        Args:
            planned_users: Desired user state from CSV
            existing_users: Current user state from F5 XC
            dry_run: If True, log operations without executing
            delete_users: If True, delete F5 XC users not in CSV

        Returns:
            UserSyncStats with operation counts and error details
        """
        stats = UserSyncStats()

        # Build set of planned emails (lowercase for comparison)
        planned_emails = {user.email.lower() for user in planned_users}

        # Process planned users: create or update
        for user in planned_users:
            email_lower = user.email.lower()

            if email_lower not in existing_users:
                # User doesn't exist - create it
                self._create_user(user, dry_run, stats)
            else:
                # User exists - check if update needed
                existing_user = existing_users[email_lower]
                if self._user_needs_update(user, existing_user):
                    self._update_user(user, dry_run, stats)
                else:
                    logger.debug(f"User unchanged: {user.email}")
                    stats.unchanged += 1

        # Delete users in F5 XC that are not in CSV (if enabled)
        if delete_users:
            for email_lower in existing_users:
                if email_lower not in planned_emails:
                    self._delete_user(email_lower, dry_run, stats)

        logger.info(f"Sync complete: {stats.summary()}")
        return stats

    def _user_needs_update(self, planned: User, existing: Dict) -> bool:
        """Check if user attributes differ between planned and existing state.

        Args:
            planned: Desired user state from CSV
            existing: Current user state from F5 XC

        Returns:
            True if any attributes differ and update is needed
        """
        # Compare all relevant attributes
        planned_dict = planned.model_dump()

        # Check each attribute for differences
        for key in ["display_name", "first_name", "last_name", "active"]:
            if planned_dict.get(key) != existing.get(key):
                return True

        # Compare groups (order-independent)
        planned_groups = set(planned_dict.get("groups", []))
        existing_groups = set(existing.get("groups", []))
        if planned_groups != existing_groups:
            return True

        return False

    def _create_user(self, user: User, dry_run: bool, stats: UserSyncStats) -> None:
        """Create a new user in F5 XC.

        Args:
            user: User to create
            dry_run: If True, log without executing
            stats: Stats object to update
        """
        try:
            if dry_run:
                logger.info(f"[DRY-RUN] Would create user: {user.email}")
            else:
                # Only send fields that the F5 XC API expects for user creation
                # Specify VOLTERRA_MANAGED to create local users (not SSO)
                user_data = {
                    "email": user.email,
                    "name": user.username or user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "type": "USER",
                    "idm_type": "VOLTERRA_MANAGED",
                }
                self.repository.create_user(user_data)
                logger.info(f"Created user: {user.email}")
            stats.created += 1
        except Exception as e:
            # Log detailed error information for debugging
            error_msg = str(e)
            if hasattr(e, "response") and e.response is not None:
                try:
                    error_detail = e.response.text
                    logger.error(
                        f"Failed to create user {user.email}: "
                        f"{error_msg}, Response: {error_detail}"
                    )
                except Exception:
                    logger.error(f"Failed to create user {user.email}: {error_msg}")
            else:
                logger.error(f"Failed to create user {user.email}: {error_msg}")
            stats.errors += 1
            stats.error_details.append(
                {"email": user.email, "operation": "create", "error": str(e)}
            )

    def _update_user(self, user: User, dry_run: bool, stats: UserSyncStats) -> None:
        """Update an existing user in F5 XC.

        Args:
            user: User with updated data
            dry_run: If True, log without executing
            stats: Stats object to update
        """
        try:
            if dry_run:
                logger.info(f"[DRY-RUN] Would update user: {user.email}")
            else:
                user_data = user.model_dump()
                self.repository.update_user(user.email, user_data)
                logger.info(f"Updated user: {user.email}")
            stats.updated += 1
        except Exception as e:
            logger.error(f"Failed to update user {user.email}: {e}")
            stats.errors += 1
            stats.error_details.append(
                {"email": user.email, "operation": "update", "error": str(e)}
            )

    def _delete_user(self, email: str, dry_run: bool, stats: UserSyncStats) -> None:
        """Delete a user from F5 XC.

        Args:
            email: Email of user to delete
            dry_run: If True, log without executing
            stats: Stats object to update
        """
        try:
            if dry_run:
                logger.info(f"[DRY-RUN] Would delete user: {email}")
            else:
                self.repository.delete_user(email)
                logger.info(f"Deleted user: {email}")
            stats.deleted += 1
        except Exception as e:
            logger.error(f"Failed to delete user {email}: {e}")
            stats.errors += 1
            stats.error_details.append(
                {"email": email, "operation": "delete", "error": str(e)}
            )

    def cleanup_orphaned_users(
        self,
        planned_users: List["User"],
        existing_users: Dict[str, Dict],
        dry_run: bool = False,
    ) -> UserSyncStats:
        """Delete users that exist in XC but not in planned list.

        Args:
            planned_users: Users from CSV
            existing_users: Currently existing users from XC
            dry_run: If True, only log without deleting

        Returns:
            UserSyncStats with deletion results

        """
        stats = UserSyncStats()
        planned_emails = {u.email.lower() for u in planned_users}
        extra_emails = [
            email
            for email in existing_users.keys()
            if email.lower() not in planned_emails
        ]

        if extra_emails:
            logger.info(f"Extra users in XC not in CSV: {len(extra_emails)}")
            for email in extra_emails:
                logger.info(f" - {email}")

            for email in extra_emails:
                self._delete_user(email, dry_run, stats)

        return stats
