# GitHub Actions

Automated F5 XC user/group synchronization using GitHub Actions workflows.

## Setup

### 1. Configure GitHub Secrets

Navigate to **Settings → Secrets → Actions** and add:

| Secret Name | Description |
|-------------|-------------|
| `TENANT_ID` | Your F5 XC tenant ID |
| `XC_P12` | Base64-encoded P12 certificate |
| `XC_P12_PASSWORD` | P12 certificate password |

**Automated Setup**:

```bash
./scripts/setup_xc_credentials.sh --p12 ~/Downloads/tenant.p12 --github-secrets
```

**Manual Encoding**:

```bash
# macOS
base64 -i ~/Downloads/tenant.p12 | pbcopy

# Linux
base64 -w 0 ~/Downloads/tenant.p12
```

### 2. Create Workflow File

Create `.github/workflows/xc-sync.yml`:

```yaml
name: F5 XC User/Group Sync

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM UTC
  push:
    branches: [main]
    paths:
      - 'User-Database.csv'
  workflow_dispatch:  # Manual trigger
  pull_request:
    paths:
      - 'User-Database.csv'

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install tool
        run: |
          pip install git+https://github.com/robinmordasiewicz/f5-xc-user-group-sync.git

      - name: Decode P12 certificate
        run: |
          echo "${{ secrets.XC_P12 }}" | base64 -d > /tmp/cert.p12
          chmod 600 /tmp/cert.p12

      - name: Dry-run
        env:
          TENANT_ID: ${{ secrets.TENANT_ID }}
          XC_API_URL: https://${{ secrets.TENANT_ID }}.console.ves.volterra.io
          VOLT_API_P12_FILE: /tmp/cert.p12
          VES_P12_PASSWORD: ${{ secrets.XC_P12_PASSWORD }}
        run: |
          xc_user_group_sync --csv User-Database.csv --dry-run

      - name: Execute sync
        if: github.event_name != 'pull_request'
        env:
          TENANT_ID: ${{ secrets.TENANT_ID }}
          XC_API_URL: https://${{ secrets.TENANT_ID }}.console.ves.volterra.io
          VOLT_API_P12_FILE: /tmp/cert.p12
          VES_P12_PASSWORD: ${{ secrets.XC_P12_PASSWORD }}
        run: |
          xc_user_group_sync --csv User-Database.csv

      - name: Cleanup
        if: always()
        run: rm -f /tmp/cert.p12
```

## Workflow Triggers

- **Schedule**: Runs daily at 2 AM UTC (`cron: '0 2 * * *'`)
- **CSV Changes**: Triggers on commits to `User-Database.csv`
- **Manual**: Run from Actions tab → **Run workflow**
- **Pull Requests**: Dry-run only for validation

## Corporate Proxy Support

For runners behind a corporate proxy, add environment variables:

```yaml
- name: Execute sync
  env:
    TENANT_ID: ${{ secrets.TENANT_ID }}
    XC_API_URL: https://${{ secrets.TENANT_ID }}.console.ves.volterra.io
    VOLT_API_P12_FILE: /tmp/cert.p12
    VES_P12_PASSWORD: ${{ secrets.XC_P12_PASSWORD }}
    HTTPS_PROXY: http://proxy.example.com:8080
    REQUESTS_CA_BUNDLE: /etc/ssl/certs/ca-bundle.crt
  run: |
    xc_user_group_sync --csv User-Database.csv
```

Or add GitHub secrets: `PROXY_URL`, `CA_BUNDLE_PATH`  <!-- pragma: allowlist secret -->

## Troubleshooting

**Workflow fails with SSL error**:
- Verify P12 certificate base64 encoding
- Check `XC_P12_PASSWORD` matches certificate
- See [Troubleshooting Guide](../troubleshooting.md#issue-4-corporate-proxy-configuration-and-authentication)

**No changes applied**:
- Check CSV format matches requirements
- Verify `TENANT_ID` is correct
- Review workflow logs for errors
