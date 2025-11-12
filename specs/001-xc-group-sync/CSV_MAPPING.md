# CSV to F5 XC API Field Mapping

## Overview

This document maps fields from the Active Directory export CSV (`User-Database.csv`) to the F5 Distributed Cloud (F5 XC) user_group API schema.

## CSV Structure

### Sample CSV Row

```csv
"User Name","Login ID","User Display Name","Cof Account Type","Application Name","Entitlement Attribute","Entitlement Display Name","Related Application","Sox","Job Level ","Job Title","Created Date","Account Locker","Employee Status","Email","Cost Center","Finc Level 4","Manager EID","Manager Name","Manager Email"
"USER001","CN=USER001,OU=Developers,OU=All Users,DC=example,DC=com","Alice Anderson","User","Active Directory","memberOf","CN=EADMIN_STD,OU=Groups,DC=example,DC=com","Example App","true","50","Lead Software Engineer","2025-09-23 00:00:00","0","A","alice.anderson@example.com","IT Infrastructure","Network Engineering","MGR001","David Wilson","David.Wilson@example.com"
```text

### Data Model

Each CSV row represents:

- One **user** (identified by `Email`)
- One **group membership** (identified by `Entitlement Display Name`)

Multiple rows with the same `Entitlement Display Name` represent multiple users in the same group.

## F5 XC User Group API Schema

### Endpoint: `POST /api/web/custom/namespaces/system/user_groups`

```json
{
  "name": "string",           // Required: Internal identifier (extracted CN)
  "display_name": "string",   // Optional: Human-readable name
  "description": "string",    // Optional: Descriptive text
  "usernames": [             // Required: Array of user email addresses
    "user@example.com"
  ],
  "namespace_roles": [       // Optional: RBAC role assignments
    {
      "namespaces": ["ns1"],
      "role": "role-name"
    }
  ],
  "sync_id": "string"        // Optional: External sync identifier
}
```text

## Field Mappings

### Group-Level Fields

| F5 XC Field | Source | Transformation | Example |
|-------------|--------|----------------|---------|
| `name` | `Entitlement Display Name` | Extract CN from LDAP DN | "EADMIN_STD" |
| `display_name` | `Entitlement Display Name` OR `name` | **[Q2: NEEDS DECISION]** Use CN or derive from other field | "EADMIN_STD" |
| `description` | N/A (not in CSV) | Optional: could use `Application Name` or leave blank | null or "Active Directory" |
| `namespace` | Hardcoded | Always "system" per API docs | "system" |

### User Membership Fields

| F5 XC Field | Source | Transformation | Example |
|-------------|--------|----------------|---------|
| `usernames[]` | `Email` (aggregated by group) | Collect all emails with same group DN | ["alice.anderson@example.com"] |

### Unused CSV Fields (for this tool)

These fields are available in the CSV but not directly used for group sync:

- `User Name` - AD username (not used; F5 XC identifies by email)
- `Login ID` - Full user LDAP DN (not used)
- `User Display Name` - Full name (could be used if auto-creating users - see Q1)
- `Cof Account Type` - Account type (not used)
- `Application Name` - Could map to `description` (see Q2)
- `Entitlement Attribute` - Always "memberOf" (validation only)
- `Related Application`, `Sox`, `Job Level`, `Job Title`, etc. - Metadata (not used)
- `Manager EID`, `Manager Name`, `Manager Email` - Org hierarchy (not used)

## Processing Logic

### 1. Parse CSV
```text
For each row in CSV:
  1. Validate required columns exist
  2. Extract group name: Parse CN from "Entitlement Display Name" LDAP DN
  Example: "CN=EADMIN_STD,OU=Groups,..." → "EADMIN_STD"
  3. Extract user email from "Email" column
  4. Aggregate: group_name → list of user emails
```text

### 2. Build Group Objects
```text
For each unique group_name:
  {
    "name": group_name,
    "display_name": group_name,  // Or per Q2 decision
    "description": "",            // Or per Q2 decision
    "usernames": [email1, email2, ...],
    "namespace": "system"
  }
```text

### 3. Sync to F5 XC
```text
1. GET existing groups from /api/web/custom/namespaces/system/user_groups
2. Compare CSV groups vs XC groups:
  - CREATE: Group in CSV, not in XC
  - UPDATE: Group in CSV and XC, but usernames differ
  - DELETE: Group in XC, not in CSV (only if --cleanup flag enabled)
  - NO-OP: Group in CSV and XC with identical usernames
3. Execute operations (or log if --dry-run)
```text

## LDAP DN Parsing

### Pattern
```text
Entitlement Display Name: "CN=EADMIN_STD,OU=Groups,DC=example,DC=com"
                              ^^^^^^^^^^
                              Extract this as group name
```text

### Edge Cases (Q6)

- Multiple CN components: "CN=Users,CN=Admin,OU=..."
- Special characters in CN: "CN=Group (Test),OU=..."
- Escaped characters: "CN=Group\, Inc,OU=..."

**Recommendation**: Use proper LDAP DN parser library.

## Outstanding Decisions

| Question | Decision Needed | Impact |
|----------|-----------------|--------|
| Q1 | User validation strategy | Error handling for non-existent users |
| Q2 | `display_name` source | Group creation payload |
| Q3 | Membership removal behavior | Update operation logic (full sync vs append-only) |
| Q4 | CSV format support | Parser library choice |
| Q5 | Multi-namespace support | Scope of v1 (defer or implement) |
| Q6 | LDAP DN parsing method | Dependency choice, error handling |

## Example Transformation

### Input: CSV Rows
```csv
"USER001","...","Alice Anderson",...,"Active Directory","memberOf","CN=EADMIN_STD,OU=Groups,...","...","alice.anderson@example.com",...
"USER002","...","Jane Doe",...,"Active Directory","memberOf","CN=EADMIN_STD,OU=Groups,...","...","jane.doe@example.com",...
"USER003","...","Bob Smith",...,"Active Directory","memberOf","CN=DEV_TEAM,OU=Groups,...","...","bob.smith@example.com",...
```text

### Output: F5 XC API Calls

**Create Group: EADMIN_STD**
```bash
POST /api/web/custom/namespaces/system/user_groups
Content-Type: application/json
Authorization: APIToken <token>

{
  "name": "EADMIN_STD",
  "display_name": "EADMIN_STD",
  "description": "",
  "usernames": [
    "alice.anderson@example.com",
    "jane.doe@example.com"
  ]
}
```text

**Create Group: DEV_TEAM**
```bash
POST /api/web/custom/namespaces/system/user_groups
Content-Type: application/json
Authorization: APIToken <token>

{
  "name": "DEV_TEAM",
  "display_name": "DEV_TEAM",
  "description": "",
  "usernames": [
    "bob.smith@example.com"
  ]
}
```text

## Validation Rules

### Pre-Flight Checks

1. **CSV schema**: Validate required columns present
2. **LDAP DN format**: Validate `Entitlement Display Name` contains "CN="
3. **Email format**: Validate `Email` column contains valid email addresses
4. **Entitlement attribute**: Validate `Entitlement Attribute` == "memberOf"

### F5 XC API Constraints

(Need to verify from API docs or testing)

- Group `name` length: likely max 64-320 characters
- Allowed characters: likely alphanumeric, hyphen, underscore
- Email format: standard RFC 5322
- Usernames array: likely no hard limit, but practical limit ~1000s

### Error Handling

- **Malformed LDAP DN**: Skip row, log error, continue
- **Duplicate group names in CSV**: Error, halt processing
- **Empty usernames for group**: Skip group creation, log warning
- **API 401/403**: Halt immediately, report auth failure
- **API 404 on user**: Handle per Q1 decision
- **API 429 rate limit**: Retry with backoff
- **API 5xx**: Retry with backoff, fail after max retries
