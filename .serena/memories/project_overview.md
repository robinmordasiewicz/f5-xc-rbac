# F5 XC User and Group Sync - Project Overview

## Purpose

Automated synchronization tool for managing F5 Distributed Cloud (XC) users and groups from CSV user databases. The tool ensures user and group membership in F5 XC matches an authoritative user database (e.g., Active Directory exports) with validation, dry-run testing, and automated cleanup capabilities.

**Key Distinction**: This is a user and group reconciliation tool, not specifically an RBAC management tool. While groups may be used for role-based access control, the tool's primary purpose is to synchronize user and group data from CSV exports to F5 XC.

## Key Features

- Reads user and group memberships from CSV exports (e.g., from Active Directory)
- Syncs users and groups to F5 Distributed Cloud via API
- Validates all users exist in XC before creating groups
- Manages user and group lifecycle (create, update, prune with `--prune`)
- Provides dry-run mode for safe testing
- Integrates with CI/CD pipelines (GitHub Actions, Jenkins)

## Tech Stack

- **Python**: 3.10+ (target: 3.12)
- **Dependencies**:
  - `click`: CLI framework
  - `ldap3`: LDAP DN parsing
  - `pydantic`: Data validation
  - `python-dotenv`: Environment variable management
  - `requests`: HTTP client for F5 XC API
  - `tenacity`: Retry logic with exponential backoff

## Architecture

- **CLI Entry Point**: `xc_user_group_sync.cli` - Command-line interface
- **API Client**: `xc_user_group_sync.client.XCClient` - F5 XC API interactions with retry logic
- **Sync Service**: `xc_user_group_sync.sync_service.GroupSyncService` - Business logic for group synchronization
- **User Sync Service**: `xc_user_group_sync.user_sync_service.UserSyncService` - Business logic for user synchronization
- **Data Models**: `xc_user_group_sync.models` - Pydantic models for validation
- **Protocols**: `xc_user_group_sync.protocols.GroupRepository` - Dependency injection interface
- **Utilities**: `xc_user_group_sync.ldap_utils` - LDAP DN parsing

## Authentication

Supports two methods:

1. **Certificate-based**: `VOLT_API_CERT_FILE` + `VOLT_API_CERT_KEY_FILE`
2. **Token-based**: `XC_API_TOKEN`

Required: `TENANT_ID` environment variable
