# CareLoop backend

## Run locally

From `backend`:

```powershell
..\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload
```

The API is available at `http://localhost:8000`; OpenAPI documentation is at
`http://localhost:8000/docs`.

The scaffold uses a deterministic in-memory development store until
`SUPABASE_URL` and `SUPABASE_KEY` are configured. It does not claim a Supabase
connection is healthy without those credentials.

## Test

```powershell
python -m pytest
```
