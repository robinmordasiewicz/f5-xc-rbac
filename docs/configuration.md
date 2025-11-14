# Configuration

## Environment Variables

The tool uses these environment variables for authentication and configuration:

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `TENANT_ID` | Yes | Your F5 XC tenant ID | N/A |
| `VOLT_API_P12_FILE` | Yes | Path to P12/PKCS12 certificate file | N/A |
| `VES_P12_PASSWORD` | Yes | Password for P12 certificate file | N/A |
| `XC_API_URL` | No | F5 XC API endpoint URL (for staging) | `https://{TENANT_ID}.console.ves.volterra.io` |

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
- Set restrictive permissions: `chmod 600` on P12 files
- Rotate API credentials regularly
- Use separate credentials for dev/staging/production
- Use strong passwords for P12 files

**❌ DON'T:**

- Commit `.p12` or `.env` files to git
- Share credentials in logs or documentation
- Use production credentials in development
- Store P12 passwords in plain text outside of secure storage
