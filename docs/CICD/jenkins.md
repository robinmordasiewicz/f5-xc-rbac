# Jenkins

Automated F5 XC user/group synchronization using Jenkins pipelines.

## Setup

### 1. Configure Jenkins Credentials

Navigate to **Manage Jenkins → Manage Credentials** and add:

| Credential Type | ID | Value |
|-----------------|-----|-------|
| Secret text | `xc-tenant-id` | Your F5 XC tenant ID |
| Secret file | `xc-p12` | Upload P12 certificate file |
| Secret text | `xc-p12-password` | P12 certificate password |

### 2. Create Jenkinsfile

Create `Jenkinsfile` in your repository:

```groovy
pipeline {
  agent any

  triggers {
    cron('H 2 * * *')  // Daily at 2 AM
  }

  environment {
    TENANT_ID = credentials('xc-tenant-id')
    VOLT_API_P12_FILE = credentials('xc-p12')
    VES_P12_PASSWORD = credentials('xc-p12-password')
    XC_API_URL = "https://${env.TENANT_ID}.console.ves.volterra.io"
  }

  stages {
    stage('Setup') {
      steps {
        sh '''
          python3 -m venv .venv
          . .venv/bin/activate
          pip install git+https://github.com/robinmordasiewicz/f5-xc-user-group-sync.git
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

    stage('Sync') {
      when {
        branch 'main'
      }
      steps {
        sh '''
          . .venv/bin/activate
          xc_user_group_sync --csv User-Database.csv
        '''
      }
    }
  }

  post {
    always {
      archiveArtifacts artifacts: '*.log', allowEmptyArchive: true
    }
    failure {
      emailext (
        subject: "XC Sync Failed: ${env.JOB_NAME} ${env.BUILD_NUMBER}",
        body: "Check ${env.BUILD_URL}",
        to: 'ops-team@example.com'
      )
    }
  }
}
```

## Pipeline Behavior

- **Schedule**: Runs daily at 2 AM
- **Dry-Run**: Always validates before sync (all branches)
- **Sync**: Only executes on `main` branch
- **Logs**: Archived automatically for audit trail
- **Notifications**: Email sent on failure

## Corporate Proxy Support

Add proxy environment variables to the pipeline:

```groovy
environment {
  TENANT_ID = credentials('xc-tenant-id')
  VOLT_API_P12_FILE = credentials('xc-p12')
  VES_P12_PASSWORD = credentials('xc-p12-password')
  XC_API_URL = "https://${env.TENANT_ID}.console.ves.volterra.io"
  HTTPS_PROXY = 'http://proxy.example.com:8080'
  REQUESTS_CA_BUNDLE = '/etc/ssl/certs/ca-bundle.crt'
}
```

Or use Jenkins credentials for proxy URL:

```groovy
environment {
  // ... existing credentials ...
  HTTPS_PROXY = credentials('proxy-url')
  REQUESTS_CA_BUNDLE = credentials('ca-bundle-path')
}
```

## Troubleshooting

**Build fails with SSL error**:
- Verify P12 certificate uploaded correctly to Jenkins
- Check `xc-p12-password` matches certificate
- See [Troubleshooting Guide](../troubleshooting.md#issue-4-corporate-proxy-and-mitm-ssl-interception)

**Sync stage skipped**:
- Verify pipeline runs on `main` branch
- Check branch protection settings
- Review Jenkins build logs

**Python not found**:
- Ensure Jenkins agent has Python 3.10+
- Install Python on Jenkins agents
- Update agent configuration
