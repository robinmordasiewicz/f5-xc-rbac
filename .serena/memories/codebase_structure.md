# Codebase Structure

## Directory Layout

```text
f5-xc-rbac/
├── src/xc_rbac_sync/       # Main package
│   ├── __init__.py         # Package initialization
│   ├── cli.py              # CLI entry point (Click commands)
│   ├── client.py           # XCClient - F5 XC API client with retry logic
│   ├── sync_service.py     # GroupSyncService - sync business logic
│   ├── models.py           # Pydantic models (Group, Config)
│   ├── protocols.py        # Protocol interfaces (GroupRepository)
│   └── ldap_utils.py       # LDAP DN parsing utilities
├── tests/                  # Test suite
│   ├── __init__.py
│   ├── conftest.py         # Pytest fixtures
│   ├── test_cli.py         # CLI tests
│   ├── test_client.py      # XCClient tests
│   ├── test_sync_service.py # GroupSyncService tests
│   ├── test_models.py      # Model validation tests
│   ├── test_ldap_utils.py  # LDAP parsing tests
│   └── unit/               # Unit tests subdirectory
├── scripts/                # Utility scripts
│   └── setup_xc_credentials.sh  # Credential setup automation
├── secrets/                # Credentials (gitignored)
│   ├── .env                # Environment variables
│   ├── cert.pem            # API certificate
│   └── key.pem             # API private key
├── .github/workflows/      # CI/CD
│   └── xc-group-sync.yml   # GitHub Actions workflow
├── pyproject.toml          # Python package configuration
├── README.md               # User documentation
└── .gitignore              # Git ignore rules
```text
## Key Components

### CLI Layer (`cli.py`)

- Entry point: `xc-group-sync` command
- Commands: Main command (with --dry-run, --prune, --log-level options)
- Handles environment loading, authentication, error reporting

### API Client (`client.py`)

- `XCClient`: REST API client for F5 XC
- Retry logic with exponential backoff using tenacity
- Supports both token and certificate authentication
- Methods: list_groups, create_group, update_group, delete_group, list_user_roles, create_user

### Sync Service (`sync_service.py`)

- `GroupSyncService`: Core business logic
- CSV parsing with LDAP DN extraction
- User pre-validation
- Group reconciliation (create, update, skip)
- Orphaned group cleanup
- Statistics tracking with `SyncStats`

### Data Models (`models.py`)

- `Group`: Pydantic model with name validation (alphanumeric, -, _, 1-128 chars)
- `Config`: Authentication configuration model

### Protocols (`protocols.py`)

- `GroupRepository`: Protocol interface for dependency injection
- Enables testing with mock implementations

### Utilities (`ldap_utils.py`)

- `extract_cn()`: Parse LDAP DNs to extract CN values
- Validation against F5 XC group name constraints
- Uses ldap3 library for robust DN parsing
