"""User synchronization service for F5 XC RBAC management.

This module provides business logic for synchronizing users between CSV files
and F5 Distributed Cloud, treating CSV as the source of truth.
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List

from xc_rbac_sync.models import User
from xc_rbac_sync.protocols import UserRepository

logger = logging.getLogger(__name__)


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

    def parse_csv_to_users(self, csv_path: str) -> List[User]:
        """Parse CSV file to User objects with enhanced attributes.

        Args:
            csv_path: Absolute path to CSV file

        Returns:
            List of User objects parsed from CSV

        Raises:
            FileNotFoundError: If CSV file doesn't exist
            ValueError: If required CSV columns are missing
        """
        import csv
        from pathlib import Path

        from xc_rbac_sync.ldap_utils import extract_cn
        from xc_rbac_sync.user_utils import parse_active_status, parse_display_name

        csv_file = Path(csv_path)
        if not csv_file.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        users = []
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

                    display_name = row["User Display Name"].strip()
                    first_name, last_name = parse_display_name(display_name)

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
        return users

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
                user_data = user.model_dump()
                self.repository.create_user(user_data)
                logger.info(f"Created user: {user.email}")
            stats.created += 1
        except Exception as e:
            logger.error(f"Failed to create user {user.email}: {e}")
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
