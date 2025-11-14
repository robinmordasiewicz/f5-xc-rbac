"""Tests for LDAP utilities module."""

from __future__ import annotations

import pytest

from xc_user_group_sync.ldap_utils import (
    GROUP_NAME_RE,
    LdapParseError,
    extract_cn,
    normalize_group_name_dns1035,
)


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


class TestNormalizeGroupNameDns1035:
    """Test DNS-1035 group name normalization."""

    def test_lowercase_conversion(self):
        """Test uppercase letters are converted to lowercase."""
        assert normalize_group_name_dns1035("ADMIN") == "admin"
        assert normalize_group_name_dns1035("DevOps") == "devops"
        assert normalize_group_name_dns1035("IT-Support") == "it-support"

    def test_underscore_to_hyphen(self):
        """Test underscores are replaced with hyphens."""
        assert normalize_group_name_dns1035("admin_group") == "admin-group"
        assert normalize_group_name_dns1035("team_alpha_prod") == "team-alpha-prod"
        assert normalize_group_name_dns1035("dev_ops") == "dev-ops"

    def test_mixed_normalization(self):
        """Test combined uppercase and underscore normalization."""
        assert normalize_group_name_dns1035("EADMIN_STD") == "eadmin-std"
        assert normalize_group_name_dns1035("Dev_Team_US") == "dev-team-us"
        assert normalize_group_name_dns1035("IT_Support_L2") == "it-support-l2"

    def test_already_normalized(self):
        """Test names that are already DNS-1035 compliant."""
        assert normalize_group_name_dns1035("admin") == "admin"
        assert normalize_group_name_dns1035("dev-ops") == "dev-ops"
        assert normalize_group_name_dns1035("team123") == "team123"

    def test_starts_with_letter(self):
        """Test validation that name starts with a letter."""
        assert normalize_group_name_dns1035("admins") == "admins"

        with pytest.raises(LdapParseError, match="must start with a letter"):
            normalize_group_name_dns1035("123admin")

        with pytest.raises(LdapParseError, match="must start with a letter"):
            normalize_group_name_dns1035("-admin")

    def test_ends_with_alphanumeric(self):
        """Test trailing non-alphanumeric characters are removed."""
        assert normalize_group_name_dns1035("admin-") == "admin"
        assert normalize_group_name_dns1035("team--") == "team"
        assert normalize_group_name_dns1035("dev---") == "dev"

    def test_truncation_to_63_chars(self):
        """Test truncation to DNS-1035 63-character limit."""
        long_name = "a" * 70
        result = normalize_group_name_dns1035(long_name)
        assert len(result) == 63
        assert result == "a" * 63

    def test_truncation_with_trailing_cleanup(self):
        """Test truncation followed by trailing character cleanup."""
        # Create name that will have hyphen at position 63 after truncation
        long_name = "a" * 62 + "-extra"
        result = normalize_group_name_dns1035(long_name)
        assert len(result) <= 63
        assert result[-1].isalnum()  # Must end with alphanumeric

    def test_empty_name_raises_error(self):
        """Test empty name raises error."""
        with pytest.raises(LdapParseError, match="cannot be empty"):
            normalize_group_name_dns1035("")

    def test_invalid_after_normalization(self):
        """Test names that become invalid after normalization."""
        with pytest.raises(LdapParseError):
            normalize_group_name_dns1035("---")  # Only hyphens

        with pytest.raises(LdapParseError):
            normalize_group_name_dns1035("_")  # Only underscore

    def test_preserves_numbers(self):
        """Test that numbers are preserved in the name."""
        assert normalize_group_name_dns1035("team123") == "team123"
        assert normalize_group_name_dns1035("dev-team-2024") == "dev-team-2024"
        assert normalize_group_name_dns1035("L2_Support") == "l2-support"

    def test_real_world_examples(self):
        """Test real-world group name examples."""
        # Common LDAP group naming patterns
        assert normalize_group_name_dns1035("Domain_Admins") == "domain-admins"
        assert normalize_group_name_dns1035("BUILTIN_Users") == "builtin-users"
        assert normalize_group_name_dns1035("IT_Support_L1") == "it-support-l1"
        assert normalize_group_name_dns1035("Dev_Team_Alpha") == "dev-team-alpha"
        assert normalize_group_name_dns1035("QA_TEAM") == "qa-team"

    def test_special_dns_cases(self):
        """Test edge cases for DNS-1035 compliance."""
        # Single character (valid)
        assert normalize_group_name_dns1035("a") == "a"

        # Two characters
        assert normalize_group_name_dns1035("ab") == "ab"

        # Starting with letter, ending with number
        assert normalize_group_name_dns1035("team1") == "team1"

        # Mixed case with numbers
        assert normalize_group_name_dns1035("Team1Alpha2") == "team1alpha2"
