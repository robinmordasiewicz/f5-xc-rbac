# Enhancement Specification: Enhanced CSV Validation & Feedback

**Parent Spec**: `059-user-lifecycle`
**Enhancement ID**: `059-ENH-001`
**Created**: 2025-11-11
**Status**: Reverse-Engineered from Implementation
**Applies to**: `sync_users` CLI command

## Overview

This enhancement documents the comprehensive CSV validation and feedback features implemented in the user synchronization service but not specified in the original PRD. These features provide detailed data quality validation before API operations, giving users actionable feedback about CSV issues.

## Enhanced Requirements

### CSV Validation Infrastructure

**FR-VAL-001**: System MUST validate email format using RFC-compliant regex pattern before processing users

**Implementation**: `user_sync_service.py:validate_email_format():18-28`

```python
def validate_email_format(email: str) -> bool:
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))
```text

**Rationale**: Catch invalid email addresses before attempting API operations, reducing failures and improving data quality feedback

**Testing**:

```python
assert validate_email_format("user@example.com") == True
assert validate_email_format("invalid.email") == False
assert validate_email_format("user@") == False
```text
---

**FR-VAL-002**: System MUST detect and report duplicate email addresses across CSV rows (case-insensitive)

**Implementation**: `user_sync_service.py:parse_csv_to_users():143-180`

```python
email_tracker: Dict[str, List[int]] = {}  # Track emails for duplicates

# ...

email_lower = email.lower()
if email_lower in email_tracker:
    email_tracker[email_lower].append(row_num)
else:
    email_tracker[email_lower] = [row_num]

# Identify duplicate emails (only those that appear more than once)

duplicate_emails = {
    email: rows for email, rows in email_tracker.items() if len(rows) > 1
}
```text

**Rationale**: Duplicate emails violate F5 XC unique email constraint; detection prevents API failures and clarifies data quality issues

**Testing**:

```bash

# CSV with duplicate emails

echo "Email,User Display Name,Employee Status,Entitlement Display Name" > test.csv
echo "john@example.com,John Doe,A,CN=group1" >> test.csv
echo "john@example.com,John Doe,A,CN=group2" >> test.csv
xc-group-sync sync_users --csv test.csv --dry-run

# Should display: "⚠️ Validation Warnings: - 1 duplicate email(s) found: • john@example.com (rows: 2, 3)"

```text

---

**FR-VAL-003**: System MUST track and report users with no group assignments

**Implementation**: `user_sync_service.py:parse_csv_to_users():207-209`

```python
if not groups:
    users_without_groups += 1
```text

**Rationale**: Users without groups may indicate data quality issues (missing entitlements) or legitimate edge cases requiring user attention

**Edge Case**: Empty "Entitlement Display Name" field is valid but should be flagged for review

---

**FR-VAL-004**: System MUST track and report users with missing display names

**Implementation**: `user_sync_service.py:parse_csv_to_users():189-191`

```python
if not display_name:
    users_without_names += 1
```text

**Rationale**: Missing display names reduce user experience quality in F5 XC interface; system will fall back to email prefix

**Fallback Behavior**: `user_utils.py:parse_display_name()` extracts first name from email prefix when display name is empty

---

**FR-VAL-005**: System MUST collect unique group names across all users for summary reporting

**Implementation**: `user_sync_service.py:parse_csv_to_users():205, 245`

```python
unique_groups: Set[str] = set()

# ...

cn = extract_cn(dn)
if cn:
    groups.append(cn)
    unique_groups.add(cn)
```text

**Rationale**: Provides users with visibility into which LDAP groups are being synchronized, helps validate against expected group list

---

**FR-VAL-006**: System MUST support pipe-separated LDAP Distinguished Names for multiple group assignments per user

**Implementation**: `user_sync_service.py:parse_csv_to_users():195-205`

```python
entitlements = row["Entitlement Display Name"].strip()
if entitlements:
    dn_list = [dn.strip() for dn in entitlements.split("|")]
    for dn in dn_list:
        if dn:
            cn = extract_cn(dn)
            if cn:
                groups.append(cn)
                unique_groups.add(cn)
```text

**Format**: `CN=group1,OU=Groups,DC=example,DC=com|CN=group2,OU=Groups,DC=example,DC=com`

**Rationale**: Enables single CSV row to represent user with multiple group memberships, matching common LDAP export formats

**Testing**:

```bash

# CSV with pipe-separated groups

echo "Email,User Display Name,Employee Status,Entitlement Display Name" > test.csv
echo 'john@example.com,John Doe,A,CN=admins,OU=Groups|CN=users,OU=Groups' >> test.csv
xc-group-sync sync_users --csv test.csv --dry-run

# Should parse both 'admins' and 'users' groups

```text

---

### User Update Detection

**FR-VAL-007**: System MUST use order-independent group comparison when detecting user update requirements

**Implementation**: `user_sync_service.py:_user_needs_update():332-336`

```python

# Compare groups (order-independent)

planned_groups = set(planned_dict.get("groups", []))
existing_groups = set(existing.get("groups", []))
if planned_groups != existing_groups:
    return True
```text

**Rationale**: Group order is not semantically meaningful; set comparison prevents unnecessary updates when group lists are equivalent but ordered differently

**Example**:

- CSV groups: `["admins", "users"]`
- F5 XC groups: `["users", "admins"]`
- **Behavior**: No update required (sets are equal)

---

### Error Tracking and Reporting

**FR-VAL-008**: System MUST collect detailed error information with operation context for all failed API operations

**Implementation**: `user_sync_service.py:UserSyncStats:85, _create_user():359-361, _update_user():382-384, _delete_user():404-406`

```python
@dataclass
class UserSyncStats:
    error_details: List[Dict[str, str]] = field(default_factory=list)

# Example error collection

stats.error_details.append(
    {"email": user.email, "operation": "create", "error": str(e)}
)
```text

**Error Details Schema**:

```python
{
    "email": "user@example.com",
    "operation": "create|update|delete",
    "error": "API error message"
}
```text

**Rationale**: Enables users to identify exactly which operations failed and why, facilitating targeted remediation

---

**FR-VAL-009**: System MUST provide `has_errors()` and `has_warnings()` convenience methods for validation result evaluation

**Implementation**: `user_sync_service.py:CSVValidationResult.has_warnings():57-64, UserSyncStats.has_errors():95-97`

```python
def has_warnings(self) -> bool:
    return (
        len(self.duplicate_emails) > 0
        or len(self.invalid_emails) > 0
        or self.users_without_groups > 0
        or self.users_without_names > 0
    )

def has_errors(self) -> bool:
    return self.errors > 0
```text

**Rationale**: Simplifies CLI logic for determining whether to display warning/error sections

---

### Enhanced CLI Feedback

**FR-CLI-001**: CLI MUST display comprehensive CSV validation results before executing API operations

**Implementation**: `cli.py:_display_csv_validation():280-343`

**Display Sections**:

1. **Dry-run banner** (if applicable)
2. **Basic counts** (total, active, inactive)
3. **Sample users** (first 3 with status icons)
4. **Unique groups count**
5. **Validation warnings** (if any)

**Visual Indicators**:

- `✓` Active user
- `⚠` Inactive user
- `⚠️` Validation warnings section
- `🔍` Dry-run mode banner

**Example Output**:

```text
🔍 DRY RUN MODE - No changes will be made to F5 XC

Users planned from CSV: 150

  - Active: 145, Inactive: 5

Sample of parsed users:
  ✓ john@example.com (John Doe) - Active [3 groups]
  ⚠ jane@example.com (Jane Smith) - Inactive [2 groups]
  ✓ bob@example.com (Bob Johnson) - Active [5 groups]
  ... and 147 more users

Groups assigned: 12 unique LDAP groups

⚠️ Validation Warnings:

  - 2 duplicate email(s) found:

    • duplicate@example.com (rows: 15, 42)
    • another@example.com (rows: 78, 91)

  - 3 invalid email format(s):

    • invalid.email (row 23)
    • user@ (row 56)
    • @example.com (row 89)

  - 5 user(s) have no group assignments
  - 2 user(s) missing display names (will use email prefix)

```text

---

**FR-CLI-002**: CLI MUST limit validation warning display to first 5 instances with overflow indicators

**Implementation**: `cli.py:_display_csv_validation():320-331`

```python
for email, rows in list(result.duplicate_emails.items())[:5]:
    click.echo(f"    • {email} (rows: {', '.join(map(str, rows))})")
if len(result.duplicate_emails) > 5:
    click.echo(f"    ... and {len(result.duplicate_emails) - 5} more")
```text

**Rationale**: Prevents terminal flooding with hundreds of validation warnings while preserving visibility into issue scale

---

**FR-CLI-003**: CLI MUST display detailed error information at end of sync operation if any operations failed

**Implementation**: `cli.py:sync_users():456-461`

```python
if stats.has_errors():
    click.echo("\nErrors encountered:")
    for err in stats.error_details:
        click.echo(f" - {err['email']}: {err['operation']} failed - {err['error']}")
    raise click.ClickException("One or more operations failed; see details above")
```text

**Rationale**: Provides actionable error details grouped at end of operation for easy review and remediation planning

---

## Validation Result Data Structure

### CSVValidationResult

```python
@dataclass
class CSVValidationResult:
    users: List[User]                              # Successfully parsed users
    total_count: int                                # Total users in CSV
    active_count: int                               # Active users
    inactive_count: int                             # Inactive users
    duplicate_emails: Dict[str, List[int]]         # Email -> row numbers
    invalid_emails: List[tuple[str, int]]          # (email, row_number)
    users_without_groups: int                       # Count without groups
    users_without_names: int                        # Count without names
    unique_groups: Set[str]                         # Unique group names found
```text

**Usage Pattern**:

```python
result = service.parse_csv_to_users(csv_path)
if result.has_warnings():
    display_warnings(result)
proceed = confirm_with_user()
if proceed:
    stats = service.sync_users(result.users, existing_users, dry_run)
```text

---

## Success Criteria

- **SC-VAL-001**: Email validation catches 100% of invalid formats before API operations
- **SC-VAL-002**: Duplicate email detection identifies all duplicates with accurate row numbers
- **SC-VAL-003**: Users without groups/names are accurately counted and reported
- **SC-VAL-004**: Pipe-separated LDAP DNs are correctly parsed to multiple group assignments
- **SC-VAL-005**: Order-independent group comparison prevents unnecessary user updates
- **SC-VAL-006**: Error details capture email, operation, and error message for 100% of failures
- **SC-VAL-007**: CLI validation display provides clear, actionable feedback within 2 seconds
- **SC-VAL-008**: Validation warning overflow indicators prevent terminal flooding

---

## Documentation Requirements

- **DOC-VAL-001**: README MUST document CSV validation features and warning interpretation
- **DOC-VAL-002**: README MUST provide examples of validation warnings and remediation steps
- **DOC-VAL-003**: README MUST document pipe-separated LDAP DN format with examples
- **DOC-VAL-004**: README MUST explain dry-run mode for safe CSV validation before execution

---

## Testing Recommendations

### Unit Tests

```python
def test_email_validation():
    assert validate_email_format("valid@example.com") == True
    assert validate_email_format("invalid") == False

def test_duplicate_detection():

    # CSV with duplicates should return duplicate_emails dict

    result = service.parse_csv_to_users("test_duplicates.csv")
    assert len(result.duplicate_emails) > 0

def test_pipe_separated_groups():

    # User with "CN=g1|CN=g2" should have 2 groups

    result = service.parse_csv_to_users("test_multiple_groups.csv")
    user = result.users[0]
    assert len(user.groups) == 2

def test_order_independent_groups():
    user1 = User(email="test@example.com", groups=["a", "b"])
    existing = {"email": "test@example.com", "groups": ["b", "a"]}
    assert not service._user_needs_update(user1, existing)
```text

### Integration Tests

```bash

# Test CSV validation feedback

xc-group-sync sync_users --csv invalid_emails.csv --dry-run

# Expect: Invalid email warnings displayed

# Test duplicate detection

xc-group-sync sync_users --csv duplicates.csv --dry-run

# Expect: Duplicate email warnings with row numbers

# Test pipe-separated groups

xc-group-sync sync_users --csv multi_groups.csv --dry-run

# Expect: Users show multiple group assignments

# Test error reporting

xc-group-sync sync_users --csv valid.csv --delete-users

# Expect: Error details section if API failures occur

```text

---

## Security Considerations

- **Email validation** prevents malformed email addresses from reaching F5 XC API
- **Duplicate detection** prevents accidental user overwrites and data corruption
- **Error details** do NOT expose sensitive credential information, only email and operation type
- **Validation warnings** are logged but do NOT contain personally identifiable information beyond email addresses

---

## Performance Considerations

- **CSV parsing**: Single-pass validation with O(n) complexity for n users
- **Duplicate detection**: O(n) with hash-based email tracking
- **Group comparison**: O(m) set operations for m groups per user (typically small)
- **Memory usage**: CSVValidationResult holds full user list in memory; acceptable for typical CSV sizes (<10K users)

---

## Future Enhancement Opportunities

- **FR-VAL-010** (Future): Add configurable email validation regex for non-RFC email formats
- **FR-VAL-011** (Future): Support CSV schema validation (column name variations, encoding detection)
- **FR-VAL-012** (Future): Add group name validation against F5 XC allowed patterns
- **FR-VAL-013** (Future): Provide CSV repair suggestions (e.g., "Did you mean john@example.com instead of john@exampl.com?")
- **FR-VAL-014** (Future): Add validation summary JSON export for CI/CD integration
