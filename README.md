# F5 Distributed Cloud User and Group Sync

Automated synchronization tool for managing F5 Distributed Cloud (XC) users and groups from CSV user databases.

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Code Quality](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Test Coverage](https://img.shields.io/badge/coverage-93%25-brightgreen)](https://github.com/robinmordasiewicz/f5-xc-user-group-sync)
[![Documentation](https://img.shields.io/badge/docs-live-success)](https://robinmordasiewicz.github.io/f5-xc-user-group-sync/)

## 📖 Documentation

Complete documentation is available at **https://robinmordasiewicz.github.io/f5-xc-user-group-sync/**

The documentation includes:

- **Get Started** - Installation and quick start guide
- **Configuration** - Environment setup and authentication
- **CLI Reference** - Command-line options and usage examples
- **Development** - Contributing guidelines and code standards
- **Specifications** - Detailed system requirements and architecture

## Overview

**f5-xc-user-group-sync** reconciles F5 Distributed Cloud users and groups with your authoritative user database (exported as CSV). This enables automated user lifecycle management and group membership synchronization from existing identity sources like Active Directory or LDAP.

### Key Features

- 🔄 Automated reconciliation between CSV and F5 XC
- ✅ Pre-validates CSV data and user existence before changes
- 🔒 Safe dry-run mode to preview changes
- 🚀 CI/CD ready with sample GitHub Actions and Jenkins workflows
- 📊 Detailed reporting with comprehensive statistics
- 🔁 Automatic retry with exponential backoff
- 🎯 Optional pruning for automated cleanup
- 🧪 Well-tested: 195 tests with 93% coverage

## Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/robinmordasiewicz/f5-xc-user-group-sync.git
cd f5-xc-user-group-sync

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install
pip install -e .
```

### Setup Credentials

```bash
# Automated setup (recommended)
./scripts/setup_xc_credentials.sh --p12 ~/Downloads/your-tenant.p12
```

### Basic Usage

```bash
# Load credentials
source secrets/.env

# Preview changes (dry-run)
xc_user_group_sync --csv ./User-Database.csv --dry-run

# Apply synchronization
xc_user_group_sync --csv ./User-Database.csv

# Full reconciliation with pruning
xc_user_group_sync --csv ./User-Database.csv --prune
```

**⚠️ Important**: Always test with `--dry-run` first. The `--prune` flag will permanently delete F5 XC users and groups not in your CSV.

## CSV Format

Your CSV must include these columns:

- `Login ID` - User's LDAP DN (e.g., `CN=USER001,OU=Users,DC=example,DC=com`)
- `Email` - User's email matching F5 XC profile
- `Entitlement Attribute` - Must be `memberOf`
- `Entitlement Display Name` - Group LDAP DN (e.g., `CN=ADMINS,OU=Groups,DC=example,DC=com`)

See the [Configuration Guide](https://robinmordasiewicz.github.io/f5-xc-user-group-sync/configuration/) for complete CSV format specifications.

## CI/CD Integration

Sample workflows available in `samples/ci-cd/`:

- **GitHub Actions** - Automated sync workflows with secrets management
- **Jenkins** - Declarative and scripted pipeline samples

See the [CI/CD samples README](samples/ci-cd/README.md) for detailed setup instructions.

## Support

- **Documentation**: https://robinmordasiewicz.github.io/f5-xc-user-group-sync/
- **Issues**: https://github.com/robinmordasiewicz/f5-xc-user-group-sync/issues
- **F5 XC API**: https://docs.cloud.f5.com/docs/api

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Code quality checks
black src/ tests/
ruff check src/ tests/
mypy src/

# All pre-commit hooks
pre-commit run --all-files
```

See [CLAUDE.md](CLAUDE.md) for detailed development guidelines.

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

**Maintainer**: Robin Mordasiewicz
**Python**: 3.9+ (tested on 3.12)
**Status**: Active Development
