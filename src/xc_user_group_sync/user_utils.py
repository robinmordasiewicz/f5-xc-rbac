"""Utility functions for user data parsing and transformation."""


def parse_display_name(display_name: str) -> tuple[str, str]:
    """Parse display name into (first_name, last_name).

    Args:
        display_name: Full name from CSV (e.g., "Alice Anderson")

    Returns:
        Tuple of (first_name, last_name)

    Rules:
        - Last space-separated word → last_name
        - Remaining words → first_name
        - Whitespace trimmed before parsing
        - Multiple spaces normalized to single space

    Examples:
        >>> parse_display_name("Alice Anderson")
        ('Alice', 'Anderson')
        >>> parse_display_name("John Paul Smith")
        ('John Paul', 'Smith')
        >>> parse_display_name("Madonna")
        ('Madonna', '')
        >>> parse_display_name("  Alice  Anderson  ")
        ('Alice', 'Anderson')

    Edge Cases:
        - Empty string → ('', '')
        - Single name → (name, '')
        - Multiple spaces → normalized to single space
    """
    # Trim and normalize whitespace
    trimmed = " ".join(display_name.split())

    if not trimmed:
        return ("", "")

    parts = trimmed.split()

    if len(parts) == 1:
        return (parts[0], "")

    # Last word is last name, everything else is first name
    first_name = " ".join(parts[:-1])
    last_name = parts[-1]

    return (first_name, last_name)


def parse_active_status(employee_status: str) -> bool:
    """Map employee status code to active boolean.

    Args:
        employee_status: Status code from CSV (e.g., "A", "I", "T")

    Returns:
        True if status is "A" (Active), False otherwise

    Rules:
        - "A" (case-insensitive) → True
        - All other values → False
        - Whitespace trimmed before comparison

    Examples:
        >>> parse_active_status("A")
        True
        >>> parse_active_status("a")  # case-insensitive
        True
        >>> parse_active_status("I")  # Inactive
        False
        >>> parse_active_status("T")  # Terminated
        False
        >>> parse_active_status("  A  ")  # with whitespace
        True

    Notes:
        - Safe default: unknown codes treated as inactive (False)
        - Common AD codes: A=Active, I=Inactive, T=Terminated, L=Leave
    """
    return employee_status.strip().upper() == "A"
