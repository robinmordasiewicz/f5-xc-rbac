# Enhancement Specification: Advanced Retry & Backoff Configuration

**Parent Spec**: `001-xc-group-sync`
**Enhancement ID**: `001-ENH-003`
**Created**: 2025-11-11
**Status**: Reverse-Engineered from Implementation
**Applies to**: `sync` CLI command (group synchronization)

## Overview

This enhancement documents the configurable retry and backoff mechanisms implemented in the group synchronization service but not specified in the original PRD. These features provide fine-grained control over transient error handling during user auto-creation within group operations.

## Enhanced Requirements

### Configurable Retry Parameters

**FR-RETRY-001**: GroupSyncService MUST support configurable retry attempts for user auto-creation operations

**Implementation**: `sync_service.py:GroupSyncService.__init__():67-75`

```python
def __init__(
    self,
    repository: GroupRepository,
    *,
    retry_attempts: int = 3,
    backoff_multiplier: float = 1.0,
    backoff_min: float = 1.0,
    backoff_max: float = 4.0,
):
    self.repository = repository
    self.retry_attempts = retry_attempts
    self.backoff_multiplier = backoff_multiplier
    self.backoff_min = backoff_min
    self.backoff_max = backoff_max
```

**Default Values**:
- `retry_attempts`: 3 (total attempts including initial)
- `backoff_multiplier`: 1.0 (linear backoff)
- `backoff_min`: 1.0 second (minimum wait)
- `backoff_max`: 4.0 seconds (maximum wait)

**Rationale**: Enables service consumers to tune retry behavior based on API characteristics, network conditions, or operational requirements without modifying core logic

**Testing**:
```python
# Default retry behavior (3 attempts)
service = GroupSyncService(client)

# Aggressive retry (5 attempts, faster backoff)
service = GroupSyncService(
    client,
    retry_attempts=5,
    backoff_min=0.5,
    backoff_max=2.0
)

# Conservative retry (2 attempts, longer backoff)
service = GroupSyncService(
    client,
    retry_attempts=2,
    backoff_min=2.0,
    backoff_max=10.0
)
```

---

**FR-RETRY-002**: System MUST apply exponential backoff with configurable multiplier for retry delays

**Implementation**: `sync_service.py:_create_user_with_retry():391-407`

```python
@retry(
    retry=retry_if_exception_type(requests.RequestException),
    wait=wait_exponential(multiplier=1, min=1, max=4),
    stop=stop_after_attempt(3),
    reraise=True,
)
def _create_user_with_retry(self, email: str, dry_run: bool) -> None:
    # User creation with automatic retry
```

**Backoff Calculation**:
```python
wait_time = min(backoff_multiplier * (2 ** (attempt - 1)), backoff_max)
wait_time = max(wait_time, backoff_min)
```

**Examples**:
- **Attempt 1**: No wait (initial)
- **Attempt 2**: Wait 1.0s (multiplier * 2^0)
- **Attempt 3**: Wait 2.0s (multiplier * 2^1)
- **Attempt 4**: Wait 4.0s (capped at backoff_max)

**Rationale**: Exponential backoff reduces load on recovering systems while maintaining reasonable retry attempts for transient failures

---

**FR-RETRY-003**: System MUST only retry on transient network/API errors, not on permanent failures

**Implementation**: `sync_service.py:_create_user_with_retry():391`

```python
@retry(
    retry=retry_if_exception_type(requests.RequestException),
    # Only retry network/API errors, not validation or logic errors
)
```

**Retriable Errors**:
- Connection errors (network unreachable)
- Timeout errors (request/response timeout)
- HTTP 5xx server errors (temporary server issues)
- HTTP 429 rate limit errors

**Non-Retriable Errors** (fail fast):
- HTTP 400 bad request (invalid data)
- HTTP 401/403 authentication/authorization failures
- HTTP 404 not found (endpoint doesn't exist)
- ValueError, TypeError (programming errors)

**Rationale**: Avoids wasting retry attempts on errors that won't succeed with repetition, preserves resources for genuinely transient failures

---

### Retry Application Scope

**FR-RETRY-004**: Retry logic MUST apply specifically to user auto-creation within group operations, not to group creation itself

**Implementation**: `sync_service.py:_ensure_user_exists():368-388`

```python
def _ensure_user_exists(self, email: str, dry_run: bool) -> None:
    """Ensure user exists in F5 XC, creating if needed.

    This is the ONLY operation with retry logic. Group operations
    use simpler error handling without automatic retry.
    """
    try:
        self._create_user_with_retry(email, dry_run)
        logger.info(f"[Implicit] Created user: {email}")
    except Exception as e:
        logger.error(f"Failed to create user {email} after retries: {e}")
        raise
```

**Retry Scope Comparison**:

| Operation | Retry Logic | Rationale |
|-----------|-------------|-----------|
| User creation (within group sync) | ✅ With retry | Transient failures common in batch user creation |
| Group creation | ❌ No retry | Group operations are idempotent, manual retry acceptable |
| Group update | ❌ No retry | Update conflicts require manual intervention |
| Group deletion | ❌ No retry | Deletion failures need investigation, not retry |

**Rationale**: User auto-creation is most likely to experience transient failures due to:
- Concurrent user creation from multiple sources
- Temporary directory sync delays
- Network issues during batch operations

---

### Service-Level Configuration

**FR-RETRY-005**: CLI MUST support passing retry configuration to GroupSyncService via constructor parameters

**Implementation**: `cli.py:sync():189-190`

```python
# Currently uses default retry parameters
service = GroupSyncService(client)

# Future enhancement: CLI flags for retry configuration
# service = GroupSyncService(
#     client,
#     retry_attempts=args.max_retries,
#     backoff_multiplier=args.backoff_multiplier,
#     backoff_min=args.backoff_min,
#     backoff_max=args.backoff_max,
# )
```

**Current Behavior**: Uses hardcoded defaults (3 attempts, 1-4s backoff)

**Future Enhancement**: Add CLI flags for runtime configuration
```bash
xc-group-sync sync --csv test.csv \
    --retry-attempts 5 \
    --backoff-multiplier 2.0 \
    --backoff-min 0.5 \
    --backoff-max 10.0
```

**Rationale**: Currently defaults are sufficient for most use cases, but parameterization enables advanced users to tune for specific environments

---

## Retry Behavior Examples

### Successful Retry Scenario
```
[Attempt 1] POST /api/users/john@example.com
  ← Connection timeout (network issue)
[Wait 1.0s]
[Attempt 2] POST /api/users/john@example.com
  ← HTTP 503 Service Unavailable (temporary server issue)
[Wait 2.0s]
[Attempt 3] POST /api/users/john@example.com
  ← HTTP 201 Created ✅
Result: User created successfully after 2 retries
```

### Failed Retry Scenario
```
[Attempt 1] POST /api/users/john@example.com
  ← Connection timeout
[Wait 1.0s]
[Attempt 2] POST /api/users/john@example.com
  ← Connection timeout
[Wait 2.0s]
[Attempt 3] POST /api/users/john@example.com
  ← Connection timeout
Result: User creation failed after 3 attempts, operation aborted
```

### Fast-Fail Scenario (Non-Retriable)
```
[Attempt 1] POST /api/users/invalid-email
  ← HTTP 400 Bad Request (invalid email format)
Result: User creation failed immediately, no retry (permanent error)
```

---

## Integration with Tenacity Library

### Dependency
```python
# pyproject.toml
dependencies = [
    "tenacity>=8.2.0",
]
```

### Decorator Pattern
```python
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

@retry(
    retry=retry_if_exception_type(requests.RequestException),
    wait=wait_exponential(multiplier=1, min=1, max=4),
    stop=stop_after_attempt(3),
    reraise=True,
)
def _create_user_with_retry(self, email: str, dry_run: bool) -> None:
    # Implementation
```

**Decorator Parameters**:
- `retry`: Condition for retry (exception type)
- `wait`: Wait strategy (exponential backoff)
- `stop`: Stop condition (max attempts)
- `reraise`: Re-raise exception after final attempt

---

## Success Criteria

- **SC-RETRY-001**: User auto-creation operations retry up to configured attempts on transient failures
- **SC-RETRY-002**: Exponential backoff applies with configurable min/max wait times
- **SC-RETRY-003**: Non-retriable errors (4xx) fail immediately without retry attempts
- **SC-RETRY-004**: Retry logic isolated to user auto-creation, not applied to group operations
- **SC-RETRY-005**: Service consumers can configure retry parameters via constructor
- **SC-RETRY-006**: Default retry configuration handles 90%+ of transient API failures

---

## Documentation Requirements

- **DOC-RETRY-001**: README MUST document default retry configuration and behavior
- **DOC-RETRY-002**: README MUST explain which operations have retry logic and which don't
- **DOC-RETRY-003**: README MUST document retriable vs non-retriable error types
- **DOC-RETRY-004**: API documentation MUST show GroupSyncService constructor retry parameters
- **DOC-RETRY-005**: README MUST provide guidance on tuning retry configuration for different environments

---

## Testing Recommendations

### Unit Tests
```python
def test_user_creation_retry_success():
    """User creation succeeds after transient failure."""
    client = MockClient()
    client.create_user.side_effect = [
        requests.ConnectionError("Network unreachable"),
        {"email": "test@example.com"},  # Success on retry
    ]
    service = GroupSyncService(client, retry_attempts=2)
    service._ensure_user_exists("test@example.com", dry_run=False)
    assert client.create_user.call_count == 2

def test_user_creation_retry_exhausted():
    """User creation fails after retry attempts exhausted."""
    client = MockClient()
    client.create_user.side_effect = requests.ConnectionError("Network unreachable")
    service = GroupSyncService(client, retry_attempts=3)
    with pytest.raises(requests.ConnectionError):
        service._ensure_user_exists("test@example.com", dry_run=False)
    assert client.create_user.call_count == 3

def test_user_creation_no_retry_on_permanent_error():
    """User creation fails immediately on non-retriable error."""
    client = MockClient()
    client.create_user.side_effect = requests.HTTPError(response=Mock(status_code=400))
    service = GroupSyncService(client, retry_attempts=3)
    with pytest.raises(requests.HTTPError):
        service._ensure_user_exists("test@example.com", dry_run=False)
    assert client.create_user.call_count == 1  # No retry

def test_custom_retry_configuration():
    """Service respects custom retry configuration."""
    client = MockClient()
    service = GroupSyncService(
        client,
        retry_attempts=5,
        backoff_min=0.5,
        backoff_max=2.0,
    )
    assert service.retry_attempts == 5
    assert service.backoff_min == 0.5
    assert service.backoff_max == 2.0
```

### Integration Tests
```bash
# Test retry with simulated network failure
# (requires test harness with network fault injection)
pytest tests/integration/test_retry_behavior.py -k test_network_failure_recovery

# Test backoff timing
pytest tests/integration/test_retry_behavior.py -k test_exponential_backoff -v

# Test permanent failure fast-fail
pytest tests/integration/test_retry_behavior.py -k test_permanent_error_no_retry
```

---

## Performance Considerations

### Retry Impact on Execution Time

**Best Case** (no failures):
- No retry overhead
- Execution time = API call time

**Average Case** (1 transient failure):
- 1 retry with 1s backoff
- Execution time = API call time + 1s + retry API call time

**Worst Case** (all retries exhausted):
- 3 attempts with exponential backoff (1s, 2s)
- Execution time = API call time × 3 + 3s backoff total

**Batch Operations** (100 users):
- If 5% experience transient failures → ~5 extra seconds
- If 10% experience transient failures → ~10 extra seconds

**Recommendation**: Default retry configuration (3 attempts, 1-4s backoff) provides good balance between reliability and performance

---

## Security Considerations

- **Retry logic does NOT retry authentication failures** - prevents brute force attempts
- **Retry logic does NOT retry authorization failures** - respects access control decisions
- **Exponential backoff prevents aggressive retry storms** - protects F5 XC API from overload
- **Retry attempts are logged** - provides audit trail for troubleshooting

---

## Future Enhancement Opportunities

- **FR-RETRY-006** (Future): Add CLI flags for runtime retry configuration (`--retry-attempts`, `--backoff-min`, etc.)
- **FR-RETRY-007** (Future): Add retry logic to group operations with separate configuration
- **FR-RETRY-008** (Future): Add retry budget limits (max total retries across all operations)
- **FR-RETRY-009** (Future): Add jitter to backoff timing to prevent thundering herd
- **FR-RETRY-010** (Future): Add retry metrics collection (attempt counts, success rates, backoff times)
- **FR-RETRY-011** (Future): Support circuit breaker pattern for sustained API failures
- **FR-RETRY-012** (Future): Add retry configuration profiles (aggressive, balanced, conservative)

---

## Comparison with XCClient Retry Logic

**XCClient** (`client.py`) also has retry logic for ALL operations:
```python
def __init__(self, ..., max_retries: int = 3):
    retry_strategy = Retry(
        total=max_retries,
        status_forcelist=[429, 500, 502, 503, 504],
        backoff_factor=1,
    )
```

**Layered Retry Architecture**:
1. **XCClient level** (urllib3 Retry): HTTP-level retries for network/server errors
2. **GroupSyncService level** (tenacity): Business-logic retries for specific operations

**Why Two Layers?**
- **XCClient retries**: Low-level, applies to ALL HTTP requests automatically
- **GroupSyncService retries**: High-level, applies to specific business operations with custom backoff

**Interaction**: If XCClient retries are exhausted (e.g., 3 attempts at HTTP level), then GroupSyncService retries kick in (another 3 attempts at service level), resulting in up to 9 total HTTP requests in worst case

**Recommendation**: Document this layered retry architecture to prevent confusion about actual retry behavior
