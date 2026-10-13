insert into patients (id, external_ref, display_name)
values ('11111111-1111-4111-8111-111111111111', 'DEMO-001', 'Demo Patient')
on conflict (id) do nothing;

insert into care_plans (id, patient_id, version, status, source_text, created_by)
values ('22222222-2222-4222-8222-222222222222', '11111111-1111-4111-8111-111111111111', 1, 'APPROVED', 'Complete an ECG, then perform a cardiology review.', 'demo-coordinator')
on conflict (id) do nothing;

insert into care_actions (id, care_plan_id, title, action_type, status, responsible_role)
values
  ('33333333-3333-4333-8333-333333333333', '22222222-2222-4222-8222-222222222222', 'ECG', 'DIAGNOSTIC', 'READY', 'DIAGNOSTICS'),
  ('44444444-4444-4444-8444-444444444444', '22222222-2222-4222-8222-222222222222', 'Cardiology review', 'REVIEW', 'PENDING', 'CARDIOLOGY')
on conflict (id) do nothing;

insert into action_dependencies (action_id, depends_on_action_id, requirement_type)
values ('44444444-4444-4444-8444-444444444444', '33333333-3333-4333-8333-333333333333', 'ACTION_VERIFIED')
on conflict do nothing;
