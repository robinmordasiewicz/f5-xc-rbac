# Testing Guide

> **Audience**: Contributors, Developers, QA Engineers
> **Last Updated**: 2025-11-14

## Overview

This guide covers testing practices, requirements, and procedures for the F5 XC User and Group Sync project. Comprehensive testing ensures code quality, reliability, and maintainability.

## Test Coverage

**Current Status**: 195 tests with 93.13% code coverage

**Requirements**:

- Minimum **80% overall coverage** required
- New code should achieve **≥90% coverage**
- Critical paths (auth, sync, API) must have **100% coverage**

## Test Categories

Tests are organized using pytest markers for easy selection:

### Unit Tests (`unit`)

- **Purpose**: Fast tests with mocking
- **Scope**: Individual functions and methods
- **Mocking**: External dependencies mocked
- **Speed**: < 1 second per test

**Example**:

```python
@pytest.mark.unit
def test_parse_ldap_dn():
    result = parse_ldap_dn("CN=user,OU=Users,DC=example,DC=com")
    assert result["cn"] == "user"
```

### Integration Tests (`integration`)

- **Purpose**: Real component interactions
- **Scope**: Multiple components working together
- **Mocking**: Minimal or no mocking
- **Speed**: 1-5 seconds per test

**Example**:

```python
@pytest.mark.integration
def test_api_client_authentication(api_client):
    response = api_client.authenticate()
    assert response.status_code == 200
```

### CLI Tests (`cli`)

- **Purpose**: Command-line interface validation
- **Scope**: CLI argument parsing and execution
- **Runner**: CliRunner for testing

**Example**:

```python
@pytest.mark.cli
def test_sync_command_dry_run(cli_runner):
    result = cli_runner.invoke(cli, ['--csv', 'test.csv', '--dry-run'])
    assert result.exit_code == 0
```

### API Tests (`api`)

- **Purpose**: F5 XC API client functionality
- **Scope**: API request/response handling
- **Mocking**: API responses mocked

**Example**:

```python
@pytest.mark.api
def test_create_user_group(mock_api):
    result = client.create_user_group("test-group", ["user1@example.com"])
    assert result["status"] == "created"
```

### Service Tests (`service`)

- **Purpose**: Business logic validation
- **Scope**: Sync services and orchestration
- **Focus**: Algorithms and workflows

**Example**:

```python
@pytest.mark.service
def test_group_sync_creates_missing_groups(sync_service):
    result = sync_service.sync_groups(csv_data)
    assert result.created == 3
```

### Edge Case Tests (`edge_case`)

- **Purpose**: Error handling and edge cases
- **Scope**: Boundary conditions, invalid input
- **Focus**: Resilience and error messages

**Example**:

```python
@pytest.mark.edge_case
def test_sync_with_empty_csv():
    with pytest.raises(ValueError, match="CSV cannot be empty"):
        sync_service.sync_groups([])
```

### Security Tests (`security`)

- **Purpose**: Security-related functionality
- **Scope**: Auth, credential handling, validation
- **Focus**: Security vulnerabilities

**Example**:

```python
@pytest.mark.security
def test_credentials_not_logged(caplog):
    client = APIClient(cert="secret", key="secret")
    assert "secret" not in caplog.text
```

## Running Tests

### All Tests

```bash
# Run complete test suite
pytest tests/

# With verbose output
pytest tests/ -v

# With very verbose output
pytest tests/ -vv
```

### By Category

```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# Multiple categories
pytest -m "unit or integration"

# Exclude category
pytest -m "not integration"
```

### By File or Directory

```bash
# Specific test file
pytest tests/unit/test_sync_service.py

# Specific directory
pytest tests/unit/

# Specific test function
pytest tests/unit/test_sync_service.py::test_create_group
```

### With Coverage

```bash
# Coverage report in terminal
pytest --cov=xc_user_group_sync --cov-report=term

# Coverage with missing lines
pytest --cov=xc_user_group_sync --cov-report=term-missing

# HTML coverage report
pytest --cov=xc_user_group_sync --cov-report=html
open htmlcov/index.html
```

### Debug Mode

```bash
# Show print statements
pytest tests/ -s

# Stop on first failure
pytest tests/ -x

# Run last failed tests
pytest tests/ --lf

# Full traceback
pytest tests/ --tb=long
```

## Writing Tests

### Test Structure

Follow the **Arrange-Act-Assert** pattern:

```python
def test_example():
    # Arrange: Set up test data and conditions
    user_data = {"email": "test@example.com", "name": "Test User"}

    # Act: Execute the code being tested
    result = create_user(user_data)

    # Assert: Verify the expected outcome
    assert result.email == "test@example.com"
    assert result.name == "Test User"
```

### Fixtures

Use pytest fixtures for reusable test setup:

```python
@pytest.fixture
def api_client():
    """Provide configured API client for tests."""
    return APIClient(
        tenant_id="test-tenant",
        p12_file="test-cert.p12",
        p12_password="test-password"  # pragma: allowlist secret
    )

def test_with_fixture(api_client):
    result = api_client.get_user_groups()
    assert isinstance(result, list)
```

### Mocking

Use mocking to isolate units under test:

```python
from unittest.mock import Mock, patch

@patch('xc_user_group_sync.client.requests.post')
def test_api_call(mock_post):
    # Configure mock
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {"success": True}

    # Test
    result = api_client.create_group("test-group")

    # Verify
    assert result["success"] is True
    mock_post.assert_called_once()
```

### Parametrized Tests

Test multiple scenarios efficiently:

```python
@pytest.mark.parametrize("input,expected", [
    ("CN=user,DC=example,DC=com", "user"),
    ("CN=admin,OU=Users,DC=example,DC=com", "admin"),
    ("CN=test user,DC=example,DC=com", "test user"),
])
def test_extract_cn(input, expected):
    result = extract_cn_from_dn(input)
    assert result == expected
```

## Test Requirements

### For New Features

When adding new functionality:

1. ✅ **Unit tests** for all new functions/methods
2. ✅ **Integration tests** for component interactions
3. ✅ **CLI tests** if adding/modifying CLI options
4. ✅ **Edge case tests** for error handling
5. ✅ **Security tests** if touching auth/credentials

### For Bug Fixes

When fixing bugs:

1. ✅ Write **failing test** that reproduces the bug
2. ✅ Fix the bug
3. ✅ Verify test now passes
4. ✅ Add **edge case tests** to prevent regression

### Coverage Requirements

- **Overall**: Maintain ≥80% coverage
- **New code**: Achieve ≥90% coverage
- **Critical paths**: Require 100% coverage
  - Authentication flows
  - User/group synchronization
  - API client operations
  - CSV parsing and validation

## CI/CD Testing

### Automated Testing in CI

GitHub Actions runs tests automatically:

**Triggers**:

- Every commit to pull request
- Merges to main branch
- Scheduled daily runs

**Test Stages**:

1. Unit tests (must pass)
2. Integration tests (must pass)
3. Coverage check (must meet threshold)
4. Build validation (must succeed)

### Coverage Reports

Coverage reports are:

- Generated for every PR
- Displayed in PR checks
- Archived as CI artifacts
- Published to coverage service (if configured)

## Troubleshooting

### Test Failures

```bash
# Run with verbose output
pytest tests/ -vv --tb=short

# Show local variables
pytest tests/ --tb=long

# Stop on first failure
pytest tests/ -x
```

### Coverage Issues

```bash
# Show uncovered lines
pytest --cov=xc_user_group_sync --cov-report=term-missing

# Generate HTML report for analysis
pytest --cov=xc_user_group_sync --cov-report=html
open htmlcov/index.html
```

### Fixture Errors

```bash
# List all available fixtures
pytest --fixtures

# Show fixture setup/teardown
pytest tests/ --setup-show
```

### Slow Tests

```bash
# Show slowest tests
pytest tests/ --durations=10

# Profile test execution
pytest tests/ --profile
```

## Best Practices

### DO ✅

- Write tests before or alongside code (TDD)
- Use descriptive test names
- Keep tests independent and isolated
- Mock external dependencies
- Test edge cases and error conditions
- Maintain fast test execution
- Use appropriate markers for categorization

### DON'T ❌

- Skip tests to make builds pass
- Write tests that depend on other tests
- Test implementation details (test behavior)
- Ignore failing tests
- Commit without running tests locally
- Write tests that require manual setup

## Related Documentation

- [Contributing Guide](contributing.md) - Contribution workflow
- [Quality Standards](quality-standards.md) - Code quality requirements
- [Development Guide](development.md) - Development setup
