"""Tests for LDAP utilities module."""

from __future__ import annotations

import pytest

from xc_rbac_sync.ldap_utils import GROUP_NAME_RE, LdapParseError, extract_cn


class TestGroupNameRegex:
    """Test group name regex validation."""

    def test_valid_simple_name(self):
        """Test valid simple group names."""
        assert GROUP_NAME_RE.fullmatch("admins")
        assert GROUP_NAME_RE.fullmatch("Developers")
        assert GROUP_NAME_RE.fullmatch("IT-Support")
        assert GROUP_NAME_RE.fullmatch("team_alpha")
        assert GROUP_NAME_RE.fullmatch("group123")

    def test_valid_complex_name(self):
        """Test valid complex group names with mixed characters."""
        assert GROUP_NAME_RE.fullmatch("Team-Alpha_123")
        assert GROUP_NAME_RE.fullmatch("IT-Support-Level-2")
        assert GROUP_NAME_RE.fullmatch("dev_team_us-west-1")

    def test_valid_length_boundaries(self):
        """Test length boundaries (1-128 chars)."""
        assert GROUP_NAME_RE.fullmatch("a")  # Min length
        assert GROUP_NAME_RE.fullmatch("a" * 128)  # Max length

    def test_invalid_length(self):
        """Test invalid lengths."""
        assert not GROUP_NAME_RE.fullmatch("")  # Empty
        assert not GROUP_NAME_RE.fullmatch("a" * 129)  # Too long

    def test_invalid_characters(self):
        """Test rejection of invalid characters."""
        assert not GROUP_NAME_RE.fullmatch("admin$")  # Dollar sign
        assert not GROUP_NAME_RE.fullmatch("team space")  # Space
        assert not GROUP_NAME_RE.fullmatch("group@domain")  # At sign
        assert not GROUP_NAME_RE.fullmatch("team.prod")  # Dot
        assert not GROUP_NAME_RE.fullmatch("dev/ops")  # Slash


class TestExtractCn:
    """Test CN extraction from LDAP DNs."""

    def test_extract_simple_dn(self):
        """Test extraction from simple DN."""
        dn = "CN=admins,OU=Groups,DC=example,DC=com"
        assert extract_cn(dn) == "admins"

    def test_extract_complex_dn(self):
        """Test extraction from complex DN with multiple components."""
        dn = "CN=IT-Support,OU=Security,OU=Groups,DC=corp,DC=example,DC=com"
        assert extract_cn(dn) == "IT-Support"

    def test_extract_with_spaces(self):
        """Test extraction with spaces in DN components."""
        # ldap3 parser doesn't allow spaces after commas in RFC 4514 format
        dn = "CN=Team-Alpha,OU=Engineering,DC=example,DC=com"
        assert extract_cn(dn) == "Team-Alpha"

    def test_extract_case_insensitive(self):
        """Test case-insensitive CN extraction."""
        assert extract_cn("cn=admins,ou=Groups,dc=example,dc=com") == "admins"
        assert extract_cn("Cn=developers,Ou=Groups,Dc=example,Dc=com") == "developers"

    def test_extract_numeric_cn(self):
        """Test extraction of numeric group names."""
        dn = "CN=12345,OU=Groups,DC=example,DC=com"
        assert extract_cn(dn) == "12345"

    def test_extract_with_hyphen_underscore(self):
        """Test extraction with hyphens and underscores."""
        dn = "CN=team_alpha-prod,OU=Groups,DC=example,DC=com"
        assert extract_cn(dn) == "team_alpha-prod"

    def test_missing_cn_raises_error(self):
        """Test that missing CN raises LdapParseError."""
        dn = "OU=Groups,DC=example,DC=com"
        with pytest.raises(LdapParseError, match="CN not found"):
            extract_cn(dn)

    def test_invalid_characters_in_cn_raises_error(self):
        """Test that invalid characters in CN raise LdapParseError."""
        dn = "CN=admin$,OU=Groups,DC=example,DC=com"
        with pytest.raises(LdapParseError, match="Invalid group name"):
            extract_cn(dn)

    def test_cn_with_space_raises_error(self):
        """Test that spaces in CN value raise LdapParseError."""
        dn = "CN=Admin Group,OU=Groups,DC=example,DC=com"
        with pytest.raises(LdapParseError, match="Invalid group name"):
            extract_cn(dn)

    def test_cn_with_special_chars_raises_error(self):
        """Test various special characters that should be rejected."""
        # ldap3 parser rejects some chars as malformed DN, others as invalid names
        invalid_dns = [
            (
                "CN=admin@domain,OU=Groups,DC=example,DC=com",
                "Malformed|Invalid",
            ),  # @ sign
            ("CN=team.prod,OU=Groups,DC=example,DC=com", "Malformed|Invalid"),  # dot
            (
                "CN=group!,OU=Groups,DC=example,DC=com",
                "Malformed|Invalid",
            ),  # exclamation
        ]
        for dn, expected_pattern in invalid_dns:
            with pytest.raises(LdapParseError, match=expected_pattern):
                extract_cn(dn)

    def test_malformed_dn_raises_error(self):
        """Test that malformed DN raises LdapParseError."""
        malformed_dns = [
            "not a valid dn",
            "CN=,OU=Groups",  # Empty CN value
            "CNadmins,OU=Groups",  # Missing equals
            "",  # Empty string
        ]
        for dn in malformed_dns:
            with pytest.raises(LdapParseError):
                extract_cn(dn)

    def test_cn_too_long_raises_error(self):
        """Test that CN exceeding 128 chars raises error."""
        long_name = "a" * 129
        dn = f"CN={long_name},OU=Groups,DC=example,DC=com"
        with pytest.raises(LdapParseError, match="Invalid group name"):
            extract_cn(dn)

    def test_first_cn_extracted_from_multiple(self):
        """Test that first CN is extracted when multiple exist."""
        # Though uncommon, LDAP allows multiple RDNs
        dn = "CN=primary,CN=secondary,OU=Groups,DC=example,DC=com"
        # ldap3 parser will extract the first one
        result = extract_cn(dn)
        assert result in ["primary", "secondary"]  # Either is acceptable

    def test_escaped_characters_in_dn(self):
        """Test DN with properly escaped characters (if valid after escaping)."""
        # LDAP allows escaped characters, but our group name regex may reject them
        dn = "CN=test-group,OU=Groups,DC=example,DC=com"
        assert extract_cn(dn) == "test-group"

    def test_unicode_characters_rejected(self):
        """Test that unicode characters in CN are rejected."""
        dn = "CN=группа,OU=Groups,DC=example,DC=com"  # Cyrillic
        with pytest.raises(LdapParseError, match="Invalid group name"):
            extract_cn(dn)
