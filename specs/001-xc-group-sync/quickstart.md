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
