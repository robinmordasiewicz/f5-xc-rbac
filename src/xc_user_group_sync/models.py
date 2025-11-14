"""Data models for F5 XC group synchronization.

Defines Pydantic models for validating group and configuration data
with proper type constraints and validation rules.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, StringConstraints
from typing_extensions import Annotated

GroupName = Annotated[
    str, StringConstraints(pattern=r"^[A-Za-z0-9_-]+$", min_length=1, max_length=128)
]


class User(BaseModel):
    """User data model for F5 XC synchronization.

    Attributes:
        email: User's email address (unique identifier, primary key)
        username: Username for F5 XC (typically same as email)
        display_name: Full name as shown in UI (from CSV "User Display Name")
        first_name: Given name (parsed from display_name)
        last_name: Family name (parsed from display_name)
        active: Whether user can access system (from CSV "Employee Status")
        groups: List of group names user belongs to (for coordination with group sync)

    """

    email: EmailStr
    username: str = Field(default="")
    display_name: str
    first_name: str
    last_name: str
    active: bool = True
    groups: List[str] = Field(default_factory=list)

    def model_post_init(self, __context) -> None:
        """Set username to email if not provided."""
        if not self.username:
            self.username = str(self.email)


class Group(BaseModel):
    """Represents an F5 XC user group with members and roles.

    Attributes:
        name: DNS-1035 compliant group name used in API calls
            (lowercase alphanumeric or hyphen, starts with letter)
        original_name: Original group name from CSV/LDAP before normalization
        description: Optional human-readable description
        users: List of user email addresses belonging to the group
        roles: List of role names assigned to the group

    """

    name: str  # DNS-1035 compliant normalized name
    original_name: Optional[str] = None  # Original name from source
    description: Optional[str] = None
    users: List[str] = Field(default_factory=list)
    roles: List[str] = Field(default_factory=list)


class Config(BaseModel):
    """Configuration for F5 XC authentication and connection.

    Attributes:
        tenant_id: F5 XC tenant identifier
        volt_api_cert_file: Optional path to API certificate file (for cert-based auth)
        volt_api_cert_key_file: Optional path to API key file (for cert-based auth)
        volt_api_p12_file: Optional path to P12/PKCS12 certificate archive
        ves_p12_password: Optional password for P12 file
        xc_api_token: Optional API token (for token-based auth)

    """

    tenant_id: str
    volt_api_cert_file: Optional[str] = None
    volt_api_cert_key_file: Optional[str] = None
    volt_api_p12_file: Optional[str] = None
    ves_p12_password: Optional[str] = None
    xc_api_token: Optional[str] = None
