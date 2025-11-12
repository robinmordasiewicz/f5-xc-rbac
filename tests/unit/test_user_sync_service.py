"""Unit tests for UserSyncService."""

from unittest.mock import Mock

import pytest

from xc_user_group_sync.models import User
from xc_user_group_sync.user_sync_service import UserSyncService, UserSyncStats


class TestUserSyncStats:
    """Test UserSyncStats dataclass."""

    def test_stats_initialization(self):
        """Test stats initialize with zeros."""
        stats = UserSyncStats()
        assert stats.created == 0
        assert stats.updated == 0
        assert stats.deleted == 0
        assert stats.unchanged == 0
        assert stats.errors == 0
        assert stats.error_details == []

    def test_stats_summary(self):
        """Test summary generation."""
        stats = UserSyncStats(created=5, updated=3, deleted=2, unchanged=10, errors=1)
        summary = stats.summary()
        assert "created=5" in summary
        assert "updated=3" in summary
        assert "deleted=2" in summary
        assert "unchanged=10" in summary
        assert "errors=1" in summary

    def test_has_errors_true(self):
        """Test has_errors returns True when errors exist."""
        stats = UserSyncStats(errors=1)
        assert stats.has_errors() is True

    def test_has_errors_false(self):
        """Test has_errors returns False when no errors."""
        stats = UserSyncStats()
        assert stats.has_errors() is False


class TestParseCSVToUsers:
    """Test CSV parsing to User objects."""

    def test_parse_csv_valid_data(self, tmp_path):
        """Test CSV parsing with valid data (T014)."""
        csv_content = (
            "Email,User Display Name,Employee Status,"
            "Entitlement Display Name\n"
            "alice@example.com,Alice Anderson,A,"
            '"CN=EADMIN_STD,OU=Groups,DC=example,DC=com"\n'
            "bob@example.com,Bob Smith,I,"
            '"CN=DEVELOPERS,OU=Groups,DC=example,DC=com|'
            'CN=TESTERS,OU=Groups,DC=example,DC=com"'
        )

        csv_file = tmp_path / "test_users.csv"
        csv_file.write_text(csv_content)

        mock_repo = Mock()
        service = UserSyncService(mock_repo)

        result = service.parse_csv_to_users(str(csv_file))
        assert result.total_count == 2
        assert result.active_count == 1
        assert result.inactive_count == 1
        users = result.users
        assert len(users) == 2
        assert users[0].email == "alice@example.com"
        assert users[0].first_name == "Alice"
        assert users[0].last_name == "Anderson"
        assert users[0].active is True
        assert "EADMIN_STD" in users[0].groups
        assert users[1].email == "bob@example.com"
        assert users[1].active is False
        assert "DEVELOPERS" in users[1].groups
        assert "TESTERS" in users[1].groups

    def test_parse_csv_missing_required_columns(self, tmp_path):
        """Test CSV parsing raises ValueError on missing columns (T015)."""
        csv_content = "Email,User Display Name\n" "alice@example.com,Alice Anderson"

        csv_file = tmp_path / "invalid.csv"
        csv_file.write_text(csv_content)

        mock_repo = Mock()
        service = UserSyncService(mock_repo)

        with pytest.raises(ValueError, match="Missing required columns"):
            service.parse_csv_to_users(str(csv_file))

    def test_parse_csv_name_variations(self, tmp_path):
        """Test CSV parsing with name variations (T016)."""
        csv_content = (
            "Email,User Display Name,Employee Status,Entitlement Display Name\n"
            "single@example.com,Madonna,A,\n"
            "three@example.com,John Paul Smith,A,\n"
            "whitespace@example.com,  Alice  Anderson  ,A,"
        )

        csv_file = tmp_path / "names.csv"
        csv_file.write_text(csv_content)

        mock_repo = Mock()
        service = UserSyncService(mock_repo)

        result = service.parse_csv_to_users(str(csv_file))
        users = result.users
        assert users[0].first_name == "Madonna"
        assert users[0].last_name == ""
        assert users[1].first_name == "John Paul"
        assert users[1].last_name == "Smith"
        assert users[2].first_name == "Alice"
        assert users[2].last_name == "Anderson"

    def test_parse_csv_status_mapping(self, tmp_path):
        """Test CSV parsing with status mapping (T017)."""
        csv_content = (
            "Email,User Display Name,Employee Status,Entitlement Display Name\n"
            "active@example.com,Active User,A,\n"
            "inactive@example.com,Inactive User,I,\n"
            "terminated@example.com,Terminated User,T,"
        )

        csv_file = tmp_path / "status.csv"
        csv_file.write_text(csv_content)

        mock_repo = Mock()
        service = UserSyncService(mock_repo)

        result = service.parse_csv_to_users(str(csv_file))
        users = result.users
        assert users[0].active is True
        assert users[1].active is False
        assert users[2].active is False

    def test_parse_csv_pipe_separated_groups(self, tmp_path):
        """Test CSV parsing with pipe-separated group DNs (T018)."""
        csv_content = (
            "Email,User Display Name,Employee Status,Entitlement Display Name\n"
            'alice@example.com,Alice Anderson,A,"CN=GROUP1,OU=Groups,DC=ex,DC=com|'
            "CN=GROUP2,OU=Groups,DC=ex,DC=com|"
            'CN=GROUP3,OU=Groups,DC=ex,DC=com"'
        )

        csv_file = tmp_path / "groups.csv"
        csv_file.write_text(csv_content)

        mock_repo = Mock()
        service = UserSyncService(mock_repo)

        result = service.parse_csv_to_users(str(csv_file))
        users = result.users
        assert len(users[0].groups) == 3
        assert "GROUP1" in users[0].groups
        assert "GROUP2" in users[0].groups
        assert "GROUP3" in users[0].groups


class TestSyncUsersOperations:
    """Test sync_users reconciliation logic."""

    def test_sync_creates_new_user(self):
        """Test sync_users creates user when not in F5 XC (T019)."""
        mock_repo = Mock()
        mock_repo.create_user.return_value = {"email": "alice@example.com"}

        service = UserSyncService(mock_repo)

        planned = [
            User(
                email="alice@example.com",
                display_name="Alice Anderson",
                first_name="Alice",
                last_name="Anderson",
            )
        ]
        existing = {}

        stats = service.sync_users(planned, existing, dry_run=False, delete_users=False)
        assert stats.created == 1
        assert stats.unchanged == 0
        assert stats.updated == 0
        assert stats.deleted == 0
        assert stats.errors == 0
        mock_repo.create_user.assert_called_once()

    def test_sync_updates_changed_user(self):
        """Test sync_users updates user when attributes differ (T020)."""
        mock_repo = Mock()
        mock_repo.update_user.return_value = {"email": "alice@example.com"}

        service = UserSyncService(mock_repo)

        planned = [
            User(
                email="alice@example.com",
                display_name="Alice Smith",  # Name changed
                first_name="Alice",
                last_name="Smith",
                active=True,
            )
        ]
        existing = {
            "alice@example.com": {
                "email": "alice@example.com",
                "display_name": "Alice Anderson",
                "first_name": "Alice",
                "last_name": "Anderson",
                "active": True,
            }
        }

        stats = service.sync_users(planned, existing, dry_run=False, delete_users=False)
        assert stats.updated == 1
        assert stats.created == 0
        assert stats.unchanged == 0
        mock_repo.update_user.assert_called_once()

    def test_sync_skips_unchanged_user(self):
        """Test sync_users skips user when attributes match (T021)."""
        mock_repo = Mock()

        service = UserSyncService(mock_repo)

        planned = [
            User(
                email="alice@example.com",
                username="alice@example.com",
                display_name="Alice Anderson",
                first_name="Alice",
                last_name="Anderson",
                active=True,
                groups=["GROUP1"],
            )
        ]
        existing = {
            "alice@example.com": {
                "email": "alice@example.com",
                "username": "alice@example.com",
                "display_name": "Alice Anderson",
                "first_name": "Alice",
                "last_name": "Anderson",
                "active": True,
                "groups": ["GROUP1"],
            }
        }

        stats = service.sync_users(planned, existing, dry_run=False, delete_users=False)
        assert stats.unchanged == 1
        assert stats.created == 0
        assert stats.updated == 0
        assert stats.deleted == 0
        mock_repo.create_user.assert_not_called()
        mock_repo.update_user.assert_not_called()


class TestIntegration:
    """Integration tests for full sync workflow."""

    def test_full_sync_workflow(self, tmp_path):
        """Test complete sync: parse CSV → fetch existing → reconcile (T022)."""
        # Create test CSV
        csv_content = (
            "Email,User Display Name,Employee Status,Entitlement Display Name\n"
            'alice@example.com,Alice Anderson,A,"CN=GROUP1,OU=Groups,DC=example,DC=com"'
        )
        csv_file = tmp_path / "test.csv"
        csv_file.write_text(csv_content)

        # Mock F5 XC API
        mock_repo = Mock()
        mock_repo.list_users.return_value = {}
        mock_repo.create_user.return_value = {"email": "alice@example.com"}

        service = UserSyncService(mock_repo)

        result = service.parse_csv_to_users(str(csv_file))
        existing = service.fetch_existing_users()
        stats = service.sync_users(
            result.users, existing, dry_run=False, delete_users=False
        )
        assert stats.created == 1
        assert stats.errors == 0
        mock_repo.create_user.assert_called_once()

    def test_idempotency_no_changes_on_rerun(self):
        """Test running sync twice produces no changes on second run (T023)."""
        mock_repo = Mock()

        # First run: user doesn't exist
        mock_repo.create_user.return_value = {"email": "alice@example.com"}

        service = UserSyncService(mock_repo)

        planned = [
            User(
                email="alice@example.com",
                display_name="Alice Anderson",
                first_name="Alice",
                last_name="Anderson",
            )
        ]

        # First run - creates user
        stats1 = service.sync_users(planned, {}, dry_run=False, delete_users=False)
        assert stats1.created == 1

        # Second run - user now exists and matches
        existing = {
            "alice@example.com": {
                "email": "alice@example.com",
                "username": "alice@example.com",
                "display_name": "Alice Anderson",
                "first_name": "Alice",
                "last_name": "Anderson",
                "active": True,
                "groups": [],
            }
        }
        stats2 = service.sync_users(
            planned, existing, dry_run=False, delete_users=False
        )
        assert stats2.unchanged == 1
        assert stats2.created == 0
        assert stats2.updated == 0


class TestUserDeletion:
    """Test user deletion functionality (Phase 4 - US3)."""

    def test_sync_deletes_user_when_delete_users_true(self):
        """Test sync_users deletes user when delete_users=True (T045)."""
        mock_repo = Mock()
        mock_repo.delete_user.return_value = None

        service = UserSyncService(mock_repo)

        # CSV has no users, but F5 XC has one user
        planned = []
        existing = {
            "orphan@example.com": {
                "email": "orphan@example.com",
                "username": "orphan@example.com",
                "display_name": "Orphan User",
                "first_name": "Orphan",
                "last_name": "User",
                "active": True,
                "groups": [],
            }
        }

        stats = service.sync_users(planned, existing, dry_run=False, delete_users=True)
        assert stats.deleted == 1
        assert stats.created == 0
        assert stats.updated == 0
        assert stats.unchanged == 0
        mock_repo.delete_user.assert_called_once_with("orphan@example.com")

    def test_sync_preserves_user_when_delete_users_false(self):
        """Test sync_users preserves user when delete_users=False (T046)."""
        mock_repo = Mock()

        service = UserSyncService(mock_repo)

        # CSV has no users, but F5 XC has one user
        planned = []
        existing = {
            "orphan@example.com": {
                "email": "orphan@example.com",
                "username": "orphan@example.com",
                "display_name": "Orphan User",
                "first_name": "Orphan",
                "last_name": "User",
                "active": True,
                "groups": [],
            }
        }

        stats = service.sync_users(planned, existing, dry_run=False, delete_users=False)
        assert stats.deleted == 0
        assert stats.created == 0
        assert stats.updated == 0
        assert stats.unchanged == 0
        mock_repo.delete_user.assert_not_called()

    def test_delete_user_error_handling(self):
        """Test delete_user handles errors gracefully (T045)."""
        mock_repo = Mock()
        mock_repo.delete_user.side_effect = Exception("API Error")

        service = UserSyncService(mock_repo)

        planned = []
        existing = {"orphan@example.com": {"email": "orphan@example.com"}}

        stats = service.sync_users(planned, existing, dry_run=False, delete_users=True)
        assert stats.errors == 1
        assert stats.deleted == 0
        assert len(stats.error_details) == 1
        assert stats.error_details[0]["email"] == "orphan@example.com"
        assert stats.error_details[0]["operation"] == "delete"

    def test_cleanup_orphaned_users_deletes_extra_users(self):
        """Test cleanup_orphaned_users deletes users not in CSV."""
        mock_repo = Mock()
        mock_repo.delete_user.return_value = None

        service = UserSyncService(mock_repo)

        # CSV has one user, but XC has two users
        from xc_user_group_sync.models import User

        planned = [
            User(
                email="keep@example.com",
                display_name="Keep User",
                first_name="Keep",
                last_name="User",
                active=True,
                groups=[],
            )
        ]
        existing = {
            "keep@example.com": {"email": "keep@example.com"},
            "delete@example.com": {"email": "delete@example.com"},
        }

        stats = service.cleanup_orphaned_users(planned, existing, dry_run=False)
        assert stats.deleted == 1
        assert stats.errors == 0
        mock_repo.delete_user.assert_called_once_with("delete@example.com")

    def test_cleanup_orphaned_users_dry_run(self):
        """Test cleanup_orphaned_users in dry-run mode doesn't delete."""
        mock_repo = Mock()

        service = UserSyncService(mock_repo)

        # CSV has no users, but XC has one user
        planned = []
        existing = {"orphan@example.com": {"email": "orphan@example.com"}}

        stats = service.cleanup_orphaned_users(planned, existing, dry_run=True)
        assert stats.deleted == 1  # Count shows what would be deleted
        assert stats.errors == 0
        mock_repo.delete_user.assert_not_called()  # But no actual deletion

    def test_cleanup_orphaned_users_handles_errors(self):
        """Test cleanup_orphaned_users handles deletion errors gracefully."""
        mock_repo = Mock()
        mock_repo.delete_user.side_effect = Exception("API Error")

        service = UserSyncService(mock_repo)

        planned = []
        existing = {"orphan@example.com": {"email": "orphan@example.com"}}

        stats = service.cleanup_orphaned_users(planned, existing, dry_run=False)
        assert stats.errors == 1
        assert stats.deleted == 0
        assert len(stats.error_details) == 1
        assert stats.error_details[0]["email"] == "orphan@example.com"

    def test_cleanup_orphaned_users_case_insensitive(self):
        """Test cleanup_orphaned_users handles email case insensitivity."""
        mock_repo = Mock()

        service = UserSyncService(mock_repo)

        # CSV has user with lowercase email
        from xc_user_group_sync.models import User

        planned = [
            User(
                email="keep@example.com",
                display_name="Keep User",
                first_name="Keep",
                last_name="User",
                active=True,
                groups=[],
            )
        ]
        # XC has same user with uppercase email
        existing = {
            "Keep@Example.Com": {"email": "Keep@Example.Com"},
            "delete@example.com": {"email": "delete@example.com"},
        }

        stats = service.cleanup_orphaned_users(planned, existing, dry_run=False)
        assert stats.deleted == 1  # Only delete@example.com should be deleted
        assert stats.errors == 0
        mock_repo.delete_user.assert_called_once_with("delete@example.com")


class TestDryRunMode:
    """Test dry-run mode functionality (Phase 5 - US5)."""

    def test_dry_run_logs_creates_without_executing(self):
        """Test dry_run logs creates without executing (T059)."""
        mock_repo = Mock()
        service = UserSyncService(mock_repo)

        planned = [
            User(
                email="new@example.com",
                display_name="New User",
                first_name="New",
                last_name="User",
            )
        ]
        existing = {}

        stats = service.sync_users(planned, existing, dry_run=True, delete_users=False)
        assert stats.created == 1
        assert stats.errors == 0
        # Verify no actual API calls made
        mock_repo.create_user.assert_not_called()

    def test_dry_run_logs_updates_without_executing(self):
        """Test dry_run logs updates without executing (T060)."""
        mock_repo = Mock()
        service = UserSyncService(mock_repo)

        planned = [
            User(
                email="existing@example.com",
                display_name="Updated Name",
                first_name="Updated",
                last_name="Name",
            )
        ]
        existing = {
            "existing@example.com": {
                "email": "existing@example.com",
                "username": "existing@example.com",
                "display_name": "Old Name",
                "first_name": "Old",
                "last_name": "Name",
                "active": True,
                "groups": [],
            }
        }

        stats = service.sync_users(planned, existing, dry_run=True, delete_users=False)
        assert stats.updated == 1
        assert stats.errors == 0
        # Verify no actual API calls made
        mock_repo.update_user.assert_not_called()

    def test_dry_run_logs_deletes_without_executing(self):
        """Test dry_run logs deletes without executing (T061)."""
        mock_repo = Mock()
        service = UserSyncService(mock_repo)

        planned = []
        existing = {
            "orphan@example.com": {
                "email": "orphan@example.com",
                "username": "orphan@example.com",
                "display_name": "Orphan User",
                "first_name": "Orphan",
                "last_name": "User",
                "active": True,
                "groups": [],
            }
        }

        stats = service.sync_users(planned, existing, dry_run=True, delete_users=True)
        assert stats.deleted == 1
        assert stats.errors == 0
        # Verify no actual API calls made
        mock_repo.delete_user.assert_not_called()

    def test_dry_run_shows_correct_summary_counts(self):
        """Test dry_run shows correct summary counts (T062)."""
        mock_repo = Mock()
        service = UserSyncService(mock_repo)

        # Mix of operations: 1 create, 1 update, 1 unchanged, 1 delete
        planned = [
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
                display_name="Same Name",
                first_name="Same",
                last_name="Name",
                active=True,
                groups=["GROUP1"],
            ),
        ]

        existing = {
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
                "display_name": "Same Name",
                "first_name": "Same",
                "last_name": "Name",
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

        stats = service.sync_users(planned, existing, dry_run=True, delete_users=True)
        assert stats.created == 1
        assert stats.updated == 1
        assert stats.unchanged == 1
        assert stats.deleted == 1
        assert stats.errors == 0

        # Verify summary string format
        summary = stats.summary()
        assert "created=1" in summary
        assert "updated=1" in summary
        assert "unchanged=1" in summary
        assert "deleted=1" in summary
        assert "errors=0" in summary

        # Verify no actual API calls made
        mock_repo.create_user.assert_not_called()
        mock_repo.update_user.assert_not_called()
        mock_repo.delete_user.assert_not_called()
