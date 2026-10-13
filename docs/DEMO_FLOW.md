# Demo flow

1. Start the backend and load the seeded synthetic patient.
2. Open the patient journey and observe the ECG action as `READY` and the
   cardiology review as `PENDING`.
3. Report completion as a patient; the action becomes
   `AWAITING_VERIFICATION`.
4. Verify with authorized evidence; the action becomes `VERIFIED_COMPLETE` and
   the dependent action becomes eligible.
5. Create, send, and acknowledge a handoff to demonstrate persisted
   responsibility and audit history.
