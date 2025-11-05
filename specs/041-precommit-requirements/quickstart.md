# Quickstart: Pre-commit + CI Parity

## Local

- Install pre-commit
- Run once to install hooks: `pre-commit install --install-hooks`
- Validate all files: `pre-commit run --all-files`

## CI

- Add a PR-blocking workflow that runs `pre-commit run --all-files` on pull_request.
- Ensure the job is marked as a required status check for the default branch.

## Success Criteria

- All hooks pass locally and in CI.
- CI is required and blocks merges on failures.
