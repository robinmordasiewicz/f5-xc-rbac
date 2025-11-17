# GitLab CI/CD

Automated F5 XC user/group synchronization using GitLab CI/CD pipelines.

## Setup

### 1. Configure GitLab CI/CD Variables

In your GitLab project, navigate to **Settings → CI/CD → Variables** and add:

| Variable | Value | Masked | Protected |
|----------|-------|--------|-----------|
| `TENANT_ID` | Your F5 XC tenant ID | ✓ | ✓ |
| `XC_P12` | Base64-encoded P12 certificate | ✓ | ✓ |
| `XC_P12_PASSWORD` | P12 certificate password | ✓ | ✓ |

**Encode P12 certificate**:

```bash
base64 -i your-tenant.p12 | tr -d '\n' > xc-p12-base64.txt
# Copy contents and paste into XC_P12 variable
```

### 2. Create Pipeline Configuration

Create `.gitlab-ci.yml` in your repository root:

```yaml
stages:
  - sync

variables:
  VOLT_API_P12_FILE: "/tmp/cert.p12"

sync_users_groups:
  stage: sync
  image: python:3.12-slim
  before_script:
    # Install tool
    - pip install --quiet git+https://github.com/robinmordasiewicz/f5-xc-user-group-sync.git

    # Decode P12 certificate
    - echo "$XC_P12" | base64 -d > $VOLT_API_P12_FILE
    - chmod 600 $VOLT_API_P12_FILE

    # Set environment
    - export XC_API_URL="https://${TENANT_ID}.console.ves.volterra.io"
    - export VES_P12_PASSWORD="$XC_P12_PASSWORD"

  script:
    # Dry-run for validation
    - xc_user_group_sync --csv User-Database.csv --dry-run

    # Execute sync (only on main branch)
    - |
      if [ "$CI_COMMIT_BRANCH" = "main" ]; then
        xc_user_group_sync --csv User-Database.csv
      else
        echo "Skipping sync - not on main branch"
      fi

  after_script:
    # Cleanup
    - rm -f $VOLT_API_P12_FILE

  rules:
    # Run on schedule
    - if: $CI_PIPELINE_SOURCE == "schedule"
    # Run on CSV changes
    - if: $CI_COMMIT_BRANCH == "main"
      changes:
        - User-Database.csv
    # Allow manual execution
    - when: manual

  only:
    - main
    - merge_requests

# Optional: Scheduled pipeline (Settings → CI/CD → Schedules)
# Add schedule: Daily at 2 AM UTC
```

### 3. Configure Scheduled Pipeline

In GitLab, navigate to **CI/CD → Schedules** and add:

- **Description**: Daily User Sync
- **Interval Pattern**: `0 2 * * *` (daily at 2 AM UTC)
- **Target Branch**: `main`
- **Activated**: ✓

## Pipeline Behavior

- **On CSV commit to main**: Runs dry-run and sync automatically
- **On schedule**: Runs daily at configured time
- **On merge request**: Runs dry-run only for validation
- **Manual trigger**: Available in GitLab UI

## Corporate Proxy Support

If your GitLab runner is behind a corporate proxy, add these variables:

| Variable | Value | Masked |
|----------|-------|--------|
| `HTTP_PROXY` | `http://proxy.example.com:8080` | - |
| `HTTPS_PROXY` | `http://proxy.example.com:8080` | - |
| `REQUESTS_CA_BUNDLE` | `/path/to/ca-bundle.crt` | - |

## Troubleshooting

**Pipeline fails with SSL error**:
- Verify P12 certificate is base64-encoded correctly
- Check `XC_P12_PASSWORD` is correct
- See [Troubleshooting Guide](../troubleshooting.md#issue-4-corporate-proxy-and-mitm-ssl-interception)

**Pipeline runs but no changes**:
- Check CSV format matches requirements
- Verify `TENANT_ID` is correct
- Review pipeline logs for validation errors
