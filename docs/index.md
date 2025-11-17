# F5 Distributed Cloud User and Group Sync

Automated synchronization tool for managing F5 XC users and groups from CSV user databases.

Synchronizes users and groups between your CSV database and F5 Distributed Cloud:

- Creates users/groups that exist in CSV but not in F5 XC
- Updates user attributes and group memberships to match CSV
- Optionally prunes users/groups not in CSV (with `--prune` flag)

## Prerequisites

1. **Python 3.9 or higher** installed

   ```bash
   python3 --version  # Should show 3.9 or higher
   ```

2. **F5 XC API credentials** (P12 certificate with password)
   - Download from: F5 XC Console → Administration → Credentials → API Credentials
   - Save the `.p12` file securely (e.g., `~/Downloads/your-tenant.p12`)

3. **CSV export** from your user database
   - Must include user emails and group memberships in LDAP DN format

## Installation

### Option 1: Local Development Installation

```bash
# Clone the repository
git clone https://github.com/robinmordasiewicz/f5-xc-user-group-sync.git
cd f5-xc-user-group-sync

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode
pip install -e .

# Verify installation
xc_user_group_sync --help
```

### Option 2: Direct Installation from Git

```bash
# Install directly from GitHub
pip install git+https://github.com/robinmordasiewicz/f5-xc-user-group-sync.git

# Verify installation
xc_user_group_sync --help
```

## Quick Start

### 1. Setup Credentials

Use the automated setup script with intelligent proxy detection:

```bash
# Auto-detects .p12 file in ~/Downloads
./scripts/setup_xc_credentials.sh

# Or specify P12 file path
./scripts/setup_xc_credentials.sh --p12 ~/Downloads/your-tenant.p12

# Optionally set GitHub repository secrets for CI/CD
./scripts/setup_xc_credentials.sh --p12 ~/Downloads/your-tenant.p12 --github-secrets
```

The script will:
- Extract tenant ID from the P12 filename
- Copy P12 file to `secrets/` directory
- **Test API connectivity** to detect network requirements
- **Prompt for proxy configuration** if direct connection fails (interactive mode)
- Create `secrets/.env` with P12 authentication and optional proxy settings
- Optionally set GitHub repository secrets (with `--github-secrets` flag)

**Intelligent Proxy Detection**:
- ✅ **Direct connection works**: No proxy configuration added
- ⚠️ **Connection fails**: Interactive prompts guide through proxy setup
  - Asks if you use a corporate proxy
  - Tests proxy connectivity
  - Detects MITM SSL inspection needs
  - Prompts for CA certificate location
  - Adds proxy settings to `secrets/.env` automatically

**Note**: The tool uses native P12 authentication. Certificate and key are extracted at runtime into temporary files and automatically cleaned up.

### 2. Prepare Your CSV File

See the [CSV Format](configuration.md#csv-format) section for complete specifications.

### 3. Test with Dry-Run

Always test first to preview changes:

```bash
source secrets/.env
xc_user_group_sync --csv ./User-Database.csv --dry-run
```

### 4. Apply Changes

Once satisfied with dry-run results:

```bash
xc_user_group_sync --csv ./User-Database.csv
```

See [CLI Reference](cli-reference.md) for all available options including `--prune`, `--log-level`, `--timeout`, and more.

## Documentation

- **[CLI Reference](cli-reference.md)** - Command options
- **[Configuration](configuration.md)** - Environment variables and CSV format
- **[Troubleshooting](troubleshooting.md)** - Common issues

### CI/CD Examples

- **[GitHub Actions](CICD/github-actions.md)** - Automated workflow
- **[GitLab CI](CICD/gitlab-ci.md)** - Pipeline configuration
- **[Jenkins](CICD/jenkins.md)** - Jenkinsfile example

## Support

- **Repository**: [github.com/robinmordasiewicz/f5-xc-user-group-sync](https://github.com/robinmordasiewicz/f5-xc-user-group-sync)
- **Issues**: [GitHub Issues](https://github.com/robinmordasiewicz/f5-xc-user-group-sync/issues)
