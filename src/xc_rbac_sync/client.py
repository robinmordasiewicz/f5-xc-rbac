from __future__ import annotations

import os
from typing import Any, Dict, Optional

import requests
from requests import Response
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type


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
    ) -> None:
        self.tenant_id = tenant_id
        self.base_url = f"https://{tenant_id}.console.ves.volterra.io"
        self.session = requests.Session()
        self.timeout = timeout

        if api_token:
            self.session.headers.update({"Authorization": f"APIToken {api_token}"})
        elif p12_file:
            # requests doesn't support .p12 directly; assume caller split to PEM before
            # Keeping branch for completeness if adapter is added later
            raise ValueError("requests does not support .p12; provide cert/key or split the p12")
        elif cert_file and key_file:
            self.session.cert = (cert_file, key_file)
        else:
            raise ValueError("No authentication provided (token or cert/key)")

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception_type((requests.RequestException,)),
    )
    def _request(self, method: str, path: str, **kwargs: Any) -> Response:
        url = f"{self.base_url}{path}"
        resp = self.session.request(method, url, timeout=self.timeout, **kwargs)
        if resp.status_code in (429, 500, 502, 503, 504):
            # Let tenacity retry
            raise requests.RequestException(f"Transient error: {resp.status_code}: {resp.text}")
        resp.raise_for_status()
        return resp

    # User Groups
    def list_groups(self, namespace: str = "system") -> Dict[str, Any]:
        r = self._request("GET", f"/api/web/namespaces/{namespace}/usergroups")
        return r.json()

    def create_group(self, group: Dict[str, Any], namespace: str = "system") -> Dict[str, Any]:
        r = self._request(
            "POST",
            f"/api/web/namespaces/{namespace}/usergroups",
            json=group,
        )
        return r.json()

    def update_group(self, name: str, group: Dict[str, Any], namespace: str = "system") -> Dict[str, Any]:
        r = self._request(
            "PUT",
            f"/api/web/namespaces/{namespace}/usergroups/{name}",
            json=group,
        )
        return r.json()

    def delete_group(self, name: str, namespace: str = "system") -> None:
        self._request("DELETE", f"/api/web/namespaces/{namespace}/usergroups/{name}")
