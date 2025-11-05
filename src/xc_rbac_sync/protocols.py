"""Protocol definitions for dependency injection and testing."""

from __future__ import annotations

from typing import Any, Dict, Protocol


class GroupRepository(Protocol):
    """Protocol for group management operations.

    This protocol defines the interface for interacting with group storage,
    whether that's an API, database, or mock implementation for testing.
    """

    def list_groups(self, namespace: str = "system") -> Dict[str, Any]:
        """List all groups in the given namespace.

        Args:
            namespace: The namespace to list groups from (default: "system")

        Returns:
            Dictionary with "items" key containing list of group dicts

        Raises:
            Exception: If the operation fails

        """
        ...

    def create_group(
        self, group: Dict[str, Any], namespace: str = "system"
    ) -> Dict[str, Any]:
        """Create a new group.

        Args:
            group: Group data dictionary with name, display_name, usernames
            namespace: The namespace to create the group in (default: "system")

        Returns:
            Created group data dictionary

        Raises:
            Exception: If the operation fails

        """
        ...

    def update_group(
        self, name: str, group: Dict[str, Any], namespace: str = "system"
    ) -> Dict[str, Any]:
        """Update an existing group.

        Args:
            name: The name of the group to update
            group: Updated group data dictionary
            namespace: The namespace containing the group (default: "system")

        Returns:
            Updated group data dictionary

        Raises:
            Exception: If the operation fails

        """
        ...

    def delete_group(self, name: str, namespace: str = "system") -> None:
        """Delete a group.

        Args:
            name: The name of the group to delete
            namespace: The namespace containing the group (default: "system")

        Raises:
            Exception: If the operation fails

        """
        ...

    def list_user_roles(self, namespace: str = "system") -> Dict[str, Any]:
        """List all user roles for pre-validation.

        Args:
            namespace: The namespace to list user roles from (default: "system")

        Returns:
            Dictionary with "items" key containing list of user role dicts

        Raises:
            Exception: If the operation fails

        """
        ...
