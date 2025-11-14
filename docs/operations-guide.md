# Operations Guide

> **Audience**: DevOps Engineers, IAM Administrators, Platform Engineers
> **Last Updated**: 2025-11-13

## Overview

This guide provides operational procedures and best practices for managing F5 XC user and group synchronization in production environments. It covers data preparation, routine operations, and advanced reconciliation scenarios.

## Active Directory CSV Export

### PowerShell Export Command

Export user and group data from Active Directory:

```powershell
# Export group memberships with user details
Get-ADGroupMember -Identity "All Groups" -Recursive |
  Export-Csv -Path "User-Database.csv" -NoTypeInformation
```

### CSV Analysis Tools

Review changes before synchronization:

```bash
# Compare with previous export
diff previous-export.csv User-Database.csv | head -20

# Count unique groups
csvcut -c "Entitlement Display Name" User-Database.csv | sort -u | wc -l

# Count unique users
csvcut -c "Email" User-Database.csv | sort -u | wc -l
```

## Regular Synchronization Operations

### Pre-Sync Checklist

Before running synchronization:

- ✅ CSV export contains latest AD data
- ✅ CSV format matches required schema (see [Configuration](configuration.md#csv-format))
- ✅ Changes reviewed with diff commands
- ✅ Dry-run executed and validated

### Execution Pattern

```bash
# 1. Review changes
diff previous-export.csv User-Database.csv

# 2. Test with dry-run
xc_user_group_sync --csv User-Database.csv --dry-run

# 3. Execute synchronization
xc_user_group_sync --csv User-Database.csv
```

### Post-Sync Validation

After synchronization completes:

- ✅ Sync completes with errors=0
- ✅ Operation counts match expectations
- ✅ Spot-checks confirm accuracy (see [Manual Verification](#manual-verification))

## Error Investigation Workflow

If errors occur during synchronization:

1. **Review error details** in command output
2. **Check F5 XC API logs** in the console
3. **Verify CSV data quality**:
   - Check for malformed LDAP DNs
   - Validate email format
   - Confirm required columns present
4. **Retry failed operations** if errors are transient (network, rate limits)

## Manual Verification in F5 XC Console

Periodically verify synchronization accuracy:

1. Log into F5 XC Console
2. Navigate to **IAM → User Groups**
3. Spot-check random groups for correct membership
4. Verify new groups from CSV are present
5. Confirm removed groups are deleted (if using `--prune`)

## Pruning Operations

### When to Prune

Execute pruning operations in these scenarios:

- **After major organizational restructuring** - Large-scale AD changes
- **Quarterly reconciliation** - Audit compliance requirements
- **After decommissioning applications** - Remove obsolete access groups
- **Cleaning up test/obsolete groups** - Maintenance operations

### Pre-Prune Backup

**REQUIRED**: Backup current F5 XC state before pruning:

```bash
# Export current groups for backup
curl -X GET \
  "https://${TENANT_ID}.console.ves.volterra.io/api/web/namespaces/system/user_groups" \
  --cert ${VOLT_API_CERT_FILE} \
  --key ${VOLT_API_CERT_KEY_FILE} \
  > f5xc-groups-backup-$(date +%Y%m%d).json
```

### Prune Execution Workflow

```bash
# 1. Backup current state (see above)

# 2. Dry-run with prune to preview deletions
xc_user_group_sync --csv User-Database.csv --prune --dry-run

# 3. Review prune targets carefully
#    - Groups to be deleted (not in CSV)
#    - Users to be deleted (not in any CSV group)

# 4. Validate with stakeholders
#    - Confirm deletions are intentional
#    - Check for production-critical groups
#    - Verify no active users lose access unintentionally

# 5. Execute prune (only after validation)
xc_user_group_sync --csv User-Database.csv --prune
```

### Prune Safety Considerations

⚠️ **DESTRUCTIVE OPERATION WARNINGS**:

- **Prune is DESTRUCTIVE** - Deleted resources cannot be easily recovered
- **Always dry-run first** with `--prune` to preview deletions
- **Coordinate with application owners** before pruning
- **Consider backup export** before executing prune
- **Start with small prune operations** to build confidence
- **Document deleted resources** for audit trail

### Post-Prune Validation

After prune completes:

- ✅ Dry-run prune list was reviewed and approved
- ✅ Stakeholders were notified of deletions
- ✅ Backup export completed successfully
- ✅ Prune execution completed without unexpected deletions
- ✅ Audit log updated with prune operation details

## Operational Checklists

### Initial Setup Validation

- ✅ Configuration loaded successfully
- ✅ Dry-run shows expected operations
- ✅ Sync completes without errors
- ✅ Groups visible in F5 XC console

### Regular Sync Validation

- ✅ CSV export contains latest AD data
- ✅ Dry-run shows expected changes
- ✅ Sync completes with errors=0
- ✅ Operation counts match expectations
- ✅ Spot-checks confirm accuracy

### Prune Operation Validation

- ✅ Dry-run prune list reviewed and approved
- ✅ Stakeholders notified of deletions
- ✅ Backup export completed
- ✅ Prune execution completed without unexpected deletions
- ✅ Audit log updated with prune operation

## Related Documentation

- [Getting Started](get-started.md) - Installation and setup
- [CLI Reference](cli-reference.md) - Command-line options
- [Configuration](configuration.md) - Environment variables and CSV format
- [Development](development.md) - Contributing and testing
