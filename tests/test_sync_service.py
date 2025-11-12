"""Tests for group synchronization service."""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from xc_user_group_sync.models import Group
from xc_user_group_sync.sync_service import (
    CSVParseError,
    GroupSyncService,
    SyncStats,
)


class TestSyncStats:
    """Test SyncStats dataclass."""

    def test_default_values(self):
        """Test default initialization."""
        stats = SyncStats()
        assert stats.created == 0
        assert stats.updated == 0
        assert stats.deleted == 0
        assert stats.skipped == 0
        assert stats.errors == 0
        assert stats.skipped_due_to_unknown == 0

    def test_custom_values(self):
        """Test initialization with custom values."""
        stats = SyncStats(created=5, updated=3, deleted=2, skipped=1, errors=0)
        assert stats.created == 5
        assert stats.updated == 3
        assert stats.deleted == 2
        assert stats.skipped == 1
        assert stats.errors == 0

    def test_summary(self):
        """Test summary message generation."""
        stats = SyncStats(created=1, updated=2, deleted=3, skipped=4, errors=5)
        summary = stats.summary()
        assert "created=1" in summary
        assert "updated=2" in summary
        assert "deleted=3" in summary
        assert "skipped=4" in summary
        assert "errors=5" in summary

    def test_has_errors_false(self):
        """Test has_errors returns False when no errors."""
        stats = SyncStats(created=5, updated=3)
        assert not stats.has_errors()

    def test_has_errors_true(self):
        """Test has_errors returns True when errors present."""
        stats = SyncStats(errors=1)
        assert stats.has_errors()


class TestGroupSyncService:
    """Test GroupSyncService functionality."""

    @pytest.fixture
    def mock_repository(self):
        """Create mock repository."""
        return Mock()

    @pytest.fixture
    def service(self, mock_repository):
        """Create service with mock repository."""
        return GroupSyncService(mock_repository)

    def test_service_initialization(self, mock_repository):
        """Test service initializes with repository."""
        service = GroupSyncService(mock_repository)
        assert service.repository == mock_repository

    def test_parse_csv_to_groups_valid(self, service, temp_csv_file):
        """Test parsing valid CSV file."""
        groups = service.parse_csv_to_groups(temp_csv_file)
        assert len(groups) == 2
        assert groups[0].name == "admins"
        assert len(groups[0].users) == 2
        assert "admin@example.com" in groups[0].users
        assert "root@example.com" in groups[0].users

    def test_parse_csv_to_groups_missing_columns(self, service, tmp_path):
        """Test CSV missing required columns raises error."""
        csv_file = tmp_path / "invalid.csv"
        csv_file.write_text("Name,Value\ntest,data\n")

        with pytest.raises(CSVParseError, match="missing required columns"):
            service.parse_csv_to_groups(str(csv_file))

    def test_parse_csv_to_groups_empty_rows(self, service, tmp_path):
        """Test CSV with empty rows are skipped."""
        csv_content = """Email,Entitlement Display Name
admin@example.com,"CN=admins,OU=Groups,DC=example,DC=com"
,
,"CN=empty,OU=Groups,DC=example,DC=com"
"""
        csv_file = tmp_path / "partial.csv"
        csv_file.write_text(csv_content)

        groups = service.parse_csv_to_groups(str(csv_file))
        assert len(groups) == 1
        assert groups[0].name == "admins"

    def test_parse_csv_to_groups_invalid_dn(self, service, tmp_path, caplog):
        """Test CSV with invalid DN logs warning and skips row."""
        csv_content = """Email,Entitlement Display Name
admin@example.com,"not a valid dn"
user@example.com,"CN=users,OU=Groups,DC=example,DC=com"
"""
        csv_file = tmp_path / "invalid_dn.csv"
        csv_file.write_text(csv_content)

        groups = service.parse_csv_to_groups(str(csv_file))
        assert len(groups) == 1
        assert groups[0].name == "users"
        assert "DN parse error" in caplog.text

    def test_fetch_existing_groups(self, service, mock_repository):
        """Test fetching existing groups from repository."""
        mock_repository.list_groups.return_value = {
            "items": [
                {"name": "admins", "usernames": ["admin@example.com"]},
                {"name": "users", "usernames": ["user@example.com"]},
            ]
        }

        existing = service.fetch_existing_groups()
        assert len(existing) == 2
        assert "admins" in existing
        assert "users" in existing
        mock_repository.list_groups.assert_called_once()

    def test_fetch_existing_groups_filters_non_dict(self, service, mock_repository):
        """Test fetch filters out non-dict items."""
        mock_repository.list_groups.return_value = {
            "items": [
                {"name": "admins"},
                "invalid",
                None,
                {"name": "users"},
            ]
        }

        existing = service.fetch_existing_groups()
        assert len(existing) == 2

    def test_fetch_existing_users_success(self, service, mock_repository):
        """Test fetching existing users."""
        mock_repository.list_user_roles.return_value = {
            "items": [
                {"username": "admin@example.com"},
                {"email": "user@example.com"},
                {"username": None, "email": "other@example.com"},
            ]
        }

        users = service.fetch_existing_users()
        assert len(users) == 3
        assert "admin@example.com" in users
        assert "user@example.com" in users
        assert "other@example.com" in users

    def test_fetch_existing_users_failure_returns_none(
        self, service, mock_repository, caplog
    ):
        """Test fetch users returns None on error."""
        mock_repository.list_user_roles.side_effect = Exception("API error")

        users = service.fetch_existing_users()
        assert users is None
        assert "Could not pre-validate users" in caplog.text

    def test_sync_groups_skip_unknown_users(self, service, mock_repository):
        """Test sync skips groups with unknown users."""
        planned = [Group(name="test", users=["unknown@example.com"])]
        existing_groups = {}
        existing_users = {"known@example.com"}

        stats = service.sync_groups(planned, existing_groups, existing_users, False)

        assert stats.skipped_due_to_unknown == 1
        assert stats.errors == 1
        assert stats.created == 0

    def test_sync_groups_create_new_group(self, service, mock_repository):
        """Test sync creates new groups."""
        planned = [Group(name="new-group", users=["user@example.com"])]
        existing_groups = {}
        existing_users = {"user@example.com"}

        mock_repository.create_group.return_value = {"name": "new-group"}

        stats = service.sync_groups(planned, existing_groups, existing_users, False)

        assert stats.created == 1
        assert stats.errors == 0
        mock_repository.create_group.assert_called_once()

    def test_sync_groups_create_dry_run(self, service, mock_repository):
        """Test sync in dry-run mode doesn't create."""
        planned = [Group(name="new-group", users=["user@example.com"])]
        existing_groups = {}
        existing_users = {"user@example.com"}

        stats = service.sync_groups(planned, existing_groups, existing_users, True)

        assert stats.created == 0
        mock_repository.create_group.assert_not_called()

    def test_sync_groups_create_error(self, service, mock_repository, caplog):
        """Test sync handles creation errors."""
        planned = [Group(name="new-group", users=["user@example.com"])]
        existing_groups = {}
        existing_users = {"user@example.com"}

        mock_repository.create_group.side_effect = Exception("API error")

        stats = service.sync_groups(planned, existing_groups, existing_users, False)

        assert stats.created == 0
        assert stats.errors == 1
        assert "Failed to create new-group" in caplog.text

    def test_sync_groups_update_existing(self, service, mock_repository):
        """Test sync updates existing groups with changes."""
        planned = [
            Group(name="admins", users=["admin@example.com", "root@example.com"])
        ]
        existing_groups = {
            "admins": {"name": "admins", "usernames": ["admin@example.com"]}
        }
        existing_users = {"admin@example.com", "root@example.com"}

        mock_repository.update_group.return_value = {"name": "admins"}

        stats = service.sync_groups(planned, existing_groups, existing_users, False)

        assert stats.updated == 1
        assert stats.errors == 0
        mock_repository.update_group.assert_called_once()

    def test_sync_groups_skip_unchanged(self, service, mock_repository):
        """Test sync skips groups with no changes."""
        planned = [Group(name="admins", users=["admin@example.com"])]
        existing_groups = {
            "admins": {"name": "admins", "usernames": ["admin@example.com"]}
        }
        existing_users = {"admin@example.com"}

        stats = service.sync_groups(planned, existing_groups, existing_users, False)

        assert stats.skipped == 1
        assert stats.updated == 0
        mock_repository.update_group.assert_not_called()

    def test_sync_groups_update_dry_run(self, service, mock_repository):
        """Test sync in dry-run mode doesn't update."""
        planned = [
            Group(name="admins", users=["admin@example.com", "root@example.com"])
        ]
        existing_groups = {
            "admins": {"name": "admins", "usernames": ["admin@example.com"]}
        }
        existing_users = {"admin@example.com", "root@example.com"}

        stats = service.sync_groups(planned, existing_groups, existing_users, True)

        assert stats.updated == 0
        mock_repository.update_group.assert_not_called()

    def test_sync_groups_update_error(self, service, mock_repository, caplog):
        """Test sync handles update errors."""
        planned = [
            Group(name="admins", users=["admin@example.com", "root@example.com"])
        ]
        existing_groups = {
            "admins": {"name": "admins", "usernames": ["admin@example.com"]}
        }
        existing_users = {"admin@example.com", "root@example.com"}

        mock_repository.update_group.side_effect = Exception("API error")

        stats = service.sync_groups(planned, existing_groups, existing_users, False)

        assert stats.updated == 0
        assert stats.errors == 1
        assert "Failed to update admins" in caplog.text

    def test_sync_groups_no_user_validation(self, service, mock_repository):
        """Test sync without user validation (existing_users=None)."""
        planned = [Group(name="new-group", users=["any@example.com"])]
        existing_groups = {}

        mock_repository.create_group.return_value = {"name": "new-group"}

        stats = service.sync_groups(planned, existing_groups, None, False)

        assert stats.created == 1
        assert stats.skipped_due_to_unknown == 0

    def test_cleanup_orphaned_groups(self, service, mock_repository):
        """Test cleanup deletes orphaned groups."""
        planned = [Group(name="keep", users=[])]
        existing_groups = {
            "keep": {"name": "keep"},
            "delete1": {"name": "delete1"},
            "delete2": {"name": "delete2"},
        }

        deleted = service.cleanup_orphaned_groups(planned, existing_groups, False)

        assert deleted == 2
        assert mock_repository.delete_group.call_count == 2

    def test_cleanup_dry_run(self, service, mock_repository):
        """Test cleanup in dry-run mode."""
        planned = [Group(name="keep", users=[])]
        existing_groups = {
            "keep": {"name": "keep"},
            "delete": {"name": "delete"},
        }

        deleted = service.cleanup_orphaned_groups(planned, existing_groups, True)

        assert deleted == 0
        mock_repository.delete_group.assert_not_called()

    def test_cleanup_delete_error(self, service, mock_repository, caplog):
        """Test cleanup handles deletion errors."""
        planned = []
        existing_groups = {"delete": {"name": "delete"}}

        mock_repository.delete_group.side_effect = Exception("API error")

        deleted = service.cleanup_orphaned_groups(planned, existing_groups, False)

        assert deleted == 0
        assert "Failed to delete delete" in caplog.text

    def test_cleanup_no_extra_groups(self, service, mock_repository):
        """Test cleanup with no orphaned groups."""
        planned = [Group(name="keep", users=[])]
        existing_groups = {"keep": {"name": "keep"}}

        deleted = service.cleanup_orphaned_groups(planned, existing_groups, False)

        assert deleted == 0
        mock_repository.delete_group.assert_not_called()
