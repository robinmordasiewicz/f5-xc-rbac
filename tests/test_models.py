"""Tests for data models module."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from xc_rbac_sync.models import Config, Group


class TestGroup:
    """Test Group model validation."""

    def test_valid_group_minimal(self):
        """Test creating group with minimal valid data."""
        group = Group(name="admins")
        assert group.name == "admins"
        assert group.description is None
        assert group.users == []
        assert group.roles == []

    def test_valid_group_full(self):
        """Test creating group with all fields."""
        group = Group(
            name="admins",
            description="Administrator group",
            users=["admin@example.com", "root@example.com"],
            roles=["admin", "superuser"],
        )
        assert group.name == "admins"
        assert group.description == "Administrator group"
        assert group.users == ["admin@example.com", "root@example.com"]
        assert group.roles == ["admin", "superuser"]

    def test_valid_group_name_with_hyphen(self):
        """Test group name with hyphens."""
        group = Group(name="it-support")
        assert group.name == "it-support"

    def test_valid_group_name_with_underscore(self):
        """Test group name with underscores."""
        group = Group(name="team_alpha")
        assert group.name == "team_alpha"

    def test_valid_group_name_alphanumeric(self):
        """Test group name with numbers."""
        group = Group(name="group123")
        assert group.name == "group123"

    def test_valid_group_name_mixed(self):
        """Test group name with mixed valid characters."""
        group = Group(name="Team-Alpha_123")
        assert group.name == "Team-Alpha_123"

    def test_valid_group_name_min_length(self):
        """Test group name with minimum length (1 char)."""
        group = Group(name="a")
        assert group.name == "a"

    def test_valid_group_name_max_length(self):
        """Test group name with maximum length (128 chars)."""
        name = "a" * 128
        group = Group(name=name)
        assert group.name == name
        assert len(group.name) == 128

    def test_invalid_group_name_empty(self):
        """Test that empty group name is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            Group(name="")
        errors = exc_info.value.errors()
        assert any("name" in str(e["loc"]) for e in errors)

    def test_invalid_group_name_too_long(self):
        """Test that group name exceeding 128 chars is rejected."""
        name = "a" * 129
        with pytest.raises(ValidationError) as exc_info:
            Group(name=name)
        errors = exc_info.value.errors()
        assert any("name" in str(e["loc"]) for e in errors)

    def test_invalid_group_name_with_space(self):
        """Test that group name with spaces is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            Group(name="admin group")
        errors = exc_info.value.errors()
        assert any("name" in str(e["loc"]) for e in errors)

    def test_invalid_group_name_special_chars(self):
        """Test that group names with invalid special characters are rejected."""
        invalid_names = [
            "admin@domain",  # @ sign
            "team.prod",  # dot
            "dev/ops",  # slash
            "group$",  # dollar sign
            "team!",  # exclamation
            "group#1",  # hash
            "team*",  # asterisk
        ]
        for name in invalid_names:
            with pytest.raises(ValidationError) as exc_info:
                Group(name=name)
            errors = exc_info.value.errors()
            assert any("name" in str(e["loc"]) for e in errors)

    def test_group_users_default_empty_list(self):
        """Test that users defaults to empty list."""
        group = Group(name="test")
        assert group.users == []
        assert isinstance(group.users, list)

    def test_group_roles_default_empty_list(self):
        """Test that roles defaults to empty list."""
        group = Group(name="test")
        assert group.roles == []
        assert isinstance(group.roles, list)

    def test_group_with_multiple_users(self):
        """Test group with multiple users."""
        users = ["user1@example.com", "user2@example.com", "user3@example.com"]
        group = Group(name="test", users=users)
        assert group.users == users
        assert len(group.users) == 3

    def test_group_with_multiple_roles(self):
        """Test group with multiple roles."""
        roles = ["admin", "developer", "viewer"]
        group = Group(name="test", roles=roles)
        assert group.roles == roles
        assert len(group.roles) == 3

    def test_group_serialization(self):
        """Test group can be serialized to dict."""
        group = Group(
            name="admins",
            description="Admin group",
            users=["admin@example.com"],
            roles=["admin"],
        )
        data = group.model_dump()
        assert data["name"] == "admins"
        assert data["description"] == "Admin group"
        assert data["users"] == ["admin@example.com"]
        assert data["roles"] == ["admin"]

    def test_group_from_dict(self):
        """Test group can be created from dict."""
        data = {
            "name": "developers",
            "description": "Developer group",
            "users": ["dev@example.com"],
            "roles": ["developer"],
        }
        group = Group(**data)
        assert group.name == "developers"
        assert group.description == "Developer group"
        assert group.users == ["dev@example.com"]
        assert group.roles == ["developer"]


class TestConfig:
    """Test Config model validation."""

    def test_valid_config_minimal(self):
        """Test creating config with minimal required data."""
        config = Config(tenant_id="test-tenant")
        assert config.tenant_id == "test-tenant"
        assert config.volt_api_cert_file is None
        assert config.volt_api_cert_key_file is None
        assert config.xc_api_token is None

    def test_valid_config_with_cert_files(self):
        """Test config with certificate file paths."""
        config = Config(
            tenant_id="test-tenant",
            volt_api_cert_file="/path/to/cert.pem",
            volt_api_cert_key_file="/path/to/key.pem",
        )
        assert config.tenant_id == "test-tenant"
        assert config.volt_api_cert_file == "/path/to/cert.pem"
        assert config.volt_api_cert_key_file == "/path/to/key.pem"
        assert config.xc_api_token is None

    def test_valid_config_with_api_token(self):
        """Test config with API token."""
        config = Config(tenant_id="test-tenant", xc_api_token="secret-token-123")
        assert config.tenant_id == "test-tenant"
        assert config.xc_api_token == "secret-token-123"
        assert config.volt_api_cert_file is None
        assert config.volt_api_cert_key_file is None

    def test_valid_config_with_all_fields(self):
        """Test config with all authentication methods (though only one used)."""
        config = Config(
            tenant_id="test-tenant",
            volt_api_cert_file="/path/to/cert.pem",
            volt_api_cert_key_file="/path/to/key.pem",
            xc_api_token="secret-token-123",
        )
        assert config.tenant_id == "test-tenant"
        assert config.volt_api_cert_file == "/path/to/cert.pem"
        assert config.volt_api_cert_key_file == "/path/to/key.pem"
        assert config.xc_api_token == "secret-token-123"

    def test_invalid_config_missing_tenant_id(self):
        """Test that config requires tenant_id."""
        with pytest.raises(ValidationError) as exc_info:
            Config()
        errors = exc_info.value.errors()
        assert any("tenant_id" in str(e["loc"]) for e in errors)

    def test_config_serialization(self):
        """Test config can be serialized to dict."""
        config = Config(
            tenant_id="test-tenant",
            xc_api_token="secret-token",
            volt_api_cert_file="/cert.pem",
            volt_api_cert_key_file="/key.pem",
        )
        data = config.model_dump()
        assert data["tenant_id"] == "test-tenant"
        assert data["xc_api_token"] == "secret-token"
        assert data["volt_api_cert_file"] == "/cert.pem"
        assert data["volt_api_cert_key_file"] == "/key.pem"

    def test_config_from_dict(self):
        """Test config can be created from dict."""
        data = {
            "tenant_id": "test-tenant",
            "xc_api_token": "secret-token",
        }
        config = Config(**data)
        assert config.tenant_id == "test-tenant"
        assert config.xc_api_token == "secret-token"

    def test_config_optional_fields_none_by_default(self):
        """Test that optional authentication fields default to None."""
        config = Config(tenant_id="test-tenant")
        assert config.volt_api_cert_file is None
        assert config.volt_api_cert_key_file is None
        assert config.xc_api_token is None
