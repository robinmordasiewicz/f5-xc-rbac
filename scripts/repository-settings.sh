#!/usr/bin/env bash
#
# apply-repository-settings.sh
# Apply GitHub repository settings from configuration file
#
# Usage:
#   ./apply-repository-settings.sh [config-file]
#
# Default config file: .github/repository-settings.json
#

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Default config file location
DEFAULT_CONFIG="${SCRIPT_DIR}/repository-settings.json"
CONFIG_FILE="${1:-${DEFAULT_CONFIG}}"

# Function to print colored messages
info() {
  echo -e "${BLUE}ℹ${NC} $*"
}

success() {
  echo -e "${GREEN}✓${NC} $*"
}

warning() {
  echo -e "${YELLOW}⚠${NC} $*"
}

error() {
  echo -e "${RED}✗${NC} $*"
}

# Check if required tools are installed
check_prerequisites() {
  local missing_tools=()

  if ! command -v gh &>/dev/null; then
    missing_tools+=("gh (GitHub CLI)")
  fi

  if ! command -v jq &>/dev/null; then
    missing_tools+=("jq")
  fi

  if [ ${#missing_tools[@]} -gt 0 ]; then
    error "Missing required tools:"
    for tool in "${missing_tools[@]}"; do
      echo "  - ${tool}"
    done
    echo ""
    echo "Install missing tools:"
    echo "  brew install gh jq"
    exit 1
  fi
}

# Validate configuration file
validate_config() {
  local config_file="$1"

  if [ ! -f "${config_file}" ]; then
    error "Configuration file not found: ${config_file}"
    exit 1
  fi

  if ! jq empty "${config_file}" 2>/dev/null; then
    error "Invalid JSON in configuration file: ${config_file}"
    exit 1
  fi

  # Ensure at least one settings section exists
  if ! jq -e '.protection or .repository' "${config_file}" >/dev/null 2>&1; then
    error "Configuration file must contain at least one of: 'protection' or 'repository'"
    exit 1
  fi

  # If protection config is present, branch must be provided
  if jq -e '.protection' "${config_file}" >/dev/null 2>&1; then
    if ! jq -e '.branch and (.branch|type=="string")' "${config_file}" >/dev/null 2>&1; then
      error "When 'protection' is specified, 'branch' must be a non-empty string"
      exit 1
    fi
  fi

  success "Configuration file validated: ${config_file}"
}
# Apply repository metadata (description, homepage, etc.)
apply_repository_metadata() {
  local config_file="$1"

  # Build patch body from available fields
  local patch
  patch=$(jq -c 'if .repository then (.repository | {
      description: (.description // empty),
      homepage: (.homepage // empty)
    } | with_entries(select(.value != null))) else {} end' "${config_file}")

  if [ -z "${patch}" ] || [ "${patch}" = "{}" ]; then
    info "No repository metadata to update"
    return 0
  fi

  info "Updating repository metadata (description/homepage)"
  echo "${patch}" | jq '.'

  if echo "${patch}" | gh api -X PATCH -H "Accept: application/vnd.github+json" "repos/${REPO_FULL}" --input - >/dev/null 2>&1; then
    success "Repository metadata updated"
    return 0
  else
    warning "Failed to update repository metadata (continuing)"
    return 0
  fi
}

# Apply repository topics
apply_repository_topics() {
  local config_file="$1"
  local topics_json

  topics_json=$(jq -c 'if .repository and (.repository.topics != null) then {names: (.repository.topics // [])} else empty end' "${config_file}")

  if [ -z "${topics_json}" ]; then
    info "No repository topics to set"
    return 0
  fi

  info "Setting repository topics"
  echo "${topics_json}" | jq '.'

  if echo "${topics_json}" | gh api -X PUT -H "Accept: application/vnd.github+json" "repos/${REPO_FULL}/topics" --input - >/dev/null 2>&1; then
    success "Repository topics updated"
    return 0
  else
    warning "Failed to update repository topics (continuing)"
    return 0
  fi
}

# Enable/disable vulnerability alerts
apply_vulnerability_alerts() {
  local config_file="$1"
  local val
  val=$(jq -r 'if .repository and (.repository.vulnerability_alerts != null) then .repository.vulnerability_alerts else empty end' "${config_file}")

  if [ -z "${val}" ]; then
    info "No vulnerability alerts setting provided"
    return 0
  fi

  if [ "${val}" = "true" ]; then
    info "Enabling vulnerability alerts"
    if gh api -X PUT -H "Accept: application/vnd.github+json" "repos/${REPO_FULL}/vulnerability-alerts" >/dev/null 2>&1; then
      success "Vulnerability alerts enabled"
    else
      warning "Failed to enable vulnerability alerts (may require org plan or permissions)"
    fi
  else
    info "Disabling vulnerability alerts"
    if gh api -X DELETE -H "Accept: application/vnd.github+json" "repos/${REPO_FULL}/vulnerability-alerts" >/dev/null 2>&1; then
      success "Vulnerability alerts disabled"
    else
      warning "Failed to disable vulnerability alerts"
    fi
  fi
}

# Enable/disable automated security fixes
apply_automated_security_fixes() {
  local config_file="$1"
  local val
  val=$(jq -r 'if .repository and (.repository.automated_security_fixes != null) then .repository.automated_security_fixes else empty end' "${config_file}")

  if [ -z "${val}" ]; then
    info "No automated security fixes setting provided"
    return 0
  fi

  if [ "${val}" = "true" ]; then
    info "Enabling automated security fixes"
    if gh api -X PUT -H "Accept: application/vnd.github+json" "repos/${REPO_FULL}/automated-security-fixes" >/dev/null 2>&1; then
      success "Automated security fixes enabled"
    else
      warning "Failed to enable automated security fixes"
    fi
  else
    info "Disabling automated security fixes"
    if gh api -X DELETE -H "Accept: application/vnd.github+json" "repos/${REPO_FULL}/automated-security-fixes" >/dev/null 2>&1; then
      success "Automated security fixes disabled"
    else
      warning "Failed to disable automated security fixes"
    fi
  fi
}

# Apply security and analysis settings (secret scanning, dependabot updates, etc.)
apply_security_and_analysis() {
  local config_file="$1"
  local sa
  sa=$(jq -c 'if .repository and (.repository.security_and_analysis != null) then {security_and_analysis: .repository.security_and_analysis} else empty end' "${config_file}")

  if [ -z "${sa}" ]; then
    info "No security_and_analysis settings provided"
    return 0
  fi

  info "Applying security_and_analysis settings"
  echo "${sa}" | jq '.'

  if echo "${sa}" | gh api -X PATCH -H "Accept: application/vnd.github+json" "repos/${REPO_FULL}" --input - >/dev/null 2>&1; then
    success "security_and_analysis settings applied"
    return 0
  else
    warning "Failed to apply security_and_analysis (feature may require org plan or permissions)"
    return 0
  fi
}

# Get repository information
get_repo_info() {
  local repo_info
  repo_info=$(gh repo view --json owner,name 2>&1)

  if [ $? -ne 0 ]; then
    error "Failed to get repository information"
    echo "Make sure you're in a Git repository with a GitHub remote"
    exit 1
  fi

  REPO_OWNER=$(echo "${repo_info}" | jq -r '.owner.login')
  REPO_NAME=$(echo "${repo_info}" | jq -r '.name')
  REPO_FULL="${REPO_OWNER}/${REPO_NAME}"

  info "Repository: ${REPO_FULL}"
}

# Get current branch protection settings
get_current_protection() {
  local branch="$1"
  local endpoint="repos/${REPO_FULL}/branches/${branch}/protection"

  info "Fetching current protection settings for branch: ${branch}"

  if gh api "${endpoint}" >/dev/null 2>&1; then
    gh api "${endpoint}" | jq '.'
    return 0
  else
    warning "No branch protection currently set for: ${branch}"
    return 1
  fi
}

# Apply branch protection settings
apply_protection() {
  local config_file="$1"
  local branch
  local protection_settings
  local endpoint

  # Extract branch name and protection settings from config
  branch=$(jq -r '.branch' "${config_file}")
  protection_settings=$(jq '.protection' "${config_file}")

  endpoint="repos/${REPO_FULL}/branches/${branch}/protection"

  info "Applying branch protection to: ${branch}"

  # Show what will be applied
  echo ""
  echo "Protection settings to apply:"
  echo "${protection_settings}" | jq '.'
  echo ""

  # Apply the settings
  if echo "${protection_settings}" | gh api -X PUT "${endpoint}" --input - >/dev/null 2>&1; then
    success "Branch protection applied successfully to: ${branch}"
    return 0
  else
    error "Failed to apply branch protection to: ${branch}"
    return 1
  fi
}

# Show summary of applied settings
show_summary() {
  local config_file="$1"
  local branch
  branch=$(jq -r '.branch' "${config_file}")

  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "Branch Protection Summary"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo ""

  local require_pr
  local required_reviews
  local force_pushes
  local deletions

  require_pr=$(jq -r 'if .protection.required_pull_request_reviews != null then "✓ Required" else "✗ Not required" end' "${config_file}")
  required_reviews=$(jq -r '.protection.required_pull_request_reviews.required_approving_review_count // 0' "${config_file}")
  force_pushes=$(jq -r 'if .protection.allow_force_pushes == true then "✓ Allowed" else "✗ Blocked" end' "${config_file}")
  deletions=$(jq -r 'if .protection.allow_deletions == true then "✓ Allowed" else "✗ Blocked" end' "${config_file}")

  echo "Branch: ${branch}"
  echo "Repository: ${REPO_FULL}"
  echo ""
  echo "Settings:"
  echo "  Pull Requests:       ${require_pr}"
  echo "  Required Reviews:    ${required_reviews}"
  echo "  Force Pushes:        ${force_pushes}"
  echo "  Branch Deletion:     ${deletions}"
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# Main function
main() {
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "GitHub Repository Settings Configuration"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo ""

  # Check prerequisites
  info "Checking prerequisites..."
  check_prerequisites
  success "All required tools found"
  echo ""

  # Validate configuration file
  info "Validating configuration..."
  validate_config "${CONFIG_FILE}"
  echo ""

  # Get repository information
  info "Getting repository information..."
  get_repo_info
  echo ""

  # Show current protection (if any)
  local branch
  branch=$(jq -r '.branch // empty' "${CONFIG_FILE}")
  if [ -n "${branch}" ]; then
    echo ""
    get_current_protection "${branch}" || true
    echo ""
  fi

  local had_error=0

  # Apply protection settings (optional)
  if jq -e '.protection' "${CONFIG_FILE}" >/dev/null 2>&1; then
    if apply_protection "${CONFIG_FILE}"; then
      show_summary "${CONFIG_FILE}"
    else
      had_error=1
    fi
  else
    info "No branch protection configuration provided; skipping"
  fi

  # Apply repository-level settings
  apply_repository_metadata "${CONFIG_FILE}" || had_error=1
  apply_repository_topics "${CONFIG_FILE}" || had_error=1
  apply_vulnerability_alerts "${CONFIG_FILE}" || had_error=1
  apply_automated_security_fixes "${CONFIG_FILE}" || had_error=1
  apply_security_and_analysis "${CONFIG_FILE}" || had_error=1

  echo ""
  if [ ${had_error} -eq 0 ]; then
    success "Repository settings configuration complete!"
    echo ""
    exit 0
  else
    error "Some repository settings failed to apply"
    echo ""
    exit 1
  fi
}

# Run main function
main "$@"
