---
title: GitHub Actions Deployment Guide
last_updated: 2025-11-13
version: 1.0.0
status: Production Ready
audience: DevOps Engineers, GitHub Users, CI/CD Engineers
---

## Overview

This guide provides complete instructions for deploying F5 XC User and Group Sync tool using GitHub Actions for automated synchronization triggered by CSV commits or scheduled runs. GitHub Actions provides fully automated, integrated workflow execution with built-in secrets management and no server maintenance requirements.

## Use Case

**Automated synchronization triggered by CSV commits or scheduled runs**

**Best For**: Teams using GitHub, automated daily/weekly syncs, GitOps workflows

## Setup Instructions

### 1. Configure GitHub Secrets

**Required Secrets** (see [Configuration Guide](../configuration.md#environment-variables) for variable descriptions):

Navigate to: `Settings → Secrets → Actions → New repository secret`

| Secret Name | Description |
|-------------|-------------|
| `TENANT_ID` | Your F5 XC tenant ID |
| `XC_P12` | Base64-encoded P12/PKCS12 certificate file |
| `XC_P12_PASSWORD` | Password for P12 certificate file |

**Setup Options**:

**Option A: Automated** (Recommended)

```bash
./scripts/setup_xc_credentials.sh --p12 ~/Downloads/tenant.p12 --github-secrets
# Script automatically sets TENANT_ID, XC_P12, and XC_P12_PASSWORD secrets
```

**Option B: Manual**

```bash
# Encode P12 file to base64
base64 -i ~/Downloads/tenant.p12 | pbcopy  # macOS
base64 -w 0 ~/Downloads/tenant.p12         # Linux (copy output)

# Add XC_P12 secret with base64 output
# Add XC_P12_PASSWORD secret with your P12 password
# Add TENANT_ID secret with your tenant ID
```

### 2. Create Workflow File

Copy the example workflow to your repository:

```bash
cp docs/CICD/examples/xc-sync-workflow.yml .github/workflows/xc-sync.yml
```

Or create `.github/workflows/xc-sync.yml` manually. See [xc-sync-workflow.yml](examples/xc-sync-workflow.yml) for the complete example.

**Key workflow features**:

- Scheduled daily execution (2 AM UTC)
- Manual trigger support
- Automatic trigger on CSV changes
- Dry-run mode for pull requests

## Workflow Behavior

### Trigger Modes

**Scheduled Execution**:

- Runs daily at 2 AM UTC automatically
- Uses cron syntax: `'0 2 * * *'`
- Configurable to any frequency (hourly, weekly, etc.)

**On CSV Change**:

- Triggers when User-Database.csv committed to repository
- Automatically syncs new data to F5 XC
- Useful for GitOps-style workflows

**Manual Trigger**:

- Can be triggered manually via GitHub Actions UI
- Navigate to: `Actions → XC Group Sync → Run workflow`
- Useful for on-demand synchronization

**Pull Request Validation**:

- Runs dry-run for PR validation
- Prevents accidental changes to production
- Shows planned operations in PR comments

## Advanced Configurations

### Weekly Execution

```yaml
on:
  schedule:
    - cron: '0 2 * * 0'  # Weekly on Sunday at 2 AM UTC
```

### Multiple Environment Support

```yaml
jobs:
  sync:
    strategy:
      matrix:
        environment: [production, staging]
    runs-on: ubuntu-latest
    environment: ${{ matrix.environment }}
    steps:
      # ... same steps with environment-specific secrets
```

### Prune Operation on Schedule

```yaml
- name: Sync with prune (scheduled only)
  if: github.event_name == 'schedule'
  env:
    TENANT_ID: ${{ secrets.TENANT_ID }}
    VOLT_API_P12_FILE: /tmp/cert.p12
    VES_P12_PASSWORD: ${{ secrets.XC_P12_PASSWORD }}
  run: |
    xc_user_group_sync --csv User-Database.csv --prune
```

### Notification on Failure

```yaml
jobs:
  sync:
    # ... existing steps ...

    - name: Notify on failure
      if: failure()
      uses: 8398a7/action-slack@v3
      with:
        status: ${{ job.status }}
        text: 'XC Group Sync failed!'
        webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

### Corporate Proxy Configuration

If your GitHub Actions runners operate behind a corporate proxy:

**Option 1: Environment Variables** (Recommended for self-hosted runners)

```yaml
- name: Sync to F5 XC
  env:
    TENANT_ID: ${{ secrets.TENANT_ID }}
    VOLT_API_P12_FILE: /tmp/cert.p12
    VES_P12_PASSWORD: ${{ secrets.XC_P12_PASSWORD }}
    HTTP_PROXY: http://proxy.example.com:8080
    HTTPS_PROXY: http://proxy.example.com:8080
    NO_PROXY: localhost,127.0.0.1
    REQUESTS_CA_BUNDLE: /etc/ssl/certs/ca-bundle.crt
  run: |
    xc_user_group_sync --csv User-Database.csv --dry-run
```

**Option 2: CLI Flags** (For dynamic proxy configuration)

```yaml
- name: Sync to F5 XC with proxy
  env:
    TENANT_ID: ${{ secrets.TENANT_ID }}
    VOLT_API_P12_FILE: /tmp/cert.p12
    VES_P12_PASSWORD: ${{ secrets.XC_P12_PASSWORD }}
  run: |
    xc_user_group_sync --csv User-Database.csv \
      --proxy "http://proxy.example.com:8080" \
      --ca-bundle "/etc/ssl/certs/corporate-ca.crt"
```

**Option 3: GitHub Secrets** (For sensitive proxy credentials)

Add these secrets:
- `PROXY_URL`: `http://username:password@proxy.example.com:8080`  <!-- pragma: allowlist secret -->
- `CA_BUNDLE_PATH`: `/path/to/corporate-ca.crt`

```yaml
- name: Sync to F5 XC via proxy
  env:
    TENANT_ID: ${{ secrets.TENANT_ID }}
    VOLT_API_P12_FILE: /tmp/cert.p12
    VES_P12_PASSWORD: ${{ secrets.XC_P12_PASSWORD }}
    HTTPS_PROXY: ${{ secrets.PROXY_URL }}
    REQUESTS_CA_BUNDLE: ${{ secrets.CA_BUNDLE_PATH }}
  run: |
    xc_user_group_sync --csv User-Database.csv
```

**Self-Hosted Runners**: Install corporate CA certificate:

```yaml
- name: Install corporate CA certificate
  run: |
    sudo cp /path/to/corporate-ca.crt /usr/local/share/ca-certificates/
    sudo update-ca-certificates

- name: Sync to F5 XC
  env:
    TENANT_ID: ${{ secrets.TENANT_ID }}
    VOLT_API_P12_FILE: /tmp/cert.p12
    VES_P12_PASSWORD: ${{ secrets.XC_P12_PASSWORD }}
    HTTPS_PROXY: http://proxy.example.com:8080
  run: |
    xc_user_group_sync --csv User-Database.csv
```

## Pros and Cons

### Pros

- ✅ Fully automated
- ✅ Integrated with GitHub workflow
- ✅ Scheduled execution
- ✅ No server maintenance
- ✅ Built-in secrets management
- ✅ Execution logs in GitHub Actions

### Cons

- ❌ Requires GitHub repository
- ❌ GitHub Actions minutes consumption
- ❌ CSV must be committed to repo (consider security)

## Security Considerations

**CSV Security**:

- CSV contains email addresses (potentially sensitive)
- Consider using private repository
- Alternative: Fetch CSV from secure storage during workflow

**Credentials Management**:

- Always use GitHub Secrets, never commit credentials
- Rotate P12 certificates periodically
- Use strong passwords for P12 files
- Use environment-specific secrets for production/staging

**Audit Trail**:

- GitHub Actions logs provide complete execution history
- Review logs regularly for unexpected changes
- Enable branch protection for production workflows

## Related Documentation

- [Deployment Guide](deployment-guide.md) - Overview of all deployment scenarios
- [Operations Guide](../operations-guide.md) - Step-by-step operational procedures
- [Jenkins Guide](jenkins-guide.md) - Alternative CI/CD with Jenkins
- [Troubleshooting Guide](../troubleshooting.md) - Common issues and resolutions
- [Testing Strategy](../specifications/implementation/testing-strategy.md) - Validation approaches
