# F5 Distributed Cloud User and Group Sync

Synchronizes users and groups from CSV to F5 Distributed Cloud.

## Getting Started

### 1. Create Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 2. Install

```bash
pip install git+https://github.com/robinmordasiewicz/f5-xc-user-group-sync.git
```

### 3. Setup Credentials

```bash
./scripts/setup_xc_credentials.sh
```

The script will auto-detect your P12 certificate and configure the environment.

### 4. Load Environment

```bash
source secrets/.env
```

### 5. Run

```bash
# Preview changes
xc_user_group_sync --csv User-Database.csv --dry-run

# Apply changes
xc_user_group_sync --csv User-Database.csv

# Full reconciliation (includes cleanup)
xc_user_group_sync --csv User-Database.csv --prune
```

## Documentation

- [Configuration](configuration.md)
- [CLI Reference](cli-reference.md)
- [Troubleshooting](troubleshooting.md)

## CI/CD Examples

- [GitLab CI](CICD/gitlab-ci.md)
- [GitHub Actions](CICD/github-actions.md)
- [Jenkins](CICD/jenkins.md)
