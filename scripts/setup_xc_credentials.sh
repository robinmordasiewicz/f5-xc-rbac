#!/usr/bin/env bash
set -euo pipefail
umask 077

# Setup script for F5 XC credentials and CI secrets
# - Derive TENANT_ID from a p12 filename or prompt
# - Configure P12 file authentication (no extraction needed - native P12 support)
# - Create .env with appropriate variables (now written under secrets/ by default)
# - Optionally create GitHub repo secrets via gh CLI (opt-in with --github-secrets)

usage() {
  cat <<'USAGE'
Usage: scripts/setup_xc_credentials.sh [--p12 <path>] [--tenant <id>] [--github-secrets] [--no-env]

Options:
  --p12 <path>          Path to p12 file; if omitted, auto-detect in ~/Downloads when exactly one .p12 exists
  --tenant <id>         Tenant ID (prefix before '.' in https://<tenant>.console.ves.volterra.io)
  --github-secrets      Set GitHub repository secrets via gh CLI (TENANT_ID, XC_P12, XC_P12_PASSWORD)
  --no-env              Do NOT write a .env file (default writes secrets/.env)

This script will:
  - Copy p12 file to ./secrets/ (created if missing)
  - Test API connectivity to detect network requirements
  - Prompt for proxy configuration if direct connection fails (interactive mode only)
  - Write secrets/.env with TENANT_ID, VOLT_API_P12_FILE, VES_P12_PASSWORD, and optional proxy settings
  - Optionally set repo secrets via gh CLI (only if --github-secrets is provided)
  - Avoid leftover temporary files

Intelligent Proxy Detection:
  - If direct API connectivity works: No proxy configuration added
  - If connectivity fails: Interactive prompts guide through proxy setup
  - Proxy settings (HTTP_PROXY, HTTPS_PROXY, REQUESTS_CA_BUNDLE) added to secrets/.env only when needed
  - Non-interactive mode: Skips proxy configuration with manual setup instructions

Note: The tool now supports P12 authentication natively - no cert/key extraction needed!
USAGE
}

P12=""
TENANT=""
SET_SECRETS="false"
WRITE_ENV="true"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --p12)
      P12=${2:-}
      shift 2
      ;;
    --tenant)
      TENANT=${2:-}
      shift 2
      ;;
    --github-secrets)
      SET_SECRETS="true"
      shift
      ;;
    --no-env)
      WRITE_ENV="false"
      shift
      ;;
    -h | --help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown arg: $1"
      usage
      exit 1
      ;;
  esac
done

# Detect p12 in ~/Downloads if not provided (portable for macOS bash)
if [[ -z "$P12" ]]; then
  set +u
  CANDIDATES=(~/Downloads/*.p12)
  set -u
  # If the glob didn't expand, the first element will still contain the pattern
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
      else
        echo "Invalid selection. Please try again." >&2
      fi
    done
  else
    # No p12 files found
    echo "No p12 files found in ~/Downloads. Provide --p12 <path>." >&2
    exit 1
  fi
fi

if [[ ! -f "$P12" ]]; then
  echo "p12 not found: $P12" >&2
  exit 1
fi

# Derive tenant and API URL if not provided
if [[ -z "$TENANT" ]]; then
  base=$(basename "$P12")
  name_no_ext=${base%.p12}

  # Detect environment type from filename patterns:
  # Production: <tenant>.console.ves.volterra.io.api-creds.p12 -> tenant=<tenant>, url=console.ves.volterra.io
  # Staging: <tenant>.staging.api-creds.p12 -> tenant=<tenant>, url=staging.volterra.us
  if [[ "$name_no_ext" =~ ^([^.]+)\.console\.ves\.volterra\.io ]]; then
    # Production format: acme-corp.console.ves.volterra.io.api-creds
    TENANT="${BASH_REMATCH[1]}"
    XC_API_URL="https://${TENANT}.console.ves.volterra.io"
    ENV_TYPE="production"
  elif [[ "$name_no_ext" =~ ^([^.]+)\.staging ]]; then
    # Staging format: acme-staging.staging.api-creds
    TENANT="${BASH_REMATCH[1]}"
    XC_API_URL="https://${TENANT}.staging.volterra.us"
    ENV_TYPE="staging"
  else
    # Fallback: assume production format with first segment as tenant
    TENANT=${name_no_ext%%.*}
    XC_API_URL="https://${TENANT}.console.ves.volterra.io"
    ENV_TYPE="production (assumed)"
  fi

  if [[ -z "$TENANT" ]]; then
    echo "Could not derive tenant; pass --tenant <id>" >&2
    exit 1
  fi
fi

# If API URL not set, default to production format
if [[ -z "$XC_API_URL" ]]; then
  XC_API_URL="https://${TENANT}.console.ves.volterra.io"
  ENV_TYPE="production (default)"
fi

echo "Using TENANT_ID=$TENANT"
echo "Using XC_API_URL=$XC_API_URL ($ENV_TYPE)"

# Warn about staging SSL limitations
if [[ "$ENV_TYPE" == "staging" ]]; then
  echo ""
  echo "⚠️  WARNING: Staging environments use self-signed CAs"
  echo "Python requests library may fail SSL verification."
  echo "See README 'SSL Certificate Verification Issues' for solutions."
  echo ""
fi

mkdir -p secrets

# Track temporary files for cleanup on failure
TMP_P12=""
TMP_ENV=""
cleanup() {
  # Remove any temp files if they still exist
  [[ -n "$TMP_P12" && -f "$TMP_P12" ]] && rm -f "$TMP_P12" || true
  [[ -n "$TMP_ENV" && -f "$TMP_ENV" ]] && rm -f "$TMP_ENV" || true
}
trap cleanup EXIT

# Obtain p12 password
if [[ -n "${VES_P12_PASSWORD:-}" ]]; then
  P12_PASS="$VES_P12_PASSWORD"
else
  if [[ -t 0 ]]; then
    # Interactive TTY: prompt silently
    read -r -s -p "Enter p12 passphrase: " P12_PASS
    echo ""
  else
    # Non-interactive: read first line from stdin
    IFS= read -r P12_PASS || true
  fi
fi

# Validate P12 file by attempting to read it (doesn't extract, just validates)
if ! openssl pkcs12 -in "$P12" -noout -passin pass:"$P12_PASS" 2>/dev/null; then
  # Try with -legacy flag for OpenSSL 3.x
  if ! openssl pkcs12 -legacy -in "$P12" -noout -passin pass:"$P12_PASS" 2>/dev/null; then
    echo "Error: Failed to validate P12 file. Check password and file integrity." >&2
    exit 1
  fi
fi

# Copy P12 file to secrets directory with secure permissions
P12_DEST="secrets/$(basename "$P12")"
TMP_P12=$(mktemp "secrets/$(basename "$P12").XXXXXX")
cp "$P12" "$TMP_P12"
chmod 600 "$TMP_P12"
mv "$TMP_P12" "$P12_DEST"
TMP_P12=""

echo "Copied P12 file to $P12_DEST"

if [[ "$WRITE_ENV" == "true" ]]; then
  # Test API connectivity before writing .env
  echo ""
  echo "Testing API connectivity..."

  # Determine the correct login URL based on environment
  if [[ "$XC_API_URL" =~ staging ]]; then
    LOGIN_URL="https://login.staging.volterra.us"
  else
    LOGIN_URL="https://login.ves.volterra.io"
  fi

  # Test direct connectivity with curl
  CONNECTIVITY_TEST=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 \
    --cert-type P12 --cert "$P12_DEST:$P12_PASS" \
    "$LOGIN_URL/auth/realms/ves-io/protocol/openid-connect/auth" 2>&1 || echo "FAIL")

  PROXY_NEEDED="false"
  PROXY_URL=""
  CA_BUNDLE_PATH=""

  if [[ "$CONNECTIVITY_TEST" =~ ^(200|302|400|401|403)$ ]]; then
    echo "✓ Direct API connectivity successful"
  else
    echo "⚠️  Direct API connectivity failed"
    echo ""
    echo "This could indicate:"
    echo "  - Corporate proxy blocking direct internet access"
    echo "  - Firewall restrictions"
    echo "  - Network configuration issues"
    echo ""

    # Check if we're in interactive mode
    if [[ -t 0 ]]; then
      read -r -p "Do you use a corporate proxy? (y/n): " USE_PROXY

      if [[ "$USE_PROXY" =~ ^[Yy] ]]; then
        PROXY_NEEDED="true"

        echo ""
        echo "Proxy Configuration"
        echo "==================="
        read -r -p "Proxy URL (e.g., http://proxy.example.com:8080): " PROXY_URL

        # Test proxy connectivity
        if [[ -n "$PROXY_URL" ]]; then
          echo ""
          echo "Testing proxy connectivity..."
          PROXY_TEST=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 \
            --proxy "$PROXY_URL" \
            --cert-type P12 --cert "$P12_DEST:$P12_PASS" \
            "$LOGIN_URL/auth/realms/ves-io/protocol/openid-connect/auth" 2>&1 || echo "FAIL")

          if [[ "$PROXY_TEST" =~ ^(200|302|400|401|403)$ ]]; then
            echo "✓ Proxy connectivity successful"
          else
            echo "⚠️  Proxy connectivity failed - may need MITM SSL certificate"
            echo ""
            read -r -p "Does your proxy perform MITM SSL inspection? (y/n): " USE_MITM

            if [[ "$USE_MITM" =~ ^[Yy] ]]; then
              echo ""
              echo "You'll need to provide the corporate CA certificate."
              echo "Common locations:"
              echo "  macOS:   /etc/ssl/cert.pem or Keychain Access export"
              echo "  Linux:   /etc/ssl/certs/ca-bundle.crt or /etc/pki/tls/certs/ca-bundle.crt"
              echo "  Windows: certmgr.msc export"
              echo ""
              read -r -p "Path to CA bundle (or press Enter to skip): " CA_BUNDLE_PATH

              if [[ -n "$CA_BUNDLE_PATH" && -f "$CA_BUNDLE_PATH" ]]; then
                echo "✓ CA bundle found: $CA_BUNDLE_PATH"
              elif [[ -n "$CA_BUNDLE_PATH" ]]; then
                echo "⚠️  CA bundle not found at: $CA_BUNDLE_PATH"
                echo "You can add it later to secrets/.env as REQUESTS_CA_BUNDLE"
                CA_BUNDLE_PATH=""
              fi
            fi
          fi
        fi
      fi
    else
      # Non-interactive mode - skip proxy configuration
      echo "Non-interactive mode: skipping proxy configuration"
      echo "If you need proxy support, manually add to secrets/.env:"
      echo "  HTTP_PROXY=http://proxy.example.com:8080"
      echo "  HTTPS_PROXY=http://proxy.example.com:8080"
      echo "  REQUESTS_CA_BUNDLE=/path/to/ca-bundle.crt"
    fi
  fi

  # Write secrets/.env with P12 authentication and optional proxy settings
  ENV_DIR="secrets"
  ENV_PATH="$ENV_DIR/.env"
  TMP_ENV=$(mktemp "$ENV_DIR/.env.XXXXXX")

  cat >"$TMP_ENV" <<ENV
TENANT_ID=$TENANT
XC_API_URL=$XC_API_URL
VOLT_API_P12_FILE=$(pwd)/$P12_DEST
VES_P12_PASSWORD=$P12_PASS
ENV

  # Add proxy configuration if needed
  if [[ "$PROXY_NEEDED" == "true" && -n "$PROXY_URL" ]]; then
    {
      cat <<PROXY

# Corporate proxy configuration
HTTP_PROXY=$PROXY_URL
HTTPS_PROXY=$PROXY_URL
PROXY

      if [[ -n "$CA_BUNDLE_PATH" ]]; then
        echo "REQUESTS_CA_BUNDLE=$CA_BUNDLE_PATH"
      fi

      echo ""
      echo "# Proxy configuration added by setup script"
      echo "# To disable: comment out HTTP_PROXY, HTTPS_PROXY, REQUESTS_CA_BUNDLE"
    } >>"$TMP_ENV"
  fi

  install -m 600 "$TMP_ENV" "$ENV_PATH"
  rm -f "$TMP_ENV" || true
  TMP_ENV=""

  echo ""
  echo "✓ Wrote $ENV_PATH with TENANT_ID and P12 authentication"

  if [[ "$PROXY_NEEDED" == "true" ]]; then
    echo "✓ Added proxy configuration to $ENV_PATH"
    echo ""
    echo "Next steps:"
    echo "  1. source secrets/.env"
    echo "  2. xc_user_group_sync --csv User-Database.csv --dry-run"
    echo ""
    echo "For more proxy configuration options, see docs/configuration.md"
  fi
else
  echo "Skipped writing .env (use --no-env to opt out; default writes secrets/.env)" >/dev/null
fi

if [[ "$SET_SECRETS" == "true" ]]; then
  if ! command -v gh >/dev/null 2>&1; then
    echo "gh CLI not found; install GitHub CLI to set secrets" >&2
    exit 1
  fi
  echo "Setting GitHub repo secrets (TENANT_ID, XC_P12, XC_P12_PASSWORD)..."
  # TENANT_ID is customer information and should be kept as a secret for privacy
  printf "%s" "$TENANT" | gh secret set TENANT_ID --body - 1>/dev/null || true
  # P12 must be base64 encoded (binary file)
  # Use -w 0 on Linux or tr -d '\n' on macOS to ensure single line
  base64 -w 0 <"$P12_DEST" 2>/dev/null | gh secret set XC_P12 --body - 1>/dev/null ||
    base64 <"$P12_DEST" | tr -d '\n' | gh secret set XC_P12 --body - 1>/dev/null || true
  printf "%s" "$P12_PASS" | gh secret set XC_P12_PASSWORD --body - 1>/dev/null || true
  echo "Secrets set."
fi

# Always clean up any historical temp-suffix files left by prior runs
# Only remove files matching: secrets/.env.XXXXXX (6 alphanumeric)
(
  shopt -s nullglob
  for tmp in "secrets/.env".*; do
    if [[ -f "$tmp" ]]; then
      name=${tmp##*/}
      suffix=${name##*.}
      stem=${name%.*}
      if [[ "$stem" == ".env" && "$suffix" =~ ^[[:alnum:]]{6}$ ]]; then
        rm -f "$tmp" || true
      fi
    fi
  done
  shopt -u nullglob
)

echo "Setup complete."
