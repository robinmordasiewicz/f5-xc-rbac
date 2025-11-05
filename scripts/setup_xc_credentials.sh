#!/usr/bin/env bash
set -euo pipefail

# Setup script for F5 XC credentials and CI secrets
# - Derive TENANT_ID from a p12 filename or prompt
# - Split p12 to PEM cert/key with openssl (no password)
# - Create .env with appropriate variables
# - Optionally set GitHub repo secrets via gh CLI

usage() {
  cat <<'USAGE'
Usage: scripts/setup_xc_credentials.sh [--p12 <path>] [--tenant <id>] [--set-secrets]

Options:
  --p12 <path>       Path to p12 file; if omitted, auto-detect in ~/Downloads when exactly one .p12 exists
  --tenant <id>      Tenant ID (prefix before '.' in https://<tenant>.console.ves.volterra.io)
  --set-secrets      Use gh CLI to set secrets (XC_P12 / XC_P12_PASSWORD and/or XC_CERT / XC_CERT_KEY, TENANT_ID)

This script will:
  - Split p12 to PEM (cert.pem/key.pem) in ./secrets/ (created if missing)
  - Write .env with TENANT_ID and either VOLT_API_P12_FILE/VES_P12_PASSWORD or VOLT_API_CERT_FILE/VOLT_API_CERT_KEY_FILE
  - If --set-secrets, base64-encode files and set repo secrets via gh secret set (no secret values are printed)
USAGE
}

P12=""
TENANT=""
SET_SECRETS="false"

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
      SET_SECRETS="true"
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

# Detect p12 in ~/Downloads if not provided
if [[ -z "$P12" ]]; then
  mapfile -t P12S < <(ls -1 ~/Downloads/*.p12 2>/dev/null || true)
  if [[ ${#P12S[@]} -eq 1 ]]; then
    P12="${P12S[0]}"
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
  # Derive from prefix before first '-' or '_', e.g., acme-prod-api.p12 -> acme
  TENANT=${base%%[-_]*}
  TENANT=${TENANT%%.p12}
  if [[ -z "$TENANT" ]]; then
    echo "Could not derive tenant; pass --tenant <id>" >&2
    exit 1
  fi
fi

echo "Using TENANT_ID=$TENANT"

mkdir -p secrets
CERT_PATH="secrets/cert.pem"
KEY_PATH="secrets/key.pem"

# Prompt for p12 password (won't echo)
read -r -s -p "Enter p12 passphrase: " P12_PASS
echo ""

# Split p12 to PEM cert and key (no password on key)
openssl pkcs12 -in "$P12" -clcerts -nokeys -out "$CERT_PATH" -passin pass:"$P12_PASS" 1>/dev/null
openssl pkcs12 -in "$P12" -nocerts -nodes -out "$KEY_PATH" -passin pass:"$P12_PASS" 1>/dev/null

# Some keys may be encrypted; ensure passwordless key
if grep -q "ENCRYPTED" "$KEY_PATH"; then
  openssl rsa -in "$KEY_PATH" -out "${KEY_PATH%.pem}_nopass.pem" 1>/dev/null
  mv "${KEY_PATH%.pem}_nopass.pem" "$KEY_PATH"
fi

echo "Wrote $CERT_PATH and $KEY_PATH"

# Write .env (prefers cert/key since requests can't use p12 directly)
cat >.env <<ENV
TENANT_ID=$TENANT
VOLT_API_CERT_FILE=$(pwd)/$CERT_PATH
VOLT_API_CERT_KEY_FILE=$(pwd)/$KEY_PATH
# If you prefer p12 in other tooling, keep for reference:
VOLT_API_P12_FILE=$(realpath "$P12")
VES_P12_PASSWORD=$P12_PASS
ENV

echo ".env written with TENANT_ID and cert/key paths"

if [[ "$SET_SECRETS" == "true" ]]; then
  if ! command -v gh >/dev/null 2>&1; then
    echo "gh CLI not found; install GitHub CLI to set secrets or omit --set-secrets" >&2
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
