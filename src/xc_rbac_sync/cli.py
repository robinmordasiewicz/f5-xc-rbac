"""Command-line interface for F5 XC group synchronization.

This module provides the CLI commands for synchronizing user groups
from CSV files to F5 Distributed Cloud (XC) using either API token
or certificate-based authentication.
"""

from __future__ import annotations

import base64
import logging
import os

import click
import requests
from dotenv import load_dotenv

from .client import XCClient
from .sync_service import CSVParseError, GroupSyncService


def _create_client(
    tenant_id: str,
    api_token: str | None,
    cert_file: str | None,
    key_file: str | None,
    timeout: int,
    max_retries: int,
) -> XCClient:
    """Create authenticated XC client.

    Args:
        tenant_id: XC tenant identifier
        api_token: Optional API token for authentication
        cert_file: Optional certificate file path
        key_file: Optional key file path
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
            timeout=timeout,
            max_retries=max_retries,
        )
    elif api_token:
        return XCClient(
            tenant_id=tenant_id,
            api_token=api_token,
            timeout=timeout,
            max_retries=max_retries,
        )
    else:
        raise click.UsageError(
            "Provide XC_API_TOKEN or VOLT_API_CERT_FILE/VOLT_API_CERT_KEY_FILE"
        )


@click.group()
def cli() -> None:
    """XC Group Sync CLI."""


@cli.command()
@click.option(
    "--csv",
    "csv_path",
    type=click.Path(exists=True, dir_okay=False),
    required=True,
    help="Path to CSV export",
)
@click.option("--dry-run", is_flag=True, help="Log actions without calling the API")
@click.option("--cleanup", is_flag=True, help="Delete XC groups missing from CSV")
@click.option(
    "--log-level",
    type=click.Choice(["debug", "info", "warn", "error"], case_sensitive=False),
    default="info",
    help="Logging level",
)
@click.option("--max-retries", type=int, default=3, help="Max retries for API calls")
@click.option("--timeout", type=int, default=30, help="HTTP timeout (seconds)")
def sync(
    csv_path: str,
    dry_run: bool,
    cleanup: bool,
    log_level: str,
    max_retries: int,
    timeout: int,
) -> None:
    """Synchronize XC groups from CSV file.

    Reads a CSV file containing user-to-group mappings and synchronizes
    those mappings to F5 XC. Supports creating, updating, and optionally
    deleting groups to match the CSV.

    Authentication can be provided via environment variables:
    - TENANT_ID (required): Your XC tenant ID
    - XC_API_TOKEN: API token for authentication
    - VOLT_API_CERT_FILE + VOLT_API_CERT_KEY_FILE: Certificate-based auth

    Args:
        csv_path: Path to CSV file with Email and Entitlement Display Name columns
        dry_run: If True, log actions without making API changes
        cleanup: If True, delete groups that exist in XC but not in CSV
        log_level: Logging verbosity level
        max_retries: Maximum retries for failed API requests
        timeout: HTTP timeout in seconds

    """
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(levelname)s %(message)s",
    )

    # Load environment variables
    # Check for secrets/.env first (GitHub Actions), then fallback to default .env
    dotenv_path = os.getenv("DOTENV_PATH")
    if dotenv_path and os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)
    elif os.path.exists("secrets/.env"):
        load_dotenv("secrets/.env")
    else:
        load_dotenv()

    tenant_id = os.getenv("TENANT_ID")
    if not tenant_id:
        # Try base64 encoded version (GitHub Actions workaround for secret masking)
        tenant_id_b64 = os.getenv("TENANT_ID_B64")
        if tenant_id_b64:
            tenant_id = base64.b64decode(tenant_id_b64).decode("utf-8")
        else:
            raise click.UsageError("TENANT_ID must be set in env or .env")

    api_token = os.getenv("XC_API_TOKEN")
    p12_file = os.getenv("VOLT_API_P12_FILE")
    cert_file = os.getenv("VOLT_API_CERT_FILE")
    key_file = os.getenv("VOLT_API_CERT_KEY_FILE")

    # P12 files are not supported by requests library
    if p12_file:
        logging.info(
            "P12 provided but not supported; use XC_API_TOKEN or cert/key instead"
        )

    # Create authenticated client
    try:
        client = _create_client(
            tenant_id, api_token, cert_file, key_file, timeout, max_retries
        )
    except click.UsageError:
        raise
    except Exception as e:
        raise click.ClickException(f"Failed to create client: {e}")

    # Create sync service
    service = GroupSyncService(client)

    # Parse CSV file
    try:
        planned_groups = service.parse_csv_to_groups(csv_path)
    except CSVParseError as e:
        raise click.UsageError(str(e))
    except Exception as e:
        raise click.ClickException(f"Failed to parse CSV: {e}")

    # Display planned groups
    click.echo(f"Groups planned from CSV: {len(planned_groups)}")
    for grp in planned_groups:
        click.echo(f" - {grp.name}: {len(grp.users)} users")

    # Fetch existing groups (validates authentication)
    try:
        existing_groups = service.fetch_existing_groups()
    except requests.RequestException as e:
        raise click.ClickException(f"API error listing groups: {e}")
    except Exception as e:
        raise click.ClickException(f"Unexpected error listing groups: {e}")

    # Pre-validate user existence
    try:
        existing_users = service.fetch_existing_users()
    except Exception as e:
        logging.warning("User pre-validation failed: %s", e)
        existing_users = None

    # Synchronize groups
    try:
        stats = service.sync_groups(
            planned_groups, existing_groups, existing_users, dry_run
        )
    except Exception as e:
        raise click.ClickException(f"Sync failed: {e}")

    # Cleanup orphaned groups if requested
    if cleanup:
        try:
            deleted = service.cleanup_orphaned_groups(
                planned_groups, existing_groups, dry_run
            )
            stats.deleted = deleted
        except Exception as e:
            raise click.ClickException(f"Cleanup failed: {e}")

    # Display summary
    click.echo(stats.summary())

    if stats.has_errors():
        raise click.ClickException(
            "One or more operations failed; see logs for details"
        )

    click.echo("Sync complete.")


if __name__ == "__main__":
    cli()
