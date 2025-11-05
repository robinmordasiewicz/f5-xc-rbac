from __future__ import annotations

from typing import Any, Dict, Optional

import requests
from requests import Response
from tenacity import (
    Retrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)


class XCClient:
    def __init__(
        self,
        tenant_id: str,
        api_token: Optional[str] = None,
        p12_file: Optional[str] = None,
        p12_password: Optional[str] = None,
        cert_file: Optional[str] = None,
        key_file: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        backoff_multiplier: float = 1.0,
        backoff_min: float = 1.0,
        backoff_max: float = 8.0,
    ) -> None:
        self.tenant_id = tenant_id
        self.base_url = f"https://{tenant_id}.console.ves.volterra.io"
        self.session = requests.Session()
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_multiplier = backoff_multiplier
        self.backoff_min = backoff_min
        self.backoff_max = backoff_max

        if api_token:
            self.session.headers.update({"Authorization": f"APIToken {api_token}"})
        elif p12_file:
            # requests doesn't support .p12 directly; assume caller split to PEM before
            # Keeping branch for completeness if adapter is added later
            raise ValueError(
                "requests does not support .p12; provide cert/key or split the p12"
            )
        elif cert_file and key_file:
            self.session.cert = (cert_file, key_file)
        else:
            raise ValueError("No authentication provided (token or cert/key)")

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
        r = self._request("GET", f"/api/web/custom/namespaces/{namespace}/user_groups")
        return r.json()

    def create_group(
        self, group: Dict[str, Any], namespace: str = "system"
    ) -> Dict[str, Any]:
        r = self._request(
            "POST",
            f"/api/web/custom/namespaces/{namespace}/user_groups",
            json=group,
        )
        return r.json()

    def update_group(
        self, name: str, group: Dict[str, Any], namespace: str = "system"
    ) -> Dict[str, Any]:
        r = self._request(
            "PUT",
            f"/api/web/custom/namespaces/{namespace}/user_groups/{name}",
            json=group,
        )
        return r.json()

    def delete_group(self, name: str, namespace: str = "system") -> None:
        self._request(
            "DELETE", f"/api/web/custom/namespaces/{namespace}/user_groups/{name}"
        )

    # Users / Roles (for pre-validation)
    def list_user_roles(self, namespace: str = "system") -> Dict[str, Any]:
        r = self._request("GET", f"/api/web/custom/namespaces/{namespace}/user_roles")
        return r.json()
