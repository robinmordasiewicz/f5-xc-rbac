# Quickstart: XC Group Sync

This quickstart sets up local dev for a Python-based XC Group Sync tool and shows how to run a dry-run.

## Prerequisites

- Python 3.12+
- A `.p12` cert+password OR an API token
- `.env` with either:
  - `VOLT_API_P12_FILE` and `VES_P12_PASSWORD` (preferred), or
  - `VOLT_API_CERT_FILE` and `VOLT_API_CERT_KEY_FILE`, or
  - `XC_API_TOKEN`
  - `TENANT_ID`

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Run (dry-run)

```bash
python -m xc_rbac_sync.cli sync --csv User-Database.csv --dry-run
```

Set `TENANT_ID` and credential envs via `.env` or shell; the CLI auto-detects which auth is present and prefers P12.

## Setup script (optional)

Use the helper script to derive `TENANT_ID`, split a `.p12` to PEM cert/key, and write a local `.env`:

```bash
bash scripts/setup_xc_credentials.sh --p12 ~/Downloads/your-tenant-api.p12 --tenant your-tenant
```

Add `--set-secrets` to push GitHub repo secrets via gh CLI (TENANT_ID, XC_CERT, XC_CERT_KEY, XC_P12, XC_P12_PASSWORD).

## GitHub Actions (CI)

This repo includes a workflow at `.github/workflows/xc-group-sync.yml` that:
- Installs Python 3.12 and the project
- Decodes secrets to files (`XC_CERT`/`XC_CERT_KEY` or `XC_P12`/`XC_P12_PASSWORD`)
- Runs a dry-run on push to `main`, and applies changes only on manual `workflow_dispatch`

Required repo secrets:
- `TENANT_ID`
- Either `XC_CERT` and `XC_CERT_KEY` (base64 PEM), or `XC_P12` and `XC_P12_PASSWORD`

## CLI options

```text
--dry-run          Log actions without calling the API
--cleanup          Delete XC groups missing from CSV (opt-in)
--log-level        debug|info|warn|error (default: info)
--timeout          HTTP timeout in seconds (default: 30)
--max-retries      Max retries for transient API errors (default: 3)
```

## Performance and reliability

The client retries transient errors (429/5xx) with exponential backoff. Use `--max-retries` and `--timeout` to tune behavior in CI.
