# CI/CD Integration Samples

This directory contains sample configurations for integrating F5 XC User and Group Sync into your CI/CD pipelines. These are **reference implementations** - you should review and customize them for your specific environment before use.

## Available Samples

### GitHub Actions Integration

Located in `github-actions/`:

- **`xc-user-group-sync.yml.sample`** - Main sync workflow
  - Runs dry-run on push to main (preview changes)
  - Runs apply mode on manual workflow dispatch
  - Supports both P12 and PEM certificate authentication

- **`pre-commit.yml.sample`** - Code quality checks
  - Runs linting and validation on pull requests and pushes
  - Uses pre-commit hooks for consistent code quality

### Jenkins Integration

Located in `jenkins/`:

- **`Jenkinsfile.declarative.sample`** - Declarative Pipeline syntax
  - Parameterized builds for sync mode (dry-run/apply)
  - Optional cleanup flags (groups/users)
  - Configurable CSV file path
  - Automatic credential management from Jenkins secrets

- **`Jenkinsfile.scripted.sample`** - Scripted Pipeline syntax
  - Same functionality as Declarative, alternative syntax
  - More flexible for complex logic and error handling

## Quick Start

### GitHub Actions

1. Copy the sample workflow you want to use:

    ```bash
    cp samples/ci-cd/github-actions/xc-user-group-sync.yml.sample .github/workflows/xc-user-group-sync.yml
    ```

2. Configure GitHub repository secrets:

- Go to: **Settings → Secrets and variables → Actions**
- Add required secrets:
  - `TENANT_ID` - Your F5 XC tenant ID
  - `XC_API_URL` - (Optional) F5 XC API endpoint (defaults to production if not set)
  - **Option A (PEM)**: `XC_CERT` and `XC_CERT_KEY`
  - **Option B (P12)**: `XC_P12` (base64 encoded) and `XC_P12_PASSWORD`

3. Commit and push to trigger the workflow

### Jenkins

1. Copy the sample Jenkinsfile you prefer:

    ```bash
    cp samples/ci-cd/jenkins/Jenkinsfile.declarative.sample Jenkinsfile

    # OR

    cp samples/ci-cd/jenkins/Jenkinsfile.scripted.sample Jenkinsfile
    ```

2. Configure Jenkins credentials:

- Go to: **Jenkins → Credentials → System → Global credentials**
- Add secrets with these IDs:
  - `TENANT_ID` (Secret text)
  - `XC_API_URL` (Secret text - Optional, defaults to production if not set)
  - `XC_CERT` (Secret text - PEM certificate content)
  - `XC_CERT_KEY` (Secret text - PEM private key content)

3. Create a new Pipeline job:

   - Point it to your repository
   - Configure SCM to use the Jenkinsfile
   - Run the job with parameters

## Authentication Options

Both GitHub Actions and Jenkins samples support two authentication methods:

### Option 1: PEM Certificate/Key (Recommended)

**GitHub Actions Secrets:**

```yaml
XC_CERT: |
  -----BEGIN CERTIFICATE-----
  [certificate content - full certificate data]
  -----END CERTIFICATE-----

XC_CERT_KEY: |
  -----BEGIN <TYPE> KEY-----
  [private key content - replace <TYPE> with RSA, EC, or PRIVATE]
  -----END <TYPE> KEY-----

TENANT_ID: your-tenant-id
```

**Jenkins Credentials:**

- Type: Secret text
- IDs: `XC_CERT`, `XC_CERT_KEY`, `TENANT_ID`
- Content: Raw PEM file contents (including header/footer)

### Option 2: P12 Certificate (GitHub Actions Only)

**GitHub Actions Secrets:**

```yaml
XC_P12: [base64-encoded P12 file]
XC_P12_PASSWORD: [P12 passphrase]
TENANT_ID: your-tenant-id
```

Generate base64:

```bash
base64 -w 0 your-file.p12 > xc_p12_base64.txt
```

## Environment-Specific Configuration

The tool supports targeting different F5 XC environments (production, staging, custom deployments) via the `XC_API_URL` environment variable.

### Production vs Staging

**Production (default)**:

- URL: `https://{tenant}.console.ves.volterra.io`
- Auto-detected if `XC_API_URL` not provided
- No additional configuration needed

**Staging**:

- URL: `https://{tenant}.staging.volterra.us`
- Requires explicit `XC_API_URL` configuration
- Note: May have SSL certificate issues (see local setup script warnings)

**Custom Deployments**:

- URL: Your organization's custom F5 XC endpoint
- Contact your F5 administrator for the correct URL

### CI/CD Setup for Non-Production Environments

#### GitHub Actions Configuration

Add the `XC_API_URL` secret for non-production environments:

1. Go to **Settings → Secrets and variables → Actions**
2. Add secret:
   - Name: `XC_API_URL`
   - Value: `https://your-tenant.staging.volterra.us` (or your custom endpoint)

**Example for staging**:

```yaml
XC_API_URL: https://acme-corp.staging.volterra.us
```

If `XC_API_URL` is not provided, the workflow automatically defaults to production:

```text
https://{TENANT_ID}.console.ves.volterra.io
```

#### Jenkins Configuration

Add the `XC_API_URL` credential for non-production environments:

1. Go to **Jenkins → Credentials → System → Global credentials**
2. Click **Add Credentials**
3. Configure:
   - Kind: Secret text
   - Scope: Global
   - Secret: `https://your-tenant.staging.volterra.us`  <!-- pragma: allowlist secret -->
   - ID: `XC_API_URL`
   - Description: F5 XC API URL (staging/custom)

**Note**: The credential ID **must** be `XC_API_URL` to match the Jenkinsfile configuration.

If the `XC_API_URL` credential does not exist, Jenkins will use the production endpoint.

### Local Development vs CI/CD

**Local Development** (using setup script):

- The `scripts/setup_xc_credentials.sh` script automatically detects the environment from your P12 filename
- Production: `tenant.console.ves.volterra.io.p12` → `https://tenant.console.ves.volterra.io`
- Staging: `tenant.staging.p12` → `https://tenant.staging.volterra.us`
- Writes correct `XC_API_URL` to `secrets/.env`

**CI/CD Pipelines**:

- Must explicitly configure `XC_API_URL` as a secret/credential for non-production
- Falls back to production if not provided (backward compatible)
- No automatic environment detection from certificate names

### Environment-Specific Workflows

For organizations with multiple environments, consider separate workflows:

#### GitHub Actions Multi-Environment Example

```yaml
# .github/workflows/xc-sync-staging.yml
name: XC Sync (Staging)
on:
  workflow_dispatch:
env:
  XC_API_URL: ${{ secrets.XC_API_URL_STAGING }}
  XC_TENANT_ID: ${{ secrets.TENANT_ID_STAGING }}
```

```yaml
# .github/workflows/xc-sync-production.yml
name: XC Sync (Production)
on:
  schedule:
    - cron: '0 2 * * *'
env:
  XC_TENANT_ID: ${{ secrets.TENANT_ID_PROD }}
  # XC_API_URL not set = production default
```

#### Jenkins Multi-Environment Example

Create separate Jenkins jobs or use parameters:

```groovy
parameters {
    choice(
        name: 'ENVIRONMENT',
        choices: ['production', 'staging'],
        description: 'Target F5 XC environment'
    )
}

// Then in Prepare Credentials stage:
string(
    credentialsId: params.ENVIRONMENT == 'staging' ? 'XC_API_URL_STAGING' : 'XC_API_URL_PROD',
    variable: 'XC_API_URL_VALUE',
    defaultValue: ''
)
```

### Troubleshooting Environment Configuration

**Problem**: Tool connects to production instead of staging

**Solution**: Verify `XC_API_URL` secret/credential is:

- Created with exact ID: `XC_API_URL`
- Set to correct value (e.g., `https://tenant.staging.volterra.us`)
- Accessible to the workflow/pipeline

**Problem**: SSL certificate errors with staging

**Solution**: Staging environments may have self-signed or non-standard certificates. This is expected and documented in the setup script. Contact F5 support if this blocks automation.

**Problem**: "Connection refused" or timeout errors

**Solution**:

- Verify the `XC_API_URL` format (must include `https://` and full domain)
- Ensure network access from CI/CD runners to the F5 XC endpoint
- Check firewall rules and proxy configuration

## Customization Guide

### Common Modifications

#### Change Sync Behavior

**GitHub Actions** - Edit the "Dry-run sync" or "Apply sync" steps:

```yaml
- name: Dry-run sync
  run: |
    xc_user_group_sync \
      --csv ./User-Database.csv \
      --dry-run \
      --prune \               # Add to delete users and groups not in CSV
      --log-level debug \     # Change logging verbosity
      --timeout 60 \          # Increase timeout
      --max-retries 5         # Increase retry attempts
```

**Jenkins** - Modify parameters in the Jenkinsfile:

```groovy
parameters {
    booleanParam(
        name: 'CLEANUP_GROUPS',
        defaultValue: true,    // Change default to true
        description: '...'
    )
}
```

#### Use Different CSV File

**GitHub Actions**:

```yaml
run: xc_user_group_sync --csv ./data/production-users.csv --dry-run
```

**Jenkins** - Change parameter default:

```groovy
string(
    name: 'CSV_FILE',
    defaultValue: 'data/production-users.csv',
    description: '...'
)
```

#### Add Notifications

**GitHub Actions** - Add Slack notification:

```yaml
- name: Notify Slack
  if: always()
  uses: slackapi/slack-github-action@v1
  with:
    webhook: ${{ secrets.SLACK_WEBHOOK }}
    payload: |
      {
        "text": "XC Sync Status: ${{ job.status }}"
      }
```

**Jenkins** - Add email notification in `post` block:

```groovy
post {
    failure {
        emailext (
            subject: "XC Sync Failed - ${env.JOB_NAME} #${env.BUILD_NUMBER}",
            body: "Check console output at ${env.BUILD_URL}",
            to: "ops-team@example.com"
        )
    }
}
```

#### Schedule Automatic Runs

**GitHub Actions** - Add cron schedule:

```yaml
on:
  schedule:
    - cron: '0 2 * * *'  # Run daily at 2 AM UTC
  push:
    branches: [ main ]
  workflow_dispatch: {}
```

**Jenkins** - Use Pipeline triggers:

```groovy
properties([
    pipelineTriggers([
        cron('H 2 * * *')  # Run daily at 2 AM
    ])
])
```

## Security Best Practices

### Credential Storage

- ✅ **DO**: Store credentials as secrets in GitHub/Jenkins
- ✅ **DO**: Use PEM format for Jenkins (easier to manage as text)
- ✅ **DO**: Set restrictive file permissions (600) on certificate files
- ✅ **DO**: Clean up credential files after pipeline execution
- ❌ **DON'T**: Commit credentials to repository
- ❌ **DON'T**: Print credential values in logs
- ❌ **DON'T**: Store credentials in plain text files

### Pipeline Security

- Enable dry-run by default for automatic triggers
- Require manual approval for apply mode in production
- Use separate credentials for dev/staging/production
- Implement approval gates for destructive operations (cleanup flags)
- Log all sync operations with timestamps and user attribution

### Example: Approval Gate (Jenkins)

```groovy
stage('Approval for Apply Mode') {
    when {
        expression { params.SYNC_MODE == 'apply' }
    }
    steps {
        input message: 'Approve sync to production?',
              ok: 'Apply Changes',
              submitterParameter: 'APPROVER'
    }
}
```

## Troubleshooting

### GitHub Actions Issues

**Problem**: Workflow fails with "No XC credentials found"

- **Solution**: Verify secrets are set in repository settings
- Check secret names match exactly (case-sensitive)

**Problem**: Certificate format errors

- **Solution**: Ensure PEM certificates include headers:

  ```text
  -----BEGIN CERTIFICATE-----
  -----END CERTIFICATE-----
  ```

### Jenkins Issues

**Problem**: "python3: command not found"

- **Solution**: Install Python plugin or configure Python tool in Global Tool Configuration

**Problem**: Credential binding fails

- **Solution**: Verify credential IDs match exactly in Jenkinsfile (`XC_CERT`, not `xc-cert`)

**Problem**: Permission denied on certificate files

- **Solution**: Pipeline should set `chmod 600` on certificate files after writing them

## Support

For issues with:

- **Sample configurations**: Open an issue in this repository
- **F5 XC API**: Contact F5 support or consult [F5 XC Documentation](https://docs.cloud.f5.com/docs/api)
- **Jenkins**: See [Jenkins Pipeline Documentation](https://www.jenkins.io/doc/book/pipeline/)
- **GitHub Actions**: See [GitHub Actions Documentation](https://docs.github.com/en/actions)

## Additional Resources

- [F5 XC API Reference](https://docs.cloud.f5.com/docs/api)
- [Project README](../../README.md) - Main documentation
- [Setup Script](../../scripts/setup_xc_credentials.sh) - Credential preparation helper
