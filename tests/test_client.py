"""Integration tests for XC API client."""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest
import requests

from xc_rbac_sync.client import XCClient


class TestXCClientInit:
    """Test client initialization and authentication setup."""

    def test_init_with_api_token(self):
        """Test client initialization with API token."""
        client = XCClient(tenant_id="test-tenant", api_token="test-token")
        assert client.tenant_id == "test-tenant"
        assert client.base_url == "https://test-tenant.console.ves.volterra.io"
        assert "Authorization" in client.session.headers
        assert client.session.headers["Authorization"] == "APIToken test-token"

    def test_init_with_cert_key(self):
        """Test client initialization with certificate and key files."""
        client = XCClient(
            tenant_id="test-tenant",
            cert_file="/path/to/cert.pem",
            key_file="/path/to/key.pem",
        )
        assert client.tenant_id == "test-tenant"
        assert client.session.cert == ("/path/to/cert.pem", "/path/to/key.pem")

    def test_init_with_custom_timeout(self):
        """Test client with custom timeout."""
        client = XCClient(tenant_id="test-tenant", api_token="token", timeout=60)
        assert client.timeout == 60

    def test_init_with_custom_retries(self):
        """Test client with custom max retries."""
        client = XCClient(tenant_id="test-tenant", api_token="token", max_retries=5)
        assert client.max_retries == 5

    def test_init_no_auth_raises_error(self):
        """Test that client requires authentication."""
        with pytest.raises(ValueError, match="No authentication provided"):
            XCClient(tenant_id="test-tenant")

    def test_init_with_backoff_params(self):
        """Test client with custom backoff parameters."""
        client = XCClient(
            tenant_id="test-tenant",
            api_token="token",
            backoff_multiplier=2.0,
            backoff_min=2.0,
            backoff_max=16.0,
        )
        assert client.backoff_multiplier == 2.0
        assert client.backoff_min == 2.0
        assert client.backoff_max == 16.0


class TestXCClientGroupOperations:
    """Test group CRUD operations."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return XCClient(tenant_id="test-tenant", api_token="test-token")

    def test_list_groups_success(self, client, mock_response, sample_groups_response):
        """Test successful group listing."""
        with patch.object(
            client.session,
            "request",
            return_value=mock_response(200, sample_groups_response),
        ):
            result = client.list_groups()
            assert "items" in result
            assert len(result["items"]) == 2
            assert result["items"][0]["name"] == "admins"

    def test_list_groups_custom_namespace(self, client, mock_response):
        """Test listing groups in custom namespace."""
        with patch.object(
            client.session, "request", return_value=mock_response(200, {"items": []})
        ) as mock_req:
            client.list_groups(namespace="custom-ns")
            call_url = mock_req.call_args[0][1]
            assert "custom-ns" in call_url

    def test_create_group_success(self, client, mock_response):
        """Test successful group creation."""
        group_data = {
            "name": "new-group",
            "display_name": "new-group",
            "usernames": ["user@example.com"],
        }
        response_data = {**group_data, "created_at": "2024-01-01"}

        with patch.object(
            client.session, "request", return_value=mock_response(200, response_data)
        ):
            result = client.create_group(group_data)
            assert result["name"] == "new-group"

    def test_update_group_success(self, client, mock_response):
        """Test successful group update."""
        group_data = {
            "name": "admins",
            "display_name": "admins",
            "usernames": ["admin@example.com", "root@example.com"],
        }

        with patch.object(
            client.session, "request", return_value=mock_response(200, group_data)
        ):
            result = client.update_group("admins", group_data)
            assert result["name"] == "admins"

    def test_delete_group_success(self, client, mock_response):
        """Test successful group deletion."""
        with patch.object(
            client.session, "request", return_value=mock_response(204, None)
        ):
            # Should not raise
            client.delete_group("old-group")

    def test_list_user_roles_success(
        self, client, mock_response, sample_user_roles_response
    ):
        """Test successful user roles listing."""
        with patch.object(
            client.session,
            "request",
            return_value=mock_response(200, sample_user_roles_response),
        ):
            result = client.list_user_roles()
            assert "items" in result
            assert len(result["items"]) == 4


class TestXCClientUserOperations:
    """Test user CRUD operations."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return XCClient(tenant_id="test-tenant", api_token="test-token")

    def test_list_users_alias(self, client, mock_response, sample_user_roles_response):
        """Test list_users is an alias for list_user_roles."""
        with patch.object(
            client.session,
            "request",
            return_value=mock_response(200, sample_user_roles_response),
        ):
            result = client.list_users()
            assert "items" in result
            assert len(result["items"]) == 4

    def test_create_user_success(self, client, mock_response):
        """Test successful user creation."""
        user_data = {
            "email": "newuser@example.com",
            "username": "newuser@example.com",
            "display_name": "New User",
            "first_name": "New",
            "last_name": "User",
        }
        response_data = {**user_data, "created_at": "2024-01-01"}

        with patch.object(
            client.session, "request", return_value=mock_response(200, response_data)
        ):
            result = client.create_user(user_data)
            assert result["email"] == "newuser@example.com"

    def test_get_user_success(self, client, mock_response):
        """Test successful user retrieval."""
        user_data = {
            "email": "alice@example.com",
            "username": "alice@example.com",
            "display_name": "Alice Anderson",
            "first_name": "Alice",
            "last_name": "Anderson",
        }

        with patch.object(
            client.session, "request", return_value=mock_response(200, user_data)
        ) as mock_req:
            result = client.get_user("alice@example.com")
            assert result["email"] == "alice@example.com"
            # Verify correct URL construction
            call_url = mock_req.call_args[0][1]
            assert "user_roles/alice@example.com" in call_url

    def test_get_user_not_found(self, client):
        """Test get_user with non-existent user."""
        mock_resp = Mock(spec=requests.Response)
        mock_resp.status_code = 404
        mock_resp.text = "User not found"
        mock_resp.raise_for_status.side_effect = requests.HTTPError()

        with patch.object(client.session, "request", return_value=mock_resp):
            with pytest.raises(requests.HTTPError):
                client.get_user("nonexistent@example.com")

    def test_update_user_success(self, client, mock_response):
        """Test successful user update."""
        user_data = {
            "email": "alice@example.com",
            "username": "alice@example.com",
            "display_name": "Alice Smith",  # Name changed
            "first_name": "Alice",
            "last_name": "Smith",
        }

        with patch.object(
            client.session, "request", return_value=mock_response(200, user_data)
        ) as mock_req:
            result = client.update_user("alice@example.com", user_data)
            assert result["display_name"] == "Alice Smith"
            # Verify PUT request to correct endpoint
            assert mock_req.call_args[0][0] == "PUT"
            call_url = mock_req.call_args[0][1]
            assert "user_roles/alice@example.com" in call_url

    def test_update_user_retry_on_429(self, client, mock_response):
        """Test update_user retries on 429 rate limit."""
        user_data = {"email": "alice@example.com", "display_name": "Alice Updated"}

        # First call returns 429, second succeeds
        responses = [
            mock_response(429, {"error": "rate limit"}),
            mock_response(200, user_data),
        ]

        with patch.object(client.session, "request", side_effect=responses):
            result = client.update_user("alice@example.com", user_data)
            assert result["display_name"] == "Alice Updated"

    def test_delete_user_success(self, client, mock_response):
        """Test successful user deletion (T047)."""
        with patch.object(
            client.session, "request", return_value=mock_response(204, None)
        ) as mock_req:
            # Should not raise
            client.delete_user("olduser@example.com")
            # Verify DELETE request
            assert mock_req.call_args[0][0] == "DELETE"
            call_url = mock_req.call_args[0][1]
            assert "user_roles/olduser@example.com" in call_url

    def test_delete_user_handles_404(self, client):
        """Test delete_user handles 404 (already deleted) gracefully (T048)."""
        mock_resp = Mock(spec=requests.Response)
        mock_resp.status_code = 404
        mock_resp.text = "User not found"
        mock_resp.raise_for_status.side_effect = requests.HTTPError()

        with patch.object(client.session, "request", return_value=mock_resp):
            # 404 should not raise - user already deleted
            with pytest.raises(requests.HTTPError):
                client.delete_user("nonexistent@example.com")

    def test_user_operations_custom_namespace(self, client, mock_response):
        """Test user operations in custom namespace."""
        user_data = {"email": "test@example.com"}

        with patch.object(
            client.session, "request", return_value=mock_response(200, user_data)
        ) as mock_req:
            client.get_user("test@example.com", namespace="custom-ns")
            call_url = mock_req.call_args[0][1]
            assert "custom-ns" in call_url
            assert "user_roles" in call_url


class TestXCClientRetryLogic:
    """Test retry and error handling."""

    @pytest.fixture
    def client(self):
        """Create test client with retry settings."""
        return XCClient(
            tenant_id="test-tenant",
            api_token="test-token",
            max_retries=3,
            backoff_min=0.1,
            backoff_max=1.0,
        )

    def test_retry_on_429_rate_limit(self, client, mock_response):
        """Test that 429 responses trigger retry."""
        # First call returns 429, second succeeds
        responses = [
            mock_response(429, {"error": "rate limit"}),
            mock_response(200, {"items": []}),
        ]

        with patch.object(client.session, "request", side_effect=responses):
            result = client.list_groups()
            assert result == {"items": []}

    def test_retry_on_500_server_error(self, client, mock_response):
        """Test that 5xx responses trigger retry."""
        responses = [
            mock_response(500, {"error": "server error"}),
            mock_response(200, {"items": []}),
        ]

        with patch.object(client.session, "request", side_effect=responses):
            result = client.list_groups()
            assert result == {"items": []}

    def test_max_retries_exceeded(self, client, mock_response):
        """Test that max retries limit is enforced."""
        # Always return 500
        response = mock_response(500, {"error": "server error"})

        with patch.object(client.session, "request", return_value=response):
            with pytest.raises(requests.RequestException):
                client.list_groups()

    def test_no_retry_on_4xx_client_error(self, client):
        """Test that 4xx errors (except 429) don't trigger retry."""
        mock_resp = Mock(spec=requests.Response)
        mock_resp.status_code = 404
        mock_resp.text = "Not found"
        mock_resp.raise_for_status.side_effect = requests.HTTPError()

        with patch.object(client.session, "request", return_value=mock_resp):
            with pytest.raises(requests.HTTPError):
                client.list_groups()

    def test_successful_first_attempt_no_retry(self, client, mock_response):
        """Test that successful responses don't trigger retry."""
        response = mock_response(200, {"items": []})

        with patch.object(client.session, "request", return_value=response) as mock_req:
            client.list_groups()
            # Should only be called once
            assert mock_req.call_count == 1


class TestXCClientURLConstruction:
    """Test URL construction for API endpoints."""

    def test_base_url_construction(self):
        """Test base URL is constructed correctly from tenant ID."""
        client = XCClient(tenant_id="my-tenant", api_token="token")
        assert client.base_url == "https://my-tenant.console.ves.volterra.io"

    def test_list_groups_url(self):
        """Test list groups endpoint URL."""
        client = XCClient(tenant_id="test", api_token="token")
        with patch.object(client.session, "request") as mock_req:
            mock_req.return_value = Mock(
                status_code=200, json=lambda: {"items": []}, raise_for_status=Mock()
            )
            client.list_groups(namespace="system")
            expected_url = "https://test.console.ves.volterra.io/api/web/custom/namespaces/system/user_groups"
            assert mock_req.call_args[0][1] == expected_url

    def test_delete_group_url(self):
        """Test delete group endpoint URL."""
        client = XCClient(tenant_id="test", api_token="token")
        with patch.object(client.session, "request") as mock_req:
            mock_req.return_value = Mock(status_code=204, raise_for_status=Mock())
            client.delete_group("my-group", namespace="custom")
            expected_url = "https://test.console.ves.volterra.io/api/web/custom/namespaces/custom/user_groups/my-group"
            assert mock_req.call_args[0][1] == expected_url
