# API contract

Base URL: `http://localhost:8000/api`. Every successful response uses:

```json
{"success": true, "data": {}, "meta": {"request_id": "..."}, "error": null}
```

The care journey response is `{patient, care_plan, actions,
open_exception_count}`. Action transitions are controlled by the backend state
machine; a patient completion report produces `AWAITING_VERIFICATION`, not
`VERIFIED_COMPLETE`.

Implemented paths include:

- `GET /health`
- `GET /patients/{patient_id}/care-journey`
- `GET /care-plans/{plan_id}`
- `POST /care-plans`
- `POST /care-plans/{plan_id}/parse`
- `POST /care-plans/{plan_id}/approve`
- `GET /care-actions/{action_id}`
- action start/report/verify endpoints
- handoff create/send/acknowledge endpoints
- `POST /care-events`
- exception list/update and audit list endpoints
- AI classify and extraction endpoints
