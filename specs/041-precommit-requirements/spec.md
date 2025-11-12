# Feature Specification: [FEATURE NAME]

**Feature Branch**: `[###-feature-name]`
**Created**: [DATE]
**Status**: Draft
**Input**: User description: "$ARGUMENTS"

## Clarifications

### Session 2025-11-05

- Q: Should all pre-commit checks be mirrored and enforced in CI (PR-blocking) to guarantee parity and prevent bypass? → A: Enforce pre-commit checks in CI and block merges (Local + CI parity).
- Q: Should we enforce a quantitative DRY threshold to block PRs on significant duplication? → A: Duplicate blocks ≥15 lines appearing in ≥2 locations must block PRs.

### Session 2025-11-06

- Q: CSV-driven sync behavior: should the CSV be authoritative for group existence and membership, including creating groups, creating users when missing, and adding users to groups when absent? → A: Yes. The CSV MUST be used to ensure groups exist (create if missing), create users when they do not exist, and add users to the groups defined in the CSV when they are not already members.

## User Scenarios & Testing *(mandatory)*

<!--
  IMPORTANT: User stories should be PRIORITIZED as user journeys ordered by importance.
  Each user story/journey must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
  you should still have a viable MVP (Minimum Viable Product) that delivers value.

  Assign priorities (P1, P2, P3, etc.) to each story, where P1 is the most critical.
  Think of each story as a standalone slice of functionality that can be:

  - Developed independently
  - Tested independently
  - Deployed independently
  - Demonstrated to users independently

-->

### User Story 1 - [Brief Title] (Priority: P1)

[Describe this user journey in plain language]

**Why this priority**: [Explain the value and why it has this priority level]

**Independent Test**: [Describe how this can be tested independently - e.g., "Can be fully tested by [specific action] and delivers [specific value]"]

**Acceptance Scenarios**:

1. **Given** [initial state], **When** [action], **Then** [expected outcome]
2. **Given** [initial state], **When** [action], **Then** [expected outcome]

---

### User Story 2 - [Brief Title] (Priority: P2)

[Describe this user journey in plain language]

**Why this priority**: [Explain the value and why it has this priority level]

**Independent Test**: [Describe how this can be tested independently]

**Acceptance Scenarios**:

1. **Given** [initial state], **When** [action], **Then** [expected outcome]

---

### User Story 3 - [Brief Title] (Priority: P3)

[Describe this user journey in plain language]

**Why this priority**: [Explain the value and why it has this priority level]

**Independent Test**: [Describe how this can be tested independently]

**Acceptance Scenarios**:

1. **Given** [initial state], **When** [action], **Then** [expected outcome]

---

[Add more user stories as needed, each with an assigned priority]

### Edge Cases

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right edge cases.
-->

- What happens when [boundary condition]?
- How does system handle [error scenario]?

- If a CSV references a user that cannot be created automatically (missing required attributes or external identity provider rejection), the system MUST log the failure and continue processing other rows; the row should be reported in an errors summary and optionally written to a failure report for manual remediation.
- When group creation fails due to name validation or collision, the system MUST skip that group, record the failure, and continue processing other groups; collisions with existing system-managed groups must be treated as errors and surfaced for human review.
- Membership operations MUST be resilient to transient API failures (retries with backoff in accordance with repository backoff policy) and avoid partial-commit states: where practical, group creation and membership assignments for a single CSV row should be retried; permanent failures should be recorded and summarized.

## Requirements *(mandatory)*

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right functional requirements.
-->

### Functional Requirements

- **FR-001**: System MUST [specific capability, e.g., "allow users to create accounts"]
- **FR-002**: System MUST [specific capability, e.g., "validate email addresses"]
- **FR-003**: Users MUST be able to [key interaction, e.g., "reset their password"]
- **FR-004**: System MUST [data requirement, e.g., "persist user preferences"]
- **FR-005**: System MUST [behavior, e.g., "log all security events"]

*Example of marking unclear requirements:*

- **FR-006**: System MUST authenticate users via [NEEDS CLARIFICATION: auth method not specified - email/password, SSO, OAuth?]
- **FR-007**: System MUST retain user data for [NEEDS CLARIFICATION: retention period not specified]

<!-- Pre-commit and CI parity requirements (clarified 2025-11-05) -->

- **FR-008**: Pre-commit MUST enforce formatting across the codebase: Black (Python, --check), shfmt (shell, -i 2 -ci), EditorConfig compliance, end-of-file newline, trailing whitespace cleanup, and consistent LF line endings.
- **FR-009**: Pre-commit MUST enforce linting: Ruff (Python, no autofix in CI), ShellCheck (-S error), Markdown lint (PyMarkdown with repo-config), YAML validation (check-yaml + sort-simple-yaml), JSON validation/pretty-format (no key sort), and basic VCS hygiene checks (merge conflicts, case conflicts, large files, VCS permalinks).
- **FR-010**: Security scanning MUST run in pre-commit: detect-secrets (with maintained baseline excluding known benign paths like secrets/), Python security SAST (Bandit, severity=MEDIUM+ fail), and dependency vulnerability scan (pip-audit; fail on high/critical).
- **FR-011**: Repository policy gates MUST be enforced: disallow commits to main, require branch naming regex ^[0-9]+-[a-z0-9-]+$, and require commit messages reference an issue (e.g., "#N").
- **FR-012**: CI MUST mirror all pre-commit checks and block merges on any failure (PR-required status). The CI job MUST run the same versions/config as local hooks (parity).
- **FR-013**: Hook versions MUST be pinned (immutable SHAs/tags) and reviewed/updated at least quarterly; changes MUST be captured in the changelog and validated in CI.
- **FR-014**: Secrets and sensitive material MUST NOT be committed. The repository MUST .gitignore secrets/ and similar paths; detect-secrets baseline MUST be updated when intentional test fixtures create deterministic matches.
- **FR-015**: Lint/format/security checks MUST be runnable locally via pre-commit and reproducible in CI (e.g., "pre-commit run --all-files" in CI).

- **FR-016**: GitHub Actions workflows MUST be linted by actionlint via pre-commit and in CI; any violation blocks PRs.

- **FR-018**: CSV-driven synchronization MUST ensure group existence: when the CSV references a group name that does not exist in the target system, the system MUST create the group prior to assigning users.
- **FR-019**: CSV-driven synchronization MUST ensure user existence: when the CSV references a user (email/username) that does not exist in the target system, the system MUST create the user (with necessary minimal attributes drawn from the CSV or configured defaults) before attempting to add them to groups.
- **FR-020**: CSV-driven synchronization MUST ensure membership: for each group/user mapping in the CSV, if the user is not already a member of the specified group, the system MUST add the user to the group. These operations MUST be idempotent (re-running the same CSV must not produce duplicate memberships) and must respect dry-run mode.

- **FR-017**: Code MUST follow DRY. Duplicate blocks of ≥15 lines occurring in ≥2 locations are violations. A duplication detector (e.g., jscpd or equivalent) MUST run in pre-commit and CI across relevant text/code types (Python, Shell, YAML, Markdown). Generated code, vendored dependencies, and explicitly documented exclusions MAY be ignored via configuration. Any violation MUST block PRs.

### Key Entities *(include if feature involves data)*

- **[Entity 1]**: [What it represents, key attributes without implementation]
- **[Entity 2]**: [What it represents, relationships to other entities]

### CSV Sync Entities

- **User**: identified by email or username. Key attributes: email, username (optional alias), display_name (optional), created_at. Uniqueness: email is canonical unique identifier.
- **Group**: identified by name (CN derived from DN). Key attributes: name, display_name, member list. Relationship: many-to-many (users ↔ groups).
- **Membership**: association between User and Group. Operations: create, delete, query. Idempotent semantics required.

## Success Criteria *(mandatory)*

<!--
  ACTION REQUIRED: Define measurable success criteria.
  These must be technology-agnostic and measurable.
-->

### Measurable Outcomes

- **SC-001**: [Measurable metric, e.g., "Users can complete account creation in under 2 minutes"]
- **SC-002**: [Measurable metric, e.g., "System handles 1000 concurrent users without degradation"]
- **SC-003**: [User satisfaction metric, e.g., "90% of users successfully complete primary task on first attempt"]
- **SC-004**: [Business metric, e.g., "Reduce support tickets related to [X] by 50%"]

<!-- Pre-commit acceptance criteria (clarified 2025-11-05) -->

- **SC-005**: CI enforces PR-blocking "lint" workflow mirroring pre-commit; any failure blocks merge (0 policy violations allowed).
- **SC-006**: Formatting passes with 0 changes when running "black --check" and shfmt on the entire repository; EditorConfig checker reports 0 errors.
- **SC-007**: Linting passes with 0 errors: Ruff (exit code 0), ShellCheck (exit code 0), PyMarkdown (exit code 0), YAML/JSON checks (exit code 0).
- **SC-008**: Security passes: detect-secrets finds 0 new secrets (baseline clean), Bandit reports 0 MEDIUM/HIGH issues, and pip-audit reports 0 HIGH/CRITICAL vulnerabilities.
- **SC-009**: Policy gates pass: no direct commits to main observed in history; branch names and commit messages conform to policy in all new commits.

- **SC-010**: Duplication scan reports 0 violations at the DRY threshold (≥15 lines in ≥2 locations). Any needed exclusions are documented in the configuration and referenced in the PR description.
