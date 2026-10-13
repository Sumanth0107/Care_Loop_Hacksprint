# CareLoop

CareLoop is a FastAPI, Supabase PostgreSQL, and React prototype for tracking
continuity across care actions and handoffs.

## Repository layout

- `backend/` — FastAPI application, workflow services, schemas, tests, and AI
  fallback.
- `frontend/` — React/Vite coordinator dashboard and API client.
- `database/` — target PostgreSQL schema, seed data, and transaction notes.
- `docs/` — architecture, API, database, and demo documentation.

## Quick start

### Backend

```powershell
cd backend
..\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload
```

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

The backend starts with deterministic demo data and an in-memory fallback when
Supabase credentials are absent. Copy `backend/.env.example` to `backend/.env`
and fill in `SUPABASE_URL` and `SUPABASE_KEY` only after the deployed schema
has been verified.