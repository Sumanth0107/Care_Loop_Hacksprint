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
}

export interface CareJourneyPlan {
  id: string
  status: CarePlanStatus
  version: number
}

export interface CareJourneyDependency {
  requirement_type: DependencyRequirementType
  satisfied: boolean
}

export interface CareJourneyAction {
  id: string
  title: string
  status: CareActionStatus
  responsible_role: string
  dependencies: CareJourneyDependency[]
}

export interface PatientCareJourney {
  patient: CareJourneyPatient
  care_plan: CareJourneyPlan
  actions: CareJourneyAction[]
  open_exception_count: number
}

export interface CareException {
  id: string
  exception_type: string
  status: ExceptionStatus
  assigned_role: string
  reason: string
  action_id: string
  handoff_id: string
  created_at: string
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
  entity_type: string
  entity_id: string
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
