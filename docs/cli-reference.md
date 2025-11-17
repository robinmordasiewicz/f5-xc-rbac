# CLI Reference

## Command Syntax

```bash
xc_user_group_sync [OPTIONS]
```

## Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--csv <path>` | Required | N/A | Path to CSV file with user/group data |
| `--dry-run` | Flag | `false` | Preview changes without applying |
| `--prune` | Flag | `false` | Delete users/groups in F5 XC not in CSV |
| `--log-level <level>` | Choice | `info` | Logging verbosity: `debug`, `info`, `warn`, `error` |
| `--timeout <seconds>` | Integer | `30` | HTTP request timeout |
| `--max-retries <n>` | Integer | `3` | Maximum retries for API errors |
| `--proxy <url>` | String | None | Proxy URL (e.g., `http://proxy:8080`) |
| `--ca-bundle <path>` | Path | None | Custom CA certificate bundle for SSL verification |
| `--no-verify` | Flag | `false` | Disable SSL verification (insecure, debugging only) |

## Default Behavior

By default, the tool synchronizes **both users and groups**:

- Creates users and groups from CSV that don't exist in F5 XC
- Updates existing users and groups to match CSV data
- Does **not** delete anything unless `--prune` flag is specified

## Usage Examples

### Basic Operations

```bash
# Preview reconciliation (recommended first step)
xc_user_group_sync --csv User-Database.csv --dry-run

# Apply reconciliation (create/update only)
xc_user_group_sync --csv User-Database.csv

# Full reconciliation including pruning
xc_user_group_sync --csv User-Database.csv --prune

# Dry-run with pruning preview
xc_user_group_sync --csv User-Database.csv --prune --dry-run
```

### Advanced Configuration

```bash
# Debug logging for troubleshooting
xc_user_group_sync --csv User-Database.csv --dry-run --log-level debug

# Increased timeout for large datasets
xc_user_group_sync --csv User-Database.csv --timeout 60

# More retries for unstable networks
xc_user_group_sync --csv User-Database.csv --max-retries 5

# Combined: debug with increased retry
xc_user_group_sync --csv User-Database.csv --log-level debug --max-retries 5 --timeout 60
```

### Corporate Proxy Configuration

For proxy configuration and troubleshooting, see [Configuration Guide - Corporate Proxy](configuration.md#corporate-proxy-configuration).

## Output Example

```text
============================================================
📦 GROUP SYNCHRONIZATION
============================================================
Groups planned from CSV: 3
    - EADMIN_STD: 5 users
    - DEVELOPER: 3 users
    - SECURITY_TEAM: 2 users

Existing groups in F5 XC: 2

✅ Creating group: SECURITY_TEAM
✅ Updating group: EADMIN_STD (membership changed)
➡️  No changes needed: DEVELOPER

============================================================
👤 USER SYNCHRONIZATION
============================================================
CSV Validation Results:
    ✅ Valid users: 8
    ⚠️  Warnings: 1
        - alice@example.com: Multiple group memberships (2 groups)

Existing users in F5 XC: 7

✅ Creating user: charlie@example.com
✅ Updating user: alice@example.com (groups changed)
➡️  No changes for 6 users

============================================================
✅ SYNCHRONIZATION COMPLETE
============================================================
Execution time: 3.45 seconds
Groups: 1 created, 1 updated
Users: 1 created, 1 updated
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Invalid arguments |
| 3 | Authentication failure |
| 4 | CSV validation error |
