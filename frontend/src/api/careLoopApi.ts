import { request } from './client'
import type {
  AuditQuery,
  AuditResponse,
  ExceptionListQuery,
  ExceptionListResponse,
  HandoffAcknowledgmentRequest,
  PatientCareJourney,
} from './types'

export interface ApiCallOptions {
  signal?: AbortSignal
}

export function getHealth(options: ApiCallOptions = {}): Promise<unknown | undefined> {
  return request<unknown>('/api/health', {
    method: 'GET',
    signal: options.signal,
  })
}

export function getPatientCareJourney(
  patientId: string,
  options: ApiCallOptions = {},
): Promise<PatientCareJourney | undefined> {
  return request<PatientCareJourney>(`/api/patients/${encodeURIComponent(patientId)}/care-journey`, {
    method: 'GET',
    signal: options.signal,
  })
}

export function getExceptions(
  query: ExceptionListQuery = {},
  options: ApiCallOptions = {},
): Promise<ExceptionListResponse | undefined> {
  const searchParams = new URLSearchParams()
  if (query.status !== undefined) searchParams.set('status', query.status)
  if (query.assigned_role !== undefined) searchParams.set('assigned_role', query.assigned_role)
  if (query.limit !== undefined) searchParams.set('limit', String(query.limit))
  if (query.cursor !== undefined) searchParams.set('cursor', query.cursor)

  const search = searchParams.toString()
  const path = search.length > 0 ? `/api/exceptions?${search}` : '/api/exceptions'

  return request<ExceptionListResponse>(path, {
    method: 'GET',
    signal: options.signal,
  })
}

export function getAudit(
  query: AuditQuery = {},
  options: ApiCallOptions = {},
): Promise<AuditResponse | undefined> {
  const searchParams = new URLSearchParams()
  if (query.entity_type !== undefined) searchParams.set('entity_type', query.entity_type)
  if (query.entity_id !== undefined) searchParams.set('entity_id', query.entity_id)

  const search = searchParams.toString()
  const path = search.length > 0 ? `/api/audit?${search}` : '/api/audit'

  return request<AuditResponse>(path, {
    method: 'GET',
    signal: options.signal,
  })
}

/**
 * The contract does not define the acknowledgment endpoint's response schema.
 * The result remains unknown until confirmed by the backend.
 */
export function acknowledgeHandoff(
  handoffId: string,
  body: HandoffAcknowledgmentRequest,
  options: ApiCallOptions = {},
): Promise<unknown | undefined> {
  return request<unknown, HandoffAcknowledgmentRequest>(
    `/api/handoffs/${encodeURIComponent(handoffId)}/acknowledge`,
    {
      method: 'POST',
      body,
      signal: options.signal,
    },
  )
}
