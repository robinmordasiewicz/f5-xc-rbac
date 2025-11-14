# Configuration

## Environment Variables

The tool uses these environment variables for authentication and configuration:

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `TENANT_ID` | Yes | Your F5 XC tenant ID | N/A |
| `VOLT_API_CERT_FILE` | Yes* | Path to PEM certificate file | N/A |
| `VOLT_API_CERT_KEY_FILE` | Yes* | Path to PEM private key file | N/A |
| `XC_API_TOKEN` | Yes** | API token (alternative to cert auth) | N/A |
| `XC_API_URL` | No | F5 XC API endpoint URL | `https://{TENANT_ID}.console.ves.volterra.io` |

\* Required for certificate-based authentication (recommended)
\*\* Required if not using certificate authentication

## Configuration File

Store environment variables in `secrets/.env`:

```bash
# Required
TENANT_ID=your-tenant-id

# Certificate-based authentication (recommended)
VOLT_API_CERT_FILE=/absolute/path/to/secrets/cert.pem
VOLT_API_CERT_KEY_FILE=/absolute/path/to/secrets/key.pem

# Optional: Override API URL
XC_API_URL=https://your-tenant-id.console.ves.volterra.io
```

Load the configuration:

```bash
source secrets/.env
xc_user_group_sync --csv ./User-Database.csv --dry-run
```

## CSV Format

### Required Columns

Your CSV must include these exact column headers:

- **User Name** (optional): Display name for the user
- **Login ID** (required): LDAP Distinguished Name in DN format
- **Email** (required): User's email address matching their F5 XC profile
- **Entitlement Attribute** (required): Must contain `memberOf`
- **Entitlement Display Name** (required): Group LDAP DN

### LDAP DN Format

Both user and group identifiers must be in LDAP Distinguished Name format:

**User DN Example:**

```text
CN=USER001,OU=Users,DC=example,DC=com
```

**Group DN Example:**

```text
CN=EADMIN_STD,OU=Groups,DC=example,DC=com
```

### Sample CSV

```csv
"User Name","Login ID","Email","Entitlement Attribute","Entitlement Display Name"
"Alice Anderson","CN=USER001,OU=Users,DC=example,DC=com","alice@example.com","memberOf","CN=EADMIN_STD,OU=Groups,DC=example,DC=com"
"Bob Brown","CN=USER002,OU=Users,DC=example,DC=com","bob@example.com","memberOf","CN=EADMIN_STD,OU=Groups,DC=example,DC=com"
```

## Security Best Practices

**✅ DO:**

- Store credentials in `secrets/` directory (gitignored)
- Use repository secrets for CI/CD
- Set restrictive permissions: `chmod 600` on PEM files
- Rotate API credentials regularly
- Use separate credentials for dev/staging/production

**❌ DON'T:**

- Commit `.p12`, `.pem`, or `.env` files to git
- Share credentials in logs or documentation
- Use production credentials in development
