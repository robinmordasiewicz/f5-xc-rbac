from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, constr


GroupName = constr(regex=r"^[A-Za-z0-9_-]+$", min_length=1, max_length=128)


class Group(BaseModel):
    name: GroupName
    description: Optional[str] = None
    users: List[str] = Field(default_factory=list)
    roles: List[str] = Field(default_factory=list)


class Config(BaseModel):
    tenant_id: str
    volt_api_p12_file: Optional[str] = None
    ves_p12_password: Optional[str] = None
    volt_api_cert_file: Optional[str] = None
    volt_api_cert_key_file: Optional[str] = None
    xc_api_token: Optional[str] = None
