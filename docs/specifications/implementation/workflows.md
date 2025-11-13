---
title: Operational Workflows
last_updated: 2025-11-13
version: 1.0.0
status: Production Ready
audience: DevOps Engineers, IAM Administrators, Platform Engineers
---

## Overview

This document defines operational workflows for F5 XC User and Group Sync tool, covering initial setup, regular synchronization, and prune operations. Each workflow provides step-by-step instructions, prerequisites, validation criteria, and expected outcomes for DevOps engineers, IAM administrators, and platform engineers managing user and group synchronization.

## Initial Setup Workflow

**Scenario**: DevOps engineer setting up tool for first time

**Prerequisites**:

- Python 3.9+ installed
- Access to F5 XC tenant with P12 certificate or API token
- CSV export from Active Directory

**Steps**:

1. **Clone Repository & Install**

   ```bash
   git clone https://github.com/organization/f5-xc-user-group-sync.git
   cd f5-xc-user-group-sync
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -e .
   ```

2. **Run Credential Setup Script**

   ```bash
   # With P12 file in ~/Downloads
   ./scripts/setup_xc_credentials.sh

   # Or with explicit path
   ./scripts/setup_xc_credentials.sh --p12 /path/to/tenant.p12

   # Script will:
   # - Auto-detect environment (production/staging)
   # - Extract cert/key from P12
   # - Create secrets/.env with configuration
   # - Optionally configure GitHub secrets
   ```

3. **Verify Configuration**

   ```bash
   # Check secrets/.env was created
   cat secrets/.env

   # Should contain:
   # TENANT_ID=your-tenant
   # XC_API_URL=https://your-tenant.console.ves.volterra.io
   # VOLT_API_CERT_FILE=/path/to/cert.pem
   # VOLT_API_CERT_KEY_FILE=/path/to/key.pem
   ```

4. **Test with Dry-Run**

   ```bash
   xc_user_group_sync sync --csv User-Database.csv --dry-run

   # Should display:
   # - Dry-run banner
   # - Planned groups from CSV
   # - Existing groups in F5 XC
   # - Planned operations (create/update)
   # - Operation summary
   # - Execution time
   ```

5. **Execute First Sync**

   ```bash
   # After validating dry-run output
   xc_user_group_sync sync --csv User-Database.csv

   # Monitor output for errors
   # Verify success with operation summary
   ```

**Validation**:
- ✅ Configuration loaded successfully
- ✅ Dry-run shows expected operations
- ✅ Sync completes without errors
- ✅ Groups visible in F5 XC console

---

## Regular Synchronization Workflow

**Scenario**: IAM administrator performing periodic group sync

**Frequency**: Daily, weekly, or on-demand

**Steps**:

1. **Export Latest CSV from Active Directory**

   ```powershell
   # Active Directory export command (example)
   Get-ADGroupMember -Identity "All Groups" -Recursive |
     Export-Csv -Path "User-Database.csv" -NoTypeInformation
   ```

2. **Review CSV Changes**

   ```bash
   # Compare with previous export
   diff previous-export.csv User-Database.csv | head -20

   # Count groups and users
   csvcut -c "Entitlement Display Name" User-Database.csv | sort -u | wc -l
   csvcut -c "Email" User-Database.csv | sort -u | wc -l
   ```

3. **Perform Dry-Run Validation**

   ```bash
   xc_user_group_sync sync --csv User-Database.csv --dry-run

   # Review planned operations:
   # - New groups to create
   # - Groups with membership changes
   # - Expected user count changes
   ```

4. **Execute Synchronization**

   ```bash
   # Standard sync (create + update)
   xc_user_group_sync sync --csv User-Database.csv

   # Or with pruning (delete orphaned resources)
   xc_user_group_sync sync --csv User-Database.csv --prune
   ```

5. **Verify Results**

   ```bash
   # Check operation summary:
   # - created: New groups added
   # - updated: Groups with membership changes
   # - deleted: Orphaned groups removed (if --prune)
   # - unchanged: Groups matching CSV
   # - errors: Failed operations (investigate)

   # If errors > 0:
   # - Review error details in output
   # - Check F5 XC API logs
   # - Verify CSV data quality
   # - Retry failed operations if transient
   ```

6. **Validate in F5 XC Console** (Optional)
   - Log into F5 XC console
   - Navigate to IAM → User Groups
   - Spot-check random groups for correct membership
   - Verify new groups are present

**Validation**:
- ✅ CSV export contains latest AD data
- ✅ Dry-run shows expected changes
- ✅ Sync completes with errors=0
- ✅ Operation counts match expectations
- ✅ Spot-checks confirm accuracy

---

## Prune Operation Workflow

**Scenario**: Platform engineer performing full reconciliation to remove orphaned resources

**When to Prune**:
- After major organizational restructuring
- When cleaning up test/obsolete groups
- Quarterly reconciliation for audit compliance
- After decommissioning applications

**Steps**:

1. **Backup Current State** (Recommended)

   ```bash
   # Export current F5 XC groups for backup
   curl -X GET \
     "https://${TENANT_ID}.console.ves.volterra.io/api/web/namespaces/system/user_groups" \
     --cert ${VOLT_API_CERT_FILE} \
     --key ${VOLT_API_CERT_KEY_FILE} \
     > f5xc-groups-backup-$(date +%Y%m%d).json
   ```

2. **Dry-Run with Prune Flag**

   ```bash
   xc_user_group_sync sync --csv User-Database.csv --prune --dry-run

   # Carefully review prune section:
   # - Groups to be deleted (not in CSV)
   # - Users to be deleted (not in any CSV group)
   # - Verify these are truly orphaned/unwanted
   ```

3. **Validate Prune Targets**
   - Review list of resources to be deleted
   - Confirm with IAM team these are intended deletions
   - Check for production-critical groups
   - Verify no active users will lose access unintentionally

4. **Execute Prune Operation**

   ```bash
   # Only after validation!
   xc_user_group_sync sync --csv User-Database.csv --prune

   # Monitor both:
   # - Main sync summary (create/update)
   # - Prune summary (deleted counts)
   ```

5. **Post-Prune Verification**

   ```bash
   # Verify expected resources were deleted
   # Spot-check F5 XC console
   # Confirm no unintended deletions
   # Document deleted resources for audit trail
   ```

**Safety Considerations**:
- ⚠️ Prune is **DESTRUCTIVE** - deleted resources cannot be easily recovered
- ⚠️ Always dry-run first with --prune to preview deletions
- ⚠️ Coordinate with application owners before pruning
- ⚠️ Consider backup export before prune
- ⚠️ Start with small prune operations to build confidence

**Validation**:
- ✅ Dry-run prune list reviewed and approved
- ✅ Stakeholders notified of deletions
- ✅ Backup export completed
- ✅ Prune execution completed without unexpected deletions
- ✅ Audit log updated with prune operation

---

## Related Documentation

- [Testing Strategy](testing-strategy.md) - Comprehensive testing approaches
- [Deployment Guide](../guides/deployment-guide.md) - Deployment scenarios and automation
- [Troubleshooting Guide](../guides/troubleshooting-guide.md) - Common issues and resolutions
- [GitHub Actions Guide](../guides/github-actions-guide.md) - CI/CD automation with GitHub
- [Jenkins Guide](../guides/jenkins-guide.md) - CI/CD automation with Jenkins
