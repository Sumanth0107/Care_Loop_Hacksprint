# CareLoop v3 Contract Alignment Update

## Purpose
This document records the additions and changes made to align the current backend workflow with the authoritative CareLoop Shared Technical Contract v3 while preserving existing routes, schemas, state names, canonical event types, actor compatibility, and workflow semantics.

## Added

### Contract-focused validation suite
- Added `backend/tests/test_v3_contract_behaviors.py`
- Covers the required behaviors:
  - all six canonical event types dispatch to the correct service logic
  - nested and legacy flat actor payloads both work
  - completion reporting cannot bypass verification
  - handoff acknowledgment and rejection follow valid distinct transitions
  - required state changes persist in the database
  - dependent actions stay blocked until prerequisites are satisfied
  - exception resolution and audit history remain consistent
  - replayed events do not reapply side effects
  - database failures do not return false success
  - v3-compatible endpoints remain usable

### Test isolation for in-memory persistence
- Added `backend/tests/conftest.py`
- Ensures each test runs against a fresh in-memory database to prevent cross-test state leakage.
- Re-seeds demo data after reset so baseline contract tests and demo workflows remain stable.

## Changed

### State machine alignment
- Updated `backend/app/services/state_machine.py`
- Added the valid v3 completion transition from READY/IN_PROGRESS to `AWAITING_VERIFICATION`.
- Preserved allowed verification flow into `VERIFIED_COMPLETE`.

### Exception transition rules
- Updated `backend/app/services/exception_service.py`
- Allowed open exceptions to resolve directly while keeping dismissal and in-progress flows valid.

### Error surface consistency
- Updated `backend/app/core/exceptions.py`
- `CareLoopError.__str__()` now includes the error code, making invalid-state and internal-error assertions match contract-style error codes.

### Database reset support
- Updated `backend/app/core/database.py`
- Added `reset_database()` so the in-memory persistence layer can be safely reinitialized for deterministic tests.

## Validation
Executed:
- `cd backend`
- `python -m pytest tests -v`

Result:
- 17 tests passed
- 2 warnings from the Supabase dependency deprecation path
- Exit code: 0

## Notes and remaining blockers
- The repository’s local validation is against the configured in-memory database, not a live production Supabase/PostgreSQL deployment.
- Real transactional database verification remains unavailable because no live configured database workflow was executed in this environment.
- The workflow is aligned to the v3 contract and verified locally for the configured test/in-memory backend.

## Files touched
- `backend/tests/test_v3_contract_behaviors.py`
- `backend/tests/conftest.py`
- `backend/app/services/state_machine.py`
- `backend/app/services/exception_service.py`
- `backend/app/core/exceptions.py`
- `backend/app/core/database.py`

## Follow-up guidance
Use this summary as the baseline handoff for any further instruction set you want to give. If the next phase includes dashboard integration or a live database-backed environment, the next step is to verify the same persisted event and dependency flows against the actual external database and endpoint contract in that environment.
