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
