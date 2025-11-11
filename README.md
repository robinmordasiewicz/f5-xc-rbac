# F5 XC RBAC Group Sync

Automated synchronization tool for managing F5 Distributed Cloud (XC) RBAC groups from CSV user databases. Ensures group membership in F5 XC matches your authoritative user database with validation, dry-run testing, and automated cleanup.

## Overview

This tool:

- **Reads** user group memberships from CSV exports (e.g., from Active Directory)
- **Syncs** RBAC groups to F5 Distributed Cloud via API
- **Validates** all users exist in XC before creating groups
- **Manages** group and user lifecycle (create, update, delete with `--cleanup-groups` and `--cleanup-users`)
- **Provides** dry-run mode for safe testing
- **Integrates** with CI/CD pipelines (GitHub Actions)

## Quick Start

### 1. Prerequisites

- **Python 3.12+** installed
- **F5 XC API Credentials** (`.p12` certificate file with password)
- **CSV file** with user data including LDAP DNs and group memberships

### 2. Installation

```bash
# Clone the repository
git clone https://github.com/robinmordasiewicz/f5-xc-rbac.git
cd f5-xc-rbac

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the tool
pip install -e .
```

### 3. Setup Credentials

You need F5 XC API credentials (`.p12` file). Download from:
- F5 XC Console → Administration → Credentials → API Credentials

#### Option A: Automated Setup (Recommended)

```bash
# Run setup script with your .p12 file
./scripts/setup_xc_credentials.sh --p12 ~/Downloads/your-tenant.p12

# The script will:
# - Extract your TENANT_ID from the filename
# - Split .p12 to PEM cert/key files (stored in secrets/)
# - Create secrets/.env with credentials
# - Set GitHub repository secrets (if gh CLI is installed)
```

**Script prompts for:**
- P12 passphrase (if not set via `VES_P12_PASSWORD` environment variable)

**Script options:**

```bash
--p12 <path>          Path to .p12 file (auto-detects from ~/Downloads if unique)
--tenant <id>         Tenant ID (extracted from filename if omitted)
--no-secrets          Skip GitHub secret creation
--no-env              Skip .env file creation
--tidy-legacy-env     Remove old root .env if present
```

#### Option B: Manual Setup

**1. Extract credentials from `.p12`:**

```bash
mkdir -p secrets

# Extract certificate
openssl pkcs12 -in your-tenant.p12 -clcerts -nokeys -out secrets/cert.pem

# Extract private key (no password)
openssl pkcs12 -in your-tenant.p12 -nocerts -nodes -out secrets/key.pem
```

**2. Create `secrets/.env`:**

```bash
TENANT_ID=your-tenant-id
VOLT_API_CERT_FILE=/absolute/path/to/secrets/cert.pem
VOLT_API_CERT_KEY_FILE=/absolute/path/to/secrets/key.pem
```

**Important:** Replace `your-tenant-id` with the prefix from your XC console URL:
`https://<tenant-id>.console.ves.volterra.io`

### 4. Prepare CSV File

Your CSV must include:
- `Login ID` column with LDAP Distinguished Names (DN)
- `Entitlement Attribute` column with value `memberOf`
- `Entitlement Display Name` column with group DNs
- `Email` column with user email addresses

**Example CSV format:**

```csv
"User Name","Login ID","Email","Entitlement Attribute","Entitlement Display Name"
"Alice Anderson","CN=USER001,OU=Users,DC=example,DC=com","alice@example.com","memberOf","CN=EADMIN_STD,OU=Groups,DC=example,DC=com"
"Bob Brown","CN=USER002,OU=Users,DC=example,DC=com","bob@example.com","memberOf","CN=EADMIN_STD,OU=Groups,DC=example,DC=com"
```

**CSV Requirements:**
- LDAP DNs parsed to extract CN (Common Name)
- Group names validated against F5 XC naming constraints (alphanumeric, hyphens, underscores)
- All email addresses must match existing users in XC

### 5. Run Sync

#### Dry-Run (Test Mode)

```bash
# Preview changes without applying
xc-group-sync sync --csv ./User-Database.csv --dry-run --log-level info
```

**Dry-run shows:**

- Groups to be created/updated/deleted
- Membership changes for each group
- Validation errors (missing users, invalid names)
- No API calls are made

#### Apply Changes

```bash
# Apply sync (create/update groups)
xc-group-sync sync --csv ./User-Database.csv --log-level info

# Apply with cleanup (also delete groups and users not in CSV)
xc-group-sync sync --csv ./User-Database.csv --cleanup-groups --cleanup-users --log-level info
```

**⚠️ Warning:** `--cleanup-groups` and `--cleanup-users` flags will **delete** F5 XC groups and users that don't exist in your CSV. Use with caution.

## Command Options

```text
--csv <path>          Path to CSV file with user data (required)
--dry-run             Preview changes without applying (no API calls)
--cleanup-groups      Delete XC groups not present in CSV (opt-in, use carefully)
--cleanup-users       Delete XC users not present in CSV (opt-in, use carefully)
--log-level <level>   Logging verbosity: debug|info|warn|error (default: info)
--timeout <seconds>   HTTP request timeout (default: 30)
--max-retries <n>     Max retries for transient API errors (default: 3)
```

## How It Works

### Workflow

1. **Load Credentials**: Reads `TENANT_ID` and API credentials from environment/`.env`
2. **Parse CSV**: Extracts LDAP DNs and group memberships
3. **Fetch XC Users**: Retrieves all users from F5 XC `user_roles` API
4. **Validate**: Checks all CSV emails exist in XC
5. **Calculate Changes**: Determines groups to create/update/delete
6. **Apply Changes**: Executes API calls (unless `--dry-run`)

### Technical Details

- **LDAP Parsing**: Uses `ldap3` library to parse DNs and extract CN values
- **Name Validation**: Enforces F5 XC naming rules (alphanumeric, `-`, `_` only)
- **API Retry Logic**: Exponential backoff for 429/5xx errors
- **User Validation**: Pre-checks all emails exist in XC before creating groups
- **Error Handling**: Skips groups with unknown users, logs warnings

### Group Lifecycle

**Create**: Groups in CSV but not in XC are created with member lists

**Update**: Groups in both CSV and XC have memberships synchronized:
- Adds missing members
- Removes extra members (if they exist in XC)

**Delete** (with `--cleanup-groups`): Groups in XC but not in CSV are deleted

**Delete Users** (with `--cleanup-users`): Users in XC but not in CSV are deleted

## CI/CD Integration

### GitHub Actions Setup

The repository includes a GitHub Actions workflow (`.github/workflows/xc-group-sync.yml`) that:
- Runs on push to `main` (dry-run only)
- Supports manual trigger via `workflow_dispatch` (applies changes)
- Uses repository secrets for credentials

#### Configure Repository Secrets

If you used `./scripts/setup_xc_credentials.sh`, secrets are already set. Otherwise:

1. Navigate to: **Settings** → **Secrets and variables** → **Actions**
2. Add repository secrets:

```text
TENANT_ID          Your F5 XC tenant ID
XC_CERT            PEM certificate (raw text, not base64)
XC_CERT_KEY        PEM private key (raw text, not base64)
```

**Alternative (if using `.p12` directly):**

```text
TENANT_ID          Your F5 XC tenant ID
XC_P12             Base64-encoded .p12 file
XC_P12_PASSWORD    P12 passphrase
```

#### Workflow Behavior

**Automatic (on push to `main`):**
- Runs dry-run sync
- Shows what would change
- No modifications applied

**Manual (workflow_dispatch):**
- Run from Actions tab → "XC Group Sync" → "Run workflow"
- Applies actual changes to F5 XC
- Use for production sync

### Other CI/CD Platforms

**Environment Variables Required:**

```bash
TENANT_ID                  # Your tenant ID
VOLT_API_CERT_FILE         # Path to cert.pem
VOLT_API_CERT_KEY_FILE     # Path to key.pem
```

**Example GitLab CI:**

```yaml
sync-xc-groups:
  script:
    - pip install -e .
    - xc-group-sync sync --csv ./User-Database.csv --dry-run
  only:
    - main
```

## Security Best Practices

### Credential Management

- ✅ **DO**: Store credentials in `secrets/` directory (gitignored)
- ✅ **DO**: Use repository secrets for CI/CD
- ✅ **DO**: Set restrictive permissions (`chmod 600`) on PEM files
- ❌ **DON'T**: Commit `.p12`, `.pem`, or `.env` files to git
- ❌ **DON'T**: Share credentials in logs or screenshots

### Safe Sync Practices

1. **Always dry-run first**: Test with `--dry-run` before applying
2. **Review changes**: Check dry-run output for unexpected modifications
3. **Start without cleanup**: Omit `--cleanup-groups` and `--cleanup-users` until confident
4. **Monitor logs**: Use `--log-level debug` for troubleshooting
5. **Backup groups and users**: Document current XC state before bulk changes

### File Permissions

The setup script automatically sets secure permissions:

```bash
secrets/cert.pem     600 (rw-------)
secrets/key.pem      600 (rw-------)
secrets/.env         600 (rw-------)
```

## Troubleshooting

### Common Issues

#### "TENANT_ID environment variable not set"

```bash
# Check secrets/.env exists and is sourced
cat secrets/.env
source secrets/.env  # or load via python-dotenv
```

#### "User email@example.com not found in XC"

- User doesn't exist in F5 XC yet
- Email mismatch between CSV and XC user profile
- Run: `xc-group-sync sync --csv file.csv --log-level debug` to see all XC emails

#### "Invalid group name: GROUP-NAME"

- F5 XC allows only alphanumeric, hyphens, underscores
- LDAP group names may have spaces/special chars
- Tool automatically converts names (e.g., `Group Name` → `Group_Name`)

#### "API rate limit (429) exceeded"

- Tool automatically retries with exponential backoff
- Increase `--max-retries` if needed
- Contact F5 support if persistent

#### Certificate/Authentication Errors

```bash
# Verify PEM files are valid
openssl x509 -in secrets/cert.pem -noout -text
openssl rsa -in secrets/key.pem -check

# Re-run setup if corrupted
./scripts/setup_xc_credentials.sh --p12 your-file.p12
```

#### SSL Certificate Verification Issues (Staging Environments)

**Problem**: Python `requests` library fails with SSL verification errors when connecting to staging F5 XC environments:

```text
SSLError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed
```

**Root Cause**: F5 XC staging environments (e.g., `*.staging.ves.volterra.io`, `*.nferreira.staging`) use self-signed root Certificate Authorities (CAs) that are not trusted by the standard Python `certifi` trust store.

**Why curl works but Python fails:**

- **curl**: Uses system certificate stores (macOS Keychain, Linux ca-certificates) which may include custom CAs
- **Python requests**: Uses bundled `certifi` package with only standard public CAs
- Staging self-signed CAs are not in `certifi` trust store

**Solutions:**

##### Option 1: Disable SSL Verification (Testing Only)

Add `--no-verify-ssl` flag (if implemented) or set environment variable:

```bash
# DANGER: Only for non-production testing
export REQUESTS_CA_BUNDLE=""
xc-group-sync sync --csv file.csv
```

**⚠️ Security Warning**: Disabling SSL verification exposes you to man-in-the-middle attacks. **Never use in production.**

##### Option 2: Add Staging CA to Python Trust Store

1. Export staging root CA certificate:

```bash
# Get the CA from staging endpoint
openssl s_client -showcerts -connect tenant.staging.ves.volterra.io:443 </dev/null 2>/dev/null | \
  openssl x509 -outform PEM > staging-ca.pem
```

1. Append to certifi bundle:

```bash
python3 -c "import certifi; print(certifi.where())"  # Find certifi location
cat staging-ca.pem >> $(python3 -c "import certifi; print(certifi.where())")
```

1. Or set `REQUESTS_CA_BUNDLE`:

```bash
export REQUESTS_CA_BUNDLE=/path/to/staging-ca.pem
xc-group-sync sync --csv file.csv
```

##### Option 3: Use Production Environment

Production F5 XC environments (`*.console.ves.volterra.io`) use standard publicly-trusted certificates and work without modification:

```bash
# Production environments don't have SSL issues
TENANT_ID=your-prod-tenant xc-group-sync sync --csv file.csv
```

##### Verify Your Environment

Check if your tenant uses staging:

```bash
echo $TENANT_ID
# If it ends in .staging, you're using staging environment
```

Test SSL connectivity:

```bash
curl -v https://${TENANT_ID}.console.ves.volterra.io 2>&1 | grep -i "SSL certificate verify"
```

**Best Practice**: Use production credentials for CI/CD pipelines to avoid SSL verification issues entirely.

### Debug Mode

```bash
# Maximum verbosity
xc-group-sync sync --csv ./User-Database.csv --dry-run --log-level debug

# Shows:
# - All API requests/responses
# - CSV parsing details
# - Validation logic
# - Group membership calculations
```

### Getting Help

- **Issues**: https://github.com/robinmordasiewicz/f5-xc-rbac/issues
- **F5 XC API Docs**: https://docs.cloud.f5.com/docs/api
- **Logs**: Check `--log-level debug` output

## Development

### Project Structure

```text
f5-xc-rbac/
├── src/
│   └── xc_group_sync/    # Main package
│       ├── cli.py        # CLI entry point
│       ├── api.py        # F5 XC API client
│       ├── sync.py       # Sync logic
│       └── parser.py     # CSV/LDAP parsing
├── tests/                # Test suite
├── scripts/
│   └── setup_xc_credentials.sh  # Credential setup
├── secrets/              # Credentials (gitignored)
│   ├── .env
│   ├── cert.pem
│   └── key.pem
├── .github/
│   └── workflows/
│       └── xc-group-sync.yml    # CI/CD pipeline
├── pyproject.toml        # Python package config
└── README.md             # This file
```

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=xc_group_sync --cov-report=html
```

### Code Quality

```bash
# Linting
ruff check .

# Formatting
ruff format .

# Type checking
mypy src/
```

## License

See [LICENSE](LICENSE) file for details.

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

## Support

For issues related to:
- **This tool**: Open GitHub issue
- **F5 XC Platform**: Contact F5 support
- **API access**: Check F5 XC documentation
