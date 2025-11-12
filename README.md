# F5 Distributed Cloud RBAC Sync

Automated synchronization tool for managing F5 Distributed Cloud (XC) users and RBAC groups from CSV user databases.

## What Does This Tool Do?

This tool keeps your F5 XC security **users and groups** synchronized with your authoritative user database (exported as CSV):

**User Synchronization:**
- ✅ **Creates** users that exist in CSV but not in F5 XC
- ✅ **Updates** user attributes (name, active status) to match CSV
- ✅ **Deletes** users not in CSV (optional, with explicit flag)

**Group Synchronization:**
- ✅ **Creates** groups that exist in CSV but not in F5 XC
- ✅ **Updates** group memberships to match CSV (adds/removes users)
- ✅ **Deletes** groups not in CSV (optional, with explicit flag)

**Safety & Automation:**
- ✅ **Validates** all data before making changes
- ✅ **Dry-run mode** to preview changes safely before applying
- ✅ **CI/CD ready** for automated synchronization workflows

## Prerequisites

Before you start, you need:

1. **Python 3.9 or higher** installed on your system
2. **F5 XC API credentials** (.p12 certificate file with password)
   - Download from: F5 XC Console → Administration → Credentials → API Credentials
3. **CSV export** from your user database (Active Directory, LDAP, etc.)
   - Must include user emails and group memberships

## Quick Start

### Step 1: Installation

```bash
# Clone the repository
git clone https://github.com/robinmordasiewicz/f5-xc-rbac.git
cd f5-xc-rbac

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the tool
pip install -e .
```

### Step 2: Setup Credentials

#### Automated Setup (Recommended)

The easiest way to set up your credentials:

```bash
./scripts/setup_xc_credentials.sh --p12 ~/Downloads/your-tenant.p12
```

This script will:
- Extract your tenant ID from the filename
- Auto-detect environment (production/staging)
- Convert .p12 to PEM certificate and key files
- Create `secrets/.env` with all required variables
- Set GitHub repository secrets (if using CI/CD)

**The script will prompt you for:**
- P12 passphrase (if not already set via environment variable)

#### Manual Setup

If you prefer manual setup:

1. Create the secrets directory:
```bash
mkdir -p secrets
```

2. Extract certificate and key from .p12:
```bash
# Extract certificate
openssl pkcs12 -in your-tenant.p12 -clcerts -nokeys -out secrets/cert.pem

# Extract private key (no password)
openssl pkcs12 -in your-tenant.p12 -nocerts -nodes -out secrets/key.pem
```

3. Create `secrets/.env` file:
```bash
TENANT_ID=your-tenant-id
XC_API_URL=https://your-tenant-id.console.ves.volterra.io
VOLT_API_CERT_FILE=/absolute/path/to/secrets/cert.pem
VOLT_API_CERT_KEY_FILE=/absolute/path/to/secrets/key.pem
```

> **Note:** The `XC_API_URL` is auto-derived if not specified. For production, it defaults to `https://{TENANT_ID}.console.ves.volterra.io`. For staging, use `https://{TENANT_ID}.staging.volterra.us`.

### Step 3: Prepare Your CSV File

Your CSV must include these columns:

- `Login ID` - LDAP Distinguished Names (DN format)
- `Email` - User email addresses (must match F5 XC user profiles)
- `Entitlement Attribute` - Must contain value `memberOf`
- `Entitlement Display Name` - Group DNs (LDAP format)

**Example CSV:**

```csv
"User Name","Login ID","Email","Entitlement Attribute","Entitlement Display Name"
"Alice Anderson","CN=USER001,OU=Users,DC=example,DC=com","alice@example.com","memberOf","CN=EADMIN_STD,OU=Groups,DC=example,DC=com"
"Bob Brown","CN=USER002,OU=Users,DC=example,DC=com","bob@example.com","memberOf","CN=EADMIN_STD,OU=Groups,DC=example,DC=com"
```

### Step 4: Test with Dry-Run

**Always test first** to see what changes will be made:

```bash
xc-group-sync sync --csv ./User-Database.csv --dry-run
```

This shows you:
- ✅ Groups to be created
- ✅ Groups to be updated (with membership changes)
- ✅ Groups to be deleted (if using `--cleanup-groups`)
- ✅ Users to be deleted (if using `--cleanup-users`)
- ✅ Validation errors (missing users, invalid names)
- ✅ **No actual changes are made**

### Step 5: Apply Changes

Once you're satisfied with the dry-run output:

```bash
# Basic sync (create/update groups only)
xc-group-sync sync --csv ./User-Database.csv

# Sync with cleanup (also delete groups/users not in CSV)
xc-group-sync sync --csv ./User-Database.csv --cleanup-groups --cleanup-users
```

> **⚠️ Important:** The `--cleanup-groups` and `--cleanup-users` flags will **permanently delete** F5 XC groups and users that don't exist in your CSV. Use these flags carefully and always test with `--dry-run` first.

## Command Reference

### Basic Commands

```bash
# Preview changes without applying them
xc-group-sync sync --csv file.csv --dry-run

# Apply changes (create/update groups)
xc-group-sync sync --csv file.csv

# Apply with detailed logging
xc-group-sync sync --csv file.csv --log-level debug
```

### Cleanup Options

```bash
# Delete groups not in CSV
xc-group-sync sync --csv file.csv --cleanup-groups

# Delete users not in CSV
xc-group-sync sync --csv file.csv --cleanup-users

# Delete both groups and users not in CSV
xc-group-sync sync --csv file.csv --cleanup-groups --cleanup-users
```

### All Available Options

| Option | Description | Default |
|--------|-------------|---------|
| `--csv <path>` | Path to CSV file with user data | **(required)** |
| `--dry-run` | Preview changes without applying | `false` |
| `--cleanup-groups` | Delete XC groups not in CSV | `false` |
| `--cleanup-users` | Delete XC users not in CSV | `false` |
| `--log-level <level>` | Logging verbosity: `debug`, `info`, `warn`, `error` | `info` |
| `--timeout <seconds>` | HTTP request timeout | `30` |
| `--max-retries <n>` | Max retries for API errors | `3` |

## How It Works

### Synchronization Process

1. **Load Credentials** - Reads API credentials from `secrets/.env` or environment variables
2. **Parse CSV** - Extracts user information and group memberships from CSV
3. **Fetch XC Users** - Retrieves all users from F5 XC via API
4. **Validate** - Checks that all CSV emails exist in XC
5. **Calculate Changes** - Determines what groups need to be created/updated/deleted
6. **Apply Changes** - Makes API calls to F5 XC (unless using `--dry-run`)

### Group Lifecycle

**Create**: Groups in CSV but not in XC → Created with member lists

**Update**: Groups in both CSV and XC → Memberships synchronized:
- Adds users missing from XC group
- Removes users not in CSV (if they exist in XC group)

**Delete** (with `--cleanup-groups`): Groups in XC but not in CSV → Deleted

**Delete Users** (with `--cleanup-users`): Users in XC but not in CSV → Deleted

## Troubleshooting

### Common Issues

#### "TENANT_ID environment variable not set"

**Solution:**
```bash
# Verify secrets/.env exists
cat secrets/.env

# Source it manually
source secrets/.env

# Or re-run setup script
./scripts/setup_xc_credentials.sh --p12 your-file.p12
```

#### "User email@example.com not found in XC"

**Possible causes:**
- User doesn't exist in F5 XC yet
- Email in CSV doesn't match F5 XC user profile
- Email address has typo or formatting issue

**Solution:**
```bash
# Run with debug logging to see all XC emails
xc-group-sync sync --csv file.csv --log-level debug --dry-run
```

#### "Invalid group name: GROUP-NAME"

**Cause:** F5 XC only allows alphanumeric characters, hyphens, and underscores in group names.

**Solution:** The tool automatically converts invalid characters (e.g., spaces to underscores). Check the logs to see the converted name.

#### "API rate limit (429) exceeded"

**Cause:** Too many API requests in a short time.

**Solution:** The tool automatically retries with exponential backoff. If the problem persists:
```bash
# Increase max retries
xc-group-sync sync --csv file.csv --max-retries 5
```

#### Certificate/Authentication Errors

**Solution:**
```bash
# Verify certificate is valid
openssl x509 -in secrets/cert.pem -noout -text

# Verify private key is valid
openssl rsa -in secrets/key.pem -check

# Re-run setup if files are corrupted
./scripts/setup_xc_credentials.sh --p12 your-file.p12
```

#### SSL Certificate Verification Issues (Staging Environments)

**Problem:** Python fails with SSL verification errors when connecting to staging F5 XC environments.

**Why it happens:**
- Staging environments use self-signed CAs not in Python's trust store
- curl works because it uses system certificate stores
- Python uses its own bundled `certifi` package

**Solutions:**

**Option 1 (Testing Only):** Disable SSL verification
```bash
# ⚠️ DANGER: Only for non-production testing
export REQUESTS_CA_BUNDLE=""
xc-group-sync sync --csv file.csv
```

**Option 2 (Recommended):** Add staging CA to Python trust store
```bash
# Export staging CA
openssl s_client -showcerts -connect tenant.staging.ves.volterra.io:443 </dev/null 2>/dev/null | \
  openssl x509 -outform PEM > staging-ca.pem

# Find certifi location
python3 -c "import certifi; print(certifi.where())"

# Append to certifi bundle
cat staging-ca.pem >> $(python3 -c "import certifi; print(certifi.where())")
```

**Option 3 (Best):** Use production credentials
```bash
# Production environments use standard certificates and work without issues
TENANT_ID=your-prod-tenant xc-group-sync sync --csv file.csv
```

### Debug Mode

For maximum visibility into what the tool is doing:

```bash
xc-group-sync sync --csv file.csv --dry-run --log-level debug
```

This shows:
- All API requests and responses
- CSV parsing details
- Validation logic decisions
- Group membership calculations
- LDAP DN parsing

## CI/CD Integration

This repository provides **sample CI/CD configurations** that serve as starting points for production deployments. The samples are **disabled by default** and require customization for your environment.

### Available Samples

**📁 Location**: `samples/ci-cd/`

**GitHub Actions:**
- `xc-group-sync.yml.sample` - Main synchronization workflow
- `pre-commit.yml.sample` - Code quality and linting

**Jenkins:**
- `Jenkinsfile.declarative.sample` - Declarative Pipeline syntax
- `Jenkinsfile.scripted.sample` - Scripted Pipeline syntax

### Quick Start

**For GitHub Actions:**

1. Copy the sample workflow:
   ```bash
   cp samples/ci-cd/github-actions/xc-group-sync.yml.sample \
      .github/workflows/xc-group-sync.yml
   ```

2. Configure secrets in **Settings → Secrets and variables → Actions**:
   ```text
   TENANT_ID          Your F5 XC tenant ID
   XC_CERT            PEM certificate (raw text, not base64)
   XC_CERT_KEY        PEM private key (raw text, not base64)
   ```

3. Review and customize the workflow, then commit to enable it

**For Jenkins:**

1. Copy the sample Jenkinsfile:
   ```bash
   cp samples/ci-cd/jenkins/Jenkinsfile.declarative.sample Jenkinsfile
   ```

2. Configure Jenkins credentials with IDs:
   - `TENANT_ID` (Secret text)
   - `XC_CERT` (Secret text - PEM certificate content)
   - `XC_CERT_KEY` (Secret text - PEM private key content)

3. Create a Pipeline job pointing to your repository

### Detailed Documentation

For complete setup instructions, customization guide, and troubleshooting:

**📖 See**: [`samples/ci-cd/README.md`](samples/ci-cd/README.md)

Includes:
- Authentication options (PEM vs P12)
- Customization examples (cleanup flags, scheduling, notifications)
- Security best practices
- Troubleshooting common issues

## Security Best Practices

### Credential Management

✅ **DO:**
- Store credentials in `secrets/` directory (gitignored)
- Use repository secrets for CI/CD
- Set restrictive permissions (`chmod 600`) on PEM files
- Rotate API credentials regularly

❌ **DON'T:**
- Commit `.p12`, `.pem`, or `.env` files to git
- Share credentials in logs or screenshots
- Use production credentials in development/testing

### Safe Sync Practices

1. **Always dry-run first** - Test with `--dry-run` before applying
2. **Review changes** - Check dry-run output for unexpected modifications
3. **Start without cleanup** - Omit `--cleanup-groups` and `--cleanup-users` until confident
4. **Monitor logs** - Use `--log-level debug` for troubleshooting
5. **Backup first** - Document current XC state before bulk changes

## Support

- **GitHub Issues**: https://github.com/robinmordasiewicz/f5-xc-rbac/issues
- **F5 XC Documentation**: https://docs.cloud.f5.com/docs/api
- **F5 Support**: Contact F5 support for platform-specific issues

## License

See [LICENSE](LICENSE) file for details.
