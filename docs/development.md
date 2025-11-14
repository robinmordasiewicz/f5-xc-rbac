# Development Guide

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

# Install pre-commit hooks
pre-commit install
```

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

## Code Quality Standards

This project enforces:

- **Black** - Code formatting (line length: 88)
- **Ruff** - Fast Python linter (PEP 8, import sorting)
- **MyPy** - Static type checking
- **pytest** - Testing framework (minimum 80% coverage, currently 93%)
- **pre-commit** - Git hooks for automated checks

## Testing

**Test Coverage**: 195 tests with 93.13% code coverage

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

## Contributing Guidelines

1. **Create feature branch** from `main`
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

6. **Submit pull request** with clear description

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
