# F5 Distributed Cloud User and Group Sync

Automated synchronization tool for managing F5 Distributed Cloud (XC) users and groups from CSV user databases.

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Code Quality](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## Overview

**f5-xc-user-group-sync** is a Python command-line tool that reconciles F5 Distributed Cloud users and groups with your authoritative user database (exported as CSV). This enables automated user lifecycle management and group membership synchronization from existing identity sources like Active Directory or LDAP.

## Key Features

- **🔄 Automated Reconciliation**: Synchronizes users and groups between CSV and F5 XC
- **✅ Data Validation**: Pre-validates CSV data and user existence before making changes
- **🔒 Safe Operations**: Dry-run mode to preview changes before applying
- **🚀 CI/CD Ready**: Sample workflows for GitHub Actions and Jenkins
- **📊 Detailed Reporting**: Comprehensive statistics and error tracking
- **🔁 Retry Logic**: Automatic retry with exponential backoff for API failures
- **🎯 Flexible Control**: Optional pruning for automated cleanup
- **🧪 Well-Tested**: 195 tests with 93% code coverage

## Getting Started by Role

### 👤 First-Time Users

**Goal**: Install and run your first synchronization

1. [Installation](get-started.md#installation) - Set up the tool
2. [Setup Credentials](get-started.md#setup-credentials) - Configure F5 XC access
3. [Prepare CSV](configuration.md#csv-format) - Format your user database
4. [Quick Start](get-started.md#quick-start) - Run your first sync

**Next Steps**: [Configuration Guide](configuration.md) for advanced options

---

### 🔧 DevOps Engineers / Operators

**Goal**: Automate user synchronization in production

1. [Operations Guide](operations-guide.md) - Production workflows and best practices
2. [CI/CD Deployment](CICD/deployment-guide.md) - Automation strategies
   - [GitHub Actions](CICD/github-actions-guide.md) - Automated workflows
   - [Jenkins](CICD/jenkins-guide.md) - Pipeline integration
3. [Troubleshooting](troubleshooting.md) - Common issues and solutions
4. [CLI Reference](cli-reference.md) - Complete command options

**Next Steps**: [Operations Guide](operations-guide.md#pruning-operations) for advanced reconciliation

---

### 💻 Contributors / Developers

**Goal**: Contribute code and improvements

1. [Development Setup](development.md#development-setup) - Environment configuration
2. [Contributing Guide](contributing.md) - Workflow and guidelines
3. [Quality Standards](quality-standards.md) - Code requirements
4. [Testing Guide](testing.md) - Writing and running tests

**Next Steps**: Review [Project Structure](development.md#project-structure) and pick an issue

---

## Quick Reference

| Task | Guide | Section |
|------|-------|---------|
| Install tool | [Getting Started](get-started.md) | Installation |
| Configure credentials | [Configuration](configuration.md) | Environment Variables |
| Format CSV file | [Configuration](configuration.md) | CSV Format |
| Run first sync | [Getting Started](get-started.md) | Quick Start |
| Automate with CI/CD | [Deployment Guide](CICD/deployment-guide.md) | Scenarios |
| Troubleshoot errors | [Troubleshooting](troubleshooting.md) | Common Issues |
| Contribute code | [Contributing](contributing.md) | Development Workflow |
| Write tests | [Testing](testing.md) | Writing Tests |

## What Does It Do?

This tool performs bidirectional reconciliation between your CSV user database and F5 XC:

**Synchronization Operations:**

- ✅ **Creates** users and groups that exist in CSV but not in F5 XC
- ✅ **Updates** user attributes (name, active status) and group memberships to match CSV
- ✅ **Prunes** users and groups not in CSV (optional, with `--prune` flag)

**Safety Features:**

- ✅ **Validates** all data before making changes
- ✅ **Dry-run mode** to preview changes safely
- ✅ **Error handling** with detailed reporting
- ✅ **Transaction safety** with atomic operations

## Support

- **GitHub Repository**: [robinmordasiewicz/f5-xc-user-group-sync](https://github.com/robinmordasiewicz/f5-xc-user-group-sync)
- **Issues**: [GitHub Issues](https://github.com/robinmordasiewicz/f5-xc-user-group-sync/issues)
- **F5 XC Documentation**: [F5 Distributed Cloud Docs](https://docs.cloud.f5.com/docs/api)
