# F5 XC RBAC Group Sync - Project Overview

## Purpose
Automated synchronization tool for managing F5 Distributed Cloud (XC) RBAC groups from CSV user databases. The tool ensures group membership in F5 XC matches an authoritative user database (e.g., Active Directory exports) with validation, dry-run testing, and automated cleanup capabilities.

## Key Features
- Reads user group memberships from CSV exports (e.g., from Active Directory)
- Syncs RBAC groups to F5 Distributed Cloud via API
- Validates all users exist in XC before creating groups
- Manages group lifecycle (create, update, delete with `--cleanup`)
- Provides dry-run mode for safe testing
- Integrates with CI/CD pipelines (GitHub Actions)

## Tech Stack
- **Python**: 3.9+ (target: 3.12)
- **Dependencies**:
  - `click`: CLI framework
  - `ldap3`: LDAP DN parsing
  - `pydantic`: Data validation
  - `python-dotenv`: Environment variable management
  - `requests`: HTTP client for F5 XC API
  - `tenacity`: Retry logic with exponential backoff

## Architecture
- **CLI Entry Point**: `xc_rbac_sync.cli` - Command-line interface
- **API Client**: `xc_rbac_sync.client.XCClient` - F5 XC API interactions with retry logic
- **Sync Service**: `xc_rbac_sync.sync_service.GroupSyncService` - Business logic for synchronization
- **Data Models**: `xc_rbac_sync.models` - Pydantic models for validation
- **Protocols**: `xc_rbac_sync.protocols.GroupRepository` - Dependency injection interface
- **Utilities**: `xc_rbac_sync.ldap_utils` - LDAP DN parsing

## Authentication
Supports two methods:
1. **Certificate-based**: `VOLT_API_CERT_FILE` + `VOLT_API_CERT_KEY_FILE`
2. **Token-based**: `XC_API_TOKEN`

Required: `TENANT_ID` environment variable
