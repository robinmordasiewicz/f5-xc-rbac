# F5 Distributed Cloud User and Group Sync - Development Guidelines

## Active Technologies

- Python 3.9+ (target: Python 3.12)

## Project Structure

```text
src/
  xc_user_group_sync/
    cli.py          # CLI entry point
    client.py       # F5 XC API client
    sync_service.py # Group synchronization
    user_sync_service.py # User synchronization
tests/
  unit/           # Unit tests
  integration/    # Integration tests
samples/
  ci-cd/          # CI/CD samples (GitHub Actions, Jenkins)
specs/            # Feature specifications
```

## Commands

### Development Commands

```bash
# Install in development mode
pip install -e .

# Run tests
pytest tests/ -v

# Code quality checks
ruff check .
black .
mypy src/

# Run the tool
xc_user_group_sync --csv User-Database.csv --dry-run
xc_user_group_sync --csv User-Database.csv  # Syncs both groups and users by default
xc_user_group_sync --csv User-Database.csv --prune  # Full reconciliation with cleanup
```

### CLI Usage

**Default behavior**: Synchronizes both users and groups
**Pruning**: Add `--prune` flag to delete resources not in CSV
**Dry-run**: Always test with `--dry-run` before applying changes

## Code Style

Python 3.9+ (target: Python 3.12): Follow standard conventions

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
