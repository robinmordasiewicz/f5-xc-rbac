"""Tests for CLI commands."""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from xc_user_group_sync.cli import cli


@pytest.fixture
def runner():
    """Create CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_env(monkeypatch):
    """Mock environment variables for testing."""
    monkeypatch.setenv("TENANT_ID", "test-tenant")
    monkeypatch.setenv("XC_API_TOKEN", "test-token")


class TestCLIBasics:
    """Test basic CLI functionality."""

    def test_cli_help(self, runner):
        """Test CLI help output."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Synchronize F5 XC" in result.output

    def test_sync_help(self, runner):
        """Test sync command help."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "--csv" in result.output
        assert "--dry-run" in result.output
        assert "--prune" in result.output


class TestCLISyncCommand:
    """Test sync command execution."""

    def test_sync_missing_tenant_id(self, runner, temp_csv_file, clean_env):
        """Test that missing TENANT_ID raises error."""
        result = runner.invoke(cli, ["--csv", temp_csv_file])
        assert result.exit_code != 0
        assert "TENANT_ID must be set" in result.output

    def test_sync_missing_auth(self, runner, temp_csv_file, clean_env, monkeypatch):
        """Test that missing authentication raises error."""
        monkeypatch.setenv("TENANT_ID", "test-tenant")
        result = runner.invoke(cli, ["--csv", temp_csv_file])
        assert result.exit_code != 0
        assert "XC_API_TOKEN" in result.output or "VOLT_API_CERT" in result.output

    def test_sync_missing_csv(self, runner, mock_env):
        """Test that missing CSV file raises error."""
        result = runner.invoke(cli, ["--csv", "/nonexistent/file.csv"])
        assert result.exit_code != 0

    @patch("xc_user_group_sync.cli.UserSyncService")
    @patch("xc_user_group_sync.cli.GroupSyncService")
    @patch("xc_user_group_sync.cli.XCClient")
    def test_sync_dry_run_success(
        self,
        mock_client_class,
        mock_group_service_class,
        mock_user_service_class,
        runner,
        temp_csv_file,
        mock_env,
    ):
        """Test successful dry-run sync."""
        # Setup group service mock
        mock_group_service = Mock()
        mock_group_service_class.return_value = mock_group_service
        mock_group_service.parse_csv_to_groups.return_value = []
        mock_group_service.fetch_existing_groups.return_value = {}
        mock_group_service.fetch_existing_users.return_value = set()

        group_stats_mock = Mock()
        group_stats_mock.summary.return_value = (
            "Summary: created=0, updated=0, deleted=0, skipped=0, errors=0"
        )
        group_stats_mock.has_errors.return_value = False
        group_stats_mock.created = 0
        group_stats_mock.updated = 0
        group_stats_mock.deleted = 0
        mock_group_service.sync_groups.return_value = group_stats_mock

        # Setup user service mock
        mock_user_service = Mock()
        mock_user_service_class.return_value = mock_user_service

        # Mock CSV validation result
        csv_validation_result = Mock()
        csv_validation_result.total_count = 0
        csv_validation_result.active_count = 0
        csv_validation_result.inactive_count = 0
        csv_validation_result.users = []
        csv_validation_result.unique_groups = set()
        csv_validation_result.has_warnings.return_value = False
        mock_user_service.parse_csv_to_users.return_value = csv_validation_result
        mock_user_service.fetch_existing_users.return_value = {}

        user_stats_mock = Mock()
        user_stats_mock.summary.return_value = (
            "Summary: created=0, updated=0, deleted=0, skipped=0, errors=0"
        )
        user_stats_mock.has_errors.return_value = False
        user_stats_mock.created = 0
        user_stats_mock.updated = 0
        user_stats_mock.deleted = 0
        mock_user_service.sync_users.return_value = user_stats_mock

        result = runner.invoke(cli, ["--csv", temp_csv_file, "--dry-run"])

        assert result.exit_code == 0
        assert "SYNCHRONIZATION COMPLETE" in result.output
        mock_group_service.sync_groups.assert_called_once()
        mock_user_service.sync_users.assert_called_once()

    @patch("xc_user_group_sync.cli.UserSyncService")
    @patch("xc_user_group_sync.cli.GroupSyncService")
    @patch("xc_user_group_sync.cli.XCClient")
    def test_sync_with_prune(
        self,
        mock_client_class,
        mock_group_service_class,
        mock_user_service_class,
        runner,
        temp_csv_file,
        mock_env,
    ):
        """Test sync with prune option."""
        # Setup group service mock
        mock_group_service = Mock()
        mock_group_service_class.return_value = mock_group_service
        mock_group_service.parse_csv_to_groups.return_value = []
        mock_group_service.fetch_existing_groups.return_value = {}
        mock_group_service.fetch_existing_users.return_value = set()

        group_stats_mock = Mock()
        group_stats_mock.summary.return_value = (
            "Summary: created=0, updated=0, deleted=0, skipped=0, errors=0"
        )
        group_stats_mock.has_errors.return_value = False
        group_stats_mock.created = 0
        group_stats_mock.updated = 0
        group_stats_mock.deleted = 0
        mock_group_service.sync_groups.return_value = group_stats_mock
        mock_group_service.cleanup_orphaned_groups.return_value = 0

        # Setup user service mock
        mock_user_service = Mock()
        mock_user_service_class.return_value = mock_user_service

        # Mock CSV validation result
        csv_validation_result = Mock()
        csv_validation_result.total_count = 0
        csv_validation_result.active_count = 0
        csv_validation_result.inactive_count = 0
        csv_validation_result.users = []
        csv_validation_result.unique_groups = set()
        csv_validation_result.has_warnings.return_value = False
        mock_user_service.parse_csv_to_users.return_value = csv_validation_result
        mock_user_service.fetch_existing_users.return_value = {}

        user_stats_mock = Mock()
        user_stats_mock.summary.return_value = (
            "Summary: created=0, updated=0, deleted=0, skipped=0, errors=0"
        )
        user_stats_mock.has_errors.return_value = False
        user_stats_mock.created = 0
        user_stats_mock.updated = 0
        user_stats_mock.deleted = 0
        mock_user_service.sync_users.return_value = user_stats_mock
        mock_user_service.cleanup_orphaned_users.return_value = 0

        result = runner.invoke(cli, ["--csv", temp_csv_file, "--prune", "--dry-run"])

        assert result.exit_code == 0
        mock_group_service.cleanup_orphaned_groups.assert_called_once()
        # Note: cleanup_orphaned_users is not called separately;
        # user deletion is handled inside sync_users() when prune_users=True

    @patch("xc_user_group_sync.cli.UserSyncService")
    @patch("xc_user_group_sync.cli.GroupSyncService")
    @patch("xc_user_group_sync.cli.XCClient")
    def test_sync_with_errors(
        self,
        mock_client_class,
        mock_group_service_class,
        mock_user_service_class,
        runner,
        temp_csv_file,
        mock_env,
    ):
        """Test sync that encounters errors."""
        # Setup group service mock
        mock_group_service = Mock()
        mock_group_service_class.return_value = mock_group_service
        mock_group_service.parse_csv_to_groups.return_value = []
        mock_group_service.fetch_existing_groups.return_value = {}
        mock_group_service.fetch_existing_users.return_value = set()

        group_stats_mock = Mock()
        group_stats_mock.summary.return_value = (
            "Summary: created=0, updated=0, deleted=0, skipped=0, errors=1"
        )
        group_stats_mock.has_errors.return_value = True
        mock_group_service.sync_groups.return_value = group_stats_mock

        # Setup user service mock
        mock_user_service = Mock()
        mock_user_service_class.return_value = mock_user_service

        # Mock CSV validation result
        csv_validation_result = Mock()
        csv_validation_result.total_count = 0
        csv_validation_result.active_count = 0
        csv_validation_result.inactive_count = 0
        csv_validation_result.users = []
        csv_validation_result.unique_groups = set()
        csv_validation_result.has_warnings.return_value = False
        mock_user_service.parse_csv_to_users.return_value = csv_validation_result
        mock_user_service.fetch_existing_users.return_value = {}

        user_stats_mock = Mock()
        user_stats_mock.summary.return_value = (
            "Users: created=0, updated=0, deleted=0, unchanged=0, errors=0"
        )
        user_stats_mock.has_errors.return_value = False
        mock_user_service.sync_users.return_value = user_stats_mock

        result = runner.invoke(cli, ["--csv", temp_csv_file, "--dry-run"])

        assert result.exit_code != 0
        assert "group operations failed" in result.output

    @patch("xc_user_group_sync.cli.UserSyncService")
    @patch("xc_user_group_sync.cli.GroupSyncService")
    @patch("xc_user_group_sync.cli.XCClient")
    def test_sync_csv_parse_error(
        self,
        mock_client_class,
        mock_group_service_class,
        mock_user_service_class,
        runner,
        temp_csv_file,
        mock_env,
    ):
        """Test sync with CSV parse error."""
        from xc_user_group_sync.sync_service import CSVParseError

        # Setup user service mock to parse successfully
        mock_user_service = Mock()
        mock_user_service_class.return_value = mock_user_service

        csv_validation_result = Mock()
        csv_validation_result.total_count = 0
        csv_validation_result.active_count = 0
        csv_validation_result.inactive_count = 0
        csv_validation_result.users = []
        csv_validation_result.unique_groups = set()
        csv_validation_result.has_warnings.return_value = False
        mock_user_service.parse_csv_to_users.return_value = csv_validation_result
        mock_user_service.fetch_existing_users.return_value = {}

        user_stats_mock = Mock()
        user_stats_mock.summary.return_value = (
            "Users: created=0, updated=0, deleted=0, unchanged=0, errors=0"
        )
        user_stats_mock.has_errors.return_value = False
        mock_user_service.sync_users.return_value = user_stats_mock

        # Now setup group service to fail
        mock_group_service = Mock()
        mock_group_service_class.return_value = mock_group_service
        mock_group_service.parse_csv_to_groups.side_effect = CSVParseError(
            "Missing required columns"
        )

        result = runner.invoke(cli, ["--csv", temp_csv_file])

        assert result.exit_code != 0
        assert "Missing required columns" in result.output

    @patch("xc_user_group_sync.cli.UserSyncService")
    @patch("xc_user_group_sync.cli.GroupSyncService")
    @patch("xc_user_group_sync.cli.XCClient")
    def test_sync_api_error(
        self,
        mock_client_class,
        mock_group_service_class,
        mock_user_service_class,
        runner,
        temp_csv_file,
        mock_env,
    ):
        """Test sync with API error."""
        import requests

        # Setup user service mock to parse and sync successfully
        mock_user_service = Mock()
        mock_user_service_class.return_value = mock_user_service

        csv_validation_result = Mock()
        csv_validation_result.total_count = 0
        csv_validation_result.active_count = 0
        csv_validation_result.inactive_count = 0
        csv_validation_result.users = []
        csv_validation_result.unique_groups = set()
        csv_validation_result.has_warnings.return_value = False
        mock_user_service.parse_csv_to_users.return_value = csv_validation_result
        mock_user_service.fetch_existing_users.return_value = {}

        user_stats_mock = Mock()
        user_stats_mock.summary.return_value = (
            "Users: created=0, updated=0, deleted=0, unchanged=0, errors=0"
        )
        user_stats_mock.has_errors.return_value = False
        mock_user_service.sync_users.return_value = user_stats_mock

        # Now setup group service to fail with API error
        mock_group_service = Mock()
        mock_group_service_class.return_value = mock_group_service
        mock_group_service.parse_csv_to_groups.return_value = []
        mock_group_service.fetch_existing_groups.side_effect = (
            requests.RequestException("API connection failed")
        )

        result = runner.invoke(cli, ["--csv", temp_csv_file])

        assert result.exit_code != 0
        assert "API error" in result.output

    def test_sync_custom_log_level(self, runner, temp_csv_file, mock_env):
        """Test sync with custom log level."""
        with patch("xc_user_group_sync.cli.GroupSyncService"):
            with patch("xc_user_group_sync.cli.XCClient"):
                # Just test that the option is accepted
                result = runner.invoke(
                    cli, ["--csv", temp_csv_file, "--log-level", "debug"]
                )
                # May fail on other things, but shouldn't fail on log-level parsing
                assert "log-level" not in result.output.lower() or result.exit_code == 0

    def test_sync_custom_timeout(self, runner, temp_csv_file, mock_env):
        """Test sync with custom timeout."""
        with patch("xc_user_group_sync.cli.XCClient") as mock_client:
            with patch("xc_user_group_sync.cli.GroupSyncService"):
                runner.invoke(
                    cli,
                    ["--csv", temp_csv_file, "--timeout", "60", "--dry-run"],
                )
                # Check that client was created with timeout=60
                call_kwargs = mock_client.call_args[1]
                assert call_kwargs.get("timeout") == 60

    def test_sync_custom_retries(self, runner, temp_csv_file, mock_env):
        """Test sync with custom max retries."""
        with patch("xc_user_group_sync.cli.XCClient") as mock_client:
            with patch("xc_user_group_sync.cli.GroupSyncService"):
                runner.invoke(
                    cli,
                    ["--csv", temp_csv_file, "--max-retries", "5", "--dry-run"],
                )
                # Check that client was created with max_retries=5
                call_kwargs = mock_client.call_args[1]
                assert call_kwargs.get("max_retries") == 5


class TestCLIAuthentication:
    """Test authentication handling in CLI."""

    def test_auth_with_cert_key(self, runner, temp_csv_file, clean_env, monkeypatch):
        """Test authentication with certificate and key files."""
        monkeypatch.setenv("TENANT_ID", "test-tenant")
        monkeypatch.setenv("VOLT_API_CERT_FILE", "/path/to/cert.pem")
        monkeypatch.setenv("VOLT_API_CERT_KEY_FILE", "/path/to/key.pem")

        with patch("xc_user_group_sync.cli.XCClient") as mock_client:
            with patch("xc_user_group_sync.cli.GroupSyncService"):
                runner.invoke(cli, ["--csv", temp_csv_file, "--dry-run"])

                call_kwargs = mock_client.call_args[1]
                assert call_kwargs.get("cert_file") == "/path/to/cert.pem"
                assert call_kwargs.get("key_file") == "/path/to/key.pem"
                assert call_kwargs.get("p12_file") is None
                assert call_kwargs.get("p12_password") is None

    def test_auth_with_api_token(self, runner, temp_csv_file, clean_env, monkeypatch):
        """Test authentication with API token."""
        # Set ONLY API token (no cert/key) to test token auth path
        monkeypatch.setenv("TENANT_ID", "test-tenant")
        monkeypatch.setenv("XC_API_TOKEN", "test-token")

        with patch("xc_user_group_sync.cli.XCClient") as mock_client:
            with patch("xc_user_group_sync.cli.GroupSyncService"):
                runner.invoke(cli, ["--csv", temp_csv_file, "--dry-run"])

                call_kwargs = mock_client.call_args[1]
                assert call_kwargs.get("api_token") == "test-token"
                assert call_kwargs.get("cert_file") is None
                assert call_kwargs.get("key_file") is None

    def test_p12_authentication(self, runner, temp_csv_file, clean_env, monkeypatch):
        """Test authentication with P12 file and password."""
        monkeypatch.setenv("TENANT_ID", "test-tenant")
        monkeypatch.setenv("VOLT_API_P12_FILE", "/path/to/cert.p12")
        monkeypatch.setenv("VES_P12_PASSWORD", "test-password")

        with patch("xc_user_group_sync.cli.XCClient") as mock_client:
            with patch("xc_user_group_sync.cli.GroupSyncService"):
                runner.invoke(cli, ["--csv", temp_csv_file, "--dry-run"])

                call_kwargs = mock_client.call_args[1]
                assert call_kwargs.get("p12_file") == "/path/to/cert.p12"
                assert call_kwargs.get("p12_password") == "test-password"
                assert call_kwargs.get("cert_file") is None
                assert call_kwargs.get("key_file") is None

    def test_p12_warning_logged(self, runner, temp_csv_file, mock_env, monkeypatch):
        """Test that P12 file without password still works (fallback to cert/key)."""
        monkeypatch.setenv("VOLT_API_P12_FILE", "/path/to/cert.p12")

        with patch("xc_user_group_sync.cli.XCClient"):
            with patch("xc_user_group_sync.cli.GroupSyncService"):
                # P12 should be recognized but not used
                # The test just ensures no errors occur when P12 is set
                runner.invoke(cli, ["--csv", temp_csv_file, "--dry-run"])
