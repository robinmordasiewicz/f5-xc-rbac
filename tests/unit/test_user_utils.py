"""Unit tests for user utility functions."""

from xc_rbac_sync.user_utils import parse_active_status, parse_display_name


class TestParseDisplayName:
    """Test cases for parse_display_name function."""

    def test_two_word_name(self):
        """Test parsing standard two-word name."""
        assert parse_display_name("Alice Anderson") == ("Alice", "Anderson")

    def test_three_word_name(self):
        """Test parsing three-word name (middle name)."""
        assert parse_display_name("John Paul Smith") == ("John Paul", "Smith")

    def test_four_word_name(self):
        """Test parsing four-word name (multiple middle names)."""
        assert parse_display_name("Mary Jane Elizabeth Watson") == (
            "Mary Jane Elizabeth",
            "Watson",
        )

    def test_single_name(self):
        """Test parsing single name (no last name)."""
        assert parse_display_name("Madonna") == ("Madonna", "")

    def test_whitespace_trimming(self):
        """Test trimming leading and trailing whitespace."""
        assert parse_display_name("  Alice  Anderson  ") == ("Alice", "Anderson")

    def test_multiple_spaces_between_words(self):
        """Test handling multiple spaces between words."""
        assert parse_display_name("Alice  Anderson") == ("Alice", "Anderson")

    def test_empty_string(self):
        """Test handling empty string."""
        assert parse_display_name("") == ("", "")

    def test_whitespace_only(self):
        """Test handling whitespace-only string."""
        assert parse_display_name("   ") == ("", "")


class TestParseActiveStatus:
    """Test cases for parse_active_status function."""

    def test_active_uppercase(self):
        """Test 'A' (Active) maps to True."""
        assert parse_active_status("A") is True

    def test_active_lowercase(self):
        """Test 'a' (Active) maps to True (case-insensitive)."""
        assert parse_active_status("a") is True

    def test_active_mixed_case(self):
        """Test mixed case 'A' maps to True."""
        assert parse_active_status("A") is True

    def test_inactive_status(self):
        """Test 'I' (Inactive) maps to False."""
        assert parse_active_status("I") is False

    def test_terminated_status(self):
        """Test 'T' (Terminated) maps to False."""
        assert parse_active_status("T") is False

    def test_leave_status(self):
        """Test 'L' (Leave) maps to False."""
        assert parse_active_status("L") is False

    def test_whitespace_handling(self):
        """Test trimming whitespace before comparison."""
        assert parse_active_status("  A  ") is True

    def test_whitespace_with_inactive(self):
        """Test trimming whitespace with inactive status."""
        assert parse_active_status("  I  ") is False

    def test_empty_string(self):
        """Test empty string maps to False (safe default)."""
        assert parse_active_status("") is False

    def test_unknown_status_code(self):
        """Test unknown status code maps to False (safe default)."""
        assert parse_active_status("X") is False
