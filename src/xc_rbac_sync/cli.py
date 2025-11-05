from __future__ import annotations

import csv
import logging
import os
from collections import defaultdict
from typing import Dict, Set

import click
from dotenv import load_dotenv

from .client import XCClient
from .ldap_utils import LdapParseError, extract_cn
from .models import Group

REQUIRED_COLUMNS = {
    "Email",
    "Entitlement Display Name",
}


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
def sync(csv_path: str, dry_run: bool, cleanup: bool, log_level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(levelname)s %(message)s",
    )
    load_dotenv()
    tenant_id = os.getenv("TENANT_ID")
    api_token = os.getenv("XC_API_TOKEN")
    p12_file = os.getenv("VOLT_API_P12_FILE")
    cert_file = os.getenv("VOLT_API_CERT_FILE")
    key_file = os.getenv("VOLT_API_CERT_KEY_FILE")

    if not tenant_id:
        raise click.UsageError("TENANT_ID must be set in env or .env")

    # Prefer P12 → cert/key → token
    client: XCClient
    if p12_file:
        # requests can't use p12; split to PEM; fallback to token/cert-key
        logging.info(
            (
                "P12 provided; split to PEM for requests "
                "or set XC_API_TOKEN or cert/key. Falling back."
            )
        )
    if cert_file and key_file:
        client = XCClient(tenant_id=tenant_id, cert_file=cert_file, key_file=key_file)
    elif api_token:
        client = XCClient(tenant_id=tenant_id, api_token=api_token)
    else:
        raise click.UsageError(
            (
                "Provide XC_API_TOKEN or VOLT_API_CERT_FILE/"
                "VOLT_API_CERT_KEY_FILE; p12 must be split"
            )
        )

    # Preflight: fail fast on auth issues before doing any work
    try:
        # Create client first; will validate auth via a lightweight call below
        pass
    except Exception:
        # placeholder: client not yet created
        pass

    # Build groups from CSV
    members: Dict[str, Set[str]] = defaultdict(set)
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        header = set(reader.fieldnames or [])
        missing = [c for c in REQUIRED_COLUMNS if c not in header]
        if missing:
            raise click.UsageError(
                f"CSV missing required columns: {', '.join(sorted(missing))}"
            )
        for row in reader:
            dn = row.get("Entitlement Display Name") or row.get(
                "entitlement_display_name"
            )
            email = row.get("Email") or row.get("email")
            if not dn or not email:
                continue
            try:
                cn = extract_cn(dn)
            except LdapParseError as e:
                logging.warning("Skipping row due to DN parse error: %s", e)
                continue
            members[cn].add(email)

    planned = []
    for name, users in sorted(members.items()):
        grp = Group(name=name, users=sorted(users))
        planned.append(grp)

    click.echo(f"Groups planned from CSV: {len(planned)}")
    for grp in planned:
        click.echo(f" - {grp.name}: {len(grp.users)} users")

    # List existing groups (auth preflight happens here)
    try:
        list_resp = client.list_groups()
    except Exception as e:
        raise click.ClickException(f"Authentication or API error listing groups: {e}")

    existing = {
        g.get("name"): g for g in list_resp.get("items", []) if isinstance(g, dict)
    }

    created = 0
    updated = 0
    skipped = 0
    deleted = 0
    errors = 0

    # Upsert logic with idempotency
    for grp in planned:
        desired_users = sorted(grp.users)
        if grp.name in existing:
            curr = existing[grp.name]
            curr_users = sorted(curr.get("usernames") or curr.get("users") or [])
            if curr_users == desired_users:
                skipped += 1
                logging.debug("No change for group %s", grp.name)
                continue
            payload = {
                "name": grp.name,
                "display_name": grp.name,
                "usernames": desired_users,
            }
            if dry_run:
                click.echo(
                    f"Would update group {grp.name} ({len(desired_users)} users)"
                )
            else:
                try:
                    client.update_group(grp.name, payload)
                    updated += 1
                except Exception as e:
                    errors += 1
                    logging.error("Failed to update %s: %s", grp.name, e)
        else:
            payload = {
                "name": grp.name,
                "display_name": grp.name,
                "usernames": desired_users,
            }
            if dry_run:
                click.echo(
                    f"Would create group {grp.name} ({len(desired_users)} users)"
                )
            else:
                try:
                    client.create_group(payload)
                    created += 1
                except Exception as e:
                    errors += 1
                    logging.error("Failed to create %s: %s", grp.name, e)

    # Cleanup mode
    if cleanup:
        planned_names = {g.name for g in planned}
        extra = [name for name in existing.keys() if name not in planned_names]
        if extra:
            click.echo(f"Extra groups in XC not in CSV: {len(extra)}")
            for name in extra:
                click.echo(f" - {name}")
            if not dry_run:
                for name in extra:
                    try:
                        client.delete_group(name)
                        deleted += 1
                    except Exception as e:
                        errors += 1
                        logging.error("Failed to delete %s: %s", name, e)

    # Summary
    click.echo(
        "Summary: created=%d, updated=%d, deleted=%d, skipped=%d, errors=%d"
        % (created, updated, deleted, skipped, errors)
    )
    if errors:
        raise click.ClickException(
            "One or more operations failed; see logs for details"
        )
    click.echo("Sync complete.")


if __name__ == "__main__":
    cli()
