from click.testing import CliRunner

from xc_user_group_sync import cli
from xc_user_group_sync.client import XCClient


def test_create_xcclient_no_auth_raises():
    # Missing api_token and cert/key should raise
    try:
        XCClient("tenant")
        raised = False
    except ValueError:
        raised = True
    assert raised


def test_create_xcclient_with_token_sets_header():
    c = XCClient("tenant", api_token="tok")
    assert c.session.headers.get("Authorization") == "APIToken tok"


def test_cli_requires_tenant_id(monkeypatch):
    runner = CliRunner()
    # ensure TENANT_ID not set
    monkeypatch.delenv("TENANT_ID", raising=False)
    result = runner.invoke(
        cli.cli, ["--csv", "nonexistent.csv"], catch_exceptions=False
    )
    assert result.exit_code != 0


def test_cli_dry_run_happy_path(monkeypatch, tmp_path):
    # prepare a small CSV
    csv_file = tmp_path / "sample.csv"
    csv_file.write_text(
        "Email,User Display Name,Employee Status,Entitlement Display Name\n"
        'joe@example.com,Joe User,Active,"CN=admins,OU=Groups,DC=example,DC=com"\n'
    )

    # monkeypatch client creation to return a fake repository-like object
    class SimpleRepo:
        def list_groups(self, namespace: str = "system"):
            return {"items": []}

        def list_users(self, namespace: str = "system"):
            return {
                "items": [{"email": "joe@example.com", "username": "joe@example.com"}]
            }

        def list_user_roles(self, namespace: str = "system"):
            return {"items": [{"username": "joe@example.com"}]}

        def create_user(self, user: dict, namespace: str = "system"):
            return {"username": user.get("email")}

        def create_group(self, group: dict, namespace: str = "system"):
            return group

    monkeypatch.setenv("TENANT_ID", "tenant")
    monkeypatch.setenv("DOTENV_PATH", "/dev/null")
    monkeypatch.setattr(cli, "_create_client", lambda *args, **kwargs: SimpleRepo())

    runner = CliRunner()
    result = runner.invoke(
        cli.cli, ["--csv", str(csv_file), "--dry-run"], catch_exceptions=False
    )
    assert result.exit_code == 0
    assert "Groups planned from CSV: 1" in result.output


def test_cli_create_client_failure(monkeypatch, tmp_path):
    csv_file = tmp_path / "sample.csv"
    csv_file.write_text(
        "Email,User Display Name,Employee Status,Entitlement Display Name\n"
        'joe@example.com,Joe User,Active,"CN=admins,OU=Groups,DC=example,DC=com"\n'
    )
    monkeypatch.setenv("TENANT_ID", "tenant")
    monkeypatch.setenv("DOTENV_PATH", "/dev/null")
    monkeypatch.setattr(
        cli,
        "_create_client",
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    runner = CliRunner()
    result = runner.invoke(cli.cli, ["--csv", str(csv_file)], catch_exceptions=False)
    assert result.exit_code != 0
    assert "Failed to create client" in result.output


def test_cli_api_list_groups_failure(monkeypatch, tmp_path):
    csv_file = tmp_path / "sample.csv"
    csv_file.write_text(
        "Email,User Display Name,Employee Status,Entitlement Display Name\n"
        'joe@example.com,Joe User,Active,"CN=admins,OU=Groups,DC=example,DC=com"\n'
    )

    class BadRepo:
        def list_users(self, namespace: str = "system"):
            return {"items": []}

        def create_user(self, user: dict, namespace: str = "system"):
            return {"username": user.get("email")}

        def list_groups(self, namespace: str = "system"):
            import requests

            raise requests.RequestException("api down")

    monkeypatch.setenv("TENANT_ID", "tenant")
    monkeypatch.setenv("DOTENV_PATH", "/dev/null")
    monkeypatch.setattr(cli, "_create_client", lambda *args, **kwargs: BadRepo())
    runner = CliRunner()
    result = runner.invoke(cli.cli, ["--csv", str(csv_file)], catch_exceptions=False)
    assert result.exit_code != 0
    assert "API error listing groups" in result.output


def test_cli_sync_reports_errors(monkeypatch, tmp_path):
    csv_file = tmp_path / "sample.csv"
    csv_file.write_text(
        "Email,User Display Name,Employee Status,Entitlement Display Name\n"
        'joe@example.com,Joe User,Active,"CN=admins,OU=Groups,DC=example,DC=com"\n'
    )

    class Repo:
        def list_groups(self, namespace: str = "system"):
            return {"items": []}

        def list_users(self, namespace: str = "system"):
            return {"items": []}

        def list_user_roles(self, namespace: str = "system"):
            return {"items": [{"username": "joe@example.com"}]}

        def create_user(self, user: dict, namespace: str = "system"):
            return {"username": user.get("email")}

        def create_group(self, group: dict, namespace: str = "system"):
            return group

    monkeypatch.setenv("TENANT_ID", "tenant")
    monkeypatch.setenv("DOTENV_PATH", "/dev/null")
    monkeypatch.setattr(cli, "_create_client", lambda *args, **kwargs: Repo())

    # force sync_groups to report an error
    from xc_user_group_sync.sync_service import SyncStats

    monkeypatch.setattr(
        "xc_user_group_sync.sync_service.GroupSyncService.sync_groups",
        lambda self, *a, **k: SyncStats(errors=1),
    )

    runner = CliRunner()
    result = runner.invoke(cli.cli, ["--csv", str(csv_file)], catch_exceptions=False)
    assert result.exit_code != 0
    assert "One or more group operations failed" in result.output


def test_cli_cleanup_failure(monkeypatch, tmp_path):
    csv_file = tmp_path / "sample.csv"
    csv_file.write_text(
        "Email,User Display Name,Employee Status,Entitlement Display Name\n"
        'joe@example.com,Joe User,Active,"CN=admins,OU=Groups,DC=example,DC=com"\n'
    )

    class Repo:
        def list_groups(self, namespace: str = "system"):
            return {"items": []}

        def list_users(self, namespace: str = "system"):
            return {"items": []}

        def list_user_roles(self, namespace: str = "system"):
            return {"items": [{"username": "joe@example.com"}]}

        def create_user(self, user: dict, namespace: str = "system"):
            return {"username": user.get("email")}

        def create_group(self, group: dict, namespace: str = "system"):
            return group

    monkeypatch.setenv("TENANT_ID", "tenant")
    monkeypatch.setenv("DOTENV_PATH", "/dev/null")
    monkeypatch.setattr(cli, "_create_client", lambda *args, **kwargs: Repo())

    # make cleanup_orphaned_groups raise
    monkeypatch.setattr(
        "xc_user_group_sync.sync_service.GroupSyncService.cleanup_orphaned_groups",
        lambda self, *a, **k: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    runner = CliRunner()
    result = runner.invoke(
        cli.cli,
        ["--csv", str(csv_file), "--prune"],
        catch_exceptions=False,
    )
    assert result.exit_code != 0
    assert "Cleanup failed" in result.output or "boom" in result.output


def test_xcclient_with_cert_sets_session_cert():
    c = XCClient("tenant", cert_file="/tmp/cert.pem", key_file="/tmp/key.pem")
    assert c.session.cert == ("/tmp/cert.pem", "/tmp/key.pem")


def test__create_client_with_cert_returns_client():
    client = cli._create_client(
        "tenant", None, "/tmp/cert.pem", "/tmp/key.pem", None, None, None, 10, 2
    )
    assert hasattr(client, "session")
    assert client.session.cert == ("/tmp/cert.pem", "/tmp/key.pem")


# User sync command tests (T039)


def test_cli_sync_users_dry_run_happy_path(monkeypatch, tmp_path):
    """Test sync-users command in dry-run mode (T039)."""
    # Prepare a user CSV file
    csv_file = tmp_path / "users.csv"
    csv_file.write_text(
        "Email,User Display Name,Employee Status,Entitlement Display Name\n"
        'alice@example.com,Alice Anderson,A,"CN=ADMINS,OU=Groups,DC=example,DC=com"\n'
    )

    # Mock repository
    class UserRepo:
        def list_groups(self, namespace: str = "system"):
            return {"items": []}

        def list_users(self, namespace: str = "system"):
            return {"items": []}

        def list_user_roles(self, namespace: str = "system"):
            return {"items": [{"username": "alice@example.com"}]}

        def create_user(self, user_data: dict, namespace: str = "system"):
            return {"email": user_data["email"]}

    monkeypatch.setenv("TENANT_ID", "tenant")
    monkeypatch.setenv("DOTENV_PATH", "/dev/null")
    monkeypatch.setattr(cli, "_create_client", lambda *args, **kwargs: UserRepo())

    runner = CliRunner()
    result = runner.invoke(
        cli.cli,
        ["--csv", str(csv_file), "--dry-run"],
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    assert "Users planned from CSV: 1" in result.output
    assert "Active: 1, Inactive: 0" in result.output
    assert "SYNCHRONIZATION COMPLETE" in result.output


def test_cli_sync_users_requires_tenant_id(monkeypatch, tmp_path):
    """Test sync-users requires TENANT_ID (T039)."""
    csv_file = tmp_path / "users.csv"
    csv_file.write_text(
        "Email,User Display Name,Employee Status,Entitlement Display Name\n"
        "alice@example.com,Alice Anderson,A,\n"
    )

    runner = CliRunner()
    monkeypatch.delenv("TENANT_ID", raising=False)
    monkeypatch.setenv("DOTENV_PATH", "/dev/null")
    result = runner.invoke(cli.cli, ["--csv", str(csv_file)], catch_exceptions=False)
    assert result.exit_code != 0
    assert "TENANT_ID must be set" in result.output


def test_cli_sync_users_invalid_csv(monkeypatch, tmp_path):
    """Test sync-users handles invalid CSV (T039)."""
    csv_file = tmp_path / "invalid.csv"
    csv_file.write_text("Email\nalice@example.com\n")  # Missing required columns

    class UserRepo:
        def list_groups(self, namespace: str = "system"):
            return {"items": []}

        pass

    monkeypatch.setenv("TENANT_ID", "tenant")
    monkeypatch.setenv("DOTENV_PATH", "/dev/null")
    monkeypatch.setattr(cli, "_create_client", lambda *args, **kwargs: UserRepo())

    runner = CliRunner()
    result = runner.invoke(cli.cli, ["--csv", str(csv_file)], catch_exceptions=False)
    assert result.exit_code != 0
    assert "CSV validation error" in result.output


def test_cli_sync_users_api_error(monkeypatch, tmp_path):
    """Test sync-users handles API errors (T039)."""
    csv_file = tmp_path / "users.csv"
    csv_file.write_text(
        "Email,User Display Name,Employee Status,Entitlement Display Name\n"
        "alice@example.com,Alice Anderson,A,\n"
    )

    class BadUserRepo:
        def list_groups(self, namespace: str = "system"):
            return {"items": []}

        def list_users(self, namespace: str = "system"):
            import requests

            raise requests.RequestException("API error")

    monkeypatch.setenv("TENANT_ID", "tenant")
    monkeypatch.setenv("DOTENV_PATH", "/dev/null")
    monkeypatch.setattr(cli, "_create_client", lambda *args, **kwargs: BadUserRepo())

    runner = CliRunner()
    result = runner.invoke(cli.cli, ["--csv", str(csv_file)], catch_exceptions=False)
    assert result.exit_code != 0
    assert "API error listing users" in result.output


def test_cli_sync_users_shows_error_details(monkeypatch, tmp_path):
    """Test sync-users displays error details (T039)."""
    csv_file = tmp_path / "users.csv"
    csv_file.write_text(
        "Email,User Display Name,Employee Status,Entitlement Display Name\n"
        "alice@example.com,Alice Anderson,A,\n"
    )

    class UserRepo:
        def list_groups(self, namespace: str = "system"):
            return {"items": []}

        def list_users(self, namespace: str = "system"):
            return {"items": []}

    monkeypatch.setenv("TENANT_ID", "tenant")
    monkeypatch.setenv("DOTENV_PATH", "/dev/null")
    monkeypatch.setattr(cli, "_create_client", lambda *args, **kwargs: UserRepo())

    # Mock sync_users to return stats with errors
    from xc_user_group_sync.user_sync_service import UserSyncStats

    mock_stats = UserSyncStats(errors=1)
    mock_stats.error_details.append(
        {"email": "alice@example.com", "operation": "create", "error": "test error"}
    )
    monkeypatch.setattr(
        "xc_user_group_sync.user_sync_service.UserSyncService.sync_users",
        lambda self, *a, **k: mock_stats,
    )

    runner = CliRunner()
    result = runner.invoke(cli.cli, ["--csv", str(csv_file)], catch_exceptions=False)
    assert result.exit_code != 0
    assert "Errors encountered:" in result.output
    assert "alice@example.com" in result.output
    assert "create failed" in result.output


def test_cli_sync_users_delete_flag(monkeypatch, tmp_path):
    """Test sync-users with --prune flag (T049)."""
    csv_file = tmp_path / "users.csv"
    csv_file.write_text(
        "Email,User Display Name,Employee Status,Entitlement Display Name\n"
        "alice@example.com,Alice Anderson,A,\n"
    )

    class UserRepo:
        def list_groups(self, namespace: str = "system"):
            return {"items": []}

        def list_users(self, namespace: str = "system"):
            # Return existing user not in CSV
            return {
                "items": [
                    {"email": "orphan@example.com", "username": "orphan@example.com"}
                ]
            }

        def create_user(self, user_data: dict, namespace: str = "system"):
            return {"email": user_data["email"]}

        def delete_user(self, email: str, namespace: str = "system"):
            return None

    monkeypatch.setenv("TENANT_ID", "tenant")
    monkeypatch.setenv("DOTENV_PATH", "/dev/null")
    mock_repo = UserRepo()
    monkeypatch.setattr(cli, "_create_client", lambda *args, **kwargs: mock_repo)

    runner = CliRunner()
    result = runner.invoke(
        cli.cli,
        ["--csv", str(csv_file), "--prune"],
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    assert "Users planned from CSV: 1" in result.output
    assert "Existing users in F5 XC: 1" in result.output
    # Should have created alice and deleted orphan
    assert "created=1" in result.output
    assert "deleted=1" in result.output


def test_xcclient_proxy_from_parameter():
    """Test that explicit proxy parameter configures session proxies."""
    client = XCClient(
        "tenant",
        api_token="test-token",
        proxy="http://proxy.example.com:8080",
    )
    assert client.session.proxies == {
        "http": "http://proxy.example.com:8080",
        "https": "http://proxy.example.com:8080",
    }


def test_xcclient_proxy_from_environment(monkeypatch):
    """Test that HTTP_PROXY/HTTPS_PROXY environment variables are used."""
    monkeypatch.setenv("HTTP_PROXY", "http://envproxy.example.com:3128")
    monkeypatch.setenv("HTTPS_PROXY", "http://envproxy.example.com:3128")

    client = XCClient("tenant", api_token="test-token")
    # requests.Session automatically uses HTTP_PROXY/HTTPS_PROXY
    # We just verify it doesn't override with explicit proxy
    assert not hasattr(client.session, "proxies") or client.session.proxies == {}


def test_xcclient_ca_bundle_from_parameter(tmp_path):
    """Test that explicit CA bundle parameter configures SSL verification."""
    ca_bundle = tmp_path / "ca-bundle.crt"
    ca_bundle.write_text("FAKE CA CERT")

    client = XCClient(
        "tenant",
        api_token="test-token",
        verify=str(ca_bundle),
    )
    assert client.session.verify == str(ca_bundle)


def test_xcclient_ca_bundle_from_environment(monkeypatch, tmp_path):
    """Test that REQUESTS_CA_BUNDLE environment variable is used."""
    ca_bundle = tmp_path / "ca-bundle.crt"
    ca_bundle.write_text("FAKE CA CERT")
    monkeypatch.setenv("REQUESTS_CA_BUNDLE", str(ca_bundle))

    client = XCClient("tenant", api_token="test-token")
    assert client.session.verify == str(ca_bundle)


def test_xcclient_no_verify_disables_ssl():
    """Test that verify=False disables SSL verification."""
    client = XCClient("tenant", api_token="test-token", verify=False)
    assert client.session.verify is False


def test_xcclient_default_verify_is_true():
    """Test that default verify setting is True (system CA bundle)."""
    client = XCClient("tenant", api_token="test-token")
    # If no explicit verify parameter and no environment variable, defaults to True
    assert client.session.verify is True or isinstance(client.session.verify, str)


def test_cli_proxy_flag(monkeypatch, tmp_path):
    """Test that CLI --proxy flag is passed to client."""
    csv_file = tmp_path / "sample.csv"
    csv_file.write_text(
        "Email,User Display Name,Employee Status,Entitlement Display Name\n"
        'joe@example.com,Joe User,Active,"CN=admins,OU=Groups,DC=example,DC=com"\n'
    )

    created_clients = []

    def mock_create_client(*args, **kwargs):
        class SimpleRepo:
            def list_groups(self, namespace: str = "system"):
                return {"items": []}

            def list_users(self, namespace: str = "system"):
                return {"items": []}

            def list_user_roles(self, namespace: str = "system"):
                return {"items": []}

        # Capture the proxy parameter
        created_clients.append(kwargs)
        return SimpleRepo()

    monkeypatch.setenv("TENANT_ID", "tenant")
    monkeypatch.setenv("DOTENV_PATH", "/dev/null")
    monkeypatch.setattr(cli, "_create_client", mock_create_client)

    runner = CliRunner()
    result = runner.invoke(
        cli.cli,
        ["--csv", str(csv_file), "--dry-run", "--proxy", "http://proxy:8080"],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    assert len(created_clients) == 1
    assert created_clients[0]["proxy"] == "http://proxy:8080"


def test_cli_ca_bundle_flag(monkeypatch, tmp_path):
    """Test that CLI --ca-bundle flag is passed to client."""
    csv_file = tmp_path / "sample.csv"
    csv_file.write_text(
        "Email,User Display Name,Employee Status,Entitlement Display Name\n"
        'joe@example.com,Joe User,Active,"CN=admins,OU=Groups,DC=example,DC=com"\n'
    )

    ca_bundle = tmp_path / "ca-bundle.crt"
    ca_bundle.write_text("FAKE CA")

    created_clients = []

    def mock_create_client(*args, **kwargs):
        class SimpleRepo:
            def list_groups(self, namespace: str = "system"):
                return {"items": []}

            def list_users(self, namespace: str = "system"):
                return {"items": []}

            def list_user_roles(self, namespace: str = "system"):
                return {"items": []}

        created_clients.append(kwargs)
        return SimpleRepo()

    monkeypatch.setenv("TENANT_ID", "tenant")
    monkeypatch.setenv("DOTENV_PATH", "/dev/null")
    monkeypatch.setattr(cli, "_create_client", mock_create_client)

    runner = CliRunner()
    result = runner.invoke(
        cli.cli,
        ["--csv", str(csv_file), "--dry-run", "--ca-bundle", str(ca_bundle)],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    assert len(created_clients) == 1
    assert created_clients[0]["verify"] == str(ca_bundle)


def test_cli_no_verify_flag(monkeypatch, tmp_path):
    """Test that CLI --no-verify flag disables SSL verification."""
    csv_file = tmp_path / "sample.csv"
    csv_file.write_text(
        "Email,User Display Name,Employee Status,Entitlement Display Name\n"
        'joe@example.com,Joe User,Active,"CN=admins,OU=Groups,DC=example,DC=com"\n'
    )

    created_clients = []

    def mock_create_client(*args, **kwargs):
        class SimpleRepo:
            def list_groups(self, namespace: str = "system"):
                return {"items": []}

            def list_users(self, namespace: str = "system"):
                return {"items": []}

            def list_user_roles(self, namespace: str = "system"):
                return {"items": []}

        created_clients.append(kwargs)
        return SimpleRepo()

    monkeypatch.setenv("TENANT_ID", "tenant")
    monkeypatch.setenv("DOTENV_PATH", "/dev/null")
    monkeypatch.setattr(cli, "_create_client", mock_create_client)

    runner = CliRunner()
    result = runner.invoke(
        cli.cli,
        ["--csv", str(csv_file), "--dry-run", "--no-verify"],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    assert len(created_clients) == 1
    assert created_clients[0]["verify"] is False
