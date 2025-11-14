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

## Quick Links

- [Getting Started](get-started.md) - Installation and first steps
- [Configuration](configuration.md) - Environment setup and credentials
- [CLI Reference](cli-reference.md) - Command-line options and usage
- [Development](development.md) - Contributing and development setup

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
