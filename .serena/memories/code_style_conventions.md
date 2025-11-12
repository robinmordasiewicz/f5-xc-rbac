# Code Style and Conventions

## Formatting

- **Formatter**: Black
- **Line Length**: 88 characters
- **Target Version**: Python 3.12

## Linting

- **Linter**: Ruff
- **Selected Rules**:
  - `E`: pycodestyle errors
  - `F`: Pyflakes
  - `I`: isort (import sorting)

## Type Hints

- **Required**: Yes, use modern Python type hints
- **Style**: Use `from __future__ import annotations` for forward references
- **Union Types**: Use `X | None` instead of `Optional[X]` (Python 3.10+ style)
- **Protocols**: Use Protocol classes for dependency injection interfaces

## Docstrings

- **Format**: Google-style docstrings
- **Required For**:
  - All public classes
  - All public methods and functions
  - Module-level docstrings
- **Sections**: Args, Returns, Raises (when applicable)

## Naming Conventions

- **Files/Modules**: `snake_case` (e.g., `sync_service.py`)
- **Classes**: `PascalCase` (e.g., `GroupSyncService`, `XCClient`)
- **Functions/Methods**: `snake_case` (e.g., `parse_csv_to_groups`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `REQUIRED_COLUMNS`)
- **Private Members**: Prefix with single underscore (e.g., `_create_user_with_retry`)

## Code Organization

- **Source**: All code in `src/xc_rbac_sync/`
- **Tests**: All tests in `tests/` mirroring source structure
- **Test Files**: Prefix with `test_` (e.g., `test_sync_service.py`)
- **Protocol Pattern**: Use Protocol classes for interfaces, enabling dependency injection and testability

## Import Style

- **Order**: Standard library, third-party, local imports (separated by blank lines)
- **Ruff** handles automatic import sorting
