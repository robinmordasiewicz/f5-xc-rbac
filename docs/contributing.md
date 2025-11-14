# Contributing Guide

> **Audience**: Contributors, Open Source Developers
> **Last Updated**: 2025-11-14

## Overview

Thank you for your interest in contributing to F5 XC User and Group Sync! This guide will help you get started with the contribution process, from setting up your development environment to submitting pull requests.

## Getting Started

### Prerequisites

1. Complete the [Development Setup](development.md#development-setup)
2. Familiarize yourself with the [Quality Standards](quality-standards.md)
3. Review the [Testing Guide](testing.md)

### First-Time Setup

```bash
# Fork and clone your fork
git clone https://github.com/YOUR_USERNAME/f5-xc-user-group-sync.git
cd f5-xc-user-group-sync

# Add upstream remote
git remote add upstream https://github.com/robinmordasiewicz/f5-xc-user-group-sync.git

# Complete development setup
pip install -e ".[dev]"
pre-commit install
```

## Development Workflow

### 1. Create Feature Branch

Branch naming convention: `###-feature-name` (issue number + descriptive name)

```bash
git checkout main
git pull upstream main
git checkout -b 123-add-saml-support
```

### 2. Make Changes

- Write code with real-time linting feedback
- Follow existing code patterns and style
- Add/update tests for your changes
- Update documentation as needed

### 3. Run Quality Checks

```bash
# Run all pre-commit checks
pre-commit run --all-files

# Run tests with coverage
pytest tests/ --cov=xc_user_group_sync

# Individual quality checks
black src/ tests/
ruff check src/ tests/
mypy src/
```

### 4. Commit Changes

```bash
git add .
git commit -m "Add SAML authentication support

Implements SAML SSO integration with configurable IdP.
Includes comprehensive tests and documentation.

Fixes #123"
```

**Note**: Pre-commit hooks run automatically and must pass before commit completes.

### 5. Push and Create Pull Request

```bash
git push origin 123-add-saml-support
```

Then create a pull request on GitHub with:
- Clear description of changes
- Link to related issue(s)
- Any breaking changes highlighted
- Screenshots/examples if applicable

### 6. Address Review Feedback

```bash
# Make requested changes
git add .
git commit -m "Address review feedback"
git push origin 123-add-saml-support
```

## Contribution Guidelines

### Code Standards

✅ **DO**:
- Follow existing code patterns and conventions
- Write comprehensive tests (maintain 80%+ coverage)
- Update documentation for user-facing changes
- Keep commits atomic and well-described
- Reference issue numbers in commits
- Run all quality checks before committing

❌ **DON'T**:
- Bypass pre-commit hooks (`--no-verify`)
- Commit directly to `main` branch
- Force-push to shared branches
- Mix unrelated changes in single PR
- Leave failing tests or quality checks

### Testing Requirements

- **Unit tests** for all new functions/methods
- **Integration tests** for API interactions
- **CLI tests** for command-line changes
- Maintain minimum **80% code coverage**
- All tests must pass before PR approval

See [Testing Guide](testing.md) for detailed information.

### Documentation Requirements

Update documentation for:
- New features or functionality
- Changed CLI options or behavior
- New configuration options
- Breaking changes
- Security considerations

## Forbidden Patterns

These actions are **strictly prohibited**:

- ❌ `git commit --no-verify` - Bypassing pre-commit hooks
- ❌ `SKIP=hook-name git commit` - Selectively skipping hooks
- ❌ Committing directly to `main` branch
- ❌ Force-pushing to shared branches (`git push --force`)

**Why**: These patterns bypass quality gates and can introduce bugs or security issues.

## Pull Request Process

### PR Requirements

Before submitting:
1. ✅ All pre-commit checks passing locally
2. ✅ All tests passing with adequate coverage
3. ✅ Documentation updated
4. ✅ Commits follow naming conventions
5. ✅ PR description is clear and complete

### CI Validation

GitHub Actions will automatically:
1. Run all pre-commit checks
2. Execute full test suite
3. Verify code coverage (≥90% for new code)
4. Validate build process
5. Check for security issues

**All checks must pass** before PR can be merged.

### Review Process

1. Automated checks run first
2. Maintainer reviews code and design
3. Feedback provided via PR comments
4. Contributor addresses feedback
5. Final approval and merge

## Common Issues

### Pre-commit Hooks Not Running

```bash
# Reinstall hooks
pre-commit uninstall
pre-commit install
pre-commit run --all-files
```

### Hook Version Conflicts

```bash
# Clear cache and reinstall
pre-commit clean
pre-commit install-hooks
```

### Test Failures

```bash
# Run specific test file for debugging
pytest tests/unit/test_sync_service.py -v

# Run with debug output
pytest tests/ -vv --tb=short
```

### Coverage Below Threshold

```bash
# Generate HTML coverage report
pytest --cov=xc_user_group_sync --cov-report=html
open htmlcov/index.html

# Focus on uncovered areas
pytest --cov=xc_user_group_sync --cov-report=term-missing
```

## Getting Help

- **Questions**: Open a GitHub issue with `question` label
- **Bugs**: Check existing issues before opening new ones
- **Feature Requests**: Discuss in issue before implementing
- **Documentation**: Improvements always welcome!

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

## Related Documentation

- [Development Guide](development.md) - Development environment setup
- [Quality Standards](quality-standards.md) - Code quality requirements
- [Testing Guide](testing.md) - Testing practices and requirements
