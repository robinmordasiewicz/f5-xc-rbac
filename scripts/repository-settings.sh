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

  # Check required fields
  if ! jq -e '.branch' "${config_file}" >/dev/null 2>&1; then
    error "Configuration file missing required field: 'branch'"
    exit 1
  fi

  if ! jq -e '.protection' "${config_file}" >/dev/null 2>&1; then
    error "Configuration file missing required field: 'protection'"
    exit 1
  fi

  success "Configuration file validated: ${config_file}"
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
  branch=$(jq -r '.branch' "${CONFIG_FILE}")
  echo ""
  get_current_protection "${branch}" || true
  echo ""

  # Apply protection settings
  if apply_protection "${CONFIG_FILE}"; then
    show_summary "${CONFIG_FILE}"
    echo ""
    success "Repository settings configuration complete!"
    echo ""
    exit 0
  else
    echo ""
    error "Failed to apply repository settings"
    echo ""
    exit 1
  fi
}

# Run main function
main "$@"
