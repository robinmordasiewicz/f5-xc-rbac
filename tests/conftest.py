"""Pytest configuration and shared fixtures."""

from __future__ import annotations

from typing import Any, Dict
from unittest.mock import Mock, patch

import pytest
from requests import Response


@pytest.fixture
def mock_response():
    """Create a mock HTTP response."""

    def _make_response(
        status_code: int = 200, json_data: Dict[str, Any] | None = None
    ) -> Mock:
        response = Mock(spec=Response)
        response.status_code = status_code
        response.json.return_value = json_data or {}
        response.text = str(json_data)
        response.raise_for_status = Mock()
        return response

    return _make_response


@pytest.fixture
def sample_groups_response():
    """Sample API response for list_groups."""
    return {
        "items": [
            {
                "name": "admins",
                "display_name": "admins",
                "usernames": ["admin@example.com", "root@example.com"],
            },
            {
                "name": "developers",
                "display_name": "developers",
                "usernames": ["dev1@example.com", "dev2@example.com"],
            },
        ]
    }


@pytest.fixture
def sample_user_roles_response():
    """Sample API response for list_user_roles."""
    return {
        "items": [
            {"username": "admin@example.com", "email": "admin@example.com"},
            {"username": "root@example.com", "email": "root@example.com"},
            {"username": "dev1@example.com", "email": "dev1@example.com"},
            {"username": "dev2@example.com", "email": "dev2@example.com"},
        ]
    }


@pytest.fixture
def sample_csv_content():
    """Sample CSV content for testing."""
    return """Email,Entitlement Display Name
admin@example.com,"CN=admins,OU=Groups,DC=example,DC=com"
root@example.com,"CN=admins,OU=Groups,DC=example,DC=com"
dev1@example.com,"CN=developers,OU=Groups,DC=example,DC=com"
dev2@example.com,"CN=developers,OU=Groups,DC=example,DC=com"
"""


@pytest.fixture
def temp_csv_file(tmp_path, sample_csv_content):
    """Create a temporary CSV file for testing."""
    csv_file = tmp_path / "test.csv"
    csv_file.write_text(sample_csv_content)
    return str(csv_file)


@pytest.fixture
def sample_user_csv_content():
    """Sample user CSV content for testing."""
    return """Email,User Display Name,Employee Status,Entitlement Display Name
alice@example.com,Alice Anderson,A,"CN=ADMINS,OU=Groups,DC=example,DC=com"
bob@example.com,Bob Builder,A,"CN=DEVELOPERS,OU=Groups,DC=example,DC=com"
charlie@example.com,Charlie Chen,I,"CN=VIEWERS,OU=Groups,DC=example,DC=com"
"""


@pytest.fixture
def sample_users_response():
    """Sample API response for list_users."""
    return {
        "items": [
            {
                "email": "alice@example.com",
                "username": "alice@example.com",
                "display_name": "Alice Anderson",
                "first_name": "Alice",
                "last_name": "Anderson",
                "active": True,
                "groups": ["ADMINS"],
            },
            {
                "email": "bob@example.com",
                "username": "bob@example.com",
                "display_name": "Bob Builder",
                "first_name": "Bob",
                "last_name": "Builder",
                "active": True,
                "groups": ["DEVELOPERS"],
            },
        ]
    }


@pytest.fixture
def clean_env(monkeypatch):
    """Clean environment fixture that removes credential environment variables.

    This ensures tests don't accidentally use real credentials from secrets/.env
    and provides a clean slate for setting up test-specific environment variables.

    Usage:
        def test_something(clean_env, monkeypatch):
            monkeypatch.setenv("TENANT_ID", "test-tenant")
            # Test with clean environment
    """
    # List of all credential and configuration environment variables
    env_vars_to_clear = [
        "TENANT_ID",
        "XC_API_TOKEN",
        "XC_API_URL",
        "VOLT_API_P12_FILE",
        "VES_P12_PASSWORD",
        "VOLT_API_CERT_FILE",
        "VOLT_API_CERT_KEY_FILE",
        "DOTENV_PATH",
    ]

    # Clear all credential environment variables
    for var in env_vars_to_clear:
        monkeypatch.delenv(var, raising=False)

    # Mock load_dotenv to prevent loading from any .env files
    with patch("xc_rbac_sync.cli.load_dotenv"):
        yield
