# Implementation Plan: User Lifecycle Management with CSV Synchronization

**Branch**: `059-user-lifecycle` | **Date**: 2025-11-10 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/059-user-lifecycle/spec.md`

## Summary

Enhance the existing F5 XC user and group synchronization tool with full user lifecycle management, adding user create/update/delete operations synchronized from CSV exports. The enhancement parses extended CSV columns (User Display Name, Employee Status), implements state-based reconciliation treating CSV as source of truth, provides configurable deletion flags with dry-run support, and generates detailed summary reports - replicating SCIM-like idempotent synchronization behavior using the F5 XC custom user_roles API.

**Technical Approach**: Extend existing architecture (XCClient, CSV parsing, sync service pattern) with new UserSyncService following the same patterns as GroupSyncService. Add user-specific operations to XCClient, create utility functions for name parsing and status mapping, enhance CLI with user management flags, and implement comprehensive state reconciliation logic.

## Technical Context

**Language/Version**: Python 3.9+ (target: Python 3.12)
**Primary Dependencies**:

- `click` 8.1.7+ (CLI framework)
- `pydantic` 2.9.2+ (data validation)
- `requests` 2.32.3+ (HTTP client)
- `tenacity` 9.0.0+ (retry logic)
- `ldap3` 2.9.1+ (LDAP DN parsing)
- `python-dotenv` 1.0.1+ (environment configuration)

**Storage**: N/A (stateless - CSV file is source of truth, F5 XC API is storage layer)
**Testing**: `pytest` 8.3.0+ with `pytest-cov` 6.0.0+, coverage target 80%
**Target Platform**: Cross-platform CLI (Linux, macOS, Windows) - Python 3.9+ runtime
**Project Type**: Single CLI application (existing structure preserved)
**Performance Goals**: Synchronize 1,000 users in under 5 minutes, 100% idempotent
**Constraints**:

- F5 XC API rate limits (defensive: 5 concurrent max, exponential backoff)
- Must preserve existing group sync functionality
- Stateless execution (no local state persistence)

**Scale/Scope**:

- CSV files: up to 10,000 user records
- API operations: create, read, update, delete users
- Enhancement scope: ~7 new files, ~15 modified files

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Status**: ✅ **PASSED** (No constitution violations - template constitution not yet defined for this project)

Since `.specify/memory/constitution.md` contains only template placeholders, there are no project-specific constitutional principles to validate against. The implementation will follow existing project patterns and Python best practices captured in Serena memories.

**Existing Project Patterns** (from Serena memories):

- ✅ Protocol-based dependency injection (following existing `GroupRepository` pattern)
- ✅ Pydantic models for validation (following existing `Group` model pattern)
- ✅ Service layer with business logic (following existing `GroupSyncService` pattern)
- ✅ XCClient for API interactions (extending existing client)
- ✅ CLI with Click framework (extending existing `cli.py`)
- ✅ Comprehensive testing with pytest (80%+ coverage requirement)
- ✅ Google-style docstrings and type hints (existing code standard)

**Re-check after Phase 1**: Will validate that design maintains these patterns.

## Project Structure

### Documentation (this feature)

```text
specs/059-user-lifecycle/
├── spec.md              # Feature specification (completed)
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (generated below)
├── data-model.md        # Phase 1 output (generated below)
├── quickstart.md        # Phase 1 output (generated below)
├── contracts/           # Phase 1 output (generated below)
│   └── user_sync_api.md # User sync operations contract
├── checklists/          # Quality validation
│   └── requirements.md  # Spec quality checklist (completed)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```text
### Source Code (repository root)

```text
src/xc_user_group_sync/
├── __init__.py          # Package initialization (existing)
├── cli.py               # CLI entry point (MODIFY: add user sync commands)
├── client.py            # XCClient API client (MODIFY: add user operations)
├── sync_service.py      # GroupSyncService (existing - preserved)
├── user_sync_service.py # UserSyncService (NEW: user lifecycle logic)
├── user_utils.py        # NEW: name parsing, status mapping utilities
├── models.py            # Pydantic models (MODIFY: add User model)
├── protocols.py         # Protocols (MODIFY: add UserRepository protocol)
├── ldap_utils.py        # LDAP DN parsing (existing - reused)
└── constants.py         # NEW: shared constants (CSV columns, status codes)

tests/
├── unit/
│   ├── test_cli.py               # CLI tests (MODIFY: add user sync tests)
│   ├── test_client.py            # XCClient tests (MODIFY: add user op tests)
│   ├── test_sync_service.py      # Group sync tests (existing - preserved)
│   ├── test_user_sync_service.py # NEW: User sync service tests
│   ├── test_user_utils.py        # NEW: Utility function tests
│   └── test_models.py            # Model tests (MODIFY: add User tests)
├── integration/
│   └── test_user_sync_integration.py # NEW: End-to-end user sync tests
├── conftest.py           # Pytest fixtures (MODIFY: add user fixtures)
└── __init__.py

scripts/
└── setup_xc_credentials.sh # Credential setup (existing - preserved)

.github/workflows/
└── xc_user_group_sync.yml     # CI/CD pipeline (MODIFY: add user sync testing)
```text
**Structure Decision**: Single project structure maintained (existing). All enhancements add to `src/xc_user_group_sync/` package following established patterns. Tests mirror source structure in `tests/` directory. No new top-level directories created - pure enhancement of existing codebase.

## Complexity Tracking

> No Constitution violations - this section left empty as no justifications needed.

## Phase 0: Outline & Research

### Research Tasks

Based on Technical Context unknowns and feature requirements:

#### F5 XC user_roles API Schema

✅ (Already researched - see conversation history)

- Decision: Use `/api/web/custom/namespaces/system/user_roles` endpoint
- Supported fields: email, username, display_name, first_name, last_name, active (based on existing tests and client code)
- Operations: GET (list), POST (create), PUT (update), DELETE (delete)

#### CSV Parsing Strategy for Multiple Groups

✅ (Clarified in conversation)

- Decision: One row per user with pipe-separated groups in "Entitlement Display Name"
- Example: `CN=GROUP1,OU=...|CN=GROUP2,OU=...`
- Already handled by existing code - split on pipe and extract CN from each

#### Name Parsing Edge Cases

✅ (Clarified in spec)

- Decision: Last space-separated word = last name, rest = first name
- Edge cases: Single name → first_name only, last_name empty
- Whitespace: Trim before parsing

#### User Deletion Safety Mechanisms

✅ (Clarified in conversation)

- Decision: Explicit `--delete-users` flag required (safe default: no deletion)
- Dry-run mode logs deletions without executing
- No automatic safeguards against bulk deletion (user responsibility with dry-run)

#### State Reconciliation Algorithm

- Research: Existing `GroupSyncService.sync_groups` pattern
- Apply same idempotency logic to users:
  - Check existence before create
  - Compare attributes before update
  - Calculate diff (creates, updates, deletes)
  - Execute only necessary operations
- Decision: Mirror GroupSyncService reconciliation pattern for consistency

#### Error Handling and Partial Failures

- Research: Existing `SyncStats` tracking and error collection
- Apply same pattern:
  - Continue on individual failures
  - Collect errors for summary
  - Return partial success
- Decision: Reuse existing error handling patterns

### Research Findings Summary

All research tasks completed. Key decisions documented above. No NEEDS CLARIFICATION markers remain.

**Artifact**: [research.md](./research.md) - Detailed findings generated below

## Phase 1: Design & Contracts

### Data Model

**Primary Entities**:

1. **User** (new model in `models.py`):

  ```python
  class User(BaseModel):
      email: str                    # Primary identifier (unique)
      username: str                 # Same as email for F5 XC
      display_name: str             # From CSV "User Display Name"
      first_name: str               # Parsed from display_name
      last_name: str                # Parsed from display_name
      active: bool                  # From CSV "Employee Status"
      groups: List[str] = []        # Group names (for coordination with group sync)
  ```

1. **UserSyncStats** (new dataclass in `user_sync_service.py`):

  ```python
  @dataclass
  class UserSyncStats:
      created: int = 0
      updated: int = 0
      deleted: int = 0
      unchanged: int = 0
      errors: int = 0
      error_details: List[dict] = field(default_factory=list)
  ```

1. **Enhanced SyncStats** (modify existing in `sync_service.py`):

  ```python
  # Add user-specific fields to existing SyncStats
  users_created: int = 0
  users_updated: int = 0
  users_deleted: int = 0
  users_unchanged: int = 0
  ```

**Entity Relationships**:

- User.groups references Group.name (coordination only, not enforced FK)
- CSV Record → User (one-to-one mapping via parsing)
- User → F5 XC user_role (one-to-one via API)

**Validation Rules** (from functional requirements):

- Email: Required, non-empty (F5 XC validates format)
- Display name: Required for name parsing
- Employee Status: Defaults to inactive if missing
- Case-insensitive email comparison

**Artifact**: [data-model.md](./data-model.md) - Complete model documentation generated below

### API Contracts

**UserRepository Protocol** (new in `protocols.py`):

```python
class UserRepository(Protocol):
    """Protocol for user management operations."""

    def list_users(self, namespace: str = "system") -> Dict[str, Any]:
        """List all users with roles."""
        ...

    def create_user(self, user: Dict[str, Any], namespace: str = "system") -> Dict[str, Any]:
        """Create new user."""
        ...

    def update_user(self, email: str, user: Dict[str, Any], namespace: str = "system") -> Dict[str, Any]:
        """Update existing user."""
        ...

    def delete_user(self, email: str, namespace: str = "system") -> None:
        """Delete user."""
        ...

    def get_user(self, email: str, namespace: str = "system") -> Dict[str, Any]:
        """Get single user by email."""
        ...
```text
**XCClient Extensions** (modify `client.py`):

```python
class XCClient:
    # Existing methods preserved...

    # NEW: User-specific operations
    def list_users(self, namespace: str = "system") -> Dict[str, Any]:
        """List users via user_roles API (alias for list_user_roles)."""
        return self.list_user_roles(namespace)

    def update_user(self, email: str, user: Dict[str, Any], namespace: str = "system") -> Dict[str, Any]:
        """Update user via PUT to user_roles/{email}."""
        ...

    def delete_user(self, email: str, namespace: str = "system") -> None:
        """Delete user via DELETE to user_roles/{email}."""
        ...

    def get_user(self, email: str, namespace: str = "system") -> Dict[str, Any]:
        """Get user via GET to user_roles/{email}."""
        ...
```text
**UserSyncService Contract** (new in `user_sync_service.py`):

```python
class UserSyncService:
    def __init__(self, repository: UserRepository, **retry_config):
        """Initialize with user repository."""
        ...

    def parse_csv_to_users(self, csv_path: str) -> List[User]:
        """Parse CSV to User objects with enhanced attributes."""
        ...

    def fetch_existing_users(self) -> Dict[str, Dict]:
        """Fetch users from F5 XC, return email -> user_data map."""
        ...

    def sync_users(
        self,
        planned_users: List[User],
        existing_users: Dict[str, Dict],
        dry_run: bool = False,
        delete_users: bool = False
    ) -> UserSyncStats:
        """Reconcile users with F5 XC."""
        ...
```text
**Artifact**: [contracts/user_sync_api.md](./contracts/user_sync_api.md) - Full API contract generated below

### Quickstart Guide

**For Developers**:

1. Set up development environment (existing process preserved)
2. Run existing tests to ensure baseline: `pytest`
3. Implement User model in `models.py`
4. Implement utility functions in `user_utils.py` (TDD)
5. Extend XCClient with user operations
6. Implement UserSyncService following GroupSyncService pattern
7. Extend CLI with `--delete-users` flag
8. Write comprehensive tests (unit + integration)
9. Validate with dry-run against test CSV
10. Update documentation

**For Users** (after implementation):

```bash
# Sync users from CSV (create/update only)
xc_user_group_sync sync --csv users.csv --dry-run

# Sync users with deletion enabled
xc_user_group_sync sync --csv users.csv --delete-users --dry-run
xc_user_group_sync sync --csv users.csv --delete-users  # Apply after dry-run verification
```text
**Artifact**: [quickstart.md](./quickstart.md) - Complete guide generated below

### Agent Context Update

**Command Executed**:

```bash
.specify/scripts/bash/update-agent-context.sh claude
```text
**Result**: ✅ Successfully updated `CLAUDE.md` with feature context

**Changes Applied**:

- Added language context: Python 3.9+ (target: Python 3.12)
- Added database context: N/A (stateless - CSV file is source of truth, F5 XC API is storage layer)
- Updated project type: Single CLI application (existing structure preserved)

**Agent Context Now Available**:

- Language/framework details for code generation
- Database/storage layer understanding
- Project structure and patterns
- Enhanced context for implementation phase

---

## Phase 2: Task Breakdown (Next Step)

**Artifact**: [tasks.md](./tasks.md) - Generated by `/speckit.tasks` command

Phase 1 (Design & Contracts) is now complete. Next steps:

1. **Run `/speckit.tasks`**: Generate dependency-ordered task breakdown
2. **Review Task Sequence**: Validate implementation order
3. **Begin Implementation**: Follow TDD approach from quickstart.md
4. **Iterative Development**: Implement → Test → Commit cycle

**Generated Artifacts Summary**:

✅ **Phase 0: Research**

- [research.md](./research.md) - Technical decisions and alternatives analysis

✅ **Phase 1: Design & Contracts**

- [data-model.md](./data-model.md) - User and UserSyncStats model definitions
- [contracts/user_sync_api.md](./contracts/user_sync_api.md) - API contracts and protocols
- [quickstart.md](./quickstart.md) - Developer and user implementation guide
- [CLAUDE.md](../../CLAUDE.md) - Updated agent context

🔜 **Phase 2: Task Breakdown** (next command: `/speckit.tasks`)

- tasks.md - Dependency-ordered implementation tasks

---

## Planning Summary

### What Was Decided

**Architecture**: Protocol-based dependency injection following existing `GroupSyncService` pattern

- UserRepository protocol for F5 XC API operations
- UserSyncService for business logic and reconciliation
- XCClient extensions for user CRUD operations
- Pydantic User model for validation

**Data Flow**: CSV → Parse → Reconcile → F5 XC API

- Name parsing: Last word = last name, rest = first name
- Status mapping: "A" → True (active), else → False (inactive)
- Group extraction: Pipe-separated LDAP DNs → CNs via existing `ldap_utils`
- Idempotent sync: CSV as source of truth, F5 XC matches exactly

**Safety Mechanisms**:

- `--delete-users` flag required for deletions (safe default: no deletion)
- `--dry-run` mode for preview without execution
- Individual operation failures don't abort sync
- Comprehensive error logging and summary reporting

**Quality Standards**:

- 80%+ test coverage for new code
- TDD approach: tests first, then implementation
- Google-style docstrings with type hints
- Black formatting, Ruff linting, mypy type checking

### What Was Generated

**Planning Artifacts** (Phase 0 & 1):

1. `spec.md` - Feature specification (6 user stories, 20 requirements, 10 success criteria)
2. `research.md` - Technical decisions and research findings
3. `data-model.md` - Complete data model documentation
4. `contracts/user_sync_api.md` - API contracts and protocols
5. `quickstart.md` - Implementation and user guide
6. `CLAUDE.md` - Updated agent context
7. `checklists/requirements.md` - Spec quality validation (all checks passed)

**Files to Create** (Phase 2 - Implementation):

- `src/xc_user_group_sync/user_sync_service.py` (new)
- `src/xc_user_group_sync/user_utils.py` (new)
- `tests/unit/test_user_sync_service.py` (new)
- `tests/unit/test_user_utils.py` (new)
- `tests/integration/test_user_sync_integration.py` (new)

**Files to Modify** (Phase 2 - Implementation):

- `src/xc_user_group_sync/models.py` (add User model)
- `src/xc_user_group_sync/protocols.py` (add UserRepository protocol)
- `src/xc_user_group_sync/client.py` (add user CRUD operations)
- `src/xc_user_group_sync/cli.py` (add --delete-users flag)
- `tests/unit/test_models.py` (add User tests)
- `tests/unit/test_cli.py` (add user sync tests)
- `tests/unit/test_client.py` (add user operation tests)
- `tests/conftest.py` (add user fixtures)

### Implementation Readiness

**✅ Ready to Implement**:

- All research completed and documented
- Data models fully specified with validation rules
- API contracts defined with clear protocols
- Utility functions specified with test cases
- TDD approach documented in quickstart guide
- Agent context updated for code generation

**Next Command**: `/speckit.tasks` to generate task breakdown

---

## Appendix: Technical Decisions Log

| Decision Area | Choice | Rationale |
|---------------|--------|-----------|
| API Endpoint | F5 XC `/api/web/custom/namespaces/system/user_roles` | Custom API (not SCIM) as specified, existing endpoint |
| Name Parsing | Last word = last name, rest = first name | Simple algorithm, handles Western names, user requirement |
| Status Mapping | "A" → True, else → False | Explicit, safe default (inactive), user clarification |
| CSV Format | One row per user, pipe-separated groups | Matches existing AD export format, single row simplifies parsing |
| Deletion Safety | Explicit `--delete-users` flag required | Safe default (no deletion), requires user confirmation |
| Reconciliation | Mirror GroupSyncService pattern | Proven idempotent approach, consistent architecture |
| Error Handling | Continue on failures, collect stats | Resilient, enables batch processing, user requirement |
| Testing | Protocol pattern for mocking | Enables unit testing without F5 XC API, existing pattern |
| Performance | Synchronize 1,000 users < 5 minutes | Based on existing retry logic and F5 XC API performance |

---

## References

- **Feature Specification**: [spec.md](./spec.md)
- **Research Findings**: [research.md](./research.md)
- **Data Models**: [data-model.md](./data-model.md)
- **API Contracts**: [contracts/user_sync_api.md](./contracts/user_sync_api.md)
- **Implementation Guide**: [quickstart.md](./quickstart.md)
- **Existing Group Sync**: `src/xc_user_group_sync/sync_service.py`
- **F5 XC API Client**: `src/xc_user_group_sync/client.py`
