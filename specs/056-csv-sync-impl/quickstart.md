# quickstart.md — CSV Sync quickstart

Date: 2025-11-06

This quickstart shows how to prepare credentials, create a sample CSV, and run the CLI in dry-run mode.

1. Prepare credentials (existing helper):

```bash
# Extract cert/key and write secrets/.env using the p12 file
bash scripts/setup_xc_credentials.sh --p12 /path/to/tenant.api-creds.p12 --no-secrets
```

1. Create a sample CSV (`User-Database.csv`):

```csv
Email,Entitlement Display Name
alice@example.com,"CN=admins,OU=Groups,DC=example,DC=com"
bob@example.com,"CN=developers,OU=Groups,DC=example,DC=com"
```

1. Run a safe dry-run to see planned actions (no API changes):

```bash
python -m xc_rbac_sync.cli sync --csv User-Database.csv --dry-run --log-level info
```

1. When ready to apply changes, run without `--dry-run` (careful; this will modify your tenant):

```bash
python -m xc_rbac_sync.cli sync --csv User-Database.csv
```

Notes:

- The CLI uses `secrets/.env` if present. To avoid loading repo-local secrets in CI or tests, set `DOTENV_PATH=/dev/null`.
- For large CSVs, consider splitting into smaller batches and increasing the client's `max_retries` and timeouts.

Create user behavior and retry/backoff configuration:

- If the sync needs to provision a missing user, it will call `repository.create_user(user_dict)`. The `user_dict` will contain at minimum `email` and may include `username` and `display_name` when available.
- The `GroupSyncService` constructor accepts retry/backoff parameters (`retry_attempts`, `backoff_multiplier`, `backoff_min`, `backoff_max`) that control how the service will retry transient failures when creating users. Defaults are conservative (3 attempts, exponential backoff up to 4s) and can be tuned for large or unreliable environments.
