# Task Completion Checklist

## Before Committing Code

### 1. Format Code
```bash
black src/ tests/
```

### 2. Lint Code
```bash
ruff check .
# Fix automatically if possible:
ruff check --fix .
```

### 3. Run Tests
```bash
pytest
# Ensure coverage meets 80% minimum threshold
```

### 4. Type Checking (if mypy is added)
```bash
mypy src/
```

### 5. Manual Verification
- [ ] All new code has docstrings (Google-style)
- [ ] All new code has type hints
- [ ] Protocol interfaces used for dependency injection where appropriate
- [ ] Error handling includes appropriate logging
- [ ] New features have corresponding tests
- [ ] Tests cover edge cases and error paths

### 6. Git Workflow
```bash
# Check status
git status

# Stage changes
git add <files>

# Commit with descriptive message
git commit -m "feat: description of feature"
# or
git commit -m "fix: description of fix"
# or
git commit -m "refactor: description of refactor"

# Push to remote
git push
```

## CI/CD Validation
- GitHub Actions workflow runs on push to main
- Automated dry-run sync validates configuration
- Repository secrets must be configured for actual sync operations

## Release Checklist
- [ ] All tests passing
- [ ] Coverage ≥ 80%
- [ ] No ruff errors
- [ ] Code formatted with black
- [ ] README.md updated if needed
- [ ] CHANGELOG.md updated (if maintained)
- [ ] Version bumped in pyproject.toml
