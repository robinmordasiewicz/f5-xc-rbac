# Contract: CI Lint Workflow (PR-blocking)

## Purpose

Mirror local pre-commit checks in CI and block merges on any failure.

## Inputs

- Trigger: pull_request
- Runner: ubuntu-latest (or macos-latest if required)

## Steps (high-level)

1. Checkout code
2. Set up Python 3.12
3. Install pre-commit and tools
4. Run `pre-commit run --all-files`

## Pass/Fail Signals

- Success: All hooks exit 0; required status check passes; PR merge allowed.
- Failure: Any non-zero exit; required status blocks merge.

## Non-Goals

- Auto-fixing or committing changes from CI.
