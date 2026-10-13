# Database schema

`database/schema.sql` contains the target Supabase PostgreSQL schema. The
repository initially had no database tables, so no existing schema was
modified. Apply the schema only after comparing it with the deployed Supabase
project.

Canonical tables are `patients`, `care_plans`, `care_actions`,
`action_dependencies`, `handoffs`, `care_events`, `exceptions`, and
`audit_log`.
