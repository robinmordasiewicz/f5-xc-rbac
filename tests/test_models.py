"""Tests for data models module."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from xc_user_group_sync.models import Config, Group, User


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


class TestUser:
    """Test User model validation."""

    def test_valid_user_minimal(self):
        """Test creating user with minimal valid data."""
        user = User(
            email="alice@example.com",
            display_name="Alice Anderson",
            first_name="Alice",
            last_name="Anderson",
        )
        assert user.email == "alice@example.com"
        assert user.username == "alice@example.com"  # Defaults to email
        assert user.display_name == "Alice Anderson"
        assert user.first_name == "Alice"
        assert user.last_name == "Anderson"
        assert user.active is True  # Default
        assert user.groups == []  # Default

    def test_valid_user_full(self):
        """Test creating user with all fields."""
        user = User(
            email="bob@example.com",
            username="bob@example.com",
            display_name="Bob Smith",
            first_name="Bob",
            last_name="Smith",
            active=False,
            groups=["EADMIN_STD", "DEVELOPERS"],
        )
        assert user.email == "bob@example.com"
        assert user.username == "bob@example.com"
        assert user.display_name == "Bob Smith"
        assert user.first_name == "Bob"
        assert user.last_name == "Smith"
        assert user.active is False
        assert user.groups == ["EADMIN_STD", "DEVELOPERS"]

    def test_user_email_validation_valid(self):
        """Test EmailStr validation accepts valid email."""
        user = User(
            email="test@example.com",
            display_name="Test User",
            first_name="Test",
            last_name="User",
        )
        assert user.email == "test@example.com"

    def test_user_email_validation_invalid(self):
        """Test EmailStr validation rejects invalid email."""
        with pytest.raises(ValidationError) as exc_info:
            User(
                email="invalid-email",
                display_name="Test User",
                first_name="Test",
                last_name="User",
            )
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("email",) for error in errors)

    def test_user_username_defaults_to_email(self):
        """Test username defaults to email if not provided."""
        user = User(
            email="charlie@example.com",
            display_name="Charlie Jones",
            first_name="Charlie",
            last_name="Jones",
        )
        assert user.username == "charlie@example.com"

    def test_user_username_explicit(self):
        """Test username can be set explicitly."""
        user = User(
            email="dave@example.com",
            username="custom_username",
            display_name="Dave Wilson",
            first_name="Dave",
            last_name="Wilson",
        )
        assert user.username == "custom_username"

    def test_user_active_default_true(self):
        """Test active defaults to True."""
        user = User(
            email="eve@example.com",
            display_name="Eve Adams",
            first_name="Eve",
            last_name="Adams",
        )
        assert user.active is True

    def test_user_groups_default_empty(self):
        """Test groups defaults to empty list."""
        user = User(
            email="frank@example.com",
            display_name="Frank Brown",
            first_name="Frank",
            last_name="Brown",
        )
        assert user.groups == []

    def test_user_single_name(self):
        """Test user with single name (empty last_name)."""
        user = User(
            email="madonna@example.com",
            display_name="Madonna",
            first_name="Madonna",
            last_name="",
        )
        assert user.first_name == "Madonna"
        assert user.last_name == ""

    def test_user_multiple_groups(self):
        """Test user with multiple groups."""
        user = User(
            email="grace@example.com",
            display_name="Grace Lee",
            first_name="Grace",
            last_name="Lee",
            groups=["GROUP1", "GROUP2", "GROUP3"],
        )
        assert len(user.groups) == 3
        assert "GROUP1" in user.groups
        assert "GROUP2" in user.groups
        assert "GROUP3" in user.groups
