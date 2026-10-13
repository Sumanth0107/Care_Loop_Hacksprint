import {
  ApiClientError,
} from './client'
import {
  getExceptions,
  getHealth,
  getPatientCareJourney,
  type ApiCallOptions,
} from './careLoopApi'
import type { ExceptionListResponse, PatientCareJourney } from './types'

export type ResourceState<T> =
  | { status: 'loading' }
  | { status: 'not-configured'; message: string }
  | { status: 'empty' }
  | { status: 'success'; data: T }
  | { status: 'error'; message: string }

export type HealthState =
  | { status: 'loading' }
  | { status: 'connected' }
  | { status: 'error'; message: string }

export interface CoordinatorDashboardState {
  health: HealthState
  journey: ResourceState<PatientCareJourney>
  exceptions: ResourceState<ExceptionListResponse>
}

export interface CoordinatorDashboardApi {
  getHealth: typeof getHealth
  getPatientCareJourney: typeof getPatientCareJourney
  getExceptions: typeof getExceptions
}

const defaultApi: CoordinatorDashboardApi = {
  getHealth,
  getPatientCareJourney,
  getExceptions,
}

const patientNotConfigured: ResourceState<PatientCareJourney> = {
  status: 'not-configured',
  message: 'Patient not configured. Set VITE_PATIENT_ID to load a care journey.',
}

function getRequestErrorMessage(error: unknown): string {
  if (error instanceof ApiClientError) {
    return error.message
  }
  return 'The dashboard data request failed.'
}

async function loadHealth(
  api: CoordinatorDashboardApi,
  options: ApiCallOptions,
): Promise<HealthState> {
  try {
    await api.getHealth(options)
    return { status: 'connected' }
  } catch (error) {
    return { status: 'error', message: getRequestErrorMessage(error) }
  }
}

async function loadJourney(
  patientId: string,
  api: CoordinatorDashboardApi,
  options: ApiCallOptions,
): Promise<ResourceState<PatientCareJourney>> {
  if (!patientId) {
    return patientNotConfigured
  }

  try {
    const data = await api.getPatientCareJourney(patientId, options)
    return data === undefined ? { status: 'empty' } : { status: 'success', data }
  } catch (error) {
    return { status: 'error', message: getRequestErrorMessage(error) }
  }
}

async function loadExceptions(
  api: CoordinatorDashboardApi,
  options: ApiCallOptions,
): Promise<ResourceState<ExceptionListResponse>> {
  try {
    const data = await api.getExceptions({ status: 'OPEN' }, options)
    if (data === undefined || data.items.length === 0) {
      return { status: 'empty' }
    }
    return { status: 'success', data }
  } catch (error) {
    return { status: 'error', message: getRequestErrorMessage(error) }
  }
}

export function createInitialCoordinatorDashboardState(
  patientId: string,
): CoordinatorDashboardState {
  return {
    health: { status: 'loading' },
    journey: patientId ? { status: 'loading' } : patientNotConfigured,
    exceptions: { status: 'loading' },
  }
}

export async function loadCoordinatorDashboard(
  patientId: string,
  options: ApiCallOptions = {},
  api: CoordinatorDashboardApi = defaultApi,
): Promise<CoordinatorDashboardState> {
  const [health, journey, exceptions] = await Promise.all([
    loadHealth(api, options),
    loadJourney(patientId, api, options),
    loadExceptions(api, options),
  ])

  return { health, journey, exceptions }
}
