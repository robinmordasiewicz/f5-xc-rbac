"""Group synchronization service with business logic.

Provides the core business logic for synchronizing user groups from CSV
files to F5 XC, including CSV parsing, group CRUD operations, user validation,
and orphaned group cleanup.

Create_user contract and payload:
- The service will call `repository.create_user(user_dict)` when it needs to
    provision a missing user. The `user_dict` SHOULD contain at minimum:
        - `email` (string) — canonical identifier used by the CSV and XC.
    Optional fields that may be provided when available:
        - `username` (string)
        - `display_name` (string)
    Concrete repository implementations MUST accept this shape or raise an
    exception. The operation is retried on transient errors.

Retry configuration:
- `GroupSyncService` accepts retry/backoff parameters to control how many
    attempts are made when creating users and the exponential backoff window.
    These default to conservative values but can be tuned per-instance.
"""

from __future__ import annotations

import csv
import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import ClassVar, Dict, List, Set

from tenacity import (
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .ldap_utils import LdapParseError, extract_cn
from .models import Group
from .protocols import GroupRepository


@dataclass
class SyncStats:
    """Statistics from a sync operation."""

    created: int = 0
    updated: int = 0
    deleted: int = 0
    skipped: int = 0
    errors: int = 0
    skipped_due_to_unknown: int = 0

    def summary(self) -> str:
        """Generate summary message."""
        return (
            f"Summary: created={self.created}, updated={self.updated}, "
            f"deleted={self.deleted}, skipped={self.skipped}, errors={self.errors}"
        )

    def has_errors(self) -> bool:
        """Check if there were any errors."""
        return self.errors > 0


class CSVParseError(Exception):
    """Error parsing CSV file."""

    pass


class GroupSyncService:
    """Service for synchronizing groups from CSV to repository."""

    REQUIRED_COLUMNS: ClassVar[set[str]] = {"Email", "Entitlement Display Name"}

    def __init__(
        self,
        repository: GroupRepository,
        *,
        retry_attempts: int = 3,
        backoff_multiplier: float = 1.0,
        backoff_min: float = 1.0,
        backoff_max: float = 4.0,
    ):
        """Initialize service with a group repository.

        Args:
            repository: Implementation of GroupRepository protocol

        """
        self.repository = repository
        # Retry/backoff tuning for user creation retries
        self.retry_attempts = int(retry_attempts)
        self.backoff_multiplier = float(backoff_multiplier)
        self.backoff_min = float(backoff_min)
        self.backoff_max = float(backoff_max)

    def parse_csv_to_groups(self, csv_path: str) -> List[Group]:
        """Parse CSV file into Group objects.

        Args:
            csv_path: Path to CSV file with user/group mappings

        Returns:
            List of Group objects with members

        Raises:
            CSVParseError: If CSV is malformed or missing required columns

        """
        members: Dict[str, Set[str]] = defaultdict(set)

        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            header = set(reader.fieldnames or [])
            missing = [c for c in self.REQUIRED_COLUMNS if c not in header]
            if missing:
                raise CSVParseError(
                    f"CSV missing required columns: {', '.join(sorted(missing))}"
                )

            for row in reader:
                dn = row.get("Entitlement Display Name") or row.get(
                    "entitlement_display_name"
                )
                email = row.get("Email") or row.get("email")
                if not dn or not email:
                    continue

                try:
                    cn = extract_cn(dn)
                except LdapParseError as e:
                    logging.warning("Skipping row due to DN parse error: %s", e)
                    continue

                members[cn].add(email)

        planned = []
        for name, users in sorted(members.items()):
            grp = Group(name=name, users=sorted(users))
            planned.append(grp)

        return planned

    def fetch_existing_groups(self) -> Dict[str, Dict]:
        """Fetch existing groups from repository.

        Returns:
            Dictionary mapping group names to group data

        Raises:
            Exception: If repository operation fails

        """
        list_resp = self.repository.list_groups()
        existing = {
            g["name"]: g
            for g in list_resp.get("items", [])
            if isinstance(g, dict) and "name" in g
        }
        return existing

    def fetch_existing_users(self) -> Set[str] | None:
        """Fetch existing users for pre-validation.

        Returns:
            Set of existing user emails/usernames, or None if fetch failed

        Raises:
            Exception: If repository operation fails

        """
        try:
            roles = self.repository.list_user_roles()
            existing_users = {
                user_id
                for u in roles.get("items", [])
                if isinstance(u, dict)
                and (user_id := u.get("username") or u.get("email"))
            }
            return existing_users
        except Exception as e:
            logging.warning("Could not pre-validate users (user_roles): %s", e)
            return None

    def _validate_and_ensure_users(
        self,
        desired_users: List[str],
        current_users: Set[str],
        existing_users: Set[str] | None,
        dry_run: bool,
        stats: SyncStats,
    ) -> tuple[List[str], Set[str], SyncStats]:
        """Validate and ensure all desired users exist.

        Args:
            desired_users: List of user emails/usernames needed for group
            current_users: Set of currently known existing users
            existing_users: Original set from caller (None if we should create users)
            dry_run: If True, only log actions without making changes
            stats: Current sync statistics

        Returns:
            Tuple of (unknown_users, updated_current_users, updated_stats)
        """
        unknown = [u for u in desired_users if u not in current_users]

        # If caller provided existing_users for strict validation, don't create users
        if unknown and existing_users is not None:
            return unknown, current_users, stats

        # Attempt to create missing users (only when existing_users was None)
        for u in unknown:
            if dry_run:
                logging.info("Would create user %s", u)
            else:
                try:
                    self._create_user_with_retry({"email": u})
                    logging.info("Created user %s", u)
                    current_users.add(u)
                except Exception as e:
                    stats.errors += 1
                    logging.error(
                        "Failed to create user %s after retries: %s",
                        u,
                        e,
                    )

        # Recompute unknown after attempted creations
        unknown = [u for u in desired_users if u not in current_users]
        return unknown, current_users, stats

    def sync_groups(
        self,
        planned_groups: List[Group],
        existing_groups: Dict[str, Dict],
        existing_users: Set[str] | None,
        dry_run: bool = False,
    ) -> SyncStats:
        """Synchronize planned groups with existing groups.

        Args:
            planned_groups: Groups to create/update
            existing_groups: Currently existing groups
            existing_users: Set of existing users (None to skip validation)
            dry_run: If True, only log actions without making changes

        Returns:
            SyncStats with operation counts

        Raises:
            Exception: If repository operations fail

        """
        stats = SyncStats()

        # If caller didn't provide existing_users for pre-validation, fetch
        # current users so we can create missing users as needed.
        if existing_users is None:
            try:
                roles = self.repository.list_user_roles()
                current_users = {
                    user_id
                    for u in roles.get("items", [])
                    if isinstance(u, dict)
                    and (user_id := u.get("username") or u.get("email"))
                }
            except Exception as e:
                logging.warning("Could not fetch existing users: %s", e)
                current_users = set()
        else:
            current_users = set(existing_users)

        for grp in planned_groups:
            desired_users = sorted(grp.users)

            # Validate and ensure users exist
            unknown, current_users, stats = self._validate_and_ensure_users(
                desired_users, current_users, existing_users, dry_run, stats
            )

            # Skip group if users are still unknown after validation/creation
            if unknown:
                stats.skipped_due_to_unknown += 1
                stats.errors += 1
                error_context = (
                    "validation only"
                    if existing_users is not None
                    else "after create attempts"
                )
                logging.error(
                    "Skipping group %s due to unknown users (%s): %s",
                    grp.name,
                    error_context,
                    ", ".join(unknown),
                )
                continue

            if grp.name in existing_groups:
                # Update existing group
                stats = self._update_group(
                    grp, existing_groups[grp.name], desired_users, dry_run, stats
                )
            else:
                # Create new group
                stats = self._create_group(grp, desired_users, dry_run, stats)

        return stats

    def _update_group(
        self,
        group: Group,
        current_data: Dict,
        desired_users: List[str],
        dry_run: bool,
        stats: SyncStats,
    ) -> SyncStats:
        """Update an existing group.

        Args:
            group: Group to update
            current_data: Current group data from repository
            desired_users: Desired user list
            dry_run: If True, only log without updating
            stats: Statistics object to update

        Returns:
            Updated statistics object

        """
        curr_users = sorted(
            current_data.get("usernames") or current_data.get("users") or []
        )
        if curr_users == desired_users:
            stats.skipped += 1
            logging.debug("No change for group %s", group.name)
            return stats

        payload = {
            "name": group.name,
            "display_name": group.name,
            "usernames": desired_users,
        }

        if dry_run:
            logging.info(
                "Would update group %s (%d users)", group.name, len(desired_users)
            )
        else:
            try:
                self.repository.update_group(group.name, payload)
                stats.updated += 1
                logging.info("Updated group %s", group.name)
            except Exception as e:
                stats.errors += 1
                logging.error("Failed to update %s: %s", group.name, e)

        return stats

    def _create_group(
        self,
        group: Group,
        desired_users: List[str],
        dry_run: bool,
        stats: SyncStats,
    ) -> SyncStats:
        """Create a new group.

        Args:
            group: Group to create
            desired_users: User list for the group
            dry_run: If True, only log without creating
            stats: Statistics object to update

        Returns:
            Updated statistics object

        """
        payload = {
            "name": group.name,
            "display_name": group.name,
            "usernames": desired_users,
        }

        if dry_run:
            logging.info(
                "Would create group %s (%d users)", group.name, len(desired_users)
            )
        else:
            try:
                self.repository.create_group(payload)
                stats.created += 1
                logging.info("Created group %s", group.name)
            except Exception as e:
                stats.errors += 1
                # Log detailed error information for debugging
                error_msg = str(e)
                if hasattr(e, "response") and e.response is not None:
                    try:
                        error_detail = e.response.text
                        logging.error(
                            "Failed to create %s: %s, Response: %s",
                            group.name,
                            error_msg,
                            error_detail,
                        )
                    except Exception:
                        logging.error("Failed to create %s: %s", group.name, error_msg)
                else:
                    logging.error("Failed to create %s: %s", group.name, error_msg)

        return stats

    def _create_user_with_retry(self, user: Dict[str, str]) -> Dict:
        """Create a user via repository with retries for transient failures.

        Uses tenacity.Retrying with the instance's retry/backoff configuration.
        Raises after retries are exhausted.

        Args:
            user: User data dictionary to create

        Returns:
            Created user response from repository
        """
        from tenacity import Retrying

        for attempt in Retrying(
            stop=stop_after_attempt(self.retry_attempts),
            wait=wait_exponential(
                multiplier=self.backoff_multiplier,
                min=self.backoff_min,
                max=self.backoff_max,
            ),
            retry=retry_if_exception_type(Exception),
            reraise=True,
        ):
            with attempt:
                return self.repository.create_user(user)

        # This line should never be reached due to reraise=True,
        # but included for type checker satisfaction
        raise RuntimeError("Retry logic failed unexpectedly")

    def cleanup_orphaned_groups(
        self,
        planned_groups: List[Group],
        existing_groups: Dict[str, Dict],
        dry_run: bool = False,
    ) -> int:
        """Delete groups that exist in repository but not in planned list.

        Args:
            planned_groups: Groups from CSV
            existing_groups: Currently existing groups
            dry_run: If True, only log without deleting

        Returns:
            Number of groups deleted

        """
        planned_names = {g.name for g in planned_groups}
        extra = [name for name in existing_groups.keys() if name not in planned_names]

        deleted = 0
        errors = 0

        if extra:
            logging.info("Extra groups in repository not in CSV: %d", len(extra))
            for name in extra:
                logging.info(" - %s", name)

            if not dry_run:
                for name in extra:
                    try:
                        self.repository.delete_group(name)
                        deleted += 1
                        logging.info("Deleted group %s", name)
                    except Exception as e:
                        errors += 1
                        logging.error("Failed to delete %s: %s", name, e)

        return deleted
