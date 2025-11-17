---
title: Jenkins Pipeline Deployment Guide
last_updated: 2025-11-13
version: 1.0.0
status: Production Ready
audience: DevOps Engineers, Jenkins Users, CI/CD Engineers
---

## Overview

This guide provides complete instructions for deploying F5 XC User and Group Sync tool using Jenkins Pipeline for automated synchronization in Jenkins-based CI/CD environments. Jenkins provides flexible scheduling, complex pipeline logic, and integration with existing enterprise infrastructure.

## Use Case

**Automated synchronization in Jenkins-based CI/CD environments**

**Best For**: Organizations with existing Jenkins infrastructure, complex CI/CD pipelines

## Setup Instructions

### 1. Configure Jenkins Credentials

**Required Credentials** (see [Configuration Guide](../configuration.md#environment-variables) for variable descriptions):

Navigate to: `Manage Jenkins → Manage Credentials → (select domain) → Add Credentials`

| Credential | Kind | ID | Purpose |
|------------|------|----|---------|
| TENANT_ID | Secret text | `xc-tenant-id` | F5 XC tenant ID |
| XC_P12 | Secret file | `xc-p12` | P12/PKCS12 certificate file |
| XC_P12_PASSWORD | Secret text | `xc-p12-password` | P12 certificate password |

**Setup**: Upload your P12 file from the F5 XC Console (Administration → Credentials → API Credentials) or from `secrets/` directory after running the setup script (see [Getting Started](../get-started.md#setup-credentials)).

### 2. Create Jenkins Pipeline

Copy the example pipeline to your repository:

```bash
cp docs/CICD/examples/Jenkinsfile Jenkinsfile
```

Or create `Jenkinsfile` manually. See [Jenkinsfile](examples/Jenkinsfile) for the complete example.

**Key pipeline features**:

- Scheduled daily execution (2 AM)
- Three-stage process: Setup → Dry-Run → Sync
- Main branch protection (sync only on main)
- Automatic log archival and email notifications

## Pipeline Behavior

### Stage Execution

**Setup Stage**:

- Creates Python virtual environment
- Installs package and dependencies
- Runs for all branches and triggers

**Dry-Run Stage**:

- Always validates before sync
- Shows planned operations
- Runs for all branches and triggers
- Useful for PR validation

**Sync Stage**:

- Only runs on main branch
- Performs actual synchronization
- Skipped for feature branches and PRs

### Post-Actions

**Always**:

- Archives log files for audit trail
- Available even if pipeline fails

**On Failure**:

- Sends email notification to ops team
- Includes link to Jenkins build
- Configurable recipients and message

## Advanced Configurations

### Weekly Execution

```groovy
triggers {
  cron('H 2 * * 0')  // Weekly on Sunday at 2 AM
}
```

### Prune Operation on Schedule

```groovy
stage('Sync') {
  when {
    allOf {
      branch 'main'
      triggeredBy 'TimerTrigger'  // Only on scheduled runs
    }
  }
  steps {
    sh '''
      . .venv/bin/activate
      xc_user_group_sync --csv User-Database.csv --prune
    '''
  }
}
```

### Multi-Environment Support

```groovy
pipeline {
  agent any

  parameters {
    choice(
      name: 'ENVIRONMENT',
      choices: ['staging', 'production'],
      description: 'Target environment'
    )
  }

  environment {
    TENANT_ID = credentials("xc-tenant-id-${params.ENVIRONMENT}")
    VOLT_API_P12_FILE = credentials("xc-p12-${params.ENVIRONMENT}")
    VES_P12_PASSWORD = credentials("xc-p12-password-${params.ENVIRONMENT}")
  }

  // ... stages ...
}
```

### Parallel Validation

```groovy
stage('Validation') {
  parallel {
    stage('Lint') {
      steps {
        sh '''
          . .venv/bin/activate
          ruff check .
        '''
      }
    }
    stage('Type Check') {
      steps {
        sh '''
          . .venv/bin/activate
          mypy src/
        '''
      }
    }
    stage('Dry-Run') {
      steps {
        sh '''
          . .venv/bin/activate
          xc_user_group_sync --csv User-Database.csv --dry-run
        '''
      }
    }
  }
}
```

### Slack Notification

```groovy
post {
  failure {
    slackSend (
      color: 'danger',
      message: "XC Group Sync Failed: ${env.JOB_NAME} ${env.BUILD_NUMBER}",
      channel: '#ops-alerts'
    )
  }
  success {
    slackSend (
      color: 'good',
      message: "XC Group Sync Successful: ${env.JOB_NAME} ${env.BUILD_NUMBER}",
      channel: '#ops-notifications'
    )
  }
}
```

### Corporate Proxy Configuration

If your Jenkins agents operate behind a corporate proxy:

**Option 1: Environment Variables** (Recommended for Jenkins agents)

```groovy
environment {
  TENANT_ID = credentials('xc-tenant-id')
  VOLT_API_P12_FILE = credentials('xc-p12')
  VES_P12_PASSWORD = credentials('xc-p12-password')
  HTTP_PROXY = 'http://proxy.example.com:8080'
  HTTPS_PROXY = 'http://proxy.example.com:8080'
  NO_PROXY = 'localhost,127.0.0.1'
  REQUESTS_CA_BUNDLE = '/etc/ssl/certs/ca-bundle.crt'
}
```

**Option 2: CLI Flags** (For dynamic proxy configuration)

```groovy
stage('Sync') {
  steps {
    sh '''
      . .venv/bin/activate
      xc_user_group_sync --csv User-Database.csv \
        --proxy "http://proxy.example.com:8080" \
        --ca-bundle "/etc/ssl/certs/corporate-ca.crt"
    '''
  }
}
```

**Option 3: Jenkins Credentials** (For sensitive proxy credentials)

Add these credentials:
- ID: `proxy-url`, Kind: Secret text, Content: `http://username:password@proxy.example.com:8080`  <!-- pragma: allowlist secret -->
- ID: `ca-bundle-path`, Kind: Secret text, Content: `/path/to/corporate-ca.crt`

```groovy
environment {
  TENANT_ID = credentials('xc-tenant-id')
  VOLT_API_P12_FILE = credentials('xc-p12')
  VES_P12_PASSWORD = credentials('xc-p12-password')
  HTTPS_PROXY = credentials('proxy-url')
  REQUESTS_CA_BUNDLE = credentials('ca-bundle-path')
}
```

**Jenkins Agent Configuration**: Install corporate CA certificate on agents:

```bash
# On Jenkins agent (Ubuntu/Debian)
sudo cp /path/to/corporate-ca.crt /usr/local/share/ca-certificates/
sudo update-ca-certificates

# On Jenkins agent (RHEL/CentOS)
sudo cp /path/to/corporate-ca.crt /etc/pki/ca-trust/source/anchors/
sudo update-ca-trust
```

## Pros and Cons

### Pros

- ✅ Integrated with existing Jenkins infrastructure
- ✅ Flexible scheduling and triggers
- ✅ Built-in notification system
- ✅ Can integrate with other Jenkins jobs
- ✅ Supports complex pipeline logic

### Cons

- ❌ Requires Jenkins server
- ❌ More complex setup than GitHub Actions
- ❌ Need to manage Jenkins agent environment

## Security Considerations

**Credentials Management**:

- Use Jenkins Credentials plugin
- Rotate certificates periodically
- Use different credentials per environment
- Enable credential masking in logs

**Agent Security**:

- Ensure Jenkins agents have Python 3.9+
- Keep agents updated with security patches
- Limit agent access to production credentials
- Use dedicated agents for production pipelines

**Audit Trail**:

- Jenkins provides complete build history
- Archive logs for compliance requirements
- Review builds regularly for unexpected changes
- Enable pipeline approval for production

## Integration with Other Jenkins Jobs

### Trigger After AD Export

```groovy
pipeline {
  agent any

  triggers {
    upstream(
      upstreamProjects: 'AD-Export-Job',
      threshold: hudson.model.Result.SUCCESS
    )
  }

  // ... stages ...
}
```

### Conditional Execution Based on CSV Changes

```groovy
stage('Check CSV Changes') {
  steps {
    script {
      def changes = sh(
        script: 'git diff HEAD~1 --name-only | grep User-Database.csv',
        returnStatus: true
      )
      if (changes == 0) {
        env.CSV_CHANGED = 'true'
      }
    }
  }
}

stage('Sync') {
  when {
    environment name: 'CSV_CHANGED', value: 'true'
  }
  // ... sync steps ...
}
```

## Related Documentation

- [Deployment Guide](deployment-guide.md) - Overview of all deployment scenarios
- [Operations Guide](../operations-guide.md) - Step-by-step operational procedures
- [GitHub Actions Guide](github-actions-guide.md) - Alternative CI/CD with GitHub Actions
- [Troubleshooting Guide](../troubleshooting.md) - Common issues and resolutions
- [Testing Strategy](../specifications/implementation/testing-strategy.md) - Validation approaches
