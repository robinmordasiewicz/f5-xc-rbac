# Usage Guide

Complete guide for using the F5 XC User and Group Sync tool.

## Quick Start

### 1. Set Up Credentials

```bash
./scripts/setup_xc_credentials.sh
source secrets/.env
```

### 2. Preview Changes

```bash
xc_user_group_sync --csv User-Database.csv --dry-run
```

### 3. Apply Synchronization

```bash
xc_user_group_sync --csv User-Database.csv
```

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `TENANT_ID` | Your F5 XC tenant ID | `my-tenant` |
| `VOLT_API_P12_FILE` | Path to P12/PKCS12 certificate file | `/path/to/cert.p12` |
| `VES_P12_PASSWORD` | Password for P12 certificate file | `your-password` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `XC_API_URL` | F5 XC API endpoint URL | `https://{TENANT_ID}.console.ves.volterra.io` |
| `HTTP_PROXY` | HTTP proxy URL | None |
| `HTTPS_PROXY` | HTTPS proxy URL | None |
| `REQUESTS_CA_BUNDLE` | Custom CA certificate bundle path | System CA bundle |

### Configuration File

Store variables in `secrets/.env`:

```bash
# Required
TENANT_ID=your-tenant-id
VOLT_API_P12_FILE=/absolute/path/to/secrets/your-tenant.p12
VES_P12_PASSWORD=your-p12-password

# Optional
XC_API_URL=https://your-tenant-id.console.ves.volterra.io
```

Load the configuration:

```bash
source secrets/.env
```

## CLI Reference

### Command Syntax

```bash
xc_user_group_sync [OPTIONS]
```

### CLI Options

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

### Default Behavior

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

### Corporate Proxy

**Using Environment Variables** (recommended):

```bash
# Add to secrets/.env
HTTP_PROXY=http://proxy.example.com:8080
HTTPS_PROXY=http://proxy.example.com:8080

# For proxies with authentication
HTTPS_PROXY=http://username:password@proxy.example.com:8080  # pragma: allowlist secret

# For MITM SSL inspection proxies
REQUESTS_CA_BUNDLE=/path/to/corporate-ca-bundle.crt
```

**Using CLI Flags**:

```bash
# Explicit proxy configuration
xc_user_group_sync --csv User-Database.csv \
  --proxy "http://proxy.example.com:8080" \
  --ca-bundle "/path/to/corporate-ca-bundle.crt"

# Disable SSL verification (debugging only, not recommended)
xc_user_group_sync --csv User-Database.csv \
  --proxy "http://proxy.example.com:8080" \
  --no-verify
```

**Getting Corporate CA Certificate**:

**Windows:**

1. Open Certificate Manager (`certmgr.msc`)
2. Navigate to Trusted Root Certification Authorities
3. Find your corporate proxy CA certificate
4. Right-click → All Tasks → Export
5. Choose Base-64 encoded X.509 format

**macOS:**

1. Open Keychain Access
2. Select "System" keychain
3. Find your corporate proxy CA certificate
4. File → Export Items
5. Save as `.crt` file

**Linux:**

- Check `/etc/ssl/certs/` for CA bundle
- Or contact your IT department

## CSV Format

### Required Columns

The tool extracts user and group data from CSV exports. Your CSV **must** include these four required columns (other columns are ignored):

| Column | Required | Description | Example Value |
|--------|----------|-------------|---------------|
| **Email** | Yes | User's email address for F5 XC authentication | `alice.anderson@example.com` |
| **User Display Name** | Yes | Full name of the user | `Alice Anderson` |
| **Employee Status** | Yes | User account status | `A` (Active) or `I` (Inactive) |
| **Entitlement Display Name** | Yes | Group membership in LDAP DN format | `CN=EADMIN_STD,OU=Groups,DC=example,DC=com` |

**Note**: Your CSV export may contain additional columns (e.g., Login ID, Manager Name, Cost Center) - these are allowed but not used by the synchronization tool.

### Employee Status Values

The tool recognizes these status values:

- **Active users**: `A` or `a` (case-insensitive, whitespace trimmed)
- **Inactive users**: Any other value (e.g., `I`, `T`, `Active`, `Inactive`, `Terminated`)

**Important**: Only the single letter `A` marks users as active. Full words like `Active` are treated as inactive.

### Group DN Format

Group identifiers must be in LDAP Distinguished Name format:

**Single Group**:

```text
CN=EADMIN_STD,OU=Groups,DC=example,DC=com
```

**Multiple Groups** (pipe-separated):

```text
CN=EADMIN_STD,OU=Groups,DC=example,DC=com|CN=DEVELOPERS,OU=Groups,DC=example,DC=com
```

### Sample CSV Files

**Minimal Format** (only required columns):

```csv
"Email","User Display Name","Employee Status","Entitlement Display Name"
"alice@example.com","Alice Anderson","A","CN=EADMIN_STD,OU=Groups,DC=example,DC=com"
"bob@example.com","Bob Brown","A","CN=DEVELOPERS,OU=Groups,DC=example,DC=com"
"charlie@example.com","Charlie Chen","A","CN=EADMIN_STD,OU=Groups,DC=example,DC=com|CN=DEVELOPERS,OU=Groups,DC=example,DC=com"
```

**Typical Export Format** (with additional metadata columns):

```csv
"User Name","Login ID","User Display Name","Cof Account Type","Application Name","Entitlement Attribute","Entitlement Display Name","Related Application","Sox","Job Level ","Job Title","Created Date","Account Locker","Employee Status","Email","Cost Center","Finc Level 4","Manager EID","Manager Name","Manager Email"
"USER001","CN=USER001,OU=Developers,OU=All Users,DC=example,DC=com","Alice Anderson","User","Active Directory","memberOf","CN=EADMIN_STD,OU=Groups,DC=example,DC=com","Example App","true","50","Lead Software Engineer","2025-09-23 00:00:00","0","A","alice.anderson@example.com","IT Infrastructure","Network Engineering","MGR001","David Wilson","David.Wilson@example.com"
```

The tool automatically extracts only the required columns from your export.

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

## Troubleshooting

For detailed troubleshooting guidance, see the [Troubleshooting Guide](troubleshooting.md).

**Common Issues**:

- Authentication failures → See [Troubleshooting Guide - Authentication](troubleshooting.md#issue-1-authentication-failures)
- CSV parsing errors → See [Troubleshooting Guide - CSV Parsing](troubleshooting.md#issue-2-csv-parsing-errors)
- Corporate proxy issues → See [Troubleshooting Guide - Corporate Proxy](troubleshooting.md#issue-4-corporate-proxy-configuration-and-authentication)
