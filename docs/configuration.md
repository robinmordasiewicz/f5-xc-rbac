# Configuration

## Environment Variables

The tool uses these environment variables for authentication and configuration:

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `TENANT_ID` | Yes | Your F5 XC tenant ID | N/A |
| `VOLT_API_P12_FILE` | Yes | Path to P12/PKCS12 certificate file | N/A |
| `VES_P12_PASSWORD` | Yes | Password for P12 certificate file | N/A |
| `XC_API_URL` | No | F5 XC API endpoint URL (for staging) | `https://{TENANT_ID}.console.ves.volterra.io` |
| `HTTP_PROXY` | No | HTTP proxy URL | None |
| `HTTPS_PROXY` | No | HTTPS proxy URL | None |
| `REQUESTS_CA_BUNDLE` | No | Path to CA certificate bundle | System CA bundle |
| `CURL_CA_BUNDLE` | No | Alternative CA bundle path | System CA bundle |

**Note**: The tool supports native P12 authentication. Certificate and private key are extracted at runtime into temporary files and automatically cleaned up on exit.

## Configuration File

Store environment variables in `secrets/.env`:

```bash
# Required
TENANT_ID=your-tenant-id

# P12 certificate authentication (recommended)
VOLT_API_P12_FILE=/absolute/path/to/secrets/your-tenant.p12
VES_P12_PASSWORD=your-p12-password

# Optional: Override API URL
XC_API_URL=https://your-tenant-id.console.ves.volterra.io
```

Load the configuration:

```bash
source secrets/.env
xc_user_group_sync --csv ./User-Database.csv --dry-run
```

## Corporate Proxy Configuration

If your organization uses an outbound proxy (especially with MITM SSL inspection), configure proxy settings.

### ⚠️ Important: mTLS Authentication and Proxy Compatibility

**Supported Proxy Types**:

- ✅ **TLS Passthrough Proxies**: Allow client certificates to pass through without inspection
- ✅ **Token-Based Authentication**: Works with all proxy types (recommended for corporate environments)

**Unsupported Proxy Types**:

- ❌ **TLS Terminating/Inspecting Proxies with mTLS**: Corporate proxies that perform SSL/TLS inspection (MITM) **cannot** forward P12 client certificates to F5 XC

**Why mTLS Fails with TLS Inspection**:

When a corporate proxy performs TLS termination/inspection:
1. Client presents mTLS certificate to the proxy (not to F5 XC)
2. Proxy terminates the TLS connection and re-encrypts with a separate connection to F5 XC
3. Client certificate cannot be forwarded (proxy lacks the matching private key)
4. F5 XC receives no client certificate → authentication fails → redirects to OIDC login

**Recommended Solutions**:

1. **Use Token-Based Authentication** (works through all proxies):

   ```bash
   # Use API tokens instead of P12 certificates
   # Contact F5 XC support for API token generation
   ```

2. **Request TLS Passthrough** for F5 XC domains (requires IT approval):
   - Configure proxy to NOT inspect traffic to `*.ves.volterra.io` and `*.console.ves.volterra.io`
   - Preserves end-to-end TLS and mTLS authentication
   - May require security policy exception

3. **Deploy in Cloud Environment** (production recommended):
   - Run from AWS/Azure/GCP without corporate proxy
   - Avoids proxy configuration complexity entirely

See [Troubleshooting - mTLS Proxy Authentication](#issue-5-mtls-client-certificate-authentication-through-corporate-proxy) for detailed analysis.

### Using Environment Variables (Recommended)

```bash
# Add to secrets/.env
HTTP_PROXY=http://proxy.example.com:8080
HTTPS_PROXY=http://proxy.example.com:8080

# For proxies with authentication
HTTPS_PROXY=http://username:password@proxy.example.com:8080  # pragma: allowlist secret

# For MITM SSL inspection proxies (token auth only)
REQUESTS_CA_BUNDLE=/path/to/corporate-ca-bundle.crt
```

### Using CLI Flags

```bash
# Explicit proxy configuration
xc_user_group_sync --csv ./User-Database.csv \
  --proxy "http://proxy.example.com:8080" \
  --ca-bundle "/path/to/corporate-ca-bundle.crt"

# Disable SSL verification (debugging only, not recommended)
xc_user_group_sync --csv ./User-Database.csv \
  --proxy "http://proxy.example.com:8080" \
  --no-verify
```

### Getting Your Corporate CA Certificate

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

For proxy troubleshooting, see [Troubleshooting Guide - Corporate Proxy](troubleshooting.md#issue-4-corporate-proxy-and-mitm-ssl-interception).

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

**Single Group Example:**

```text
CN=EADMIN_STD,OU=Groups,DC=example,DC=com
```

**Multiple Groups:**

Use pipe separator (`|`) for users belonging to multiple groups:

```text
CN=EADMIN_STD,OU=Groups,DC=example,DC=com|CN=DEVELOPERS,OU=Groups,DC=example,DC=com
```

### Sample CSV

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
