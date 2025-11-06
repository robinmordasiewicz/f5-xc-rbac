from click.testing import CliRunner

from xc_rbac_sync import cli
from xc_rbac_sync.client import XCClient


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
        cli.cli, ["sync", "--csv", "nonexistent.csv"], catch_exceptions=False
    )
    assert result.exit_code != 0


def test_cli_dry_run_happy_path(monkeypatch, tmp_path):
    # prepare a small CSV
    csv_file = tmp_path / "sample.csv"
    csv_file.write_text(
        "Email,Entitlement Display Name\n"
        'joe@example.com,"CN=admins,OU=Groups,DC=example,DC=com"\n'
    )

    # monkeypatch client creation to return a fake repository-like object
    class SimpleRepo:
        def list_groups(self, namespace: str = "system"):
            return {"items": []}

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
        cli.cli, ["sync", "--csv", str(csv_file), "--dry-run"], catch_exceptions=False
    )
    assert result.exit_code == 0
    assert "Groups planned from CSV: 1" in result.output


def test_cli_create_client_failure(monkeypatch, tmp_path):
    csv_file = tmp_path / "sample.csv"
    csv_file.write_text(
        "Email,Entitlement Display Name\n"
        'joe@example.com,"CN=admins,OU=Groups,DC=example,DC=com"\n'
    )
    monkeypatch.setenv("TENANT_ID", "tenant")
    monkeypatch.setenv("DOTENV_PATH", "/dev/null")
    monkeypatch.setattr(
        cli,
        "_create_client",
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    runner = CliRunner()
    result = runner.invoke(
        cli.cli, ["sync", "--csv", str(csv_file)], catch_exceptions=False
    )
    assert result.exit_code != 0
    assert "Failed to create client" in result.output


def test_cli_api_list_groups_failure(monkeypatch, tmp_path):
    csv_file = tmp_path / "sample.csv"
    csv_file.write_text(
        "Email,Entitlement Display Name\n"
        'joe@example.com,"CN=admins,OU=Groups,DC=example,DC=com"\n'
    )

    class BadRepo:
        def list_groups(self, namespace: str = "system"):
            import requests

            raise requests.RequestException("api down")

    monkeypatch.setenv("TENANT_ID", "tenant")
    monkeypatch.setenv("DOTENV_PATH", "/dev/null")
    monkeypatch.setattr(cli, "_create_client", lambda *args, **kwargs: BadRepo())
    runner = CliRunner()
    result = runner.invoke(
        cli.cli, ["sync", "--csv", str(csv_file)], catch_exceptions=False
    )
    assert result.exit_code != 0
    assert "API error listing groups" in result.output


def test_cli_sync_reports_errors(monkeypatch, tmp_path):
    csv_file = tmp_path / "sample.csv"
    csv_file.write_text(
        "Email,Entitlement Display Name\n"
        'joe@example.com,"CN=admins,OU=Groups,DC=example,DC=com"\n'
    )

    class Repo:
        def list_groups(self, namespace: str = "system"):
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
    from xc_rbac_sync.sync_service import SyncStats

    monkeypatch.setattr(
        "xc_rbac_sync.sync_service.GroupSyncService.sync_groups",
        lambda self, *a, **k: SyncStats(errors=1),
    )

    runner = CliRunner()
    result = runner.invoke(
        cli.cli, ["sync", "--csv", str(csv_file)], catch_exceptions=False
    )
    assert result.exit_code != 0
    assert "One or more operations failed" in result.output


def test_cli_cleanup_failure(monkeypatch, tmp_path):
    csv_file = tmp_path / "sample.csv"
    csv_file.write_text(
        "Email,Entitlement Display Name\n"
        'joe@example.com,"CN=admins,OU=Groups,DC=example,DC=com"\n'
    )

    class Repo:
        def list_groups(self, namespace: str = "system"):
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
        "xc_rbac_sync.sync_service.GroupSyncService.cleanup_orphaned_groups",
        lambda self, *a, **k: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    runner = CliRunner()
    result = runner.invoke(
        cli.cli, ["sync", "--csv", str(csv_file), "--cleanup"], catch_exceptions=False
    )
    assert result.exit_code != 0
    assert "Cleanup failed" in result.output


def test_xcclient_with_cert_sets_session_cert():
    c = XCClient("tenant", cert_file="/tmp/cert.pem", key_file="/tmp/key.pem")
    assert c.session.cert == ("/tmp/cert.pem", "/tmp/key.pem")


def test__create_client_with_cert_returns_client():
    client = cli._create_client("tenant", None, "/tmp/cert.pem", "/tmp/key.pem", 10, 2)
    assert hasattr(client, "session")
    assert client.session.cert == ("/tmp/cert.pem", "/tmp/key.pem")
