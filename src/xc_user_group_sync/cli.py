"""Command-line interface for F5 XC group synchronization.

This module provides the CLI commands for synchronizing user groups
from CSV files to F5 Distributed Cloud (XC) using either API token
or certificate-based authentication.
"""

from __future__ import annotations

import logging
import os
import time

import click
import requests
from dotenv import load_dotenv

from .client import XCClient
from .sync_service import CSVParseError, GroupSyncService
from .user_sync_service import CSVValidationResult, UserSyncService


def _create_client(
    tenant_id: str,
    api_token: str | None,
    cert_file: str | None,
    key_file: str | None,
    api_url: str | None,
    timeout: int,
    max_retries: int,
) -> XCClient:
    """Create authenticated XC client.

    Args:
        tenant_id: XC tenant identifier
        api_token: Optional API token for authentication
        cert_file: Optional certificate file path
        key_file: Optional key file path
        api_url: Optional API base URL
        timeout: HTTP request timeout in seconds
        max_retries: Maximum number of retries for failed requests

    Returns:
        Configured XCClient instance

    Raises:
        click.UsageError: If no valid authentication method provided

    """
    if cert_file and key_file:
        return XCClient(
            tenant_id=tenant_id,
            cert_file=cert_file,
            key_file=key_file,
            api_url=api_url,
            timeout=timeout,
            max_retries=max_retries,
        )
    elif api_token:
        return XCClient(
            tenant_id=tenant_id,
            api_token=api_token,
            api_url=api_url,
            timeout=timeout,
            max_retries=max_retries,
        )
    else:
        raise click.UsageError(
            "Provide XC_API_TOKEN or VOLT_API_CERT_FILE/VOLT_API_CERT_KEY_FILE"
        )


def _load_configuration() -> tuple[str, str | None, str | None, str | None, str | None]:
    """Load configuration from environment variables.

    Checks for secrets/.env first (GitHub Actions), then fallback to default .env.

    Returns:
        Tuple of (tenant_id, api_token, api_url, cert_file, key_file)

    Raises:
        click.UsageError: If TENANT_ID is not set
    """
    # Load environment variables
    dotenv_path = os.getenv("DOTENV_PATH")
    if dotenv_path and os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)
    elif os.path.exists("secrets/.env"):
        load_dotenv("secrets/.env")
    else:
        load_dotenv()

    tenant_id = os.getenv("TENANT_ID")
    if not tenant_id:
        raise click.UsageError("TENANT_ID must be set in env or .env")

    api_token = os.getenv("XC_API_TOKEN")
    api_url = os.getenv("XC_API_URL")
    p12_file = os.getenv("VOLT_API_P12_FILE")
    cert_file = os.getenv("VOLT_API_CERT_FILE")
    key_file = os.getenv("VOLT_API_CERT_KEY_FILE")

    # P12 not supported by requests - warn only if no cert/key available
    if p12_file and not (cert_file and key_file):
        logging.warning(
            "P12 file provided but Python requests library cannot use it "
            "directly. Please run setup_xc_credentials.sh to extract "
            "cert/key files."
        )

    return tenant_id, api_token, api_url, cert_file, key_file


def _display_csv_validation(result: CSVValidationResult, dry_run: bool = False) -> None:
    """Display CSV validation results with enhanced feedback.

    Args:
        result: CSV validation result with users and warnings
        dry_run: Whether this is a dry-run operation
    """
    # Dry-run banner
    if dry_run:
        click.echo("\n" + "=" * 60)
        click.echo("🔍 DRY RUN MODE - No changes will be made to F5 XC")
        click.echo("=" * 60)

    # Basic counts
    click.echo(f"\nUsers planned from CSV: {result.total_count}")
    click.echo(f" - Active: {result.active_count}, Inactive: {result.inactive_count}")

    # Sample users (first 3)
    if result.users:
        click.echo("\nSample of parsed users:")
        for user in result.users[:3]:
            icon = "✓" if user.active else "⚠"
            status = "Active" if user.active else "Inactive"
            group_count = len(user.groups)
            click.echo(
                f"  {icon} {user.email} ({user.display_name}) - "
                f"{status} [{group_count} groups]"
            )
        if len(result.users) > 3:
            click.echo(f"  ... and {len(result.users) - 3} more users")

    # Unique groups count
    if result.unique_groups:
        click.echo(f"\nGroups assigned: {len(result.unique_groups)} unique LDAP groups")

    # Validation warnings
    if result.has_warnings():
        click.echo("\n⚠️  Validation Warnings:")

        if result.duplicate_emails:
            click.echo(f"  - {len(result.duplicate_emails)} duplicate email(s) found:")
            for email, rows in list(result.duplicate_emails.items())[:5]:
                click.echo(f"    • {email} (rows: {', '.join(map(str, rows))})")
            if len(result.duplicate_emails) > 5:
                click.echo(f"    ... and {len(result.duplicate_emails) - 5} more")

        if result.invalid_emails:
            click.echo(f"  - {len(result.invalid_emails)} invalid email format(s):")
            for email, row_num in result.invalid_emails[:5]:
                click.echo(f"    • {email} (row {row_num})")
            if len(result.invalid_emails) > 5:
                click.echo(f"    ... and {len(result.invalid_emails) - 5} more")

        if result.users_without_groups > 0:
            click.echo(
                f"  - {result.users_without_groups} user(s) have no group assignments"
            )

        if result.users_without_names > 0:
            click.echo(
                f"  - {result.users_without_names} user(s) missing display names "
                f"(will use email prefix)"
            )


@click.command()
@click.option(
    "--csv",
    "csv_path",
    type=click.Path(exists=True, dir_okay=False),
    required=True,
    help="Path to CSV export",
)
@click.option("--dry-run", is_flag=True, help="Log actions without calling the API")
@click.option(
    "--prune",
    is_flag=True,
    help="Delete users and groups in F5 XC that don't exist in CSV",
)
@click.option(
    "--log-level",
    type=click.Choice(["debug", "info", "warn", "error"], case_sensitive=False),
    default="info",
    help="Logging level",
)
@click.option("--max-retries", type=int, default=3, help="Max retries for API calls")
@click.option("--timeout", type=int, default=30, help="HTTP timeout (seconds)")
def cli(
    csv_path: str,
    dry_run: bool,
    prune: bool,
    log_level: str,
    max_retries: int,
    timeout: int,
) -> None:
    """Synchronize F5 XC users and groups from CSV file.

    By default, reconciles both users and groups between CSV and F5 XC:
    - Creates users/groups that exist in CSV but not in F5 XC
    - Updates existing users/groups to match CSV data
    - With --prune flag: deletes users/groups in F5 XC that aren't in CSV

    This is a reconciliation tool - it ensures F5 XC matches your CSV source of truth.

    Authentication via environment variables:
    - TENANT_ID (required): Your XC tenant ID
    - XC_API_TOKEN: API token for authentication
    - VOLT_API_CERT_FILE + VOLT_API_CERT_KEY_FILE: Certificate-based auth

    Examples:
        # Reconcile users and groups (create/update only)
        xc_user_group_sync --csv User-Database.csv

        # Dry run to preview changes
        xc_user_group_sync --csv User-Database.csv --dry-run

        # Full reconciliation including deletions
        xc_user_group_sync --csv User-Database.csv --prune

    Args:
        csv_path: Path to CSV file with user and group data
        dry_run: If True, log actions without making API changes
        prune: If True, delete users/groups in F5 XC that don't exist in CSV
        log_level: Logging verbosity level
        max_retries: Maximum retries for failed API requests
        timeout: HTTP timeout in seconds

    """
    # Always sync both users and groups - that's the tool's purpose
    sync_groups = True
    sync_users = True
    prune_groups = prune
    prune_users = prune

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(levelname)s %(message)s",
    )

    # Load configuration from environment
    tenant_id, api_token, api_url, cert_file, key_file = _load_configuration()

    # Create authenticated client
    try:
        client = _create_client(
            tenant_id, api_token, cert_file, key_file, api_url, timeout, max_retries
        )
    except click.UsageError:
        raise
    except Exception as e:
        raise click.ClickException(f"Failed to create client: {e}")

    # Initialize services
    group_service = GroupSyncService(client) if sync_groups else None
    user_service = UserSyncService(client) if sync_users else None

    # Track overall execution time
    start_time = time.time()

    # ===== GROUP SYNCHRONIZATION =====
    if sync_groups:
        click.echo("\n" + "=" * 60)
        click.echo("📦 GROUP SYNCHRONIZATION")
        click.echo("=" * 60)

        # Parse CSV for groups
        try:
            planned_groups = group_service.parse_csv_to_groups(csv_path)
        except CSVParseError as e:
            raise click.UsageError(str(e))
        except Exception as e:
            raise click.ClickException(f"Failed to parse CSV for groups: {e}")

        # Display planned groups
        click.echo(f"Groups planned from CSV: {len(planned_groups)}")
        for grp in planned_groups:
            click.echo(f" - {grp.name}: {len(grp.users)} users")

        # Fetch existing groups
        try:
            existing_groups = group_service.fetch_existing_groups()
        except requests.RequestException as e:
            raise click.ClickException(f"API error listing groups: {e}")
        except Exception as e:
            raise click.ClickException(f"Unexpected error listing groups: {e}")

        # Pre-validate user existence
        try:
            existing_users_for_groups = group_service.fetch_existing_users()
        except Exception as e:
            logging.warning("User pre-validation failed: %s", e)
            existing_users_for_groups = None

        # Synchronize groups
        try:
            group_stats = group_service.sync_groups(
                planned_groups, existing_groups, existing_users_for_groups, dry_run
            )
        except Exception as e:
            raise click.ClickException(f"Group sync failed: {e}")

        # Prune orphaned groups if requested
        if prune_groups:
            try:
                deleted = group_service.cleanup_orphaned_groups(
                    planned_groups, existing_groups, dry_run
                )
                group_stats.deleted = deleted
            except Exception as e:
                raise click.ClickException(f"Group prune failed: {e}")

        # Display group summary
        click.echo("\n" + group_stats.summary())

        if group_stats.has_errors():
            raise click.ClickException(
                "One or more group operations failed; see logs for details"
            )

    # ===== USER SYNCHRONIZATION =====
    if sync_users:
        click.echo("\n" + "=" * 60)
        click.echo("👤 USER SYNCHRONIZATION")
        click.echo("=" * 60)

        # Parse CSV for users
        try:
            validation_result = user_service.parse_csv_to_users(csv_path)
        except FileNotFoundError as e:
            raise click.UsageError(str(e))
        except ValueError as e:
            raise click.UsageError(f"CSV validation error: {e}")
        except Exception as e:
            raise click.ClickException(f"Failed to parse CSV for users: {e}")

        # Display CSV validation results
        _display_csv_validation(validation_result, dry_run)

        # Fetch existing users
        try:
            existing_users = user_service.fetch_existing_users()
        except requests.RequestException as e:
            raise click.ClickException(f"API error listing users: {e}")
        except Exception as e:
            raise click.ClickException(f"Unexpected error listing users: {e}")

        click.echo(f"Existing users in F5 XC: {len(existing_users)}")

        # Synchronize users
        try:
            user_stats = user_service.sync_users(
                validation_result.users, existing_users, dry_run, prune_users
            )
        except Exception as e:
            raise click.ClickException(f"User sync failed: {e}")

        # Display user summary
        click.echo("\n" + user_stats.summary())

        # Show error details if any
        if user_stats.has_errors():
            click.echo("\nErrors encountered:")
            for err in user_stats.error_details:
                click.echo(
                    f" - {err['email']}: {err['operation']} failed - {err['error']}"
                )
            raise click.ClickException(
                "One or more user operations failed; see details above"
            )

    # ===== FINAL SUMMARY =====
    execution_time = time.time() - start_time
    click.echo("\n" + "=" * 60)
    click.echo("✅ SYNCHRONIZATION COMPLETE")
    click.echo("=" * 60)
    click.echo(f"Execution time: {execution_time:.2f} seconds")

    if sync_groups:
        click.echo(
            f"Groups: {group_stats.created} created, {group_stats.updated} updated"
        )
        if prune_groups:
            click.echo(f"Groups pruned: {group_stats.deleted}")

    if sync_users:
        click.echo(f"Users: {user_stats.created} created, {user_stats.updated} updated")
        if prune_users:
            click.echo(f"Users pruned: {user_stats.deleted}")


if __name__ == "__main__":
    cli()
