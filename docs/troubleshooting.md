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
4. P12 file corrupted or not accessible

**Resolution Steps**:

```bash
# Verify P12 file can be read with password
openssl pkcs12 -in secrets/your-tenant.p12 -noout -passin pass:your-password

# For OpenSSL 3.x, use -legacy flag if needed
openssl pkcs12 -legacy -in secrets/your-tenant.p12 -noout -passin pass:your-password

# Verify environment variables are set correctly
echo $TENANT_ID
echo $XC_API_URL
echo $VOLT_API_P12_FILE
echo $VES_P12_PASSWORD  # Should show password (be careful with this in shared terminals)

# Test authentication (tool will handle P12 extraction internally)
xc_user_group_sync --csv test.csv --dry-run
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
xc_user_group_sync --csv User-Database.csv \
  --timeout 60 \
  --max-retries 5

# Check for proxy/firewall issues
curl -v --proxy "" https://${TENANT_ID}.console.ves.volterra.io
```

---

### Issue 4: Corporate Proxy and MITM SSL Interception

**Symptoms**:

```text
HTTP 400 Bad Request for url: https://login.ves.volterra.io/auth/realms/...
SSLError: certificate verify failed
Connection timeout or refused
```

**Example Error Messages**:

```text
# Direct connection blocked by proxy
requests.exceptions.ConnectTimeout: HTTPSConnectionPool(host='login.ves.volterra.io', port=443):
Max retries exceeded with url: /auth/realms/ves-io/protocol/openid-connect/auth

# MITM SSL inspection without CA bundle
requests.exceptions.SSLError: HTTPSConnectionPool(host='login.ves.volterra.io', port=443):
Max retries exceeded with url: /auth/realms/ves-io/protocol/openid-connect/auth
(Caused by SSLError(SSLCertVerificationError(1, '[SSL: CERTIFICATE_VERIFY_FAILED]
certificate verify failed: self signed certificate in certificate chain (_ssl.c:1129)')))

# Proxy authentication required
requests.exceptions.ProxyError: HTTPSConnectionPool(host='login.ves.volterra.io', port=443):
Max retries exceeded with url: /auth/realms/ves-io/protocol/openid-connect/auth
(Caused by ProxyError('Unable to connect to proxy',
OSError('Tunnel connection failed: 407 Proxy Authentication Required')))
```

**Diagnostic Tests**:

Before configuring proxy settings, verify if proxy is required:

```bash
# Test 1: Direct connection (should work if no proxy needed)
curl -v --max-time 10 https://login.ves.volterra.io/auth/realms/ves-io/protocol/openid-connect/auth

# Expected output if direct works:
# * Connected to login.ves.volterra.io (IP) port 443
# < HTTP/2 400 (or 200, 302, 401, 403 - all indicate successful connection)

# Expected output if proxy needed:
# * Connection timed out after 10000 milliseconds
# curl: (28) Connection timed out after 10000 milliseconds

# Test 2: With proxy (if Test 1 fails)
curl -v --max-time 10 \
  --proxy http://proxy.example.com:8080 \
  https://login.ves.volterra.io/auth/realms/ves-io/protocol/openid-connect/auth

# Expected output if proxy works:
# < HTTP/1.1 400 (or 200, 302, 401, 403 - all indicate successful connection)

# Expected output if MITM SSL inspection:
# curl: (60) SSL certificate problem: self signed certificate in certificate chain

# Test 3: With proxy and CA bundle (if Test 2 shows SSL error)
curl -v --max-time 10 \
  --proxy http://proxy.example.com:8080 \
  --cacert /path/to/corporate-ca-bundle.crt \
  https://login.ves.volterra.io/auth/realms/ves-io/protocol/openid-connect/auth

# Expected output if CA bundle correct:
# < HTTP/1.1 400 (or 200, 302, 401, 403 - all indicate successful connection)
```

**Interpreting Results**:

- **Test 1 succeeds**: No proxy needed, direct connection works
- **Test 1 fails with timeout**: Corporate proxy blocking direct access → configure proxy
- **Test 2 succeeds**: Proxy works without MITM SSL inspection
- **Test 2 fails with SSL error**: Proxy performs MITM SSL inspection → need CA bundle
- **Test 3 succeeds**: CA bundle is correct for your corporate proxy

**Possible Causes**:

1. Corporate proxy intercepting HTTPS traffic with MITM (Man-In-The-Middle) SSL inspection
2. Proxy CA certificate not trusted by Python requests library
3. Client certificate authentication incompatible with proxy MITM
4. Proxy requiring authentication

**Resolution Steps**:

```bash
# Option 1: Configure proxy via environment variables (recommended)
export HTTP_PROXY="http://proxy.example.com:8080"
export HTTPS_PROXY="http://proxy.example.com:8080"
export NO_PROXY="localhost,127.0.0.1"

# If proxy requires authentication
export HTTP_PROXY="http://username:password@proxy.example.com:8080"  # pragma: allowlist secret
export HTTPS_PROXY="http://username:password@proxy.example.com:8080"  # pragma: allowlist secret

# Add corporate CA certificate for MITM proxy
export REQUESTS_CA_BUNDLE="/path/to/corporate-ca-bundle.crt"
# or
export CURL_CA_BUNDLE="/path/to/corporate-ca-bundle.crt"

# Run sync with environment variables
xc_user_group_sync --csv User-Database.csv

# Option 2: Use CLI flags for explicit control
xc_user_group_sync --csv User-Database.csv \
  --proxy "http://proxy.example.com:8080" \
  --ca-bundle "/path/to/corporate-ca-bundle.crt"

# Option 3: Install corporate CA in system trust store (permanent)
# Linux:
sudo cp corporate-ca.crt /usr/local/share/ca-certificates/
sudo update-ca-certificates

# macOS:
sudo security add-trusted-cert -d -r trustRoot \
  -k /Library/Keychains/System.keychain corporate-ca.crt

# Then run without explicit CA bundle
xc_user_group_sync --csv User-Database.csv

# Debugging: Test proxy connectivity with curl
curl -x http://proxy.example.com:8080 \
  --cacert /path/to/corporate-ca-bundle.crt \
  -v https://login.ves.volterra.io

# Debugging: Verify CA bundle contains correct certificate
openssl x509 -in /path/to/corporate-ca-bundle.crt -text -noout
```

**Important Notes for Corporate Networks**:

1. **MITM Proxy Compatibility**: When using P12/mTLS client certificates through a corporate proxy with SSL inspection, the proxy must be configured to allow client certificate authentication pass-through. Some proxy configurations may break mTLS authentication.

2. **Testing from Different Networks**: If authentication works from home/non-proxied networks but fails from corporate networks, this confirms proxy interference. Work with your network team to:
   - Configure proxy to allow mTLS pass-through for `*.ves.volterra.io` domains
   - Get the corporate CA certificate for the MITM proxy
   - Verify proxy doesn't strip or modify client certificates

3. **CA Bundle Sources**: Your corporate CA bundle might be available at:
   - Windows: Export from certificate store or contact IT
   - macOS: `/Library/Keychains/System.keychain` (export via Keychain Access)
   - Linux: Check `/etc/ssl/certs/` or contact IT department

4. **Proxy Bypass**: If technical constraints prevent proper proxy configuration, consider:
   - Running from a jump host or bastion that doesn't require proxy
   - Using a VPN that bypasses the corporate proxy
   - Requesting firewall exceptions for `*.ves.volterra.io` domains

---

### Issue 5: Staging SSL Certificate Verification Failures

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
xc_user_group_sync --csv User-Database.csv

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

### Python Interactive Debugging

#### Debug Authentication and Client Setup

```python
# Start Python shell in project directory
python3

# Load environment and create client
from dotenv import load_dotenv
import os
load_dotenv('secrets/.env')

# Verify environment variables loaded
print(f"TENANT_ID: {os.getenv('TENANT_ID')}")
print(f"XC_API_URL: {os.getenv('XC_API_URL')}")
print(f"VOLT_API_P12_FILE: {os.getenv('VOLT_API_P12_FILE')}")
print(f"VES_P12_PASSWORD: {'[SET]' if os.getenv('VES_P12_PASSWORD') else '[NOT SET]'}")

# Create client with P12 authentication
from xc_user_group_sync.client import XCClient

client = XCClient(
    tenant_id=os.getenv('TENANT_ID'),
    p12_file=os.getenv('VOLT_API_P12_FILE'),
    p12_password=os.getenv('VES_P12_PASSWORD'),
    api_url=os.getenv('XC_API_URL')
)

# Inspect client configuration
print(f"Base URL: {client.base_url}")
print(f"Timeout: {client.timeout}s")
print(f"Max Retries: {client.max_retries}")
print(f"Session cert configured: {client.session.cert is not None}")
print(f"Temp cert file: {client._temp_cert_file}")
print(f"Temp key file: {client._temp_key_file}")
```

#### Test API Endpoints Interactively

```python
# List existing users (test authentication)
try:
    users_response = client.list_user_roles()
    print(f"✅ Authentication successful!")
    print(f"Total users: {len(users_response.get('items', []))}")

    # Display first user
    if users_response.get('items'):
        first_user = users_response['items'][0]
        print(f"Sample user: {first_user.get('name')}")
except Exception as e:
    print(f"❌ Authentication failed: {e}")

# List existing groups
try:
    groups_response = client.list_groups()
    print(f"Total groups: {len(groups_response.get('items', []))}")

    # Display all group names
    for group in groups_response.get('items', []):
        print(f" - {group['name']}: {len(group.get('usernames', []))} users")
except Exception as e:
    print(f"Error listing groups: {e}")

# Get specific user
try:
    user = client.get_user('testuser@example.com')
    print(f"User found: {user.get('name')}")
    print(f"Display name: {user.get('display_name')}")
    print(f"First name: {user.get('first_name')}")
    print(f"Last name: {user.get('last_name')}")
except Exception as e:
    print(f"User not found or error: {e}")
```

#### Inspect HTTP Request Details

```python
# Access session headers
print("Request Headers:")
for header, value in client.session.headers.items():
    # Mask sensitive values
    if 'auth' in header.lower() or 'token' in header.lower():
        print(f"  {header}: [REDACTED]")
    else:
        print(f"  {header}: {value}")

# Check P12 authentication status
print(f"\nP12 Authentication:")
print(f"  P12 file: {os.getenv('VOLT_API_P12_FILE')}")
print(f"  Temp cert: {client._temp_cert_file if hasattr(client, '_temp_cert_file') else 'N/A'}")
print(f"  Temp key: {client._temp_key_file if hasattr(client, '_temp_key_file') else 'N/A'}")

# Test raw API request with detailed output
import requests

try:
    # Make manual request to see full response details
    url = f"{client.base_url}/api/web/custom/namespaces/system/user_groups"
    response = client.session.get(url, timeout=client.timeout)

    print(f"\nAPI Request Details:")
    print(f"  URL: {url}")
    print(f"  Status Code: {response.status_code}")
    print(f"  Response Headers:")
    for header, value in response.headers.items():
        print(f"    {header}: {value}")

    # Parse JSON response
    data = response.json()
    print(f"  Response Keys: {list(data.keys())}")

except requests.exceptions.SSLError as e:
    print(f"❌ SSL Error: {e}")
    print("Hint: Check certificate validity or CA trust")
except requests.exceptions.ConnectionError as e:
    print(f"❌ Connection Error: {e}")
    print("Hint: Check network connectivity and firewall")
except requests.exceptions.Timeout as e:
    print(f"❌ Timeout Error: {e}")
    print("Hint: Increase timeout or check F5 XC status")
except requests.HTTPError as e:
    print(f"❌ HTTP Error: {e}")
    if response.status_code == 401:
        print("Hint: Authentication failed - check credentials")
    elif response.status_code == 429:
        print("Hint: Rate limited - reduce request frequency")
```

#### Debug CSV Parsing

```python
# Parse CSV and inspect validation results
from xc_user_group_sync.user_sync_service import UserSyncService

user_service = UserSyncService(client)

# Parse CSV file
csv_path = '/tmp/test-users.csv'
try:
    validation_result = user_service.parse_csv_to_users(csv_path)

    print(f"CSV Validation Results:")
    print(f"  Total users: {validation_result.total_count}")
    print(f"  Active users: {validation_result.active_count}")
    print(f"  Inactive users: {validation_result.inactive_count}")
    print(f"  Unique groups: {len(validation_result.unique_groups)}")

    # Check for warnings
    if validation_result.has_warnings():
        print(f"\n⚠️ Validation Warnings:")
        if validation_result.duplicate_emails:
            print(f"  Duplicate emails: {len(validation_result.duplicate_emails)}")
        if validation_result.invalid_emails:
            print(f"  Invalid emails: {len(validation_result.invalid_emails)}")
        if validation_result.users_without_groups > 0:
            print(f"  Users without groups: {validation_result.users_without_groups}")

    # Inspect first user
    if validation_result.users:
        user = validation_result.users[0]
        print(f"\nSample User:")
        print(f"  Email: {user.email}")
        print(f"  Display name: {user.display_name}")
        print(f"  Active: {user.active}")
        print(f"  Groups: {user.groups}")

except ValueError as e:
    print(f"❌ CSV Validation Error: {e}")
except Exception as e:
    print(f"❌ Parse Error: {e}")
```

#### Debug Group Synchronization

```python
# Parse groups from CSV
from xc_user_group_sync.sync_service import GroupSyncService

group_service = GroupSyncService(client)

try:
    planned_groups = group_service.parse_csv_to_groups(csv_path)

    print(f"Planned Groups from CSV:")
    for group in planned_groups:
        print(f"  {group.name}:")
        print(f"    Display name: {group.display_name}")
        print(f"    User count: {len(group.users)}")
        print(f"    Users: {', '.join(group.users[:5])}")
        if len(group.users) > 5:
            print(f"           ... and {len(group.users) - 5} more")

    # Fetch existing groups from F5 XC
    existing_groups = group_service.fetch_existing_groups()
    print(f"\nExisting Groups in F5 XC: {len(existing_groups)}")
    for group in existing_groups:
        print(f"  {group['name']}: {len(group.get('usernames', []))} users")

except Exception as e:
    print(f"❌ Group Parse Error: {e}")
```

#### Test P12 Certificate Extraction

```python
# Debug P12 file loading and certificate extraction
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.backends import default_backend

p12_file = os.getenv('VOLT_API_P12_FILE')
p12_password = os.getenv('VES_P12_PASSWORD')

try:
    # Load P12 file
    with open(p12_file, 'rb') as f:
        p12_data = f.read()

    print(f"P12 file size: {len(p12_data)} bytes")

    # Extract certificate and key
    private_key, certificate, additional_certs = pkcs12.load_key_and_certificates(
        p12_data,
        p12_password.encode(),
        backend=default_backend()
    )

    print(f"✅ P12 loaded successfully")
    print(f"Private key: {type(private_key).__name__}")
    print(f"Certificate: {type(certificate).__name__}")

    # Inspect certificate details
    print(f"\nCertificate Details:")
    print(f"  Subject: {certificate.subject}")
    print(f"  Issuer: {certificate.issuer}")
    print(f"  Not valid before: {certificate.not_valid_before_utc}")
    print(f"  Not valid after: {certificate.not_valid_after_utc}")
    print(f"  Serial number: {certificate.serial_number}")

    # Check if certificate is expired
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    if now < certificate.not_valid_before_utc:
        print("⚠️ Certificate not yet valid")
    elif now > certificate.not_valid_after_utc:
        print("❌ Certificate expired!")
    else:
        print("✅ Certificate is valid")

except FileNotFoundError:
    print(f"❌ P12 file not found: {p12_file}")
except ValueError as e:
    print(f"❌ Invalid P12 password or corrupted file: {e}")
except Exception as e:
    print(f"❌ P12 load error: {e}")
```

#### Test Retry Logic and Rate Limiting

```python
# Test client retry configuration
print(f"Retry Configuration:")
print(f"  Max retries: {client.max_retries}")
print(f"  Backoff multiplier: {client.backoff_multiplier}")
print(f"  Backoff min: {client.backoff_min}s")
print(f"  Backoff max: {client.backoff_max}s")

# Simulate retry behavior with custom settings
test_client = XCClient(
    tenant_id=os.getenv('TENANT_ID'),
    p12_file=os.getenv('VOLT_API_P12_FILE'),
    p12_password=os.getenv('VES_P12_PASSWORD'),
    api_url=os.getenv('XC_API_URL'),
    max_retries=5,  # Increase retries
    backoff_multiplier=2.0,  # Double backoff each retry
    backoff_min=2.0,  # Start with 2s delay
    backoff_max=16.0  # Max 16s delay
)

print(f"\nCustom Retry Configuration:")
print(f"  Max retries: {test_client.max_retries}")
print(f"  Backoff sequence (approx): 2s, 4s, 8s, 16s, 16s")

# Test with endpoint that might rate limit
import time

print(f"\nTesting rate limit handling...")
start = time.time()

try:
    # Make multiple rapid requests to test rate limiting
    for i in range(3):
        print(f"  Request {i+1}...")
        response = client.list_groups()
        print(f"    ✅ Success ({time.time() - start:.2f}s elapsed)")
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 429:
        print(f"    ⚠️ Rate limited (HTTP 429)")
        print(f"    Retry-After header: {e.response.headers.get('Retry-After')}")
    else:
        print(f"    ❌ HTTP Error: {e.response.status_code}")
except Exception as e:
    print(f"    ❌ Error: {e}")

total_time = time.time() - start
print(f"\nTotal time for 3 requests: {total_time:.2f}s")
print(f"Average time per request: {total_time/3:.2f}s")
```

#### Monitor API Response Times

```python
# Benchmark API endpoint performance
import time

def benchmark_endpoint(endpoint_func, name, iterations=5):
    """Benchmark an API endpoint."""
    print(f"\nBenchmarking {name}:")
    times = []

    for i in range(iterations):
        start = time.time()
        try:
            result = endpoint_func()
            elapsed = time.time() - start
            times.append(elapsed)
            print(f"  Attempt {i+1}: {elapsed:.3f}s ✅")
        except Exception as e:
            elapsed = time.time() - start
            print(f"  Attempt {i+1}: {elapsed:.3f}s ❌ ({e})")

    if times:
        avg = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        print(f"  Average: {avg:.3f}s")
        print(f"  Min: {min_time:.3f}s, Max: {max_time:.3f}s")
        return avg
    return None

# Benchmark different endpoints
benchmark_endpoint(client.list_groups, "list_groups")
benchmark_endpoint(client.list_user_roles, "list_user_roles")

# Test specific operations
def test_user_create():
    user_data = {
        "email": "benchmark@example.com",
        "username": "benchmark@example.com",
        "display_name": "Benchmark User",
        "first_name": "Bench",
        "last_name": "Mark"
    }
    try:
        return client.create_user(user_data)
    finally:
        # Cleanup
        try:
            client.delete_user("benchmark@example.com")
        except:
            pass

# Note: Only run create tests in non-production environments
# benchmark_endpoint(test_user_create, "create_user", iterations=1)
```

### Test API Connectivity

**Using P12 Certificate**:

```bash
# Extract certificate and key from P12 for curl testing
# Note: The tool handles this automatically - this is just for manual testing
openssl pkcs12 -in ${VOLT_API_P12_FILE} -passin pass:${VES_P12_PASSWORD} \
  -clcerts -nokeys -out /tmp/test-cert.pem

openssl pkcs12 -in ${VOLT_API_P12_FILE} -passin pass:${VES_P12_PASSWORD} \
  -nocerts -nodes -out /tmp/test-key.pem

# Test API endpoint reachability with extracted credentials
curl -v https://${TENANT_ID}.console.ves.volterra.io/api/web/custom/namespaces/system/user_groups \
  --cert /tmp/test-cert.pem \
  --key /tmp/test-key.pem

# Cleanup temporary files
rm -f /tmp/test-cert.pem /tmp/test-key.pem

# Expected: HTTP 200 with JSON response
# If 401: Authentication failure - check P12 password or certificate validity
# If connection timeout: Network/firewall issue
```

**Using Custom API URL** (staging environment):

```bash
# Extract cert/key from P12
openssl pkcs12 -in ${VOLT_API_P12_FILE} -passin pass:${VES_P12_PASSWORD} \
  -clcerts -nokeys -out /tmp/test-cert.pem
openssl pkcs12 -in ${VOLT_API_P12_FILE} -passin pass:${VES_P12_PASSWORD} \
  -nocerts -nodes -out /tmp/test-key.pem

# Test with custom API URL
curl -v ${XC_API_URL}/api/web/custom/namespaces/system/user_groups \
  --cert /tmp/test-cert.pem \
  --key /tmp/test-key.pem

# Cleanup
rm -f /tmp/test-cert.pem /tmp/test-key.pem
```

**Recommended**: Use the Python interactive debugging methods (see above) for API testing instead of curl, as they handle P12 authentication automatically without manual certificate extraction.

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
xc_user_group_sync --csv User-Database.csv --log-level debug

# Capture full output
xc_user_group_sync --csv User-Database.csv 2>&1 | tee sync-debug.log

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
xc_user_group_sync --csv User-Database.csv --dry-run

# If dry-run succeeds, execute actual sync
xc_user_group_sync --csv User-Database.csv
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
| `HTTP 400 Bad Request` (with login.ves.volterra.io) | Proxy MITM interference | Configure proxy with --proxy and --ca-bundle |
| `HTTP 429 Too Many Requests` | Rate limiting | Reduce request frequency, increase delays |
| `HTTP 503 Service Unavailable` | F5 XC API outage | Wait and retry, check F5 status page |
| `CSVParseError` | Invalid CSV format | Validate CSV structure and encoding |
| `ConnectionTimeout` | Network issues or proxy | Check connectivity, proxy settings, firewall rules |
| `SSLError: certificate verify failed` | Untrusted CA or proxy MITM | Add corporate CA bundle with --ca-bundle |
| `ProxyError` | Proxy authentication or connectivity | Verify proxy URL and credentials in HTTP_PROXY |
| `Missing required column` | CSV missing column | Verify CSV has Email and Entitlement columns |
| `No CN component found` | Malformed LDAP DN | Check LDAP DN format in CSV |

---

## Related Documentation

- [Deployment Guide](CICD/deployment-guide.md) - Overview of deployment scenarios
- [Operations Guide](operations-guide.md) - Step-by-step operational procedures
- [Testing Strategy](specifications/implementation/testing-strategy.md) - Validation approaches
- [GitHub Actions Guide](CICD/github-actions-guide.md) - CI/CD automation with GitHub
- [Jenkins Guide](CICD/jenkins-guide.md) - CI/CD automation with Jenkins
