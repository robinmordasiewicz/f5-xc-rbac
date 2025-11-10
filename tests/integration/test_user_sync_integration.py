"""Integration tests for user synchronization (T074).

These tests verify end-to-end user sync workflows including error handling,
summary reporting, and multi-operation scenarios.
"""

from unittest.mock import Mock

from xc_rbac_sync.models import User
from xc_rbac_sync.user_sync_service import UserSyncService


class TestFullSyncSummaryWithErrors:
    """Integration test: Full sync summary with errors (T074)."""

    def test_full_sync_with_mixed_results_and_errors(self):
        """Test complete sync workflow with successes and failures (T074).

        Scenario:
        - 2 new users: 1 succeeds, 1 fails
        - 2 existing users: 1 update succeeds, 1 update fails
        - 1 unchanged user
        - 1 orphaned user: deletion succeeds
        - 1 orphaned user: deletion fails

        Expected summary:
        - created=1, updated=1, deleted=1, unchanged=1, errors=3
        - error_details contains 3 entries with user emails and operations
        """
        # Setup mock repository with partial failures
        mock_repo = Mock()

        # Configure create_user: succeed for user1, fail for user2
        def create_user_side_effect(user_data, namespace="system"):
            if user_data["email"] == "newuser2@example.com":
                raise Exception("API Error: User creation failed")
            return {"email": user_data["email"]}

        mock_repo.create_user.side_effect = create_user_side_effect

        # Configure update_user: succeed for user3, fail for user4
        def update_user_side_effect(email, user_data, namespace="system"):
            if email == "update2@example.com":
                raise Exception("API Error: User update failed")
            return {"email": email}

        mock_repo.update_user.side_effect = update_user_side_effect

        # Configure delete_user: succeed for orphan1, fail for orphan2
        def delete_user_side_effect(email, namespace="system"):
            if email == "orphan2@example.com":
                raise Exception("API Error: User deletion failed")
            return None

        mock_repo.delete_user.side_effect = delete_user_side_effect

        service = UserSyncService(mock_repo)

        # Planned users from CSV
        planned_users = [
            # New users
            User(
                email="newuser1@example.com",
                display_name="New User 1",
                first_name="New",
                last_name="User1",
            ),
            User(
                email="newuser2@example.com",
                display_name="New User 2",
                first_name="New",
                last_name="User2",
            ),
            # Updated users
            User(
                email="update1@example.com",
                display_name="Updated Name 1",
                first_name="Updated",
                last_name="Name1",
            ),
            User(
                email="update2@example.com",
                display_name="Updated Name 2",
                first_name="Updated",
                last_name="Name2",
            ),
            # Unchanged user
            User(
                email="unchanged@example.com",
                display_name="Unchanged User",
                first_name="Unchanged",
                last_name="User",
                active=True,
                groups=["GROUP1"],
            ),
        ]

        # Existing users in F5 XC
        existing_users = {
            "update1@example.com": {
                "email": "update1@example.com",
                "username": "update1@example.com",
                "display_name": "Old Name 1",
                "first_name": "Old",
                "last_name": "Name1",
                "active": True,
                "groups": [],
            },
            "update2@example.com": {
                "email": "update2@example.com",
                "username": "update2@example.com",
                "display_name": "Old Name 2",
                "first_name": "Old",
                "last_name": "Name2",
                "active": True,
                "groups": [],
            },
            "unchanged@example.com": {
                "email": "unchanged@example.com",
                "username": "unchanged@example.com",
                "display_name": "Unchanged User",
                "first_name": "Unchanged",
                "last_name": "User",
                "active": True,
                "groups": ["GROUP1"],
            },
            "orphan1@example.com": {
                "email": "orphan1@example.com",
                "username": "orphan1@example.com",
                "display_name": "Orphan 1",
                "first_name": "Orphan",
                "last_name": "1",
                "active": True,
                "groups": [],
            },
            "orphan2@example.com": {
                "email": "orphan2@example.com",
                "username": "orphan2@example.com",
                "display_name": "Orphan 2",
                "first_name": "Orphan",
                "last_name": "2",
                "active": True,
                "groups": [],
            },
        }

        # Execute sync with delete_users=True
        stats = service.sync_users(
            planned_users, existing_users, dry_run=False, delete_users=True
        )

        # Verify operation counts
        assert stats.created == 1, "Should have 1 successful create"
        assert stats.updated == 1, "Should have 1 successful update"
        assert stats.deleted == 1, "Should have 1 successful delete"
        assert stats.unchanged == 1, "Should have 1 unchanged user"
        assert stats.errors == 3, "Should have 3 total errors"

        # Verify error details collection
        assert len(stats.error_details) == 3, "Should have 3 error detail entries"

        # Verify error details content
        error_emails = {err["email"] for err in stats.error_details}
        assert (
            "newuser2@example.com" in error_emails
        ), "Create failure should be recorded"
        assert (
            "update2@example.com" in error_emails
        ), "Update failure should be recorded"
        assert (
            "orphan2@example.com" in error_emails
        ), "Delete failure should be recorded"

        # Verify error operations
        error_ops = {err["operation"] for err in stats.error_details}
        assert "create" in error_ops, "Create operation error recorded"
        assert "update" in error_ops, "Update operation error recorded"
        assert "delete" in error_ops, "Delete operation error recorded"

        # Verify has_errors() detection
        assert stats.has_errors() is True, "has_errors() should detect errors"

        # Verify summary() format
        summary = stats.summary()
        assert "created=1" in summary, "Summary should show created count"
        assert "updated=1" in summary, "Summary should show updated count"
        assert "deleted=1" in summary, "Summary should show deleted count"
        assert "unchanged=1" in summary, "Summary should show unchanged count"
        assert "errors=3" in summary, "Summary should show error count"

    def test_full_sync_all_successes_no_errors(self):
        """Test complete sync workflow with all operations succeeding (T074).

        Scenario:
        - 1 new user: succeeds
        - 1 updated user: succeeds
        - 1 unchanged user
        - 1 deleted user: succeeds

        Expected summary:
        - created=1, updated=1, deleted=1, unchanged=1, errors=0
        - error_details is empty
        - has_errors() returns False
        """
        mock_repo = Mock()
        mock_repo.create_user.return_value = {"email": "new@example.com"}
        mock_repo.update_user.return_value = {"email": "update@example.com"}
        mock_repo.delete_user.return_value = None

        service = UserSyncService(mock_repo)

        planned_users = [
            User(
                email="new@example.com",
                display_name="New User",
                first_name="New",
                last_name="User",
            ),
            User(
                email="update@example.com",
                display_name="Updated Name",
                first_name="Updated",
                last_name="Name",
            ),
            User(
                email="unchanged@example.com",
                display_name="Unchanged User",
                first_name="Unchanged",
                last_name="User",
                active=True,
                groups=["GROUP1"],
            ),
        ]

        existing_users = {
            "update@example.com": {
                "email": "update@example.com",
                "username": "update@example.com",
                "display_name": "Old Name",
                "first_name": "Old",
                "last_name": "Name",
                "active": True,
                "groups": [],
            },
            "unchanged@example.com": {
                "email": "unchanged@example.com",
                "username": "unchanged@example.com",
                "display_name": "Unchanged User",
                "first_name": "Unchanged",
                "last_name": "User",
                "active": True,
                "groups": ["GROUP1"],
            },
            "orphan@example.com": {
                "email": "orphan@example.com",
                "username": "orphan@example.com",
                "display_name": "Orphan User",
                "first_name": "Orphan",
                "last_name": "User",
                "active": True,
                "groups": [],
            },
        }

        stats = service.sync_users(
            planned_users, existing_users, dry_run=False, delete_users=True
        )

        # Verify operation counts
        assert stats.created == 1
        assert stats.updated == 1
        assert stats.deleted == 1
        assert stats.unchanged == 1
        assert stats.errors == 0

        # Verify no errors
        assert len(stats.error_details) == 0, "Should have no error details"
        assert stats.has_errors() is False, "has_errors() should be False"

        # Verify summary
        summary = stats.summary()
        assert "errors=0" in summary, "Summary should show zero errors"
