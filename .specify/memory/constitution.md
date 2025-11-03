<!--
Sync Impact Report
Version change: previous → 2.0.0
Modified principles: replaced all with new set (see below)
Added sections: Issue-First Workflow, Code Quality, Testing, PR Checklist, Definition of Done
Removed sections: Library-First, CLI Interface, Observability, etc.
Templates requiring updates:
- plan-template.md ✅
- spec-template.md ✅
- tasks-template.md ✅
Follow-up TODOs:
- TODO(RATIFICATION_DATE): Original ratification date unknown, please supply if available.
-->

# F5-XC-RBAC Constitution

## Core Principles

### Issue-First Development
Every piece of work MUST start with a GitHub issue. No coding, branches, or fixes without an issue. Issues must include problem description, expected behavior, acceptance criteria, and labels.

### Quality Gates
Pre-commit hooks, linting, and tests are mandatory. All code must pass validation checks, and no bypasses are allowed. Code review is required before merge. No hardcoded secrets. Dependencies must be kept up to date.

### Review Required
All code MUST be reviewed and approved before merging. No direct commits to main. PRs must link to issues and pass all checks.

### Clean History
Feature branches must be deleted after merge (local and remote). Branch naming follows `[issue-number]-brief-description`.

### Test-Driven
Write tests before implementation. All business logic must have unit tests (80% minimum coverage). Integration tests required for cross-module interactions. Bug fixes must include a test that would have caught the bug.

## Issue-First Workflow

1. Create Issue → 2. Create Branch → 3. Write Code → 4. Open PR → 5. Review → 6. Merge → 7. Close Issue → 8. Delete Branch

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
- [ ] Tests added and passing
- [ ] Documentation updated
- [ ] No linting errors
- [ ] Code reviewed and approved
- [ ] All CI checks passing

## Definition of Done

Work is complete when:
1. Issue created first
2. Code written and reviewed
3. All tests passing
4. Documentation updated
5. PR merged
6. Issue closed
7. Branch deleted (local + remote)
<!-- Example: Code review requirements, testing gates, deployment approval process, etc. -->


## Governance

- This constitution supersedes all other practices.
- Amendments require documentation, approval, and migration plan.
- All PRs/reviews must verify compliance.
- Versioning follows semantic rules: MAJOR for principle changes, MINOR for additions, PATCH for clarifications.
- Compliance review is mandatory for every merge.

**Version**: 2.0.0 | **Ratified**: TODO(RATIFICATION_DATE): Original ratification date unknown | **Last Amended**: 2025-11-03
