---
title: Deployment Guide
last_updated: 2025-11-13
version: 1.0.0
status: Production Ready
audience: DevOps Engineers, Platform Engineers, System Administrators
---

## Overview

This document provides an overview of deployment scenarios for F5 XC User and Group Sync tool, ranging from manual execution for development and testing to automated CI/CD pipelines for production environments. Choose the deployment method that best fits your infrastructure, automation requirements, and operational constraints.

## Deployment Scenarios

### Manual Execution (Development/Testing)

**Use Case**: Developers and IAM admins running tool manually for testing or one-off operations

**Setup**:

```bash
# Install locally
git clone <repo>
cd f5-xc-user-group-sync
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

# Configure credentials
./scripts/setup_xc_credentials.sh --p12 ~/Downloads/tenant.p12

# Run manually
xc_user_group_sync sync --csv User-Database.csv --dry-run
```

**Pros**:

- Simple setup
- Direct control
- Easy debugging
- Immediate feedback

**Cons**:
- Manual execution required
- No scheduling
- Requires local Python environment
- Credential management on individual machines

**Best For**: Development, testing, troubleshooting, one-off operations

**Detailed Guide**: See [Operations Guide](../operations-guide.md) for step-by-step manual execution procedures.

---

### Cron Job (Linux Server)

**Use Case**: Scheduled execution on dedicated Linux server

**Setup Summary**:

1. Install on server in `/opt/xc-group-sync`
2. Create wrapper script for logging and error handling
3. Configure cron for scheduled execution (daily/weekly)
4. Set up log rotation and email notifications

**Pros**:
- Simple, reliable scheduling
- No external dependencies
- Full control over execution environment
- Suitable for isolated/air-gapped environments
- Low resource overhead

**Cons**:
- Manual server maintenance
- Need to manage log rotation
- Limited visibility/monitoring
- No built-in retry on server failures

**Best For**: On-premise deployments, air-gapped environments, simple scheduled execution

**Detailed Guide**: See [Operations Guide](../operations-guide.md) for complete cron setup instructions.

---

### GitHub Actions (Recommended for GitHub Users)

**Use Case**: Automated synchronization triggered by CSV commits or scheduled runs

**Setup Summary**:

1. Configure GitHub repository secrets (TENANT_ID, XC_CERT, XC_CERT_KEY)
2. Create workflow file `.github/workflows/xc-sync.yml`
3. Configure triggers (schedule, CSV commits, manual dispatch)
4. Enable dry-run for pull requests

**Workflow Behavior**:
- **Scheduled**: Runs daily at 2 AM UTC automatically
- **On CSV Change**: Triggers when User-Database.csv committed to repository
- **Manual**: Can be triggered manually via GitHub Actions UI
- **Pull Request**: Runs dry-run for PR validation

**Pros**:
- Fully automated
- Integrated with GitHub workflow
- Scheduled execution
- No server maintenance
- Built-in secrets management
- Execution logs in GitHub Actions

**Cons**:
- Requires GitHub repository
- GitHub Actions minutes consumption
- CSV must be committed to repo (consider security)

**Best For**: Teams using GitHub, automated daily/weekly syncs, GitOps workflows

**Detailed Guide**: See [GitHub Actions Guide](github-actions-guide.md) for complete configuration and examples.

---

### Jenkins Pipeline

**Use Case**: Automated synchronization in Jenkins-based CI/CD environments

**Setup Summary**:

1. Configure Jenkins credentials (TENANT_ID, XC_CERT, XC_CERT_KEY)
2. Create Jenkinsfile with setup, dry-run, and sync stages
3. Configure cron trigger for scheduled runs
4. Set up post-actions for logging and notifications

**Pipeline Behavior**:
- **Scheduled**: Runs daily at 2 AM
- **Dry-Run Stage**: Always validates before sync
- **Sync Stage**: Only runs on main branch
- **Post-Actions**: Archives logs, sends email on failure

**Pros**:
- Integrated with existing Jenkins infrastructure
- Flexible scheduling and triggers
- Built-in notification system
- Can integrate with other Jenkins jobs
- Supports complex pipeline logic

**Cons**:
- Requires Jenkins server
- More complex setup than GitHub Actions
- Need to manage Jenkins agent environment

**Best For**: Organizations with existing Jenkins infrastructure, complex CI/CD pipelines

**Detailed Guide**: See [Jenkins Guide](jenkins-guide.md) for complete pipeline configuration and examples.

---

## Deployment Decision Matrix

| Criteria | Manual | Cron | GitHub Actions | Jenkins |
|----------|--------|------|----------------|---------|
| Setup Complexity | Low | Medium | Medium | High |
| Automation | None | Scheduled | Full | Full |
| Maintenance | Low | Medium | Low | Medium |
| Infrastructure | Local | Server | GitHub | Jenkins |
| Visibility | Console | Logs | GitHub UI | Jenkins UI |
| Best For | Dev/Test | On-Prem | GitHub Teams | Enterprise CI/CD |

## Related Documentation

- [Operations Guide](../operations-guide.md) - Step-by-step operational procedures
- [GitHub Actions Guide](github-actions-guide.md) - Complete GitHub Actions configuration
- [Jenkins Guide](jenkins-guide.md) - Complete Jenkins pipeline configuration
- [Troubleshooting Guide](../troubleshooting.md) - Common deployment issues and resolutions
- [Testing Strategy](../specifications/implementation/testing-strategy.md) - Validation approaches for all deployment scenarios
