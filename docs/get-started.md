# Getting Started

## Prerequisites

Before you begin, ensure you have:

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

Use the automated setup script:

```bash
# Auto-detects .p12 file in ~/Downloads
./scripts/setup_xc_credentials.sh

# Or specify P12 file path
./scripts/setup_xc_credentials.sh --p12 ~/Downloads/your-tenant.p12
```

The script will:
- Extract tenant ID from the P12 filename
- Convert P12 to PEM certificate and key files
- Create `secrets/.env` with required variables
- Set GitHub repository secrets (if using CI/CD)

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

## Next Steps

- [Configuration Guide](configuration.md) - Detailed configuration options
- [CLI Reference](cli-reference.md) - Complete command-line reference
- [Development Guide](development.md) - Contributing and development
