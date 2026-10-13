create extension if not exists "pgcrypto";

create table if not exists patients (
  id uuid primary key default gen_random_uuid(),
  external_ref text,
  display_name text not null,
  created_at timestamptz not null default now()
);

create table if not exists care_plans (
  id uuid primary key default gen_random_uuid(),
  patient_id uuid not null references patients(id),
  version integer not null,
  status text not null check (status in ('DRAFT', 'PENDING_APPROVAL', 'APPROVED', 'SUPERSEDED', 'CANCELLED')),
  source_text text,
  created_by text not null,
  approved_by text,
  approved_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (patient_id, version)
);

create table if not exists care_actions (
  id uuid primary key default gen_random_uuid(),
  care_plan_id uuid not null references care_plans(id),
  title text not null,
  description text,
  action_type text not null,
  status text not null check (status in ('PENDING', 'READY', 'IN_PROGRESS', 'AWAITING_VERIFICATION', 'VERIFIED_COMPLETE', 'BLOCKED', 'CANCELLED')),
  responsible_role text not null,
  due_at timestamptz,
  completion_reported_at timestamptz,
  verified_at timestamptz,
  verified_by text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists handoffs (
  id uuid primary key default gen_random_uuid(),
  action_id uuid not null references care_actions(id),
  recipient_role text not null,
  recipient_id text,
  status text not null check (status in ('PENDING', 'SENT', 'ACKNOWLEDGED', 'REJECTED', 'CANCELLED')),
  sent_at timestamptz,
  acknowledged_at timestamptz,
  acknowledged_by text,
  deadline_at timestamptz not null,
  rejection_reason text,
  created_at timestamptz not null default now()
);

create table if not exists action_dependencies (
  id uuid primary key default gen_random_uuid(),
  action_id uuid not null references care_actions(id),
  depends_on_action_id uuid not null references care_actions(id),
  requirement_type text not null check (requirement_type in ('ACTION_VERIFIED', 'HANDOFF_ACKNOWLEDGED')),
  required_handoff_id uuid references handoffs(id),
  created_at timestamptz not null default now(),
  unique (action_id, depends_on_action_id, requirement_type),
  check (action_id <> depends_on_action_id)
);

create table if not exists care_events (
  id uuid primary key default gen_random_uuid(),
  event_id uuid not null unique,
  event_type text not null,
  action_id uuid references care_actions(id),
  handoff_id uuid references handoffs(id),
  source text not null,
  actor_id text,
  actor_role text not null,
  occurred_at timestamptz not null,
  received_at timestamptz not null default now(),
  processing_status text not null check (processing_status in ('RECEIVED', 'PROCESSED', 'REJECTED')),
  payload jsonb not null default '{}'::jsonb,
  payload_hash text,
  result_snapshot jsonb,
  error_code text
);

create table if not exists exceptions (
  id uuid primary key default gen_random_uuid(),
  action_id uuid references care_actions(id),
  handoff_id uuid references handoffs(id),
  exception_type text not null,
  status text not null check (status in ('OPEN', 'IN_PROGRESS', 'RESOLVED', 'DISMISSED')),
  assigned_role text not null,
  reason text not null,
  resolution_note text,
  created_at timestamptz not null default now(),
  resolved_at timestamptz,
  resolved_by text
);

create table if not exists audit_log (
  id uuid primary key default gen_random_uuid(),
  event_id uuid references care_events(id),
  entity_type text not null,
  entity_id uuid not null,
  operation text not null,
  actor_id text,
  actor_role text not null,
  before_state jsonb,
  after_state jsonb,
  created_at timestamptz not null default now()
);

create index if not exists care_plans_patient_status_idx on care_plans(patient_id, status);
create index if not exists care_actions_plan_status_idx on care_actions(care_plan_id, status);
create index if not exists care_actions_status_due_idx on care_actions(status, due_at);
create index if not exists handoffs_status_deadline_idx on handoffs(status, deadline_at);
create index if not exists exceptions_status_role_created_idx on exceptions(status, assigned_role, created_at);
create index if not exists audit_entity_created_idx on audit_log(entity_type, entity_id, created_at);
