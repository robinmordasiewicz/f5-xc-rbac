# Feature Specification: GitHub Repository Automation

**Feature Branch**: `060-repository-automation`
**Created**: 2025-11-11
**Status**: Reverse-Engineered from Implementation
**Input**: Reverse-engineered from `scripts/repository-settings.sh` implementation

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Apply Branch Protection from Configuration (Priority: P1)

As a repository administrator, I can define branch protection rules in a JSON configuration file and apply them automatically via script, so that branch protection is version-controlled, reproducible, and consistent across repositories.

**Why this priority**: Core functionality - enables infrastructure-as-code for branch protection, preventing manual configuration drift.

**Independent Test**: Create a JSON configuration with branch protection rules, run the script, verify branch protection is applied via GitHub API or web UI.

**Acceptance Scenarios**:

1. **Given** a configuration file with required pull request reviews (2 approvals), **When** script executes, **Then** branch protection is applied with 2 required reviews
2. **Given** existing branch protection differs from config, **When** script executes, **Then** branch protection is updated to match config
3. **Given** configuration enables force push blocking, **When** script executes, **Then** force pushes are blocked on protected branch
4. **Given** configuration enables deletion blocking, **When** script executes, **Then** branch deletion is blocked

---

### User Story 2 - Manage Repository Labels from Configuration (Priority: P2)

As a repository administrator, I can define repository labels (name, color, description) in a JSON configuration file and synchronize them automatically, so that issue/PR labels are consistent and version-controlled.

**Why this priority**: Important for workflow consistency, but not blocking - labels can be managed manually initially.

**Independent Test**: Define labels in JSON config, run script with `--export-labels` to capture current state, modify config, run script to apply changes, verify labels match configuration.

**Acceptance Scenarios**:

1. **Given** configuration defines label "bug" with color "d73a4a", **When** script executes, **Then** label "bug" exists with correct color
2. **Given** label "bug" exists in repository but not in config, **When** script executes with `labels_purge_unlisted: true`, **Then** label "bug" is deleted
3. **Given** label "enhancement" exists with wrong color, **When** script executes, **Then** label is updated to match config color
4. **Given** `--export-labels` flag, **When** script executes, **Then** current labels are exported to configuration file

---

### User Story 3 - Configure Repository Metadata (Priority: P3)

As a repository administrator, I can define repository description, homepage URL, and topics in a JSON configuration file and apply them automatically, so that repository metadata is consistent and discoverable.

**Why this priority**: Nice-to-have for discoverability - lower priority than protection and labels.

**Independent Test**: Define repository metadata in JSON config, run script, verify metadata via GitHub API or web UI.

**Acceptance Scenarios**:

1. **Given** configuration defines description "F5 XC RBAC sync tool", **When** script executes, **Then** repository description is updated
2. **Given** configuration defines topics ["f5", "xc", "rbac", "automation"], **When** script executes, **Then** repository topics are set
3. **Given** configuration defines homepage URL, **When** script executes, **Then** repository homepage is updated

---

### User Story 4 - Enable Security Features (Priority: P2)

As a repository administrator, I can configure security features (vulnerability alerts, automated security fixes, secret scanning, Dependabot) in a JSON configuration file and enable them automatically, so that security posture is consistent and auditable.

**Why this priority**: Important for security compliance, but may require organization-level permissions.

**Independent Test**: Define security settings in JSON config, run script, verify security features are enabled via GitHub API.

**Acceptance Scenarios**:

1. **Given** configuration enables vulnerability alerts, **When** script executes, **Then** vulnerability alerts are enabled
2. **Given** configuration enables automated security fixes, **When** script executes, **Then** automated security fixes are enabled
3. **Given** configuration enables secret scanning, **When** script executes, **Then** secret scanning is enabled (if available for org)
4. **Given** configuration disables Dependabot alerts, **When** script executes, **Then** Dependabot alerts are disabled

---

### Edge Cases

- What happens when GitHub API returns 403 Forbidden (insufficient permissions)? (Script logs warning, continues with remaining settings, exits with non-zero code)
- What happens when configuration file contains invalid JSON? (Script exits with clear error message before making any API calls)
- What happens when branch name in configuration doesn't exist in repository? (Script fails with clear error - branch must exist before protection can be applied)
- What happens when label purge would delete all labels? (Script executes as configured - no safeguard; user should review with dry-run concept)
- What happens when multiple scripts run concurrently? (Last write wins - no locking mechanism; should be run sequentially)
- What happens when GitHub API is rate-limited? (Script fails with rate limit error - no automatic retry; user should wait and re-run)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Script MUST read configuration from JSON file with optional path argument (default: `.github/repository-settings.json`)
- **FR-002**: Script MUST validate JSON configuration file exists and is valid JSON before making any API calls
- **FR-003**: Script MUST require `branch` field when `protection` configuration is present
- **FR-004**: Script MUST apply branch protection settings via GitHub API PUT request to `/repos/{owner}/{repo}/branches/{branch}/protection`
- **FR-005**: Script MUST support all GitHub branch protection options: required pull request reviews, required status checks, enforce admins, required linear history, allow force pushes, allow deletions, required conversation resolution
- **FR-006**: Script MUST create or update repository labels idempotently (update if exists, create if missing)
- **FR-007**: Script MUST support optional label purge via `labels_purge_unlisted` boolean flag (delete labels not in config)
- **FR-008**: Script MUST support `--export-labels` flag to export current labels to configuration file
- **FR-009**: Script MUST URL-encode label names for API requests (handle spaces and special characters)
- **FR-010**: Script MUST normalize hex colors by stripping leading `#` character
- **FR-011**: Script MUST update repository metadata (description, homepage) via GitHub API PATCH request
- **FR-012**: Script MUST set repository topics via GitHub API PUT request to `/repos/{owner}/{repo}/topics`
- **FR-013**: Script MUST enable/disable vulnerability alerts via GitHub API PUT/DELETE to `/repos/{owner}/{repo}/vulnerability-alerts`
- **FR-014**: Script MUST enable/disable automated security fixes via GitHub API PUT/DELETE to `/repos/{owner}/{repo}/automated-security-fixes`
- **FR-015**: Script MUST configure security_and_analysis settings (secret scanning, Dependabot) via GitHub API PATCH
- **FR-016**: Script MUST use GitHub CLI (`gh`) for all API operations
- **FR-017**: Script MUST use `jq` for all JSON parsing and manipulation
- **FR-018**: Script MUST check for required tools (`gh`, `jq`) and fail fast with clear error if missing
- **FR-019**: Script MUST authenticate using `gh` CLI existing authentication (no credentials in script)
- **FR-020**: Script MUST determine repository owner and name automatically from current git repository
- **FR-021**: Script MUST exit with code 0 on success, non-zero on any failure
- **FR-022**: Script MUST log operations with colored output (blue info, green success, yellow warning, red error)
- **FR-023**: Script MUST continue processing remaining settings if individual operations fail (graceful degradation)
- **FR-024**: Script MUST display current branch protection settings before applying changes
- **FR-025**: Script MUST display summary of applied settings after completion

### Key Entities

- **Configuration File**: JSON file containing repository settings with optional sections: `branch`, `protection`, `repository`, `labels`, `labels_purge_unlisted`
- **Branch Protection**: GitHub branch protection rules with settings for required reviews, status checks, force pushes, deletions
- **Label**: Repository label with name, color (hex), and optional description
- **Repository Metadata**: Description, homepage URL, and topics for repository discoverability
- **Security Settings**: Vulnerability alerts, automated security fixes, secret scanning, Dependabot configuration

### Configuration Schema

```json
{
  "branch": "main",
  "protection": {
    "required_pull_request_reviews": {
      "required_approving_review_count": 2,
      "dismiss_stale_reviews": true,
      "require_code_owner_reviews": false
    },
    "required_status_checks": {
      "strict": true,
      "contexts": ["pre-commit"]
    },
    "enforce_admins": false,
    "required_linear_history": false,
    "allow_force_pushes": false,
    "allow_deletions": false,
    "required_conversation_resolution": true
  },
  "repository": {
    "description": "F5 XC User and Group Synchronization Tool",
    "homepage": "https://github.com/robinmordasiewicz/f5-xc-user-group-sync",
    "topics": ["f5", "xc", "rbac", "python", "automation"],
    "vulnerability_alerts": true,
    "automated_security_fixes": true,
    "security_and_analysis": {
      "secret_scanning": {"status": "enabled"},
      "secret_scanning_push_protection": {"status": "enabled"}
    }
  },
  "labels": [
    {
      "name": "bug",
      "color": "d73a4a",
      "description": "Something isn't working"
    },
    {
      "name": "enhancement",
      "color": "a2eeef",
      "description": "New feature or request"
    }
  ],
  "labels_purge_unlisted": false
}
```text
## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Administrators can apply branch protection to a repository in under 30 seconds
- **SC-002**: Running script twice with identical configuration produces zero changes on second run (100% idempotent)
- **SC-003**: Script successfully applies settings across 10 different repositories with 0% failure rate (given correct permissions)
- **SC-004**: Label synchronization handles 100+ labels without errors or timeouts
- **SC-005**: Script detects and reports permission errors with actionable error messages within 5 seconds
- **SC-006**: Configuration validation catches 100% of JSON syntax errors before making API calls
- **SC-007**: Label export captures all existing labels with correct colors and descriptions
- **SC-008**: Script continues and completes remaining operations when individual settings fail (graceful degradation in 100% of cases)

## Implementation Details

### Script Location

- **Path**: `scripts/repository-settings.sh`
- **Language**: Bash (requires bash 4.0+ for associative arrays)
- **Dependencies**: `gh` (GitHub CLI), `jq` (JSON processor)

### Usage

```bash
# Apply settings from default config
./scripts/repository-settings.sh

# Apply settings from custom config
./scripts/repository-settings.sh path/to/config.json

# Export current labels to config
./scripts/repository-settings.sh --export-labels

# Export to custom config
./scripts/repository-settings.sh --export-labels path/to/config.json
```text
### Authentication

- Uses GitHub CLI (`gh`) existing authentication
- Requires `gh auth login` to be completed before running script
- Permissions required: repo (full control), admin:org (for security settings)

### Exit Codes

- `0`: Success - all operations completed successfully
- `1`: Failure - missing tools, invalid config, or API errors

## Assumptions

- GitHub CLI (`gh`) is installed and authenticated
- `jq` JSON processor is installed and available
- Script is executed from within a Git repository with GitHub remote
- User has appropriate permissions in GitHub repository (push access minimum, admin for protection)
- GitHub API is available and accessible
- Configuration file follows specified JSON schema
- Branch specified in configuration already exists in repository
- Organization plan supports requested security features (secret scanning, etc.)
