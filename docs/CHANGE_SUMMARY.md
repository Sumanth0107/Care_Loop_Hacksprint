# CareLoop Contract Alignment Summary

This document captures the work completed during the latest update so that you can continue with follow-up instructions without re-explaining the current state.

## Purpose

The backend was aligned with the shared CareLoop technical contract so the API accepts the canonical event payload shape and preserves compatibility with the existing flat-field request patterns already used in this repo.

## What was added

### 1. Nested actor compatibility support

The contract expects payloads like:

```json
{
  "event_id": "...",
  "actor": {"id": "demo-cardiology", "role": "CARDIOLOGY"},
  "occurred_at": "2026-10-13T08:15:00Z",
  "payload": {}
}
```

The project already had some endpoints using flat fields such as:

```json
{
  "event_id": "...",
  "actor_id": "demo-cardiology",
  "actor_role": "CARDIOLOGY",
  "occurred_at": "2026-10-13T08:15:00Z",
  "payload": {}
}
```

The update adds support for both styles without breaking existing code.

### 2. Canonical event support for verification and rejection flows

The contract includes canonical event types such as:

- `COMPLETION_VERIFIED`
- `HANDOFF_REJECTED`

The event processing layer now routes these recognized events to the correct service logic instead of ignoring them or only handling a subset of the flow.

### 3. Validation-safe actor normalization

Actor metadata is normalized before processing so service logic can read consistent values regardless of whether the payload uses nested or flat fields.

## What was changed

### Schema files

- `backend/app/schemas/care_action.py`
  - added `ActorReference`
  - added normalization for `actor` + legacy `actor_id` / `actor_role`
  - kept API compatibility

- `backend/app/schemas/handoff.py`
  - added nested `actor` support
  - normalized actor fields before processing
  - fixed mutable default payload issue

### Services

- `backend/app/services/care_action_service.py`
  - actor metadata is resolved in a contract-safe way
  - action verification uses the normalized actor values
  - audit history records the correct actor metadata

- `backend/app/services/handoff_service.py`
  - actor metadata is resolved consistently for send/acknowledge/reject flows
  - rejection handling was added for canonical contract behavior

- `backend/app/services/event_service.py`
  - canonical event dispatch now supports:
    - `ACTION_STARTED`
    - `COMPLETION_REPORTED`
    - `COMPLETION_VERIFIED`
    - `HANDOFF_SENT`
    - `HANDOFF_ACKNOWLEDGED`
    - `HANDOFF_REJECTED`
  - idempotency conflict handling remains in place

## Behavior preserved

The existing repo behavior was intentionally preserved where it already matched the intended workflow:

- state-machine transitions remain authoritative
- care action completion still requires verification before `VERIFIED_COMPLETE`
- the flat-field format continues to work if existing clients use it
- duplicate event IDs still reject conflicting payloads

## Validation

This update was validated with the project backend tests:

- `pytest -q`
- Result: 8 passed

## Suggested next instruction prompt

Use this prompt template when continuing with more work:

```text
Continue from the current CareLoop contract-alignment update. Please review the remaining contract gaps and implement the next requested workflow change while preserving the existing state-machine behavior, canonical event contracts, and backward-compatible actor payload handling.
```

## File references

- [backend/app/schemas/care_action.py](../backend/app/schemas/care_action.py)
- [backend/app/schemas/handoff.py](../backend/app/schemas/handoff.py)
- [backend/app/services/care_action_service.py](../backend/app/services/care_action_service.py)
- [backend/app/services/handoff_service.py](../backend/app/services/handoff_service.py)
- [backend/app/services/event_service.py](../backend/app/services/event_service.py)
