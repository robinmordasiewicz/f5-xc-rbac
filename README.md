# f5-xc-rbac

XC RBAC Group Sync tool (Spec 001)

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Usage

```bash
# Dry-run
xc-group-sync --csv ./User-Database.csv --dry-run --log-level info

# Apply (with cleanup)
xc-group-sync --csv ./User-Database.csv --cleanup --log-level info
```

The CLI reads credentials from environment variables or `.env`:

- `TENANT_ID`
- Either `XC_API_TOKEN`, or `VOLT_API_CERT_FILE` + `VOLT_API_CERT_KEY_FILE`
- If you have only a `.p12`, use `scripts/setup_xc_credentials.sh` to split to PEM and write `.env`.

## CI

See `.github/workflows/xc-group-sync.yml`. Provide repo secrets:

- `TENANT_ID`
- Either `XC_CERT` and `XC_CERT_KEY` (base64 PEM), or `XC_P12` and `XC_P12_PASSWORD`

## Options

```text
--dry-run          Log actions without calling the API
--cleanup          Delete XC groups missing from CSV (opt-in)
--log-level        debug|info|warn|error (default: info)
--timeout          HTTP timeout in seconds (default: 30)
--max-retries      Max retries for transient API errors (default: 3)
```

## Notes

- LDAP DN parsing uses `ldap3` to extract CN and validates against F5 XC naming constraints.
- API client retries 429/5xx with exponential backoff.
- Pre-validation checks that all emails from CSV exist in XC (`user_roles`), and skips groups with unknown users.
