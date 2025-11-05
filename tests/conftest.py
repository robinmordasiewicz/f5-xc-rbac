"""Pytest configuration and shared fixtures."""

from __future__ import annotations

from typing import Any, Dict
from unittest.mock import Mock

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
