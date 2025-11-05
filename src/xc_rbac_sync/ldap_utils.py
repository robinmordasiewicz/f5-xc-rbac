from __future__ import annotations

import re
from typing import Optional

from ldap3.utils.dn import parse_dn

# F5 XC group name constraints (from model):
# - allowed: letters, digits, underscore, hyphen
# - length: 1..128
GROUP_NAME_RE = re.compile(r"^[A-Za-z0-9_-]{1,128}$")


class LdapParseError(ValueError):
    pass


def extract_cn(dn: str) -> str:
    """Extract CN from an LDAP DN using ldap3's parser.

    Raises LdapParseError if CN missing or invalid.
    """
    try:
        rdn_seq = parse_dn(dn, case_sensitive=False)
    except Exception as exc:  # ldap3 throws on malformed DN
        raise LdapParseError(f"Malformed DN: {dn}") from exc

    # rdn_seq is a list of RDNs; each RDN is list of (attr, value, flags)
    cn: Optional[str] = None
    for rdn in rdn_seq:
        for attr, value, _flags in rdn:
            if attr.upper() == "CN":
                cn = value
                break
        if cn:
            break

    if not cn:
        raise LdapParseError(f"CN not found in DN: {dn}")

    if not GROUP_NAME_RE.fullmatch(cn):
        raise LdapParseError(
            "Invalid group name extracted from CN; must match ^[A-Za-z0-9_-]{1,128}$"
        )

    return cn
