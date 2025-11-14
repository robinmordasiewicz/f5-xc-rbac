# F5 Distributed Cloud User and Group Sync

Automated synchronization tool for managing F5 Distributed Cloud (XC) users and groups from CSV user databases.

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Code Quality](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Test Coverage](https://img.shields.io/badge/coverage-93%25-brightgreen)](https://github.com/robinmordasiewicz/f5-xc-user-group-sync)
[![Documentation](https://img.shields.io/badge/docs-live-success)](https://robinmordasiewicz.github.io/f5-xc-user-group-sync/)

## 📖 Documentation

**Complete documentation:** https://robinmordasiewicz.github.io/f5-xc-user-group-sync/

## Overview

Reconciles F5 Distributed Cloud users and groups with your authoritative user database (CSV). Enables automated user lifecycle management and group membership synchronization from identity sources like Active Directory or LDAP.

### Key Features

- 🔄 Automated reconciliation between CSV and F5 XC
- ✅ Pre-validates CSV data before changes
- 🔒 Safe dry-run mode
- 🚀 CI/CD ready (GitHub Actions, Jenkins)
- 🧪 Well-tested: 195 tests, 93% coverage

## Quick Start

```bash
# Installation
git clone https://github.com/robinmordasiewicz/f5-xc-user-group-sync.git
cd f5-xc-user-group-sync
python3 -m venv .venv && source .venv/bin/activate
pip install -e .

# Setup credentials
./scripts/setup_xc_credentials.sh --p12 ~/Downloads/your-tenant.p12

# Run
source secrets/.env
xc_user_group_sync --csv ./User-Database.csv --dry-run
xc_user_group_sync --csv ./User-Database.csv
```

**See the [documentation](https://robinmordasiewicz.github.io/f5-xc-user-group-sync/) for complete installation, configuration, and usage instructions.**

## Support

- **Documentation**: https://robinmordasiewicz.github.io/f5-xc-user-group-sync/
- **Issues**: https://github.com/robinmordasiewicz/f5-xc-user-group-sync/issues

## License

MIT License - see [LICENSE](LICENSE) file.

---

**Maintainer**: Robin Mordasiewicz | **Python**: 3.9+ | **Status**: Active Development
