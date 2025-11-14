# Development Guide

> **Last Updated**: 2025-11-14
> **Version**: 1.0.0

## Overview

Welcome to the F5 XC User and Group Sync development guide. This document provides an overview of the development environment and links to detailed guides for contributors.

## Quick Navigation

| Guide | Purpose | Audience |
|-------|---------|----------|
| **[Contributing](contributing.md)** | Contribution workflow and guidelines | New contributors, open source developers |
| **[Quality Standards](quality-standards.md)** | Code quality requirements and enforcement | All developers |
| **[Testing](testing.md)** | Testing practices and requirements | Developers writing/running tests |

## Development Setup

### Prerequisites

Complete the base installation from [Getting Started](get-started.md#installation) guide first.

### Additional Development Setup

```bash
# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks (REQUIRED before first commit)
pre-commit install

# Verify installation
pre-commit run --all-files
```

**Note**: The `[dev]` extra includes testing tools (pytest, coverage), code quality tools (black, ruff, mypy), and pre-commit hooks.

## Development Commands

```bash
# Run tests
pytest tests/ -v

# Code quality checks
black src/ tests/
ruff check src/ tests/
mypy src/

# All quality checks (what pre-commit runs)
pre-commit run --all-files
```

For coverage reports and detailed testing options, see the [Testing Guide](testing.md).

## Quick Start for Contributors

1. **Fork and clone** the repository
2. **Install dependencies**: `pip install -e ".[dev]"`
3. **Setup pre-commit**: `pre-commit install`
4. **Create branch**: `git checkout -b 123-feature-name`
5. **Make changes** and add tests
6. **Run checks**: `pre-commit run --all-files`
7. **Commit**: Git hooks will run automatically
8. **Push and create** pull request

See [Contributing Guide](contributing.md) for detailed workflow.

## Project Structure

```text
f5-xc-user-group-sync/
├── src/xc_user_group_sync/       # Main package
│   ├── cli.py                     # Command-line interface
│   ├── client.py                  # F5 XC API client
│   ├── sync_service.py            # Group synchronization
│   ├── user_sync_service.py       # User synchronization
│   ├── models.py                  # Data models
│   ├── protocols.py               # Repository interfaces
│   ├── ldap_utils.py              # LDAP utilities
│   └── user_utils.py              # User utilities
├── tests/                         # Test suite
│   ├── unit/                      # Unit tests
│   └── integration/               # Integration tests
├── scripts/                       # Utility scripts
├── samples/ci-cd/                 # CI/CD samples
├── docs/                          # Documentation
└── pyproject.toml                 # Project metadata
```

## Key Principles

### Code Quality

- **Zero Tolerance**: All pre-commit checks must pass
- **Automated Enforcement**: Local hooks + CI/CD validation
- **No Bypassing**: Never use `--no-verify` or skip hooks

### Testing

- **Coverage**: Maintain ≥80% overall, ≥90% for new code
- **Comprehensive**: Unit, integration, CLI, edge cases
- **Fast**: Quick feedback loop for developers

### Security

- **Secret Detection**: Automated scanning for credentials
- **Dependency Auditing**: Regular vulnerability checks
- **Static Analysis**: Bandit security scanning

## Related Documentation

- **[Contributing](contributing.md)** - Detailed contribution workflow
- **[Quality Standards](quality-standards.md)** - Code quality enforcement details
- **[Testing](testing.md)** - Comprehensive testing guide
- **[Getting Started](get-started.md)** - Installation and basic setup
- **[CLI Reference](cli-reference.md)** - Command-line usage
- **[Operations Guide](operations-guide.md)** - Production operations
