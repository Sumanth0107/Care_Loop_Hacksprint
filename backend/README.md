# CareLoop backend

## Run locally

From `backend`:

```powershell
..\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload
```

The API is available at `http://localhost:8000`; OpenAPI documentation is at
`http://localhost:8000/docs`.

Read repositories use a deterministic in-memory store unless both
`SUPABASE_URL` and `SUPABASE_KEY` are configured. The health endpoint reports
the actual configured connection state; configuration alone is not treated as
a successful connection.

## Persistence status

When Supabase is configured, read repositories use Supabase, but the current
event, action, handoff, and exception mutation services still write to the
in-memory store. Those paths do not provide cross-resource database
transactions. Supabase-backed mutation and audit persistence must not be
treated as supported until those services are moved to a shared persistence
adapter and transaction boundary.

## Exception-list pagination

`GET /api/exceptions` accepts an optional opaque `cursor` alongside its
existing `status`, `assigned_role`, and `limit` filters. Pages are ordered by
`created_at` descending, then `id` descending. A cursor is a versioned,
URL-safe Base64 JSON token containing that last-row boundary and the selected
status and role filters. Clients must treat it as opaque and reuse the same
filters on subsequent pages. Malformed, unsupported, or filter-mismatched
cursors return the standard error envelope with HTTP 400 and
`INVALID_CURSOR`. `next_cursor` is null when no further row exists; otherwise
it identifies the last row returned in the current page.

## Test

```powershell
python -m pytest
```
