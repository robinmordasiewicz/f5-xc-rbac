"""LDAP distinguished name (DN) parsing utilities.

Provides functions for extracting and validating Common Name (CN)
components from LDAP DNs with F5 XC group name constraints.
"""

from __future__ import annotations

import re
from typing import Optional

from ldap3.utils.dn import parse_dn

# F5 XC group name constraints (from model):
# - allowed: letters, digits, underscore, hyphen
# - length: 1..128
GROUP_NAME_RE = re.compile(r"^[A-Za-z0-9_-]{1,128}$")

# DNS-1035 label requirements for F5 XC API:
# - lowercase alphanumeric or hyphen only
# - must start with a letter
# - must end with alphanumeric (or single letter is ok)
# - max 63 characters (DNS subdomain limit)
DNS_1035_RE = re.compile(r"^[a-z]([a-z0-9-]*[a-z0-9])?$")


class LdapParseError(ValueError):
    """Exception raised when LDAP DN parsing fails or validation errors occur."""

    pass


def normalize_group_name_dns1035(name: str) -> str:
    """Normalize a group name to DNS-1035 compliance for F5 XC API.

    Transforms group names to meet F5 XC's DNS-1035 label requirements:
    - Converts to lowercase
    - Replaces underscores with hyphens
    - Ensures it starts with a letter
    - Ensures it ends with alphanumeric
    - Truncates to 63 characters if needed

    Args:
        name: Original group name (e.g., "EADMIN_STD")

    Returns:
        DNS-1035 compliant name (e.g., "eadmin-std")

    Raises:
        LdapParseError: If name cannot be normalized to valid DNS-1035 format
    """
    if not name:
        raise LdapParseError("Group name cannot be empty")

    # Convert to lowercase and replace underscores with hyphens
    normalized = name.lower().replace("_", "-")

    # Ensure starts with a letter
    if not normalized[0].isalpha():
        raise LdapParseError(
            f"Group name '{name}' must start with a letter after normalization"
        )

    # Remove trailing non-alphanumeric characters
    while normalized and not normalized[-1].isalnum():
        normalized = normalized[:-1]

    if not normalized:
        raise LdapParseError(
            f"Group name '{name}' has no valid characters after normalization"
        )

    # Truncate to DNS-1035 limit
    if len(normalized) > 63:
        normalized = normalized[:63]
        # Ensure still ends with alphanumeric after truncation
        while normalized and not normalized[-1].isalnum():
            normalized = normalized[:-1]

    # Final validation
    if not DNS_1035_RE.fullmatch(normalized):
        raise LdapParseError(
            f"Group name '{name}' could not be normalized to "
            f"DNS-1035 format: '{normalized}'"
        )

    return normalized


def extract_cn(dn: str) -> str:
    """Extract CN from an LDAP DN using ldap3's parser.

    Raises LdapParseError if CN missing or invalid.
    """
    try:
        rdn_seq = parse_dn(dn)
    except Exception as exc:  # ldap3 throws on malformed DN
        raise LdapParseError(f"Malformed DN: {dn}") from exc

    # rdn_seq is a list of (attr, value, separator) tuples
    cn: Optional[str] = None
    for attr, value, _ in rdn_seq:
        if attr.upper() == "CN":
            cn = value
            break

    if not cn:
        raise LdapParseError(f"CN not found in DN: {dn}")

    if not GROUP_NAME_RE.fullmatch(cn):
        raise LdapParseError(
            "Invalid group name extracted from CN; must match ^[A-Za-z0-9_-]{1,128}$"
        )

    return cn
