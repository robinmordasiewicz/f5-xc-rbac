# Suggested Commands

## Development Setup

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux

# Install in editable mode with dev dependencies
pip install -e ".[dev]"
```text
## Testing

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=xc_user_group_sync --cov-report=term-missing

# Run specific test file
pytest tests/test_sync_service.py

# Run with verbose output
pytest -v

# Coverage target: 80% minimum (enforced by pytest config)
```text
## Code Quality

```bash
# Lint code with ruff
ruff check .

# Format code with black
black src/ tests/

# Auto-fix ruff issues
ruff check --fix .

# Run both formatting and linting
ruff format . && ruff check .
```text
## Running the Application

```bash
# Dry-run sync (safe, no API changes)
xc-group-sync --csv ./User-Database.csv --dry-run --log-level info

# Apply sync (create/update groups and users)
xc-group-sync --csv ./User-Database.csv --log-level info

# Apply with prune (also delete users/groups not in CSV)
xc-group-sync --csv ./User-Database.csv --prune --log-level info

# Debug mode
xc-group-sync --csv ./User-Database.csv --dry-run --log-level debug
```text
## Credential Setup

```bash
# Automated setup with .p12 file
./scripts/setup_xc_credentials.sh --p12 ~/Downloads/your-tenant.p12

# Manual extraction (if needed)
openssl pkcs12 -in tenant.p12 -clcerts -nokeys -out secrets/cert.pem
openssl pkcs12 -in tenant.p12 -nocerts -nodes -out secrets/key.pem
```text
## Git Operations (macOS/Darwin)

```bash
# Standard git commands work as expected on macOS
git status
git add .
git commit -m "message"
git push
```text
## File Operations (macOS/Darwin)

```bash
# List files
ls -la

# Find files
find . -name "*.py"

# Search in files
grep -r "pattern" .

# Change directory
cd src/xc_user_group_sync/
```text
