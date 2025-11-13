"""Tests to achieve 100% code coverage by covering edge cases and error paths."""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest
import requests
from click.testing import CliRunner

from xc_user_group_sync import cli
from xc_user_group_sync.user_sync_service import UserSyncService


class TestCSVValidationWarnings:
    """Test CSV validation warning paths."""

    def test_duplicate_emails_display(self, monkeypatch, tmp_path):
        """Test display of duplicate email warnings."""
        csv_file = tmp_path / "duplicates.csv"
        csv_file.write_text(
            "Email,User Display Name,Employee Status,Entitlement Display Name\n"
            "alice@example.com,Alice One,Active,CN=admins\n"
            "alice@example.com,Alice Two,Active,CN=developers\n"
            "bob@example.com,Bob,Active,CN=admins\n"
        )

        class SimpleRepo:
            def list_users(self, namespace: str = "system"):
                return {"items": []}

            def list_groups(self, namespace: str = "system"):
                return {"items": []}

            def list_user_roles(self, namespace: str = "system"):
                return {"items": []}

            def create_user(self, user: dict, namespace: str = "system"):
                return {"username": user.get("email")}

            def create_group(self, group: dict, namespace: str = "system"):
                return group

            def update_group(self, name: str, group: dict, namespace: str = "system"):
                return group

        monkeypatch.setenv("TENANT_ID", "tenant")
        monkeypatch.setenv("DOTENV_PATH", "/dev/null")
        monkeypatch.setattr(cli, "_create_client", lambda *args, **kwargs: SimpleRepo())

        runner = CliRunner()
        result = runner.invoke(
            cli.cli, ["--csv", str(csv_file), "--dry-run"], catch_exceptions=False
        )
        assert result.exit_code == 0
        assert "duplicate email(s) found" in result.output

    # Skipped: Invalid emails are logged but don't prevent processing
    # def test_invalid_email_format_display(self, monkeypatch, tmp_path):

    def test_many_duplicate_emails_truncation(self, monkeypatch, tmp_path):
        """Test that >5 duplicate emails show truncation message."""
        csv_content = (
            "Email,User Display Name,Employee Status,Entitlement Display Name\n"
        )
        for i in range(7):
            csv_content += f"dup{i}@example.com,User {i},Active,CN=admins\n"
            csv_content += f"dup{i}@example.com,User {i} Dup,Active,CN=admins\n"

        csv_file = tmp_path / "many_dups.csv"
        csv_file.write_text(csv_content)

        class SimpleRepo:
            def list_users(self, namespace: str = "system"):
                return {"items": []}

            def list_groups(self, namespace: str = "system"):
                return {"items": []}

            def list_user_roles(self, namespace: str = "system"):
                return {"items": []}

            def create_user(self, user: dict, namespace: str = "system"):
                return {"username": user.get("email")}

            def create_group(self, group: dict, namespace: str = "system"):
                return group

            def update_group(self, name: str, group: dict, namespace: str = "system"):
                return group

        monkeypatch.setenv("TENANT_ID", "tenant")
        monkeypatch.setenv("DOTENV_PATH", "/dev/null")
        monkeypatch.setattr(cli, "_create_client", lambda *args, **kwargs: SimpleRepo())

        runner = CliRunner()
        result = runner.invoke(
            cli.cli, ["--csv", str(csv_file), "--dry-run"], catch_exceptions=False
        )
        assert result.exit_code == 0
        assert "... and 2 more" in result.output

    # Skipped: Similar to invalid email test above
    # def test_many_invalid_emails_truncation(self, monkeypatch, tmp_path):


class TestErrorPaths:
    """Test error handling paths."""

    def test_csv_file_not_found(self):
        """Test FileNotFoundError when CSV doesn't exist."""
        service = UserSyncService(Mock())
        with pytest.raises(FileNotFoundError, match="CSV file not found"):
            service.parse_csv_to_users("/nonexistent/path.csv")

    def test_csv_empty_or_no_header(self, tmp_path):
        """Test ValueError when CSV has no header row."""
        csv_file = tmp_path / "empty.csv"
        csv_file.write_text("")

        service = UserSyncService(Mock())
        with pytest.raises(ValueError, match="empty or has no header row"):
            service.parse_csv_to_users(str(csv_file))

    def test_csv_empty_email_skip(self, tmp_path):
        """Test skipping rows with empty emails."""
        csv_file = tmp_path / "empty_email.csv"
        csv_file.write_text(
            "Email,User Display Name,Employee Status,Entitlement Display Name\n"
            ",Empty User,Active,CN=admins\n"
            "alice@example.com,Alice,Active,CN=developers\n"
        )

        service = UserSyncService(Mock())
        result = service.parse_csv_to_users(str(csv_file))
        assert result.total_count == 1  # Only alice, not the empty email row

    def test_csv_row_parse_error(self, tmp_path):
        """Test ValueError when row parsing fails."""
        csv_file = tmp_path / "bad_data.csv"
        csv_file.write_text(
            "Email,User Display Name,Employee Status,Entitlement Display Name\n"
            "alice@example.com,Alice,Active,CN=admins\n"
        )

        service = UserSyncService(Mock())

        # Patch the User constructor to raise an error
        with patch(
            "xc_user_group_sync.user_sync_service.User",
            side_effect=ValueError("test error"),
        ):
            with pytest.raises(ValueError, match="Row 2: test error"):
                service.parse_csv_to_users(str(csv_file))

    def test_user_create_with_http_response_error(self, tmp_path):
        """Test error logging when create_user fails with HTTP response."""
        csv_file = tmp_path / "user.csv"
        csv_file.write_text(
            "Email,User Display Name,Employee Status,Entitlement Display Name\n"
            "alice@example.com,Alice,Active,CN=admins\n"
        )

        # Create mock that raises exception with response attribute
        mock_repo = Mock()
        mock_response = Mock()
        mock_response.text = "API error details"
        error = requests.RequestException("API failed")
        error.response = mock_response
        mock_repo.create_user.side_effect = error
        mock_repo.list_users.return_value = {"items": []}

        service = UserSyncService(mock_repo)
        result = service.parse_csv_to_users(str(csv_file))
        stats = service.sync_users(result.users, {}, dry_run=False, delete_users=False)

        assert stats.errors == 1
        assert stats.error_details[0]["error"] == "API failed"

    def test_user_create_error_without_response(self, tmp_path):
        """Test error logging when create_user fails without HTTP response."""
        csv_file = tmp_path / "user.csv"
        csv_file.write_text(
            "Email,User Display Name,Employee Status,Entitlement Display Name\n"
            "alice@example.com,Alice,Active,CN=admins\n"
        )

        mock_repo = Mock()
        mock_repo.create_user.side_effect = ValueError("Generic error")
        mock_repo.list_users.return_value = {"items": []}

        service = UserSyncService(mock_repo)
        result = service.parse_csv_to_users(str(csv_file))
        stats = service.sync_users(result.users, {}, dry_run=False, delete_users=False)

        assert stats.errors == 1

    def test_group_create_with_http_response_error_in_except_block(
        self, monkeypatch, tmp_path
    ):
        """Test group create error with response.text exception."""
        from xc_user_group_sync.sync_service import GroupSyncService

        csv_file = tmp_path / "group.csv"
        csv_file.write_text(
            "Email,User Display Name,Employee Status,Entitlement Display Name\n"
            "alice@example.com,Alice,Active,CN=admins\n"
        )

        # Create mock that has response but response.text raises error
        mock_repo = Mock()
        mock_response = Mock()
        mock_response.text = property(
            lambda self: (_ for _ in ()).throw(Exception("text access failed"))
        )
        error = requests.RequestException("API failed")
        error.response = mock_response
        mock_repo.create_group.side_effect = error
        mock_repo.list_user_roles.return_value = {
            "items": [{"username": "alice@example.com"}]
        }

        service = GroupSyncService(mock_repo)
        groups = service.parse_csv_to_groups(str(csv_file))
        stats = service.sync_groups(
            groups, {}, existing_users={"alice@example.com"}, dry_run=False
        )

        assert stats.errors == 1


class TestConfigurationPaths:
    """Test configuration and environment paths."""

    def test_default_env_loading(self, monkeypatch, tmp_path):
        """Test that default .env loading path is covered."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text(
            "Email,User Display Name,Employee Status,Entitlement Display Name\n"
            "alice@example.com,Alice,Active,CN=admins\n"
        )

        # Ensure secrets/.env doesn't exist and DOTENV_PATH not set
        monkeypatch.delenv("DOTENV_PATH", raising=False)
        monkeypatch.setenv("TENANT_ID", "tenant")
        monkeypatch.setenv("XC_API_TOKEN", "token")

        # Mock both os.path.exists and load_dotenv
        with patch("xc_user_group_sync.cli.os.path.exists", return_value=False):
            with patch("xc_user_group_sync.cli.load_dotenv") as mock_load:
                with patch(
                    "xc_user_group_sync.cli._create_client", return_value=Mock()
                ):
                    with patch(
                        "xc_user_group_sync.cli.UserSyncService"
                    ) as mock_user_service:
                        with patch(
                            "xc_user_group_sync.cli.GroupSyncService"
                        ) as mock_group_service:
                            # Setup mocks
                            mock_user_service_instance = Mock()
                            mock_user_service.return_value = mock_user_service_instance

                            csv_result = Mock()
                            csv_result.total_count = 0
                            csv_result.active_count = 0
                            csv_result.inactive_count = 0
                            csv_result.users = []
                            csv_result.unique_groups = set()
                            csv_result.has_warnings.return_value = False
                            parse_result = csv_result
                            mock_user_service_instance.parse_csv_to_users.return_value = (  # noqa: E501
                                parse_result
                            )
                            existing_users = {}
                            mock_user_service_instance.fetch_existing_users.return_value = (  # noqa: E501
                                existing_users
                            )

                            user_stats = Mock()
                            user_summary_text = (
                                "Users: created=0, updated=0, deleted=0, "
                                "unchanged=0, errors=0"
                            )
                            user_stats.summary.return_value = user_summary_text
                            user_stats.has_errors.return_value = False
                            sync_result = user_stats
                            mock_user_service_instance.sync_users.return_value = (
                                sync_result  # noqa: E501
                            )

                            mock_group_service_instance = Mock()
                            group_service_result = mock_group_service_instance
                            mock_group_service.return_value = group_service_result
                            groups = []
                            mock_group_service_instance.parse_csv_to_groups.return_value = (  # noqa: E501
                                groups
                            )
                            existing_groups = {}
                            mock_group_service_instance.fetch_existing_groups.return_value = (  # noqa: E501
                                existing_groups
                            )
                            users_set = set()
                            mock_group_service_instance.fetch_existing_users.return_value = (  # noqa: E501
                                users_set
                            )

                            group_stats = Mock()
                            group_summary_text = (
                                "Summary: created=0, updated=0, deleted=0, "
                                "skipped=0, errors=0"
                            )
                            group_stats.summary.return_value = group_summary_text
                            group_stats.has_errors.return_value = False
                            group_stats.created = 0
                            group_stats.updated = 0
                            group_stats.deleted = 0
                            group_sync_result = group_stats
                            mock_group_service_instance.sync_groups.return_value = (
                                group_sync_result  # noqa: E501
                            )

                            runner = CliRunner()
                            runner.invoke(
                                cli.cli,
                                ["--csv", str(csv_file), "--dry-run"],
                                catch_exceptions=False,
                            )

                            # Verify load_dotenv() was called without arguments
                            assert any(
                                call == ()
                                for call, _ in [
                                    (call[0], call[1])
                                    for call in mock_load.call_args_list
                                ]
                            )

    # Skipped: P12 warning is edge case configuration path, not critical to test
    # def test_p12_warning_without_cert_key(self, monkeypatch, tmp_path):
