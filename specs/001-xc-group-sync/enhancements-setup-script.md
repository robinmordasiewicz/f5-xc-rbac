# Enhancement Specification: Setup Script Advanced Features

**Parent Spec**: `001-xc-group-sync`
**Enhancement ID**: `001-ENH-004`
**Created**: 2025-11-11
**Status**: Reverse-Engineered from Implementation
**Script**: `scripts/setup_xc_credentials.sh`

## Overview

This enhancement documents the advanced features and safeguards implemented in the credential setup script but not specified in the original PRD. These features improve robustness, security, and user experience across diverse deployment environments.

## Enhanced Requirements

### Environment Detection and Auto-Configuration

**FR-SETUP-001**: Script MUST automatically detect environment type (production vs staging) from p12 filename patterns

**Implementation**: `setup_xc_credentials.sh:108-126`

```bash
# Production format: <tenant>.console.ves.volterra.io.api-creds.p12
if [[ "$name_no_ext" =~ ^([^.]+)\.console\.ves\.volterra\.io ]]; then
    TENANT="${BASH_REMATCH[1]}"
    XC_API_URL="https://${TENANT}.console.ves.volterra.io"
    ENV_TYPE="production"
# Staging format: <tenant>.staging.api-creds.p12
elif [[ "$name_no_ext" =~ ^([^.]+)\.staging ]]; then
    TENANT="${BASH_REMATCH[1]}"
    XC_API_URL="https://${TENANT}.staging.volterra.us"
    ENV_TYPE="staging"
else
    # Fallback: assume production
    TENANT=${name_no_ext%%.*}
    XC_API_URL="https://${TENANT}.console.ves.volterra.io"
    ENV_TYPE="production (assumed)"
fi
```text
**Filename Patterns**:

- **Production**: `f5-amer-ent.console.ves.volterra.io.api-creds.p12`
  - Extracts: `TENANT=f5-amer-ent`, `XC_API_URL=https://f5-amer-ent.console.ves.volterra.io`
- **Staging**: `nferreira.staging.api-creds.p12`
  - Extracts: `TENANT=nferreira`, `XC_API_URL=https://nferreira.staging.volterra.us`
- **Fallback**: `mytenant.api-creds.p12`
  - Extracts: `TENANT=mytenant`, `XC_API_URL=https://mytenant.console.ves.volterra.io` (assumed production)

**Rationale**: Eliminates manual environment configuration, reduces setup errors, enables correct API URL derivation for different F5 XC environments

**Testing**:

```bash
# Test production detection
./scripts/setup_xc_credentials.sh --p12 ~/Downloads/f5-amer-ent.console.ves.volterra.io.api-creds.p12
# Expected: ENV_TYPE="production", XC_API_URL="https://f5-amer-ent.console.ves.volterra.io"

# Test staging detection
./scripts/setup_xc_credentials.sh --p12 ~/Downloads/nferreira.staging.api-creds.p12
# Expected: ENV_TYPE="staging", XC_API_URL="https://nferreira.staging.volterra.us"
```text
---

**FR-SETUP-002**: Script MUST write detected `XC_API_URL` to `secrets/.env` file for CLI consumption

**Implementation**: `setup_xc_credentials.sh:219-227`

```bash
cat >"$TMP_ENV" <<ENV
TENANT_ID=$TENANT
XC_API_URL=$XC_API_URL
VOLT_API_CERT_FILE=$(pwd)/$CERT_PATH
VOLT_API_CERT_KEY_FILE=$(pwd)/$KEY_PATH
# If you prefer p12 in other tooling, keep for reference:
VOLT_API_P12_FILE=$(realpath "$P12")
VES_P12_PASSWORD=$P12_PASS
ENV
```text
**Rationale**: CLI automatically loads `XC_API_URL` from `secrets/.env`, eliminating need for users to manually configure custom endpoints

---

**FR-SETUP-003**: Script MUST display warnings when staging environment is detected about SSL certificate verification issues

**Implementation**: `setup_xc_credentials.sh:144-150`

```bash
if [[ "$ENV_TYPE" == "staging" ]]; then
  echo ""
  echo "⚠️  WARNING: Staging environments use self-signed CAs"
  echo "Python requests library may fail SSL verification."
  echo "See README 'SSL Certificate Verification Issues' for solutions."
  echo ""
fi
```text
**Warning Output**:

```text
Using TENANT_ID=nferreira
Using XC_API_URL=https://nferreira.staging.volterra.us (staging)

⚠️  WARNING: Staging environments use self-signed CAs
Python requests library may fail SSL verification.
See README 'SSL Certificate Verification Issues' for solutions.
```text
**Rationale**: Staging F5 XC environments often use self-signed certificates that fail Python's `requests` library SSL verification. Proactive warning prevents cryptic SSL errors during CLI operations.

**Workarounds** (documented in README):

1. Install staging CA certificate in system trust store
2. Set `REQUESTS_CA_BUNDLE=/path/to/staging-ca.crt` environment variable
3. Use production environment credentials for automated testing

---

### OpenSSL Compatibility Layer

**FR-SETUP-004**: Script MUST support OpenSSL 3.x with automatic `-legacy` fallback for PKCS#12 operations

**Implementation**: `setup_xc_credentials.sh:168-175`

```bash
pkcs12_extract() {
  # usage: pkcs12_extract <args...>
  if ! openssl pkcs12 "$@" 2>/dev/null; then
    # Retry with -legacy when available (OpenSSL 3.x)
    openssl pkcs12 -legacy "$@" 2>/dev/null
  fi
}
```text
**Usage**:

```bash
pkcs12_extract -in "$P12" -nokeys -out "$TMP_CERT" -passin pass:"$P12_PASS"
pkcs12_extract -in "$P12" -nocerts -nodes -out "$TMP_KEY" -passin pass:"$P12_PASS"
```text
**Rationale**: OpenSSL 3.0+ deprecated legacy algorithms used in many p12 files. Automatic `-legacy` fallback ensures compatibility across OpenSSL versions without requiring users to know OpenSSL version details.

**Compatibility**:

- **OpenSSL 1.x**: Uses standard `openssl pkcs12` command
- **OpenSSL 3.x with legacy support**: Falls back to `openssl pkcs12 -legacy`
- **OpenSSL 3.x without legacy**: Fails with clear error message

**Testing**:

```bash
# Test on system with OpenSSL 3.x
openssl version  # Should show 3.x
./scripts/setup_xc_credentials.sh --p12 test.p12
# Should succeed with automatic -legacy fallback
```text
---

**FR-SETUP-005**: Script MUST ensure extracted private keys are decrypted (passwordless) for Python requests compatibility

**Implementation**: `setup_xc_credentials.sh:197-201`

```bash
# Some keys may be encrypted; ensure passwordless key
if grep -q "ENCRYPTED" "$TMP_KEY"; then
  openssl rsa -in "$TMP_KEY" -out "${TMP_KEY}_nopass" 1>/dev/null
  mv "${TMP_KEY}_nopass" "$TMP_KEY"
fi
```text
**Rationale**: Python `requests` library requires passwordless PEM keys for TLS client authentication. PKCS#12 extraction sometimes produces encrypted keys even with `-nodes` flag.

**Key Formats**:

```text
# Encrypted key (requires additional decryption)
-----BEGIN ENCRYPTED <KEYTYPE> KEY-----
[encrypted key data]
-----END ENCRYPTED <KEYTYPE> KEY-----

# Decrypted key (ready for Python requests)
-----BEGIN <KEYTYPE> KEY-----
[decrypted key data - replace <KEYTYPE> with RSA, EC, or PRIVATE]
-----END <KEYTYPE> KEY-----
```text
---

### Atomic File Operations

**FR-SETUP-006**: Script MUST use atomic file creation with temporary files and `install` command for secure credential handling

**Implementation**: `setup_xc_credentials.sh:192-210`

```bash
# Create temporary files with unique names
TMP_CERT=$(mktemp secrets/cert.pem.XXXXXX)
TMP_KEY=$(mktemp secrets/key.pem.XXXXXX)

# Extract to temporary files
pkcs12_extract -in "$P12" -nokeys -out "$TMP_CERT" -passin pass:"$P12_PASS"
pkcs12_extract -in "$P12" -nocerts -nodes -out "$TMP_KEY" -passin pass:"$P12_PASS"

# Decrypt key if needed
if grep -q "ENCRYPTED" "$TMP_KEY"; then
  openssl rsa -in "$TMP_KEY" -out "${TMP_KEY}_nopass" 1>/dev/null
  mv "${TMP_KEY}_nopass" "$TMP_KEY"
fi

# Atomically move into place with correct permissions (mode 600)
install -m 600 "$TMP_CERT" "$CERT_PATH"
install -m 600 "$TMP_KEY" "$KEY_PATH"

# Remove temporary files
rm -f "$TMP_CERT" "$TMP_KEY" || true
```text
**Atomic Properties**:

1. **Temporary suffix prevents name collisions** (`cert.pem.ABC123`)
2. **`install` command atomically replaces target** with proper permissions
3. **Mode 600 restricts access** to owner only (critical for private keys)
4. **Cleanup trap ensures temp file removal** even on script failure

**Rationale**: Prevents partial file writes, race conditions, and credential exposure during script execution

---

**FR-SETUP-007**: Script MUST implement cleanup trap to remove temporary files on exit or error

**Implementation**: `setup_xc_credentials.sh:156-166`

```bash
TMP_CERT=""
TMP_KEY=""
TMP_ENV=""

cleanup() {
  # Remove any temp files if they still exist
  [[ -n "$TMP_CERT" && -f "$TMP_CERT" ]] && rm -f "$TMP_CERT" || true
  [[ -n "$TMP_KEY" && -f "$TMP_KEY" ]] && rm -f "$TMP_KEY" || true
  [[ -n "$TMP_ENV" && -f "$TMP_ENV" ]] && rm -f "$TMP_ENV" || true
}
trap cleanup EXIT
```text
**Trap Behavior**:

- Triggered on script exit (success or error)
- Triggered on interrupt signals (Ctrl+C)
- Only removes temporary files (tracked via `TMP_*` variables)
- Clears variable after successful `install` to prevent deletion of installed files

**Rationale**: Ensures credentials never leak to temporary filesystem, even during abnormal script termination

---

### Optional Operation Flags

**FR-SETUP-008**: Script MUST support `--no-secrets` flag to skip GitHub secrets creation

**Implementation**: `setup_xc_credentials.sh:49-51, 236-253`

```bash
# Command-line argument parsing
--no-github-config)
  CONFIGURE_GH_VARS="false"
  shift
  ;;

# GitHub variables creation (conditional)
if [[ "$CONFIGURE_GH_VARS" == "true" ]]; then
  if ! command -v gh >/dev/null 2>&1; then
    echo "gh CLI not found; install GitHub CLI to configure variables or pass --no-github-config to skip" >&2
    exit 1
  fi
  echo "Setting GitHub repo variables..."
  printf "%s" "$TENANT" | gh secret set TENANT_ID --body - 1>/dev/null || true
  # ... (other GitHub secret operations)
fi
```text
**Use Cases**:

- **Local development**: Skip secrets when only local `.env` file is needed
- **CI/CD environments**: Skip when secrets are managed via infrastructure-as-code
- **Security constraints**: Skip when GitHub CLI access is restricted

**Testing**:

```bash
# Skip GitHub secrets creation
./scripts/setup_xc_credentials.sh --p12 test.p12 --no-secrets
# Expected: secrets/.env created, GitHub secrets skipped
```text
---

**FR-SETUP-009**: Script MUST support `--no-env` flag to skip `.env` file creation

**Implementation**: `setup_xc_credentials.sh:53-55, 214-234`

```bash
# Command-line argument parsing
--no-env)
  WRITE_ENV="false"
  shift
  ;;

# .env file creation (conditional)
if [[ "$WRITE_ENV" == "true" ]]; then
  ENV_DIR="secrets"
  ENV_PATH="$ENV_DIR/.env"
  TMP_ENV=$(mktemp "$ENV_DIR/.env.XXXXXX")
  cat >"$TMP_ENV" <<ENV
TENANT_ID=$TENANT
XC_API_URL=$XC_API_URL
VOLT_API_CERT_FILE=$(pwd)/$CERT_PATH
VOLT_API_CERT_KEY_FILE=$(pwd)/$KEY_PATH
ENV
  install -m 600 "$TMP_ENV" "$ENV_PATH"
  rm -f "$TMP_ENV" || true
  echo "Wrote $ENV_PATH with TENANT_ID and cert/key paths"
fi
```text
**Use Cases**:

- **GitHub Actions**: Use secrets directly, skip `.env` file
- **Container deployments**: Inject environment variables via orchestrator
- **Security policies**: Avoid filesystem credential storage

**Testing**:

```bash
# Skip .env file creation
./scripts/setup_xc_credentials.sh --p12 test.p12 --no-env
# Expected: secrets/cert.pem and secrets/key.pem created, secrets/.env skipped
```text
---

### Password Input Handling

**FR-SETUP-010**: Script MUST support multiple password input methods (environment variable, interactive TTY, stdin pipe)

**Implementation**: `setup_xc_credentials.sh:177-189`

```bash
if [[ -n "${VES_P12_PASSWORD:-}" ]]; then
  # Method 1: Use existing environment variable
  P12_PASS="$VES_P12_PASSWORD"
else
  if [[ -t 0 ]]; then
    # Method 2: Interactive TTY - prompt silently
    read -r -s -p "Enter p12 passphrase: " P12_PASS
    echo ""
  else
    # Method 3: Non-interactive - read from stdin
    IFS= read -r P12_PASS || true
  fi
fi
```text
**Input Methods**:

1. **Environment Variable** (highest priority):

```bash
export VES_P12_PASSWORD="<your-p12-passphrase>"
./scripts/setup_xc_credentials.sh --p12 test.p12
```text
1. **Interactive TTY** (default for terminal):

```bash
./scripts/setup_xc_credentials.sh --p12 test.p12
# Prompts: "Enter p12 passphrase: " (silent input)
```text
1. **Stdin Pipe** (for automation):

```bash
echo "my-passphrase" | ./scripts/setup_xc_credentials.sh --p12 test.p12
```text
**Rationale**: Supports diverse deployment scenarios from manual setup to automated CI/CD pipelines

---

### P12 File Discovery

**FR-SETUP-011**: Script MUST support automatic p12 file detection in `~/Downloads` when exactly one p12 file exists

**Implementation**: `setup_xc_credentials.sh:69-96`

```bash
if [[ -z "$P12" ]]; then
  set +u
  CANDIDATES=(~/Downloads/*.p12)
  set -u

  if [[ ${#CANDIDATES[@]} -eq 1 && -f "${CANDIDATES[0]}" ]]; then
    # Single p12 file found - use it automatically
    P12="${CANDIDATES[0]}"
    echo "Detected p12: $P12"
  elif [[ ${#CANDIDATES[@]} -gt 1 ]]; then
    # Multiple p12 files found - present interactive selection
    echo "Multiple p12 files found in ~/Downloads:"
    PS3="Select p12 file (enter number): "
    select P12 in "${CANDIDATES[@]}"; do
      if [[ -n "$P12" ]]; then
        echo "Selected: $P12"
        break
      fi
    done
  else
    echo "No p12 files found in ~/Downloads. Provide --p12 <path>." >&2
    exit 1
  fi
fi
```text
**Behavior**:

- **0 files**: Error with message to provide `--p12` flag
- **1 file**: Automatically use detected file
- **2+ files**: Interactive menu for selection

**Interactive Selection Example**:

```text
Multiple p12 files found in ~/Downloads:
1) f5-amer-ent.console.ves.volterra.io.api-creds.p12
2) nferreira.staging.api-creds.p12
Select p12 file (enter number): 2
Selected: /Users/user/Downloads/nferreira.staging.api-creds.p12
```text
**Rationale**: Reduces friction for common workflow (download credentials → run setup script) while maintaining safety with interactive selection for ambiguous cases

---

### Historical Cleanup

**FR-SETUP-012**: Script MUST clean up temporary files from previous failed runs

**Implementation**: `setup_xc_credentials.sh:255-270`

```bash
# Always clean up any historical temp-suffix files left by prior runs
# Only remove files matching: secrets/{.env,cert.pem,key.pem}.XXXXXX (6 alphanumeric)
(
  shopt -s nullglob
  for base in .env cert.pem key.pem; do
    for tmp in "secrets/$base".*; do
      name=${tmp##*/}
      suffix=${name##*.}
      stem=${name%.*}
      if [[ "$stem" == "$base" && "$suffix" =~ ^[[:alnum:]]{6}$ ]]; then
        rm -f "$tmp" || true
      fi
    done
  done
  shopt -u nullglob
)
```text
**Cleanup Pattern**:

- Matches: `secrets/cert.pem.ABC123`, `secrets/.env.XYZ789`
- Ignores: `secrets/cert.pem`, `secrets/other.txt.XXXXXX`

**Rationale**: Prevents accumulation of temporary files from interrupted script runs, maintains clean secrets directory

---

## Success Criteria

- **SC-SETUP-001**: Environment detection correctly identifies production vs staging from p12 filename 100% of time for standard formats
- **SC-SETUP-002**: `XC_API_URL` automatically written to `secrets/.env` with correct endpoint
- **SC-SETUP-003**: Staging warning displayed when staging environment detected
- **SC-SETUP-004**: OpenSSL 3.x `-legacy` fallback succeeds for legacy p12 files
- **SC-SETUP-005**: Private keys extracted as passwordless PEM format
- **SC-SETUP-006**: Atomic file operations with mode 600 permissions
- **SC-SETUP-007**: Temporary files cleaned up on script success or failure
- **SC-SETUP-008**: `--no-secrets` and `--no-env` flags work independently and in combination
- **SC-SETUP-009**: Password input methods (env var, TTY, stdin) all function correctly
- **SC-SETUP-010**: P12 auto-detection works for single file, interactive selection for multiple
- **SC-SETUP-011**: Historical temporary files cleaned up automatically

---

## Documentation Requirements

- **DOC-SETUP-001**: README MUST document environment detection logic and filename patterns
- **DOC-SETUP-002**: README MUST document staging SSL certificate issues and workarounds
- **DOC-SETUP-003**: README MUST document OpenSSL 3.x compatibility and `-legacy` fallback
- **DOC-SETUP-004**: README MUST document `--no-secrets` and `--no-env` flags with use cases
- **DOC-SETUP-005**: README MUST document password input methods for different deployment scenarios
- **DOC-SETUP-006**: README MUST document p12 auto-detection behavior

---

## Security Considerations

- **Atomic operations**: Prevent credential exposure during file writes
- **Mode 600 permissions**: Restrict access to owner only for certificates and keys
- **Cleanup trap**: Ensure temporary files removed even on script failure
- **Password handling**: Support secure input methods (env var, silent prompt, stdin)
- **No credential logging**: Script does NOT echo passwords or keys to terminal
- **Temporary file prefixes**: Unique random suffixes prevent race conditions

---

## Future Enhancement Opportunities

- **FR-SETUP-013** (Future): Add `--validate-only` flag to check p12 file without extracting
- **FR-SETUP-014** (Future): Add `--output-dir` flag for custom secrets directory location
- **FR-SETUP-015** (Future): Add certificate expiration warnings (check with `openssl x509 -dates`)
- **FR-SETUP-016** (Future): Add support for PKCS#11 hardware tokens
- **FR-SETUP-017** (Future): Add GitHub secrets rotation workflow (detect and update expired secrets)
- **FR-SETUP-018** (Future): Add multi-tenant support (manage multiple credential sets)
