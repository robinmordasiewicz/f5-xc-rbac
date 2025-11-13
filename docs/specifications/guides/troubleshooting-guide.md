---
title: Troubleshooting Guide
last_updated: 2025-11-13
version: 1.0.0
status: Production Ready
audience: DevOps Engineers, Platform Engineers, Support Teams
---

## Overview

This guide provides comprehensive troubleshooting procedures for F5 XC User and Group Sync tool, covering common issues, diagnostic commands, and resolution steps. Use this guide to quickly diagnose and resolve authentication failures, CSV parsing errors, network connectivity issues, and other operational problems encountered in production environments.

## Common Issues and Resolutions

### Issue 1: Authentication Failures

**Symptoms**:

```text
API error: Authentication failed - check credentials
HTTP 401 Unauthorized
```

**Possible Causes**:

1. Invalid or expired P12 certificate
2. Incorrect P12 password
3. Certificate not trusted by F5 XC
4. Incorrect API token

**Resolution Steps**:

```bash
# Verify certificate validity
openssl x509 -in secrets/cert.pem -noout -dates -subject

# Check certificate expiration
openssl x509 -in secrets/cert.pem -noout -checkend 0

# Re-extract certificate from P12 with correct password
./scripts/setup_xc_credentials.sh --p12 /path/to/new.p12

# Test connectivity
curl -X GET \
  "https://${TENANT_ID}.console.ves.volterra.io/api/web/namespaces/system/user_groups" \
  --cert ${VOLT_API_CERT_FILE} \
  --key ${VOLT_API_CERT_KEY_FILE}
```

---

### Issue 2: CSV Parsing Errors

**Symptoms**:

```csv
Failed to parse CSV: Missing required column 'Email'
CSVParseError: Invalid format
```

**Possible Causes**:
1. Missing required columns
2. Incorrect CSV format (delimiter, encoding)
3. Malformed LDAP DNs
4. UTF-8 encoding issues

**Resolution Steps**:

```bash
# Verify CSV structure
head -5 User-Database.csv

# Check encoding
file -bi User-Database.csv  # Should show utf-8

# Verify required columns present
csvcut -n User-Database.csv | grep -E "Email|Entitlement Display Name"

# Validate LDAP DN format in sample rows
csvcut -c "Entitlement Display Name" User-Database.csv | head -10

# Convert encoding if needed
iconv -f ISO-8859-1 -t UTF-8 User-Database.csv > User-Database-utf8.csv
```

---

### Issue 3: Retry Exhausted / Persistent Failures

**Symptoms**:

```text
Failed to create user user@example.com after 3 retries
RequestException: Connection timeout
```

**Possible Causes**:
1. Network connectivity issues
2. F5 XC API outage
3. Rate limiting (HTTP 429)
4. Firewall blocking HTTPS traffic

**Resolution Steps**:

```bash
# Test network connectivity
ping ${TENANT_ID}.console.ves.volterra.io
curl -I https://${TENANT_ID}.console.ves.volterra.io

# Check F5 XC status page
# https://status.f5.com/

# Increase timeout and retries
xc_user_group_sync sync --csv User-Database.csv \
  --timeout 60 \
  --max-retries 5

# Check for proxy/firewall issues
curl -v --proxy "" https://${TENANT_ID}.console.ves.volterra.io
```

---

### Issue 4: Staging SSL Certificate Verification Failures

**Symptoms**:

```text
SSLError: certificate verify failed
Unable to establish SSL connection
```

**Possible Causes**:
1. Staging environment uses self-signed certificates
2. Custom CA not trusted by Python requests library

**Resolution Steps**:

```bash
# Option 1: Install staging CA certificate in system trust store (recommended)
# Linux:
sudo cp staging-ca.crt /usr/local/share/ca-certificates/
sudo update-ca-certificates

# macOS:
sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain staging-ca.crt

# Option 2: Set custom CA bundle (temporary)
export REQUESTS_CA_BUNDLE=/path/to/staging-ca.crt
xc_user_group_sync sync --csv User-Database.csv

# Option 3: Use production environment for testing (if possible)
export XC_API_URL="https://${TENANT_ID}.console.ves.volterra.io"
```

---

## Diagnostic Commands

### Check Configuration

```bash
# Display loaded configuration (passwords masked)
env | grep -E "TENANT_ID|XC_API_URL|VOLT_API"

# Verify .env file exists and is readable
ls -la secrets/.env

# Test environment variable loading
python3 -c "from dotenv import load_dotenv; load_dotenv('secrets/.env'); import os; print(os.getenv('TENANT_ID'))"
```

### Test API Connectivity

```bash
# Test API endpoint reachability
curl -v https://${TENANT_ID}.console.ves.volterra.io/api/web/namespaces/system/user_groups \
  --cert ${VOLT_API_CERT_FILE} \
  --key ${VOLT_API_CERT_KEY_FILE}

# Expected: HTTP 200 with JSON response
# If 401: Authentication failure
# If connection timeout: Network/firewall issue
```

### Validate CSV

```bash
# Count rows
wc -l User-Database.csv

# List unique groups
csvcut -c "Entitlement Display Name" User-Database.csv | sort -u | wc -l

# List unique users
csvcut -c "Email" User-Database.csv | sort -u | wc -l

# Check for malformed DNs
csvcut -c "Entitlement Display Name" User-Database.csv | grep -v "^CN="
```

### Check Logs

```bash
# Run with debug logging
xc_user_group_sync sync --csv User-Database.csv --log-level debug

# Capture full output
xc_user_group_sync sync --csv User-Database.csv 2>&1 | tee sync-debug.log

# Search for specific errors
grep -i error sync-debug.log
grep -i "failed" sync-debug.log
```

---

## Issue Resolution Workflow

### Step 1: Identify the Issue Category

**Authentication Issues**:
- Symptoms: HTTP 401, "Authentication failed"
- Quick Check: Verify certificate validity and expiration

**CSV Issues**:
- Symptoms: "CSVParseError", "Missing required column"
- Quick Check: Validate CSV structure and encoding

**Network Issues**:
- Symptoms: Connection timeout, "RequestException"
- Quick Check: Test network connectivity and F5 XC status

**Configuration Issues**:
- Symptoms: "Configuration not found", missing environment variables
- Quick Check: Verify .env file and environment variables

### Step 2: Run Diagnostic Commands

Use the appropriate diagnostic commands from the sections above to gather information about the issue.

### Step 3: Apply Resolution Steps

Follow the resolution steps for the identified issue category.

### Step 4: Verify Resolution

```bash
# Test with dry-run
xc_user_group_sync sync --csv User-Database.csv --dry-run

# If dry-run succeeds, execute actual sync
xc_user_group_sync sync --csv User-Database.csv
```

### Step 5: Document and Escalate (if needed)

If issue persists:
1. Capture full debug output
2. Document steps taken
3. Check for known issues in repository
4. Contact F5 support or open GitHub issue

---

## Common Error Messages Reference

| Error Message | Likely Cause | Resolution |
|---------------|--------------|------------|
| `HTTP 401 Unauthorized` | Invalid credentials | Verify certificate and key files |
| `HTTP 429 Too Many Requests` | Rate limiting | Reduce request frequency, increase delays |
| `HTTP 503 Service Unavailable` | F5 XC API outage | Wait and retry, check F5 status page |
| `CSVParseError` | Invalid CSV format | Validate CSV structure and encoding |
| `ConnectionTimeout` | Network issues | Check connectivity, firewall rules |
| `SSLError` | SSL certificate issues | Verify CA trust, use correct certificates |
| `Missing required column` | CSV missing column | Verify CSV has Email and Entitlement columns |
| `No CN component found` | Malformed LDAP DN | Check LDAP DN format in CSV |

---

## Related Documentation

- [Deployment Guide](deployment-guide.md) - Overview of deployment scenarios
- [Operational Workflows](../implementation/workflows.md) - Step-by-step operational procedures
- [Testing Strategy](../implementation/testing-strategy.md) - Validation approaches
- [GitHub Actions Guide](github-actions-guide.md) - CI/CD automation with GitHub
- [Jenkins Guide](jenkins-guide.md) - CI/CD automation with Jenkins
