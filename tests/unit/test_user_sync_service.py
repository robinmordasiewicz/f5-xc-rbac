"""Unit tests for UserSyncService."""

from unittest.mock import Mock

import pytest

from xc_rbac_sync.models import User
from xc_rbac_sync.user_sync_service import UserSyncService, UserSyncStats


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

        users = service.parse_csv_to_users(str(csv_file))
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

        users = service.parse_csv_to_users(str(csv_file))
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

        users = service.parse_csv_to_users(str(csv_file))
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

        users = service.parse_csv_to_users(str(csv_file))
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

        planned = service.parse_csv_to_users(str(csv_file))
        existing = service.fetch_existing_users()
        stats = service.sync_users(planned, existing, dry_run=False, delete_users=False)
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
