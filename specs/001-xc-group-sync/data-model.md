# Data Model: XC Group Sync

## Entities

- Group
  - name: string (^[A-Za-z0-9_-]+$, 1..128)
  - description: string (optional)
  - users: string[] (usernames/emails; per spec, CSV authoritative)
  - roles: string[] (role names/ids, optional)

- Config
  - tenant_id: string
  - auth:
    - p12_file: path (optional)
    - p12_password: string (optional)
    - cert_file: path (optional)
    - key_file: path (optional)
    - api_token: string (optional)

- CSVRow
  - user_name: string
  - email: string
  - entitlement_dn: string (LDAP DN; extract CN as group name)

## Relationships

- Group.users derived by grouping CSV rows on `entitlement_dn` CN; values come from unique emails.
- Groups live in namespace `system`.

## Validation rules

- name must match regex and length; on violation → skip with error and include in report.
- users must be valid emails/usernames accepted by XC; unknown users cause pre-validation failures.
- When updating groups, replace entire membership array with CSV-derived set.
