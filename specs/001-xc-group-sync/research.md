# Research: XC Group Sync (Spec 001)

Date: 2025-11-04
Branch: 001-xc_user_group_sync-plan

## Decisions

- Authentication: Support both API Token and Client Certificate (P12 or split PEM).
  - Prefer P12/cert when both are present (aligns with enterprise identity practices); token is acceptable and simpler.
- Base API and scope: Use `https://<tenant>.console.ves.volterra.io` and scope IAM calls to `namespaces/system`.
- Endpoints: Use `/api/web/namespaces/system/usergroups` and `/api/web/namespaces/system/userroles` for group/role CRUD.
- Retry strategy: Implement exponential backoff on 429/5xx; respect `Retry-After` when available.
- Naming constraints: Enforce conservative validation (^[A-Za-z0-9_-]+$, max 128) with override option if schema allows wider set. Log rejections.
- Idempotency: Use PUT for updates; treat create+conflict as update when appropriate; reconcile full membership per spec.
- CI secrets: Store P12/cert/key as base64 in CI secrets; decode to files at runtime; pass paths via env vars.

## Rationale

- Cert/P12 flows are standard for org-level integrations; tokens are simpler but often tied to user lifecycle; supporting both maximizes usability.
- `system` namespace is documented as the global scope for identities and RBAC.
- The `/api/web` prefix corresponds to user/role/group management; specific resource names `usergroups` and `userroles` observed across docs and patterns.
- Retry & idempotency are necessary for robust automation with cloud APIs.
- CI best practices avoid plaintext secrets in code and favor ephemeral files created in job runners.

## Alternatives considered

- Token-only authentication: Simpler but less flexible; rejected to support enterprise cert workflows.
- Partial membership patching: Rejected; full reconciliation required by spec (CSV is source of truth).
- Embedding secrets unencoded: Rejected; use base64 + decode in job for portability and safety.

## References

- API Usage & Auth Guide: https://docs.cloud.f5.com/docs-v2/platform/how-to/volt-automation/apis
- API Reference (OpenAPI root): https://docs.cloud.f5.com/docs-v2/api
