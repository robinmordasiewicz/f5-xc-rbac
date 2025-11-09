# data-model.md — CSV Sync (Phase 1)

Date: 2025-11-06

## Entities

- User
  - Primary key: email (string, required, canonical identifier)
  - Fields: username (string, optional), display_name (string, optional), created_at (timestamp)
  - Constraints: email must be unique; username optional and may be derived from local-part if missing

- Group
  - Primary key: name (string, required) — derived CN from Entitlement Display Name DN
  - Fields: display_name (string), created_at (timestamp)
  - Constraints: name must match GROUP_NAME_RE (^[A-Za-z0-9_-]{1,128}$)

- Membership
  - Composite key: (group_name, user_email)
  - Fields: created_at (timestamp)
  - Semantics: idempotent; re-adding an existing membership is a no-op

## Validation rules

- CSV rows must contain Email and Entitlement Display Name columns (already enforced by parsing).
- CN extraction: use ldap3.parse_dn and validate against GROUP_NAME_RE; invalid DNs cause row skip and warning.
- User creation: minimal attributes allowed; if external identity provider rejects creation, row is recorded as failed.

## State transitions

- New user: non-existent -> created
- Membership: absent -> added; no duplicate state when re-adding
- Group: absent -> created

## Scale assumptions

- Typical size: up to tens of thousands of rows per CSV. For very large CSVs consider batching & rate-limiting.
