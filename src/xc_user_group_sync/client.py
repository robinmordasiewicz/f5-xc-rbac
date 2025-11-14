"""F5 XC API client with automatic retry logic.

Provides a REST API client for F5 Distributed Cloud with built-in
retry logic for transient errors, support for multiple authentication
methods, and exponential backoff.
"""

from __future__ import annotations

import atexit
import logging
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

import requests
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from requests import Response
from tenacity import (
    Retrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)


class XCClient:
    """F5 Distributed Cloud API client with automatic retry logic.

    Provides REST API interface for F5 XC with built-in retry logic
    for transient errors, exponential backoff, and support for both
    token-based and certificate-based authentication.
    """

    def __init__(
        self,
        tenant_id: str,
        api_token: Optional[str] = None,
        cert_file: Optional[str] = None,
        key_file: Optional[str] = None,
        p12_file: Optional[str] = None,
        p12_password: Optional[str] = None,
        api_url: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        backoff_multiplier: float = 1.0,
        backoff_min: float = 1.0,
        backoff_max: float = 8.0,
    ) -> None:
        """Initialize the F5 XC API client.

        Args:
            tenant_id: F5 XC tenant identifier
            api_token: API token for authentication
            cert_file: Path to API certificate file (requires key_file)
            key_file: Path to API key file (requires cert_file)
            p12_file: Path to P12/PKCS12 certificate archive (requires p12_password)
            p12_password: Password for P12 file (required with p12_file)
            api_url: Optional API base URL (defaults to production endpoint)
            timeout: HTTP request timeout in seconds
            max_retries: Maximum number of retry attempts for failed requests
            backoff_multiplier: Exponential backoff multiplier
            backoff_min: Minimum backoff time in seconds
            backoff_max: Maximum backoff time in seconds

        Raises:
            ValueError: If no authentication method provided or invalid combination

        """
        self.tenant_id = tenant_id
        self.base_url = api_url or f"https://{tenant_id}.console.ves.volterra.io"
        self.session = requests.Session()
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_multiplier = backoff_multiplier
        self.backoff_min = backoff_min
        self.backoff_max = backoff_max

        # Store temp file paths for cleanup
        self._temp_cert_file: Optional[Path] = None
        self._temp_key_file: Optional[Path] = None

        if api_token:
            self.session.headers.update({"Authorization": f"APIToken {api_token}"})
        elif p12_file and p12_password:
            self._setup_p12_auth(p12_file, p12_password)
        elif cert_file and key_file:
            self.session.cert = (cert_file, key_file)
        else:
            raise ValueError(
                "No authentication provided (token, cert/key, or p12/password)"
            )

    def _setup_p12_auth(self, p12_file: str, p12_password: str) -> None:
        """Extract cert and key from P12 and configure session.

        Creates temporary PEM files from P12 archive and registers cleanup.

        Args:
            p12_file: Path to P12/PKCS12 file
            p12_password: Password for P12 file

        Raises:
            ValueError: If P12 file cannot be loaded or parsed
        """
        try:
            from cryptography.hazmat.primitives.serialization import pkcs12

            # Load P12 file
            with open(p12_file, "rb") as f:
                p12_data = f.read()

            # Extract private key and certificate
            private_key, certificate, _ = pkcs12.load_key_and_certificates(
                p12_data,
                p12_password.encode(),
                backend=default_backend(),
            )

            if not private_key or not certificate:
                raise ValueError("P12 file does not contain valid certificate and key")

            # Create temporary files in system temp directory
            cert_fd, cert_path = tempfile.mkstemp(suffix=".pem", prefix="xc_cert_")
            key_fd, key_path = tempfile.mkstemp(suffix=".pem", prefix="xc_key_")

            self._temp_cert_file = Path(cert_path)
            self._temp_key_file = Path(key_path)

            try:
                # Write certificate to temp file
                with open(cert_fd, "wb") as cert_file:
                    cert_file.write(
                        certificate.public_bytes(serialization.Encoding.PEM)
                    )

                # Write private key to temp file
                with open(key_fd, "wb") as key_file:
                    key_file.write(
                        private_key.private_bytes(
                            encoding=serialization.Encoding.PEM,
                            format=serialization.PrivateFormat.PKCS8,
                            encryption_algorithm=serialization.NoEncryption(),
                        )
                    )

                # Configure requests session with temp files
                self.session.cert = (
                    str(self._temp_cert_file),
                    str(self._temp_key_file),
                )

                # Register cleanup on exit
                atexit.register(self._cleanup_temp_files)

                logger.debug(
                    f"Extracted P12 to temporary cert/key files: "
                    f"{self._temp_cert_file}, {self._temp_key_file}"
                )

            except Exception:
                # If writing fails, clean up immediately
                self._cleanup_temp_files()
                raise

        except Exception as e:
            raise ValueError(f"Failed to load P12 file: {e}") from e

    def _cleanup_temp_files(self) -> None:
        """Clean up temporary certificate and key files."""
        if self._temp_cert_file and self._temp_cert_file.exists():
            try:
                self._temp_cert_file.unlink()
                logger.debug(f"Deleted temporary cert file: {self._temp_cert_file}")
            except Exception as e:
                logger.warning(f"Failed to delete temp cert file: {e}")

        if self._temp_key_file and self._temp_key_file.exists():
            try:
                self._temp_key_file.unlink()
                logger.debug(f"Deleted temporary key file: {self._temp_key_file}")
            except Exception as e:
                logger.warning(f"Failed to delete temp key file: {e}")

    def __del__(self) -> None:
        """Cleanup temp files when object is garbage collected."""
        self._cleanup_temp_files()

    def _request(self, method: str, path: str, **kwargs: Any) -> Response:
        url = f"{self.base_url}{path}"
        # Use per-instance retry configuration
        for attempt in Retrying(
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential(
                multiplier=self.backoff_multiplier,
                min=self.backoff_min,
                max=self.backoff_max,
            ),
            retry=retry_if_exception_type((requests.RequestException,)),
            reraise=True,
        ):
            with attempt:
                resp = self.session.request(method, url, timeout=self.timeout, **kwargs)
                if resp.status_code in (429, 500, 502, 503, 504):
                    # Trigger retry by raising a retriable exception
                    raise requests.RequestException(
                        f"Transient error: {resp.status_code}: {resp.text}"
                    )
                resp.raise_for_status()
                return resp

    # User Groups (custom API)
    def list_groups(self, namespace: str = "system") -> Dict[str, Any]:
        """List all user groups in the specified namespace.

        Args:
            namespace: XC namespace (default: "system")

        Returns:
            Dictionary containing list of groups with their metadata

        """
        r = self._request("GET", f"/api/web/custom/namespaces/{namespace}/user_groups")
        return r.json()

    def create_group(
        self, group: Dict[str, Any], namespace: str = "system"
    ) -> Dict[str, Any]:
        """Create a new user group.

        Args:
            group: Group specification with name, display_name, and usernames
            namespace: XC namespace (default: "system")

        Returns:
            Dictionary containing created group metadata

        """
        r = self._request(
            "POST",
            f"/api/web/custom/namespaces/{namespace}/user_groups",
            json=group,
        )
        return r.json()

    def update_group(
        self, name: str, group: Dict[str, Any], namespace: str = "system"
    ) -> Dict[str, Any]:
        """Update an existing user group.

        Args:
            name: Name of the group to update
            group: Updated group specification
            namespace: XC namespace (default: "system")

        Returns:
            Dictionary containing updated group metadata

        """
        r = self._request(
            "PUT",
            f"/api/web/custom/namespaces/{namespace}/user_groups/{name}",
            json=group,
        )
        return r.json()

    def delete_group(self, name: str, namespace: str = "system") -> None:
        """Delete a user group.

        Args:
            name: Name of the group to delete
            namespace: XC namespace (default: "system")

        """
        self._request(
            "DELETE", f"/api/web/custom/namespaces/{namespace}/user_groups/{name}"
        )

    # Users / Roles (for pre-validation)
    def list_user_roles(self, namespace: str = "system") -> Dict[str, Any]:
        """List all user roles for validation purposes.

        Args:
            namespace: XC namespace (default: "system")

        Returns:
            Dictionary containing list of users with their roles

        """
        r = self._request("GET", f"/api/web/custom/namespaces/{namespace}/user_roles")
        return r.json()

    def create_user(
        self, user: Dict[str, Any], namespace: str = "system"
    ) -> Dict[str, Any]:
        """Create a new user/role entry for validation or provisioning.

        Args:
            user: User data dictionary (e.g., email, username, display_name)
            namespace: XC namespace (default: "system")

        Returns:
            Dictionary containing created user metadata

        """
        r = self._request(
            "POST",
            f"/api/web/custom/namespaces/{namespace}/user_roles",
            json=user,
        )
        return r.json()

    def list_users(self, namespace: str = "system") -> Dict[str, Any]:
        """Alias for list_user_roles for consistency with protocol.

        Args:
            namespace: XC namespace (default: "system")

        Returns:
            Dictionary containing list of users with their roles

        """
        return self.list_user_roles(namespace)

    def get_user(self, email: str, namespace: str = "system") -> Dict[str, Any]:
        """Get a single user by email from F5 XC.

        Args:
            email: User email address (primary identifier)
            namespace: XC namespace (default: "system")

        Returns:
            Dictionary containing user data

        Raises:
            requests.HTTPError: On API failures (including 404 if not found)

        """
        r = self._request(
            "GET",
            f"/api/web/custom/namespaces/{namespace}/user_roles/{email}",
        )
        return r.json()

    def update_user(
        self, email: str, user: Dict[str, Any], namespace: str = "system"
    ) -> Dict[str, Any]:
        """Update an existing user in F5 XC.

        Args:
            email: User email address (primary identifier)
            user: Updated user data dictionary
            namespace: XC namespace (default: "system")

        Returns:
            Dictionary containing updated user metadata

        Raises:
            requests.HTTPError: On API failures

        """
        r = self._request(
            "PUT",
            f"/api/web/custom/namespaces/{namespace}/user_roles/{email}",
            json=user,
        )
        return r.json()

    def delete_user(self, email: str, namespace: str = "system") -> None:
        """Delete a user from F5 XC.

        Args:
            email: User email address (primary identifier)
            namespace: XC namespace (default: "system")

        Raises:
            requests.HTTPError: On API failures

        """
        self._request(
            "DELETE",
            f"/api/web/custom/namespaces/{namespace}/user_roles/{email}",
        )
