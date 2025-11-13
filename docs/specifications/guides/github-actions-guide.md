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

**Option A: Using Setup Script** (Recommended)

```bash
# Run setup script with GitHub secrets flag
./scripts/setup_xc_credentials.sh --p12 ~/Downloads/tenant.p12

# Script will:
# - Extract certificate and key from P12
# - Base64-encode credentials
# - Display GitHub secrets configuration commands
```

**Option B: Manual Configuration**

Navigate to: `Settings → Secrets → Actions → New repository secret`

Create the following secrets:

**For PEM Certificate Authentication**:

- `TENANT_ID`: your-tenant
- `XC_CERT`: base64-encoded PEM certificate
- `XC_CERT_KEY`: base64-encoded PEM private key

```bash
# Generate base64-encoded secrets
base64 -i secrets/cert.pem | pbcopy  # macOS
base64 -w 0 secrets/cert.pem         # Linux

base64 -i secrets/key.pem | pbcopy   # macOS
base64 -w 0 secrets/key.pem          # Linux
```

**For P12 Authentication** (Alternative):
- `TENANT_ID`: your-tenant
- `XC_P12`: base64-encoded P12 file
- `XC_P12_PASSWORD`: P12 passphrase

```bash
# Generate base64-encoded P12
base64 -i tenant.p12 | pbcopy  # macOS
base64 -w 0 tenant.p12         # Linux
```

### 2. Create Workflow File

Create `.github/workflows/xc-sync.yml`:

```yaml
name: XC Group Sync

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM UTC
  workflow_dispatch:      # Manual trigger
  push:
    paths:
      - 'User-Database.csv'

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install -e .

      - name: Decode credentials
        run: |
          echo "${{ secrets.XC_CERT }}" | base64 -d > cert.pem
          echo "${{ secrets.XC_CERT_KEY }}" | base64 -d > key.pem

      - name: Sync groups (dry-run on PR)
        env:
          TENANT_ID: ${{ secrets.TENANT_ID }}
          VOLT_API_CERT_FILE: cert.pem
          VOLT_API_CERT_KEY_FILE: key.pem
        run: |
          if [ "${{ github.event_name }}" == "pull_request" ]; then
            xc_user_group_sync sync --csv User-Database.csv --dry-run
          else
            xc_user_group_sync sync --csv User-Database.csv
          fi
```

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
    VOLT_API_CERT_FILE: cert.pem
    VOLT_API_CERT_KEY_FILE: key.pem
  run: |
    xc_user_group_sync sync --csv User-Database.csv --prune
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
- Rotate certificates periodically
- Use environment-specific secrets for production/staging

**Audit Trail**:
- GitHub Actions logs provide complete execution history
- Review logs regularly for unexpected changes
- Enable branch protection for production workflows

## Related Documentation

- [Deployment Guide](deployment-guide.md) - Overview of all deployment scenarios
- [Operational Workflows](../implementation/workflows.md) - Step-by-step operational procedures
- [Jenkins Guide](jenkins-guide.md) - Alternative CI/CD with Jenkins
- [Troubleshooting Guide](troubleshooting-guide.md) - Common issues and resolutions
- [Testing Strategy](../implementation/testing-strategy.md) - Validation approaches
