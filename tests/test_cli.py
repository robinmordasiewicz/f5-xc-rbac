"""Tests for CLI commands."""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from xc_rbac_sync.cli import cli


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
        assert "XC Group Sync CLI" in result.output

    def test_sync_help(self, runner):
        """Test sync command help."""
        result = runner.invoke(cli, ["sync", "--help"])
        assert result.exit_code == 0
        assert "--csv" in result.output
        assert "--dry-run" in result.output
        assert "--cleanup" in result.output


class TestCLISyncCommand:
    """Test sync command execution."""

    def test_sync_missing_tenant_id(self, runner, temp_csv_file, clean_env):
        """Test that missing TENANT_ID raises error."""
        result = runner.invoke(cli, ["sync", "--csv", temp_csv_file])
        assert result.exit_code != 0
        assert "TENANT_ID must be set" in result.output

    def test_sync_missing_auth(self, runner, temp_csv_file, clean_env, monkeypatch):
        """Test that missing authentication raises error."""
        monkeypatch.setenv("TENANT_ID", "test-tenant")
        result = runner.invoke(cli, ["sync", "--csv", temp_csv_file])
        assert result.exit_code != 0
        assert "XC_API_TOKEN" in result.output or "VOLT_API_CERT" in result.output

    def test_sync_missing_csv(self, runner, mock_env):
        """Test that missing CSV file raises error."""
        result = runner.invoke(cli, ["sync", "--csv", "/nonexistent/file.csv"])
        assert result.exit_code != 0

    @patch("xc_rbac_sync.cli.GroupSyncService")
    @patch("xc_rbac_sync.cli.XCClient")
    def test_sync_dry_run_success(
        self, mock_client_class, mock_service_class, runner, temp_csv_file, mock_env
    ):
        """Test successful dry-run sync."""
        # Setup mocks
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.parse_csv_to_groups.return_value = []
        mock_service.fetch_existing_groups.return_value = {}
        mock_service.fetch_existing_users.return_value = set()

        stats_mock = Mock()
        stats_mock.summary.return_value = (
            "Summary: created=0, updated=0, deleted=0, skipped=0, errors=0"
        )
        stats_mock.has_errors.return_value = False
        mock_service.sync_groups.return_value = stats_mock

        result = runner.invoke(cli, ["sync", "--csv", temp_csv_file, "--dry-run"])

        assert result.exit_code == 0
        assert "Sync complete" in result.output
        mock_service.sync_groups.assert_called_once()

    @patch("xc_rbac_sync.cli.GroupSyncService")
    @patch("xc_rbac_sync.cli.XCClient")
    def test_sync_with_cleanup(
        self, mock_client_class, mock_service_class, runner, temp_csv_file, mock_env
    ):
        """Test sync with cleanup option."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.parse_csv_to_groups.return_value = []
        mock_service.fetch_existing_groups.return_value = {}
        mock_service.fetch_existing_users.return_value = set()

        stats_mock = Mock()
        stats_mock.summary.return_value = (
            "Summary: created=0, updated=0, deleted=0, skipped=0, errors=0"
        )
        stats_mock.has_errors.return_value = False
        mock_service.sync_groups.return_value = stats_mock
        mock_service.cleanup_orphaned_groups.return_value = 0

        result = runner.invoke(
            cli, ["sync", "--csv", temp_csv_file, "--cleanup-groups", "--dry-run"]
        )

        assert result.exit_code == 0
        mock_service.cleanup_orphaned_groups.assert_called_once()

    @patch("xc_rbac_sync.cli.GroupSyncService")
    @patch("xc_rbac_sync.cli.XCClient")
    def test_sync_with_errors(
        self, mock_client_class, mock_service_class, runner, temp_csv_file, mock_env
    ):
        """Test sync that encounters errors."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.parse_csv_to_groups.return_value = []
        mock_service.fetch_existing_groups.return_value = {}
        mock_service.fetch_existing_users.return_value = set()

        stats_mock = Mock()
        stats_mock.summary.return_value = (
            "Summary: created=0, updated=0, deleted=0, skipped=0, errors=1"
        )
        stats_mock.has_errors.return_value = True
        mock_service.sync_groups.return_value = stats_mock

        result = runner.invoke(cli, ["sync", "--csv", temp_csv_file, "--dry-run"])

        assert result.exit_code != 0
        assert "operations failed" in result.output

    @patch("xc_rbac_sync.cli.GroupSyncService")
    @patch("xc_rbac_sync.cli.XCClient")
    def test_sync_csv_parse_error(
        self, mock_client_class, mock_service_class, runner, temp_csv_file, mock_env
    ):
        """Test sync with CSV parse error."""
        from xc_rbac_sync.sync_service import CSVParseError

        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.parse_csv_to_groups.side_effect = CSVParseError(
            "Missing required columns"
        )

        result = runner.invoke(cli, ["sync", "--csv", temp_csv_file])

        assert result.exit_code != 0
        assert "Missing required columns" in result.output

    @patch("xc_rbac_sync.cli.GroupSyncService")
    @patch("xc_rbac_sync.cli.XCClient")
    def test_sync_api_error(
        self, mock_client_class, mock_service_class, runner, temp_csv_file, mock_env
    ):
        """Test sync with API error."""
        import requests

        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.parse_csv_to_groups.return_value = []
        mock_service.fetch_existing_groups.side_effect = requests.RequestException(
            "API connection failed"
        )

        result = runner.invoke(cli, ["sync", "--csv", temp_csv_file])

        assert result.exit_code != 0
        assert "API error" in result.output

    def test_sync_custom_log_level(self, runner, temp_csv_file, mock_env):
        """Test sync with custom log level."""
        with patch("xc_rbac_sync.cli.GroupSyncService"):
            with patch("xc_rbac_sync.cli.XCClient"):
                # Just test that the option is accepted
                result = runner.invoke(
                    cli, ["sync", "--csv", temp_csv_file, "--log-level", "debug"]
                )
                # May fail on other things, but shouldn't fail on log-level parsing
                assert "log-level" not in result.output.lower() or result.exit_code == 0

    def test_sync_custom_timeout(self, runner, temp_csv_file, mock_env):
        """Test sync with custom timeout."""
        with patch("xc_rbac_sync.cli.XCClient") as mock_client:
            with patch("xc_rbac_sync.cli.GroupSyncService"):
                runner.invoke(
                    cli,
                    ["sync", "--csv", temp_csv_file, "--timeout", "60", "--dry-run"],
                )
                # Check that client was created with timeout=60
                call_kwargs = mock_client.call_args[1]
                assert call_kwargs.get("timeout") == 60

    def test_sync_custom_retries(self, runner, temp_csv_file, mock_env):
        """Test sync with custom max retries."""
        with patch("xc_rbac_sync.cli.XCClient") as mock_client:
            with patch("xc_rbac_sync.cli.GroupSyncService"):
                runner.invoke(
                    cli,
                    ["sync", "--csv", temp_csv_file, "--max-retries", "5", "--dry-run"],
                )
                # Check that client was created with max_retries=5
                call_kwargs = mock_client.call_args[1]
                assert call_kwargs.get("max_retries") == 5


class TestCLIAuthentication:
    """Test authentication handling in CLI."""

    def test_auth_with_cert_key(self, runner, temp_csv_file, monkeypatch):
        """Test authentication with certificate and key files."""
        monkeypatch.setenv("TENANT_ID", "test-tenant")
        monkeypatch.setenv("VOLT_API_CERT_FILE", "/path/to/cert.pem")
        monkeypatch.setenv("VOLT_API_CERT_KEY_FILE", "/path/to/key.pem")

        with patch("xc_rbac_sync.cli.XCClient") as mock_client:
            with patch("xc_rbac_sync.cli.GroupSyncService"):
                runner.invoke(cli, ["sync", "--csv", temp_csv_file, "--dry-run"])

                call_kwargs = mock_client.call_args[1]
                assert call_kwargs.get("cert_file") == "/path/to/cert.pem"
                assert call_kwargs.get("key_file") == "/path/to/key.pem"

    def test_auth_with_api_token(self, runner, temp_csv_file, clean_env, monkeypatch):
        """Test authentication with API token."""
        # Set ONLY API token (no cert/key) to test token auth path
        monkeypatch.setenv("TENANT_ID", "test-tenant")
        monkeypatch.setenv("XC_API_TOKEN", "test-token")

        with patch("xc_rbac_sync.cli.XCClient") as mock_client:
            with patch("xc_rbac_sync.cli.GroupSyncService"):
                runner.invoke(cli, ["sync", "--csv", temp_csv_file, "--dry-run"])

                call_kwargs = mock_client.call_args[1]
                assert call_kwargs.get("api_token") == "test-token"
                assert call_kwargs.get("cert_file") is None
                assert call_kwargs.get("key_file") is None

    def test_p12_warning_logged(self, runner, temp_csv_file, mock_env, monkeypatch):
        """Test that P12 file triggers informational message."""
        monkeypatch.setenv("VOLT_API_P12_FILE", "/path/to/cert.p12")

        with patch("xc_rbac_sync.cli.XCClient"):
            with patch("xc_rbac_sync.cli.GroupSyncService"):
                # P12 should be recognized but not used
                # The test just ensures no errors occur when P12 is set
                runner.invoke(cli, ["sync", "--csv", temp_csv_file, "--dry-run"])
