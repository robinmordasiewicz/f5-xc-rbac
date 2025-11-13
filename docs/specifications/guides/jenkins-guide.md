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

Navigate to: `Manage Jenkins → Manage Credentials → (select domain) → Add Credentials`

Create the following credentials:

**For PEM Certificate Authentication**:

1. **TENANT_ID**
   - Kind: `Secret text`
   - ID: `xc-tenant-id`
   - Secret: `your-tenant` <!-- pragma: allowlist secret -->

2. **XC_CERT**
   - Kind: `Secret file`
   - ID: `xc-cert`
   - File: Upload `cert.pem`

3. **XC_CERT_KEY**
   - Kind: `Secret file`
   - ID: `xc-cert-key`
   - File: Upload `key.pem`

**For P12 Authentication** (Alternative):
1. **TENANT_ID** (same as above)
2. **XC_P12**
   - Kind: `Secret file`
   - ID: `xc-p12`
   - File: Upload `tenant.p12`
3. **XC_P12_PASSWORD**
   - Kind: `Secret text`
   - ID: `xc-p12-password`
   - Secret: `passphrase` <!-- pragma: allowlist secret -->

### 2. Create Jenkins Pipeline

Create `Jenkinsfile` in repository root:

```groovy
pipeline {
  agent any

  triggers {
    cron('H 2 * * *')  // Daily at 2 AM
  }

  environment {
    TENANT_ID = credentials('xc-tenant-id')
    VOLT_API_CERT_FILE = credentials('xc-cert')
    VOLT_API_CERT_KEY_FILE = credentials('xc-cert-key')
  }

  stages {
    stage('Setup') {
      steps {
        sh '''
          python3 -m venv .venv
          . .venv/bin/activate
          pip install -e .
        '''
      }
    }

    stage('Dry-Run') {
      steps {
        sh '''
          . .venv/bin/activate
          xc_user_group_sync sync --csv User-Database.csv --dry-run
        '''
      }
    }

    stage('Sync') {
      when {
        branch 'main'
      }
      steps {
        sh '''
          . .venv/bin/activate
          xc_user_group_sync sync --csv User-Database.csv
        '''
      }
    }
  }

  post {
    always {
      archiveArtifacts artifacts: 'logs/*.log', allowEmptyArchive: true
    }
    failure {
      emailext (
        subject: "XC Group Sync Failed",
        body: "Sync operation failed. Check Jenkins logs.",
        to: "ops-team@example.com"
      )
    }
  }
}
```

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
      xc_user_group_sync sync --csv User-Database.csv --prune
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
    VOLT_API_CERT_FILE = credentials("xc-cert-${params.ENVIRONMENT}")
    VOLT_API_CERT_KEY_FILE = credentials("xc-cert-key-${params.ENVIRONMENT}")
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
          xc_user_group_sync sync --csv User-Database.csv --dry-run
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
- [Operational Workflows](../implementation/workflows.md) - Step-by-step operational procedures
- [GitHub Actions Guide](github-actions-guide.md) - Alternative CI/CD with GitHub Actions
- [Troubleshooting Guide](troubleshooting-guide.md) - Common issues and resolutions
- [Testing Strategy](../implementation/testing-strategy.md) - Validation approaches
