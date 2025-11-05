<!--
Sync Impact Report
Version change: 2.3.0 → 2.4.0
Modified sections: Quality Gates, Automation Enforcement (Issue-First), Bot/Agent Behavior, Pull Request Checklist, Governance
Added sections: Pre-edit Guard (Bot/Agent hard gate)
Removed sections: (none)
Templates requiring updates:
- plan-template.md ✅ (no change required)
- spec-template.md ✅ (no change required)
- tasks-template.md ✅ (no change required)
Follow-up TODOs:
- TODO(RATIFICATION_DATE): Original ratification date unknown, please supply if available.
-->

# F5-XC-RBAC Constitution

## Core Principles

### Issue-First Development
Every piece of work MUST start with a GitHub issue. No coding, branches, or fixes without an issue. Issues must include problem description, expected behavior, acceptance criteria, and labels.

This is not advisory. It is a policy enforced by automation (see Automation Enforcement).

### Quality Gates
Pre-commit hooks, linting, and tests are mandatory. All code must pass validation checks, and no bypasses are allowed. No hardcoded secrets. Dependencies must be kept up to date.



### Clean History
Feature branches must be deleted after merge (local and remote).

Branch naming is STRICT and enforced: `^[0-9]+-[a-z0-9-]+$`
- The leading number is the GitHub issue number.
- The suffix is a short, kebab-cased description.

Examples: `123-fix-login-timeout`, `45-add-ci-policy-checks`.

### Test-Driven
Write tests before implementation. All business logic must have unit tests (80% minimum coverage). Integration tests required for cross-module interactions. Bug fixes must include a test that would have caught the bug.

## Issue-First Workflow

Issue Labels (MANDATORY)
- Before creating an issue, verify that the required label(s) already exist in the repository.
- If a needed label is missing, create the label first, then create the issue with that label.

Required sequence (enforced):
1. Create Issue (with labels) and capture the issue number N
2. Create Branch named `N-<brief-description>`
3. Write Code on that branch only
4. Open PR with title referencing the issue and body containing `Closes #N`
5. Review
6. Merge
7. Close Issue (auto-closed by `Closes #N` when merged)
8. Delete Branch (local + remote)

If at any point an issue is not present, work MUST stop and an issue MUST be created before proceeding.

## Automation Enforcement (Issue-First)

To guarantee Issue-First behavior, the following gates are MANDATORY:

0) Pre-edit Guard (Bot/Agent hard gate)
- Before ANY file modification or stateful tool call (e.g., apply_patch, create_file, edit_notebook_file), the agent MUST:
	- Verify an open Issue exists and capture its number N;
	- Verify the current branch is named `N-<description>`; if not, create/switch to it;
	- Post the Issue URL in the same assistant message BEFORE performing edits;
	- Include `Refs #N` in the tool "explanation" field for every editing action.
- If the agent lacks permission to create an issue/branch, it MUST halt and request user guidance.

1) Pre-commit (commit-msg stage)
- A commit message gate rejects commits without an issue reference (`#N`) in the subject or body.
- Example requirement: subject must start with `[N]` or contain `Refs #N`/`Closes #N`.

2) Pre-commit (commit/push stages)
- Reject commits on default branch.
- Verify current branch name matches `^[0-9]+-[a-z0-9-]+$`.

3) Pull Request Template (required)
- PR template requires explicit Issue link and `Closes #N` line.
- Reviewers must check the Issue link is correct and complete.

4) CI Policy Workflow (required)
- On pull_request, fail if:
	- PR title/body has no `#N` reference; or
	- Head branch name does not match `^[0-9]+-[a-z0-9-]+$`.
- On merge/push to main, validate that issue auto-closed or PR body included `Closes #N`.

5) Bot/Agent Behavior (Copilot/Automation)
- Before any file modification, the agent MUST:
	- Search for a related open issue; if none exists, create one with the problem statement and acceptance criteria.
	- Create/switch to a branch named with the issue number.
	- Include the issue link in the conversation BEFORE edits, and include the issue reference in all commits, PR descriptions, and edit-tool explanations.
	- Halt and request user guidance only if lacking permissions to create issues/branches.

Non-compliance with any gate MUST block the change until resolved.

## Commit Policy

All commits MUST reference the driving issue number:
- Include `Refs #N` for intermediate work and `Closes #N` in the final commit/PR.
- Commit subject may optionally begin with `[N]` for readability.

Example commit subject lines:
- `[123] Add retry/backoff options to client`
- `Refactor CSV validation (Refs #123)`

## PR Linking Requirements

- PR title must include the issue number or the branch’s issue-derived prefix.
- PR body MUST include `Closes #N` (or `Fixes #N`), ensuring auto-close on merge.

## Code Quality Requirements

- Must use pre-commit framework (read-only validation, no auto-fix)
- No bypasses (`--no-verify` not allowed)
- Validates: Terraform, YAML, JSON, Markdown, Shell scripts, Python, Go
- Must complete in <2 minutes
- Pass all linters without warnings
- Document complex logic with comments

## Testing Requirements

- Test-Driven Development (TDD) for new features
- Unit tests: 80% minimum coverage
- Integration tests for cross-module interactions
- Tests must be fast, deterministic, and isolated
- Bug fixes must include a test

## Pull Request Checklist

- [ ] Issue created FIRST before work began
- [ ] Branch name matches `^[0-9]+-[a-z0-9-]+$` and encodes the issue number
- [ ] All commits reference the issue (e.g., `Refs #N`); PR body includes `Closes #N`
- [ ] Agent posted the Issue link in the conversation before any edits (automation evidence)
- [ ] Tests added and passing
- [ ] Documentation updated
 - [ ] No linting errors
- [ ] All CI checks passing

## Definition of Done

Work is complete when:
1. Issue created first
2. Code written
3. All tests passing
4. Documentation updated
5. PR merged
6. Issue closed
7. Branch deleted (local + remote)
<!-- Example: Code review requirements, testing gates, deployment approval process, etc. -->


## Governance

- This constitution supersedes all other practices.
- Amendments require documentation, approval, and migration plan.
- All PRs must verify compliance.
- Versioning follows semantic rules: MAJOR for principle changes, MINOR for additions, PATCH for clarifications.
- Compliance checks are mandatory for every merge.

**Version**: 2.1.0 | **Ratified**: TODO(RATIFICATION_DATE): Original ratification date unknown | **Last Amended**: 2025-11-03
**Version**: 2.3.0 | **Ratified**: TODO(RATIFICATION_DATE): Original ratification date unknown | **Last Amended**: 2025-11-05
**Version**: 2.4.0 | **Ratified**: TODO(RATIFICATION_DATE): Original ratification date unknown | **Last Amended**: 2025-11-05
