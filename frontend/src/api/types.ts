export type CarePlanStatus = 'DRAFT' | 'PENDING_APPROVAL' | 'APPROVED' | 'SUPERSEDED' | 'CANCELLED'

export type CareActionStatus =
  | 'PENDING'
  | 'READY'
  | 'IN_PROGRESS'
  | 'AWAITING_VERIFICATION'
  | 'VERIFIED_COMPLETE'
  | 'BLOCKED'
  | 'CANCELLED'

export type DependencyRequirementType = 'ACTION_VERIFIED' | 'HANDOFF_ACKNOWLEDGED'

export type HandoffStatus = 'PENDING' | 'SENT' | 'ACKNOWLEDGED' | 'REJECTED' | 'CANCELLED'

export type ExceptionStatus = 'OPEN' | 'IN_PROGRESS' | 'RESOLVED' | 'DISMISSED'

export type EventProcessingStatus = 'RECEIVED' | 'PROCESSED' | 'REJECTED'

export type CareEventType =
  | 'ACTION_STARTED'
  | 'COMPLETION_REPORTED'
  | 'COMPLETION_VERIFIED'
  | 'HANDOFF_SENT'
  | 'HANDOFF_ACKNOWLEDGED'
  | 'HANDOFF_REJECTED'
  | 'BARRIER_REPORTED'
  | 'RESCHEDULE_REQUESTED'

export interface CareJourneyPatient {
  id: string
  display_name: string
  external_ref?: string | null
  created_at?: string | null
}

export interface CareJourneyPlan {
  id: string
  status: CarePlanStatus
  version: number
  patient_id?: string
  created_at?: string | null
  updated_at?: string | null
}

export interface CareJourneyDependency {
  requirement_type: DependencyRequirementType
  satisfied: boolean
}

export interface CareJourneyAction {
  id: string
  care_plan_id?: string
  title: string
  status: CareActionStatus
  responsible_role: string
  due_at?: string | null
  created_at?: string | null
  updated_at?: string | null
  completion_reported_at?: string | null
  verified_at?: string | null
  verified_by?: string | null
  dependencies: CareJourneyDependency[]
}

export interface CareJourneyHandoff {
  id: string
  action_id: string
  status: HandoffStatus
  recipient_role?: string | null
  recipient_id?: string | null
  deadline_at?: string | null
  sent_at?: string | null
  acknowledged_at?: string | null
  acknowledged_by?: string | null
  created_at?: string | null
  updated_at?: string | null
}

export interface CareJourneyException {
  id: string
  exception_type?: string
  status: ExceptionStatus
  action_id?: string | null
  handoff_id?: string | null
  assigned_role?: string | null
  reason?: string
  created_at?: string | null
  updated_at?: string | null
}

export interface PatientCareJourney {
  patient: CareJourneyPatient
  care_plan: CareJourneyPlan
  actions: CareJourneyAction[]
  handoffs: CareJourneyHandoff[]
  active_exceptions: CareJourneyException[]
  open_exception_count: number
}

export interface CareException {
  id: string
  exception_type: string
  status: ExceptionStatus
  assigned_role: string
  reason: string
  action_id: string | null
  handoff_id: string | null
  created_at: string
  resolved_at?: string | null
  resolved_by?: string | null
  resolution_note?: string | null
}

export interface ExceptionListResponse {
  items: CareException[]
  next_cursor: string | null
}

export interface ExceptionListQuery {
  status?: ExceptionStatus
  assigned_role?: string
  limit?: number
  cursor?: string
}

export interface AuditQuery {
  entity_type?: string
  entity_id?: string
}

export interface AuditEntry {
  id: string
  event_id: string | null
  entity_type: string
  entity_id: string
  operation: string
  actor_id: string | null
  actor_role: string
  before_state: Record<string, unknown> | null
  after_state: Record<string, unknown> | null
  created_at: string
}

export interface AuditResponse {
  items: AuditEntry[]
}

export interface HandoffAcknowledgmentRequest {
  event_id: string
  actor: {
    id?: string
    role: string
  }
  occurred_at: string
  payload: {
    receipt_reference: string
  }
}
