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


class LdapParseError(ValueError):
    """Exception raised when LDAP DN parsing fails or validation errors occur."""

    pass


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
