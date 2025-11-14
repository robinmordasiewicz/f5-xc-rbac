# Code Quality Standards

> **Audience**: Contributors, Developers
> **Last Updated**: 2025-11-14

## Overview

This document defines mandatory code quality standards enforced through automated tooling. All development work must adhere to these requirements to ensure code quality, security, and maintainability.

**Key Principle**: All pre-commit checks MUST be enforced locally AND in CI/CD pipelines with zero tolerance for violations.

## Formatting Requirements

**FR-DEV-001**: Pre-commit hooks enforce consistent code formatting:

### Python Formatting

- **Tool**: Black formatter
- **Line Length**: 88 characters (Black default)
- **Check**: `black --check src/ tests/`
- **Fix**: `black src/ tests/`

### Shell Script Formatting

- **Tool**: shfmt
- **Style**: 2-space indent, case indent
- **Check**: `shfmt -i 2 -ci -d scripts/`
- **Fix**: `shfmt -i 2 -ci -w scripts/`

### General File Formatting

- **Line Endings**: LF (Unix) enforced across all text files
- **End-of-File**: All files end with single newline
- **Trailing Whitespace**: Automatically removed
- **EditorConfig**: All files comply with `.editorconfig` rules

**Enforcement**: Pre-commit hook runs before every commit; CI blocks PRs on violations.

## Linting Requirements

**FR-DEV-002**: Comprehensive linting standards enforced:

### Python Linting

- **Tool**: Ruff linter (strict mode)
- **Mode**: No autofix in CI
- **Check**: `ruff check src/ tests/`
- **Fix**: `ruff check --fix src/ tests/`

### Shell Script Linting

- **Tool**: ShellCheck
- **Severity**: Error level (`-S error`)
- **Check**: `shellcheck scripts/*.sh`

### Markdown Linting

- **Tool**: PyMarkdown
- **Config**: `.pymarkdown.json`
- **Check**: `pymarkdown scan docs/`

### YAML Validation

- **Tools**: `check-yaml` + `sort-simple-yaml`
- **Validation**: Syntax and structure

### JSON Validation

- **Tools**: Validation + pretty-format
- **Enforcement**: Valid JSON required

### VCS Hygiene

- **Checks**: Merge conflicts, case conflicts, large files
- **Enforcement**: Automatic detection and blocking

**Enforcement**: Zero linting errors tolerated; CI blocks PRs on any violation.

## Security Scanning

**FR-DEV-003**: Comprehensive security scanning required:

### Secret Detection

- **Tool**: detect-secrets
- **Baseline**: `.secrets.baseline`
- **Excludes**: `secrets/` directory
- **Action**: New secrets detected → PR blocked immediately

**Update Baseline** (only after manual verification):

```bash
detect-secrets scan > .secrets.baseline
git add .secrets.baseline
```

### Python Security Analysis

- **Tool**: Bandit static analysis
- **Severity Threshold**: MEDIUM or higher blocks PR
- **Configuration**: `.bandit`
- **Check**: `bandit -c .bandit -r src/`

### Dependency Vulnerability Scanning

- **Tool**: pip-audit
- **Severity Threshold**: HIGH or CRITICAL blocks PR
- **Scope**: `requirements.txt`, `pyproject.toml`
- **Check**: `pip-audit`

**Enforcement**: Any security violation immediately blocks PR merge.

## Repository Policy Gates

**FR-DEV-004**: Repository workflow policies enforced:

### Branch Protection

- **Rule**: Direct commits to `main` branch FORBIDDEN
- **Enforcement**: Pre-commit validation + CI double-check

### Branch Naming Convention

- **Pattern**: `^[0-9]+-[a-z0-9-]+$`
- **Example**: `123-fix-auth`, `456-add-feature`
- **Enforcement**: Pre-commit hook validation

### Commit Message Requirements

- **Rule**: Must reference GitHub issue
- **Format**: "Fixes #123" or "#123" in message
- **Enforcement**: Pre-commit validation

## Code Duplication (DRY)

**FR-DEV-005**: DRY principle enforcement:

### Duplication Thresholds

- **Threshold**: Duplicate blocks ≥15 lines in ≥2 locations
- **Scanner**: jscpd
- **Config**: `.jscpd.json`
- **Scope**: Python, Shell, YAML, Markdown files

### Handling False Positives

If duplication is intentional and necessary:
1. Document why duplication is necessary
2. Add to exclusions in `.jscpd.json`
3. Get approval in PR review

**Enforcement**: Any duplication violation blocks PR merge.

## GitHub Actions Linting

**FR-DEV-006**: Workflow validation required:

### Workflow Validation

- **Tool**: actionlint
- **Scope**: All `.github/workflows/*.yml` files
- **Validation**: Syntax, action versions, job dependencies
- **Check**: `actionlint .github/workflows/`

**Enforcement**: Any actionlint violation blocks PR merge.

## CI/CD Integration

### Local-CI Parity

**FR-DEV-007**: CI mirrors ALL pre-commit checks with identical versions:

| Check | Configuration | Status |
|-------|--------------|--------|
| Black | `.pre-commit-config.yaml` | ✅ Required |
| Ruff | `.pre-commit-config.yaml` | ✅ Required |
| ShellCheck | `.pre-commit-config.yaml` | ✅ Required |
| PyMarkdown | `.pre-commit-config.yaml` | ✅ Required |
| detect-secrets | `.pre-commit-config.yaml` | ✅ Required |
| Bandit | `.pre-commit-config.yaml` | ✅ Required |
| pip-audit | `.pre-commit-config.yaml` | ✅ Required |
| actionlint | `.pre-commit-config.yaml` | ✅ Required |
| jscpd | `.pre-commit-config.yaml` | ✅ Required |

**Enforcement**: CI runs `pre-commit run --all-files`; any failure blocks PR merge.

### PR Blocking Requirements

**FR-DEV-008**: GitHub Actions block PR merges on ANY pre-commit check failure:

- **Workflow**: `.github/workflows/pre-commit.yml` (required status check)
- **Trigger**: Every PR commit
- **Behavior**: Any failure = PR blocked
- **Branch Protection**: `main` requires "pre-commit" status check

### CI Workflow Stages

**Stage 1: Pre-commit Validation** (required, blocking)
- Run: `pre-commit run --all-files`
- Fail-Fast: true
- Blocks: Merge

**Stage 2: Unit Tests** (required, blocking)
- Run: `pytest tests/unit/`
- Coverage: ≥90% required
- Blocks: Merge

**Stage 3: Integration Tests** (required, blocking)
- Run: `pytest tests/integration/`
- Blocks: Merge

**Stage 4: Build Validation** (required, blocking)
- Run: `pip install -e .`
- Validate: Package installs successfully
- Blocks: Merge

## Configuration Files

All quality standards are configured through these files:

- **Pre-commit**: `.pre-commit-config.yaml`
- **PyMarkdown**: `.pymarkdown.json`
- **Bandit**: `.bandit`
- **jscpd**: `.jscpd.json`
- **EditorConfig**: `.editorconfig`
- **Secrets Baseline**: `.secrets.baseline`

## Running Quality Checks

### All Checks

```bash
# Run everything (what CI runs)
pre-commit run --all-files
```

### Individual Checks

```bash
# Code formatting
black src/ tests/

# Linting
ruff check src/ tests/

# Type checking
mypy src/

# Security scanning
bandit -c .bandit -r src/
detect-secrets scan

# Shell scripts
shellcheck scripts/*.sh
shfmt -i 2 -ci -d scripts/

# Markdown
pymarkdown scan docs/
```

## Troubleshooting

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

### False Positive in detect-secrets

```bash
# Update baseline (only if verified safe)
detect-secrets scan > .secrets.baseline
git add .secrets.baseline
```

### jscpd Duplication False Positive

- Refactor code to eliminate duplication, or
- Document why duplication is necessary
- Add to exclusions in `.jscpd.json`

## Related Documentation

- [Contributing Guide](contributing.md) - Contribution workflow and guidelines
- [Testing Guide](testing.md) - Testing requirements and practices
- [Development Guide](development.md) - Development environment setup
