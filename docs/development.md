# Development Guide

> **Last Updated**: 2025-11-13
> **Version**: 1.0.0

## Overview

This guide defines mandatory development standards and provides setup instructions for contributors. All development work must adhere to these requirements to ensure code quality, security, and maintainability through automated enforcement.

**Key Principle**: All pre-commit checks MUST be enforced locally AND in CI/CD pipelines with zero tolerance for violations.

## Development Setup

```bash
# Clone and setup
git clone https://github.com/robinmordasiewicz/f5-xc-user-group-sync.git
cd f5-xc-user-group-sync

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install with development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks (REQUIRED before first commit)
pre-commit install

# Verify installation
pre-commit run --all-files
```

## Code Quality Standards

### Formatting Requirements

**FR-DEV-001**: Pre-commit hooks enforce consistent code formatting:

- **Python**: Black formatter (line length: 88, `black --check`)
- **Shell Scripts**: shfmt formatter (`shfmt -i 2 -ci`)
- **Line Endings**: LF (Unix) enforced across all text files
- **End-of-File**: All files end with single newline
- **Trailing Whitespace**: Automatically removed
- **EditorConfig**: All files comply with `.editorconfig` rules

**Enforcement**: Pre-commit hook runs before every commit; CI blocks PRs on violations.

### Linting Requirements

**FR-DEV-002**: Comprehensive linting standards enforced:

- **Python**: Ruff linter (strict mode, no autofix in CI)
- **Shell Scripts**: ShellCheck (`-S error`)
- **Markdown**: PyMarkdown (`.pymarkdown.json`)
- **YAML**: `check-yaml` + `sort-simple-yaml`
- **JSON**: Validation + pretty-format
- **VCS Hygiene**: Check merge conflicts, case conflicts, large files

**Enforcement**: Zero linting errors tolerated; CI blocks PRs on any violation.

### Security Scanning

**FR-DEV-003**: Comprehensive security scanning required:

- **Secret Detection**: `detect-secrets` with `.secrets.baseline`
    - Excludes: `secrets/` directory
    - New secrets detected: PR blocked immediately
- **Python Security**: Bandit static analysis
    - Severity threshold: MEDIUM or higher blocks PR
    - Configuration: `.bandit`
- **Dependency Vulnerabilities**: pip-audit
    - Severity threshold: HIGH or CRITICAL blocks PR
    - Runs on: `requirements.txt`, `pyproject.toml`

**Enforcement**: Any security violation immediately blocks PR merge.

### Repository Policy Gates

**FR-DEV-004**: Repository workflow policies enforced:

- **Branch Protection**: Direct commits to `main` branch FORBIDDEN
- **Branch Naming**: Must match `^[0-9]+-[a-z0-9-]+$` (e.g., `123-fix-auth`)
- **Commit Messages**: Must reference GitHub issue ("Fixes #123" or "#123")

**Enforcement**: Pre-commit validates locally; CI double-checks compliance.

### Code Duplication (DRY)

**FR-DEV-005**: DRY principle enforcement:

- **Threshold**: Duplicate blocks ≥15 lines in ≥2 locations are violations
- **Scanner**: jscpd (`.jscpd.json`)
- **Scope**: Python, Shell, YAML, Markdown files

**Enforcement**: Any duplication violation blocks PR merge.

### GitHub Actions Linting

**FR-DEV-006**: Workflow validation required:

- **Tool**: actionlint via pre-commit and CI
- **Scope**: All `.github/workflows/*.yml` files
- **Validation**: Syntax, action versions, job dependencies

**Enforcement**: Any actionlint violation blocks PR merge.

## Development Commands

```bash
# Run tests
pytest tests/ -v

# Run tests with coverage
pytest --cov=xc_user_group_sync --cov-report=html --cov-report=term

# Code formatting
black src/ tests/

# Linting
ruff check src/ tests/

# Type checking
mypy src/

# All quality checks (what pre-commit runs)
pre-commit run --all-files
```

## Testing

**Test Coverage**: 195 tests with 93.13% code coverage (minimum 80% required)

**Test Categories** (via pytest markers):

- `unit` - Fast unit tests with mocking
- `integration` - Real component interaction tests
- `cli` - Command-line interface tests
- `api` - API client functionality tests
- `service` - Business logic tests
- `edge_case` - Edge cases and error handling
- `security` - Security-related functionality

**Run Tests:**

```bash
# All tests
pytest tests/

# Specific category
pytest -m unit
pytest -m integration

# With coverage report
pytest --cov=xc_user_group_sync --cov-report=html
```

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

```yaml
- Run: pre-commit run --all-files
- Fail-Fast: true
- Blocks: Merge
```

**Stage 2: Unit Tests** (required, blocking)

```yaml
- Run: pytest tests/unit/
- Coverage: ≥90% required
- Blocks: Merge
```

**Stage 3: Integration Tests** (required, blocking)

```yaml
- Run: pytest tests/integration/
- Blocks: Merge
```

**Stage 4: Build Validation** (required, blocking)

```yaml
- Run: pip install -e .
- Validate: Package installs successfully
- Blocks: Merge
```

## Development Workflow

### Required Workflow Pattern

1. **Feature Branch**: Create branch following convention (`###-feature-name`)
2. **Local Development**: Write code with real-time linting feedback
3. **Pre-commit Check**: Hooks run automatically on `git commit`
4. **Fix Issues**: Address all hook failures before commit completes
5. **Push**: Only clean commits reach remote repository
6. **CI Validation**: GitHub Actions re-validates all checks
7. **PR Review**: Human review after automated checks pass
8. **Merge**: Only after CI success + approvals

### Forbidden Patterns

- ❌ `git commit --no-verify` (bypassing hooks)
- ❌ `SKIP=hook-name git commit` (selectively skipping hooks)
- ❌ Committing directly to `main` branch
- ❌ Force-pushing to shared branches

## Contributing Guidelines

1. **Create feature branch** from `main` (follow naming: `###-feature-name`)
2. **Write tests** for new functionality (maintain 80%+ coverage)
3. **Follow code style** (enforced by pre-commit hooks)
4. **Update documentation** for user-facing changes
5. **Run all checks** before committing:

   ```bash
   pytest tests/ --cov=xc_user_group_sync
   black src/ tests/
   ruff check src/ tests/
   mypy src/
   ```

6. **Submit pull request** with clear description and issue reference

## Troubleshooting

### Pre-commit hooks not running

```bash
# Solution: Reinstall hooks
pre-commit uninstall
pre-commit install
pre-commit run --all-files
```

### Hook version conflicts

```bash
# Solution: Clear cache and reinstall
pre-commit clean
pre-commit install-hooks
```

### False positive in detect-secrets

```bash
# Solution: Update baseline (only if verified safe)
detect-secrets scan > .secrets.baseline
git add .secrets.baseline
```

### jscpd duplication false positive

- Refactor code to eliminate duplication, or
- Document why duplication is necessary and add to exclusions in `.jscpd.json`

### Getting Help

For questions about development standards:

1. Check this document first
2. Review `.pre-commit-config.yaml` for hook configurations
3. Check CI logs for detailed error messages
4. Open GitHub issue with `question` label

## Configuration Files

- **Pre-commit**: `.pre-commit-config.yaml`
- **PyMarkdown**: `.pymarkdown.json`
- **Bandit**: `.bandit`
- **jscpd**: `.jscpd.json`
- **EditorConfig**: `.editorconfig`
- **Secrets Baseline**: `.secrets.baseline`

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

- **Setup Guide**: `../README.md`
- **CI/CD Integration**: `.github/workflows/pre-commit.yml`
