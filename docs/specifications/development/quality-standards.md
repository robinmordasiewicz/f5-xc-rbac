# Development Quality Standards

> **Status**: Mandatory for all development work
> **Last Updated**: 2025-11-13
> **Version**: 1.0.0

## 1. Overview

This document defines **MANDATORY** development standards that ALL contributors MUST follow. No development work shall proceed without strict adherence to these requirements. These standards ensure code quality, security, and maintainability through automated enforcement.

**Key Principle**: All pre-commit checks MUST be enforced locally AND in CI/CD pipelines with zero tolerance for violations.

## 2. Pre-commit Hook Requirements

### 2.1 Code Formatting Standards

**FR-DEV-001**: Pre-commit hooks MUST enforce consistent code formatting across all file types:

- **Python**: Black formatter (`black --check`, line length 88)
- **Shell Scripts**: shfmt formatter (`shfmt -i 2 -ci`)
- **Line Endings**: LF (Unix) line endings enforced across all text files
- **End-of-File**: All files MUST end with single newline character
- **Trailing Whitespace**: Automatically removed from all lines
- **EditorConfig**: All files MUST comply with `.editorconfig` rules

**Rationale**: Consistent formatting eliminates style debates, reduces merge conflicts, and ensures professional code quality.

**Enforcement**: Pre-commit hook runs before every commit; CI blocks PRs on formatting violations.

### 2.2 Linting Requirements

**FR-DEV-002**: Pre-commit hooks MUST enforce comprehensive linting standards:

- **Python**: Ruff linter (no autofix in CI, strict mode)
- **Shell Scripts**: ShellCheck (`-S error`, severity threshold: error only)
- **Markdown**: PyMarkdown with repository configuration (`.pymarkdown.json`)
- **YAML**: `check-yaml` + `sort-simple-yaml` for validation and consistency
- **JSON**: Validation + pretty-format (no key sorting to preserve intent)
- **VCS Hygiene**: Check for merge conflicts, case conflicts, large files, VCS permalinks

**Rationale**: Early detection of code issues prevents bugs, improves maintainability, and enforces best practices.

**Enforcement**: Zero linting errors tolerated; CI blocks PRs on any violation.

### 2.3 Security Scanning Requirements

**FR-DEV-003**: Pre-commit hooks MUST perform comprehensive security scanning:

- **Secret Detection**: `detect-secrets` with maintained baseline (`.secrets.baseline`)
    - Excludes: `secrets/` directory (documented safe paths)
    - Baseline updated only for intentional test fixtures
    - New secrets detected: **PR blocked immediately**

- **Python Security SAST**: Bandit static analysis
    - Severity threshold: MEDIUM or higher blocks PR
    - Configuration: `.bandit` with security-focused rules
    - Target: All Python code in `src/` and `tests/`

- **Dependency Vulnerabilities**: pip-audit scans Python dependencies
    - Severity threshold: HIGH or CRITICAL blocks PR
    - Runs on: `requirements.txt`, `pyproject.toml`
    - Private package handling: Configured exclusions for internal dependencies

**Rationale**: Prevent security vulnerabilities from entering codebase; shift-left security to development phase.

**Enforcement**: Any security violation **immediately blocks** PR merge; no exceptions.

### 2.4 Repository Policy Gates

**FR-DEV-004**: Pre-commit hooks MUST enforce repository workflow policies:

- **Branch Protection**: Direct commits to `main` branch are **FORBIDDEN**
- **Branch Naming**: All branches MUST match regex `^[0-9]+-[a-z0-9-]+$` (e.g., `123-fix-auth`)
- **Commit Messages**: MUST reference GitHub issue (e.g., "Fixes #123" or "#123")
- **Enforcement**: Pre-commit hook validates locally; CI double-checks compliance

**Rationale**: Ensures all work is tracked via issues, prevents accidental main branch commits, maintains clean git history.

**Enforcement**: Violations prevent commit locally; CI blocks untracked work.

### 2.5 Code Duplication (DRY) Requirements

**FR-DEV-005**: Pre-commit hooks MUST enforce DRY (Don't Repeat Yourself) principle:

- **Threshold**: Duplicate blocks ≥15 lines appearing in ≥2 locations are violations
- **Scanner**: jscpd (Copy/Paste Detector) configured in `.jscpd.json`
- **Scope**: Python, Shell, YAML, Markdown files
- **Exclusions**: Generated code, vendored dependencies (documented in config)

**Rationale**: Reduces maintenance burden, prevents bug duplication, encourages modular design.

**Enforcement**: Any duplication violation **blocks PR merge**.

### 2.6 GitHub Actions Workflow Linting

**FR-DEV-006**: Pre-commit hooks MUST lint all GitHub Actions workflows:

- **Tool**: actionlint via pre-commit hook and CI
- **Scope**: All `.github/workflows/*.yml` files
- **Validation**: Syntax, action versions, job dependencies, shell correctness

**Rationale**: Prevents CI/CD pipeline failures from invalid workflow syntax or deprecated actions.

**Enforcement**: Any actionlint violation blocks PR merge.

## 3. CI/CD Integration Requirements

### 3.1 Local-CI Parity

**FR-DEV-007**: CI MUST mirror ALL pre-commit checks with identical versions and configurations:

**Parity Matrix**:

| Check | Local (pre-commit) | CI (GitHub Actions) | Status |
|-------|-------------------|---------------------|---------|
| Black | `.pre-commit-config.yaml` version | Same version in CI | ✅ Required |
| Ruff | `.pre-commit-config.yaml` version | Same version in CI | ✅ Required |
| ShellCheck | `.pre-commit-config.yaml` version | Same version in CI | ✅ Required |
| PyMarkdown | `.pre-commit-config.yaml` version | Same version in CI | ✅ Required |
| detect-secrets | `.pre-commit-config.yaml` version | Same version in CI | ✅ Required |
| Bandit | `.pre-commit-config.yaml` version | Same version in CI | ✅ Required |
| pip-audit | `.pre-commit-config.yaml` version | Same version in CI | ✅ Required |
| actionlint | `.pre-commit-config.yaml` version | Same version in CI | ✅ Required |
| jscpd | `.pre-commit-config.yaml` version | Same version in CI | ✅ Required |

**Rationale**: Eliminates "works on my machine" issues; ensures consistent quality gates; prevents CI surprises.

**Enforcement**: CI runs `pre-commit run --all-files` with identical configuration; any failure **blocks PR merge**.

### 3.2 PR Blocking Requirements

**FR-DEV-008**: GitHub Actions workflow MUST block PR merges on ANY pre-commit check failure:

- **Workflow**: `.github/workflows/pre-commit.yml` (required status check)
- **Trigger**: Every PR commit
- **Behavior**: Runs all pre-commit hooks; any failure = PR blocked
- **Branch Protection**: `main` branch requires "pre-commit" status check to pass

**Rationale**: Enforces quality gates at merge time; prevents substandard code from entering main branch.

**Enforcement**: GitHub branch protection rules + required status checks.

### 3.3 Hook Version Management

**FR-DEV-009**: Pre-commit hook versions MUST be managed with strict controls:

- **Versioning**: All hooks pinned to immutable SHAs or semantic version tags
- **Updates**: Reviewed quarterly minimum; captured in CHANGELOG
- **Validation**: Version updates tested in CI before merging
- **Rollback**: Previous working versions documented for emergency rollback

**Rationale**: Prevents surprise breakage from upstream hook changes; maintains reproducible builds.

**Enforcement**: `.pre-commit-config.yaml` uses only pinned versions; automated alerts for outdated hooks.

## 4. Development Workflow Standards

### 4.1 Local Development Setup

**FR-DEV-010**: All developers MUST install pre-commit hooks before first commit:

```bash
# Install pre-commit framework
pip install pre-commit

# Install project hooks
pre-commit install

# Verify installation
pre-commit run --all-files
```

**Rationale**: Catches issues before commit; provides fast feedback loop.

**Enforcement**: CI detects commits without pre-commit signatures; onboarding documentation mandates setup.

### 4.2 Commit Workflow

**Required Workflow**:

1. **Feature Branch**: Create branch following naming convention (`###-feature-name`)
2. **Local Development**: Write code with real-time linting feedback
3. **Pre-commit Check**: Hooks run automatically on `git commit`
4. **Fix Issues**: Address all hook failures before commit completes
5. **Push**: Only clean commits reach remote repository
6. **CI Validation**: GitHub Actions re-validates all checks
7. **PR Review**: Human review after automated checks pass
8. **Merge**: Only after CI success + approvals

**Forbidden Patterns**:

- ❌ `git commit --no-verify` (bypassing hooks)
- ❌ `SKIP=hook-name git commit` (selectively skipping hooks)
- ❌ Committing directly to `main` branch
- ❌ Force-pushing to shared branches

### 4.3 Continuous Integration Workflow

**FR-DEV-011**: CI MUST run on every PR commit with the following stages:

**Stage 1: Pre-commit Validation** (required, blocking)

```yaml
- Run: pre-commit run --all-files
- Fail-Fast: true
- Blocks: Merge
```

**Stage 2: Unit Tests** (required, blocking)

```yaml
- Run: pytest tests/unit/
- Coverage: ≥90% required
- Blocks: Merge
```

**Stage 3: Integration Tests** (required, blocking)

```yaml
- Run: pytest tests/integration/
- Blocks: Merge
```

**Stage 4: Build Validation** (required, blocking)

```yaml
- Run: pip install -e .
- Validate: Package installs successfully
- Blocks: Merge
```

## 5. Success Criteria for Development Requirements

**SC-DEV-001**: 100% of commits pass local pre-commit hooks before push

**Measurement**: Pre-commit hook failure rate = 0% in CI (all failures caught locally)

**SC-DEV-002**: 0 violations in quarterly security audits

**Measurement**: Bandit, pip-audit, detect-secrets find zero issues in main branch

**SC-DEV-003**: 100% CI/CD parity with local checks

**Measurement**: Identical tool versions in `.pre-commit-config.yaml` and `.github/workflows/pre-commit.yml`

**SC-DEV-004**: 0 formatting inconsistencies across codebase

**Measurement**: `black --check` and `shfmt` report zero changes when run on entire repository

**SC-DEV-005**: 0 code duplication violations above DRY threshold

**Measurement**: jscpd reports zero violations of ≥15 lines in ≥2 locations

**SC-DEV-006**: 100% branch naming compliance

**Measurement**: All branches in repository match pattern `^[0-9]+-[a-z0-9-]+$`

**SC-DEV-007**: 0 direct commits to main branch

**Measurement**: Git history shows no commits directly to main (all via PR)

**SC-DEV-008**: 100% of PRs blocked on quality failures

**Measurement**: GitHub branch protection enforces all required status checks

## 6. Tool Configuration Reference

**Pre-commit Configuration**: `.pre-commit-config.yaml`
**PyMarkdown Configuration**: `.pymarkdown.json`
**Bandit Configuration**: `.bandit`
**jscpd Configuration**: `.jscpd.json`
**EditorConfig**: `.editorconfig`
**Secrets Baseline**: `.secrets.baseline`

## 7. Troubleshooting

### Common Issues

**Issue: Pre-commit hooks not running**

```bash
# Solution: Reinstall hooks
pre-commit uninstall
pre-commit install
pre-commit run --all-files
```

**Issue: Hook version conflicts**

```bash
# Solution: Clear cache and reinstall
pre-commit clean
pre-commit install-hooks
```

**Issue: False positive in detect-secrets**

```bash
# Solution: Update baseline (only if verified safe)
detect-secrets scan > .secrets.baseline
git add .secrets.baseline
```

**Issue: jscpd duplication false positive**

- Solution: Refactor code to eliminate duplication, or
- Document why duplication is necessary and add to exclusions in `.jscpd.json`

### Getting Help

For questions about development standards:

1. Check this document first
2. Review `.pre-commit-config.yaml` for hook configurations
3. Check CI logs for detailed error messages
4. Open GitHub issue with `question` label

## 8. Related Documentation

- **System Requirements Specification**: `../requirements/user-group-sync-srs.md`
- **CI/CD Integration Guide**: `../guides/github-actions-guide.md` (planned)
- **Setup Guide**: `../../README.md`
- **Pre-commit Configuration**: `../../.pre-commit-config.yaml`
