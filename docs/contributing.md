# Contributing Guide

## Setup

```bash
# Fork and clone
git clone https://github.com/YOUR_USERNAME/f5-xc-user-group-sync.git
cd f5-xc-user-group-sync

# Install with development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

## Development Workflow

### 1. Create Feature Branch

Branch naming: `###-feature-name` (issue number + description)

```bash
git checkout -b 123-add-feature
```

### 2. Make Changes

- Follow existing code patterns
- Add tests for new functionality
- Update documentation as needed

### 3. Run Quality Checks

```bash
# All pre-commit checks
pre-commit run --all-files

# Tests with coverage
pytest tests/ --cov=xc_user_group_sync
```

### 4. Commit Changes

```bash
git add .
git commit -m "Add feature description

Detailed explanation of changes.

Fixes #123"
```

Pre-commit hooks run automatically and must pass.

### 5. Push and Create PR

```bash
git push origin 123-add-feature
```

Create PR on GitHub with clear description and link to issue.

## Code Standards

### Formatting

- **Python**: Black formatter (88 char line length)
- **Shell**: shfmt with 2-space indent
- **Markdown**: PyMarkdown compliant

### Linting

- **Python**: Ruff (strict mode)
- **Shell**: ShellCheck
- **YAML/JSON**: Syntax validation

### Security

- **Secret Detection**: detect-secrets
- **Python Security**: Bandit
- **Dependencies**: pip-audit

All checks enforced via pre-commit hooks and CI.

## Testing

### Requirements

- Minimum **80% code coverage**
- All tests must pass before PR approval
- New code should achieve **90%+ coverage**

### Test Categories

```bash
# All tests
pytest tests/

# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# With coverage report
pytest --cov=xc_user_group_sync --cov-report=term-missing
```

### Writing Tests

Use **Arrange-Act-Assert** pattern:

```python
def test_example():
    # Arrange: Setup
    data = {"email": "test@example.com"}

    # Act: Execute
    result = create_user(data)

    # Assert: Verify
    assert result.email == "test@example.com"
```

## Quality Gates

### Pre-commit Hooks (Required)

All hooks must pass before commit:

- Black formatting
- Ruff linting
- ShellCheck
- PyMarkdown
- detect-secrets
- Bandit security
- EditorConfig
- jscpd (duplication check)

**Never bypass**: `--no-verify` is forbidden.

### CI Validation (Required)

GitHub Actions automatically runs:

1. All pre-commit checks
2. Full test suite
3. Coverage validation (≥90% for new code)
4. Build validation

All checks must pass before PR can merge.

## Branch Protection

- Direct commits to `main` branch **forbidden**
- Branch naming must match: `^[0-9]+-[a-z0-9-]+$`
- All PRs require passing CI checks

## Common Issues

### Pre-commit Not Running

```bash
pre-commit uninstall
pre-commit install
pre-commit run --all-files
```

### Test Failures

```bash
# Run specific test
pytest tests/unit/test_sync_service.py -v

# Debug output
pytest tests/ -vv --tb=short
```

### Coverage Below Threshold

```bash
# HTML report
pytest --cov=xc_user_group_sync --cov-report=html
open htmlcov/index.html
```

## Project Structure

```text
src/xc_user_group_sync/
  cli.py                # CLI entry point
  client.py             # F5 XC API client
  sync_service.py       # Group sync
  user_sync_service.py  # User sync
tests/
  unit/                 # Unit tests
  integration/          # Integration tests
```

## Getting Help

- **Questions**: Open GitHub issue with `question` label
- **Bugs**: Check existing issues first
- **Features**: Discuss in issue before implementing
