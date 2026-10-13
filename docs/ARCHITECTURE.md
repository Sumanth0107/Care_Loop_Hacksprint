# CareLoop architecture

The frontend reads persisted workflow state through the FastAPI API. It never
writes directly to Supabase. FastAPI validates requests, the workflow services
own state transitions, and the database layer is the persistence boundary.

The current development scaffold has a deterministic in-memory store so the
demo and tests run without credentials. Supabase is the intended production
provider and should be enabled only after its schema is inspected and
transactional RPCs are agreed.
