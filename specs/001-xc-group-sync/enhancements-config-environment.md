# Enhancement Specification: Configuration & Environment Management

**Parent Spec**: `001-xc-group-sync`
**Enhancement ID**: `001-ENH-001`
**Created**: 2025-11-11
**Status**: Reverse-Engineered from Implementation
**Applies to**: All CLI commands (`sync`, `sync_users`)

## Overview

This enhancement documents the configuration and environment management features implemented in the codebase but not specified in the original PRD.

## Enhanced Requirements

### Configuration Loading

**FR-ENV-001**: System MUST support hierarchical environment variable loading in the following order (highest to lowest priority):

1. Environment variables set in current shell
2. `secrets/.env` file (if exists)
3. `.env` file in project root (if exists)

**Implementation**: `cli.py:_load_configuration():90-96`

**FR-ENV-002**: System MUST support `DOTENV_PATH` environment variable to override default `.env` file location

**Implementation**: `cli.py:_load_configuration():90-92`

```python
dotenv_path = os.getenv("DOTENV_PATH")
if dotenv_path and os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
```text
**Rationale**: Enables CI/CD pipelines to specify custom credential locations without modifying code

**Testing**:

```bash
# Test priority order
export DOTENV_PATH="secrets/.env"
# Verify secrets/.env takes precedence over .env
```text
---

### API URL Configuration

**FR-ENV-003**: System MUST support `XC_API_URL` environment variable to override default F5 XC API endpoint

**Implementation**:

- `cli.py:_load_configuration():102`
- `client.py:XCClient.__init__():36, 62`

**Default Behavior**: If `XC_API_URL` not set, derive from `TENANT_ID` → `https://{TENANT_ID}.console.ves.volterra.io`

**Use Cases**:

- **Production**: `https://tenant.console.ves.volterra.io`
- **Staging**: `https://tenant.staging.volterra.us`
- **Development**: Custom test endpoints

**Rationale**: Enables testing against staging/development environments without code changes

**Testing**:

```bash
# Test custom API URL
export XC_API_URL="https://tenant.staging.volterra.us"
./xc-group-sync sync --csv test.csv --dry-run
# Verify requests go to staging endpoint
```text
---

### Environment Detection

**FR-ENV-004**: Setup script MUST auto-detect environment type (production vs staging) from p12 filename patterns:

- **Production**: `{tenant}.console.ves.volterra.io.api-creds.p12` → `https://{tenant}.console.ves.volterra.io`
- **Staging**: `{tenant}.staging.api-creds.p12` → `https://{tenant}.staging.volterra.us`

**Implementation**: `scripts/setup_xc_credentials.sh:108-126`

```bash
if [[ "$name_no_ext" =~ ^([^.]+)\.console\.ves\.volterra\.io ]]; then
    TENANT="${BASH_REMATCH[1]}"
    XC_API_URL="https://${TENANT}.console.ves.volterra.io"
    ENV_TYPE="production"
elif [[ "$name_no_ext" =~ ^([^.]+)\.staging ]]; then
    TENANT="${BASH_REMATCH[1]}"
    XC_API_URL="https://${TENANT}.staging.volterra.us"
    ENV_TYPE="staging"
fi
```text
**FR-ENV-005**: Setup script MUST write `XC_API_URL` to `secrets/.env` file for use by CLI commands

**Implementation**: `scripts/setup_xc_credentials.sh:135-138, 219-227`

**FR-ENV-006**: Setup script MUST warn users when staging environment is detected about SSL certificate verification issues

**Implementation**: `scripts/setup_xc_credentials.sh:144-150`

```bash
if [[ "$ENV_TYPE" == "staging" ]]; then
  echo "⚠️  WARNING: Staging environments use self-signed CAs"
  echo "Python requests library may fail SSL verification."
  echo "See README 'SSL Certificate Verification Issues' for solutions."
fi
```text
**Rationale**: Staging environments often use self-signed certificates that fail Python's `requests` library SSL verification

**Workaround Options**:

1. Install custom CA certificate in system trust store
2. Set `REQUESTS_CA_BUNDLE` environment variable (NOT RECOMMENDED for production)
3. Use production environment for automated testing

---

## Configuration File Schema

### secrets/.env Format

```bash
# Required
TENANT_ID=your-tenant-id

# Optional - Auto-derived if not set
XC_API_URL=https://your-tenant-id.console.ves.volterra.io

# Authentication (choose one method)
# Method 1: Certificate/Key (preferred for Python requests)
VOLT_API_CERT_FILE=/absolute/path/to/cert.pem
VOLT_API_CERT_KEY_FILE=/absolute/path/to/key.pem

# Method 2: P12 Certificate (reference only - Python requests cannot use directly)
VOLT_API_P12_FILE=/absolute/path/to/api.p12
VES_P12_PASSWORD=your-p12-passphrase
```text
### Load Priority Examples

#### Scenario 1: CI/CD with secrets directory

```bash
# In GitHub Actions
echo "TENANT_ID=prod-tenant" > secrets/.env
echo "VOLT_API_CERT_FILE=$(pwd)/secrets/cert.pem" >> secrets/.env
# CLI automatically loads secrets/.env (highest priority after env vars)
```text
#### Scenario 2: Local development with custom location

```bash
# In developer's shell
export DOTENV_PATH="/Users/developer/my-credentials/.env"
# CLI loads from custom location instead of default paths
```text
#### Scenario 3: Environment override

```bash
# In shell
export TENANT_ID="staging-tenant"
export XC_API_URL="https://staging-tenant.staging.volterra.us"
# Shell variables take precedence over .env files
```text
---

## Success Criteria

- **SC-ENV-001**: CLI commands load configuration from `secrets/.env` in preference to `.env` when both exist
- **SC-ENV-002**: `DOTENV_PATH` environment variable successfully overrides default `.env` loading
- **SC-ENV-003**: Custom `XC_API_URL` successfully directs API requests to staging environment
- **SC-ENV-004**: Setup script correctly detects production vs staging from p12 filename 100% of time for standard filename formats
- **SC-ENV-005**: Staging environment warning is displayed when staging detected

---

## Documentation Requirements

- **DOC-001**: README MUST document environment variable hierarchy and precedence
- **DOC-002**: README MUST document `DOTENV_PATH` usage for CI/CD integration
- **DOC-003**: README MUST document staging environment SSL certificate issues and workarounds
- **DOC-004**: README MUST provide example `.env` files for production and staging

---

## Security Considerations

- **.env files** MUST be git-ignored (enforced by `.gitignore`)
- **`secrets/` directory** MUST be git-ignored (enforced by `.gitignore`)
- **SSL verification** MUST NOT be disabled in production environments
- **Staging credentials** SHOULD use separate, limited-privilege API tokens
- **`DOTENV_PATH`** MUST use absolute paths to prevent path traversal attacks
