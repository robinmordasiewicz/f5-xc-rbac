#!/usr/bin/env bash
set -euo pipefail

# Setup script for F5 XC credentials and CI secrets
# - Derive TENANT_ID from a p12 filename or prompt
# - Split p12 to PEM cert/key with openssl (no password)
# - Create .env with appropriate variables (now written under secrets/ by default)
# - Create GitHub repo secrets via gh CLI by default (opt-out available)

usage() {
  cat <<'USAGE'
Usage: scripts/setup_xc_credentials.sh [--p12 <path>] [--tenant <id>] [--no-secrets] [--no-env]

Options:
  --p12 <path>       Path to p12 file; if omitted, auto-detect in ~/Downloads when exactly one .p12 exists
  --tenant <id>      Tenant ID (prefix before '.' in https://<tenant>.console.ves.volterra.io)
  --no-secrets       Do NOT set GitHub repo secrets (default is to set them)
  --no-env           Do NOT write a .env file (default writes secrets/.env)

This script will:
  - Split p12 to PEM (cert.pem/key.pem) in ./secrets/ (created if missing)
  - Write secrets/.env with TENANT_ID and either VOLT_API_P12_FILE/VES_P12_PASSWORD or VOLT_API_CERT_FILE/VOLT_API_CERT_KEY_FILE (unless --no-env)
  - Base64-encode files and set repo secrets via gh secret set (TENANT_ID, XC_CERT, XC_CERT_KEY, XC_P12, XC_P12_PASSWORD) by default (unless --no-secrets)
USAGE
}

P12=""
TENANT=""
SET_SECRETS="true"
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
    --set-secrets)
      # Backward compatibility: previously opted in; now default is on
      SET_SECRETS="true"
      shift
      ;;
    --no-secrets)
      SET_SECRETS="false"
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
    P12="${CANDIDATES[0]}"
    echo "Detected p12: $P12"
  else
    echo "No unique p12 found in ~/Downloads. Provide --p12 <path>." >&2
    exit 1
  fi
fi

if [[ ! -f "$P12" ]]; then
  echo "p12 not found: $P12" >&2
  exit 1
fi

# Derive tenant if not provided
if [[ -z "$TENANT" ]]; then
  base=$(basename "$P12")
  # Correct derivation: prefix before first '.' in <tenant>.console.ves.volterra.io...
  # Example: f5-amer-ent.console.ves.volterra.io.api-creds.p12 -> f5-amer-ent
  name_no_ext=${base%.p12}
  TENANT=${name_no_ext%%.*}
  if [[ -z "$TENANT" ]]; then
    echo "Could not derive tenant; pass --tenant <id>" >&2
    exit 1
  fi
fi

echo "Using TENANT_ID=$TENANT"

mkdir -p secrets
CERT_PATH="secrets/cert.pem"
KEY_PATH="secrets/key.pem"

# Helper: run openssl pkcs12, retrying with -legacy on failure (for OpenSSL 3)
pkcs12_extract() {
  # usage: pkcs12_extract <args...> (e.g., -in file -clcerts -nokeys -out out -passin pass:xxx)
  if ! openssl pkcs12 "$@" 2>/dev/null; then
    # Retry with -legacy when available
    openssl pkcs12 -legacy "$@" 2>/dev/null
  fi
}

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

# Split p12 to PEM cert and key (no password on key), with -legacy fallback
pkcs12_extract -in "$P12" -clcerts -nokeys -out "$CERT_PATH" -passin pass:"$P12_PASS"
pkcs12_extract -in "$P12" -nocerts -nodes -out "$KEY_PATH" -passin pass:"$P12_PASS"

# Some keys may be encrypted; ensure passwordless key
if grep -q "ENCRYPTED" "$KEY_PATH"; then
  openssl rsa -in "$KEY_PATH" -out "${KEY_PATH%.pem}_nopass.pem" 1>/dev/null
  mv "${KEY_PATH%.pem}_nopass.pem" "$KEY_PATH"
fi

echo "Wrote $CERT_PATH and $KEY_PATH"

if [[ "$WRITE_ENV" == "true" ]]; then
  # Write secrets/.env (prefers cert/key since requests can't use p12 directly)
  ENV_DIR="secrets"
  ENV_PATH="$ENV_DIR/.env"
  cat >"$ENV_PATH" <<ENV
TENANT_ID=$TENANT
VOLT_API_CERT_FILE=$(pwd)/$CERT_PATH
VOLT_API_CERT_KEY_FILE=$(pwd)/$KEY_PATH
# If you prefer p12 in other tooling, keep for reference:
VOLT_API_P12_FILE=$(realpath "$P12")
VES_P12_PASSWORD=$P12_PASS
ENV
  echo "Wrote $ENV_PATH with TENANT_ID and cert/key paths"
else
  echo "Skipped writing .env (use --no-env to opt out; default writes secrets/.env)" >/dev/null
fi

if [[ "$SET_SECRETS" == "true" ]]; then
  if ! command -v gh >/dev/null 2>&1; then
    echo "gh CLI not found; install GitHub CLI to set secrets or pass --no-secrets to skip" >&2
    exit 1
  fi
  # Base64 one-line
  b64() { base64 | tr -d '\n'; }

  echo "Setting GitHub repo secrets (TENANT_ID, XC_CERT, XC_CERT_KEY, XC_P12, XC_P12_PASSWORD)..."
  printf "%s" "$TENANT" | gh secret set TENANT_ID --body - 1>/dev/null || true
  b64 <"$CERT_PATH" | gh secret set XC_CERT --body - 1>/dev/null || true
  b64 <"$KEY_PATH" | gh secret set XC_CERT_KEY --body - 1>/dev/null || true
  b64 <"$P12" | gh secret set XC_P12 --body - 1>/dev/null || true
  printf "%s" "$P12_PASS" | gh secret set XC_P12_PASSWORD --body - 1>/dev/null || true
  echo "Secrets set."
fi

echo "Setup complete."
