import assert from 'node:assert/strict'
import { describe, it } from 'node:test'
import { fileURLToPath } from 'node:url'
import { createServer } from 'vite'

const frontendRoot = fileURLToPath(new URL('../', import.meta.url))

async function loadClient(t, baseUrl = 'http://localhost:8000/') {
  return loadModule(t, '/src/api/client.ts', baseUrl)
}

async function loadCareLoopApi(t, baseUrl = 'http://localhost:8000/') {
  return loadModule(t, '/src/api/careLoopApi.ts', baseUrl)
}

async function loadDashboardApi(t, baseUrl = 'http://localhost:8000/') {
  return loadModule(t, '/src/api/coordinatorDashboard.ts', baseUrl)
}

async function loadModule(t, modulePath, baseUrl) {
  const server = await createServer({
    appType: 'custom',
    configFile: false,
    define: {
      'import.meta.env.VITE_API_BASE_URL': JSON.stringify(baseUrl),
    },
    logLevel: 'silent',
    root: frontendRoot,
    server: { middlewareMode: true },
  })
  t.after(() => server.close())
  return server.ssrLoadModule(modulePath)
}

function mockFetch(t, implementation) {
  const originalFetch = globalThis.fetch
  globalThis.fetch = implementation
  t.after(() => {
    globalThis.fetch = originalFetch
  })
}

function jsonResponse(data, status = 200) {
  return new Response(JSON.stringify(data), {
    headers: { 'content-type': 'application/json' },
    status,
  })
}

describe('API request configuration and URLs', () => {
  it('throws a typed configuration error when the base URL is missing', async (t) => {
    const api = await loadClient(t, null)
    await assert.rejects(api.request('/resource'), api.ApiConfigurationError)
  })

  it('throws a typed configuration error when the base URL is invalid', async (t) => {
    const api = await loadClient(t, 'not a valid URL')
    await assert.rejects(api.request('/resource'), api.ApiConfigurationError)
  })

  it('resolves relative paths and preserves query parameters', async (t) => {
    const api = await loadClient(t, 'http://localhost:8000/api/')
    let requestedUrl
    mockFetch(t, async (url) => {
      requestedUrl = String(url)
      return jsonResponse({ result: true })
    })

    await api.request('patients?limit=5&cursor=next')

    assert.equal(requestedUrl, 'http://localhost:8000/api/patients?limit=5&cursor=next')
  })

  it('rejects absolute, protocol-relative, cross-origin, and backslash paths before fetching', async (t) => {
    const api = await loadClient(t)
    let fetchCalled = false
    mockFetch(t, async () => {
      fetchCalled = true
      return jsonResponse({})
    })

    for (const path of [
      'http://localhost:8000/other',
      'https://other.example/resource',
      '//other.example/resource',
      String.raw`\\other.example\resource`,
    ]) {
      await assert.rejects(api.request(path), api.ApiConfigurationError)
    }
    assert.equal(fetchCalled, false)
  })
})

describe('API response handling', () => {
  it('unwraps the documented success envelope', async (t) => {
    const api = await loadClient(t)
    mockFetch(t, async () => jsonResponse({
      success: true,
      data: { result: 'available' },
      meta: { request_id: 'request-1' },
      error: null,
    }))

    assert.deepEqual(await api.request('/resource'), { result: 'available' })
  })

  it('throws a typed error for the documented failure envelope without exposing the server message', async (t) => {
    const api = await loadClient(t)
    mockFetch(t, async () => jsonResponse({
      success: false,
      data: null,
      meta: { request_id: 'request-2' },
      error: { code: 'INVALID_STATE_TRANSITION', message: 'private server detail', details: {} },
    }, 409))

    await assert.rejects(api.request('/resource'), (error) => {
      assert.ok(error instanceof api.ApiEnvelopeError)
      assert.equal(error.code, 'INVALID_STATE_TRANSITION')
      assert.equal(error.requestId, 'request-2')
      assert.equal(error.status, 409)
      assert.equal(error.message.includes('private server detail'), false)
      return true
    })
  })

  it('rejects a malformed envelope-like successful response', async (t) => {
    const api = await loadClient(t)
    mockFetch(t, async () => jsonResponse({
      success: true,
      data: { result: 'available' },
      meta: {},
      error: null,
    }))

    await assert.rejects(api.request('/resource'), (error) => {
      assert.ok(error instanceof api.ApiEnvelopeError)
      assert.equal(error.code, 'INVALID_ENVELOPE')
      return true
    })
  })

  it('returns ordinary JSON that is not envelope-like', async (t) => {
    const api = await loadClient(t)
    const responseData = { data: { ordinary: true } }
    mockFetch(t, async () => jsonResponse(responseData))

    assert.deepEqual(await api.request('/resource'), responseData)
  })

  it('returns undefined for an empty successful response', async (t) => {
    const api = await loadClient(t)
    mockFetch(t, async () => new Response(null, { status: 204 }))

    assert.equal(await api.request('/resource'), undefined)
  })

  it('throws a typed error for invalid JSON on a successful response', async (t) => {
    const api = await loadClient(t)
    mockFetch(t, async () => new Response('not-json', { status: 200 }))

    await assert.rejects(api.request('/resource'), api.ApiInvalidJsonError)
  })

  it('throws an HTTP error for non-JSON HTTP failures without exposing the body', async (t) => {
    const api = await loadClient(t)
    mockFetch(t, async () => new Response('private server detail', { status: 502 }))

    await assert.rejects(api.request('/resource'), (error) => {
      assert.ok(error instanceof api.ApiHttpError)
      assert.equal(error.status, 502)
      assert.equal(error.message.includes('private server detail'), false)
      return true
    })
  })

  it('throws an HTTP error for an empty failed response', async (t) => {
    const api = await loadClient(t)
    mockFetch(t, async () => new Response(null, { status: 503 }))

    await assert.rejects(api.request('/resource'), (error) => {
      assert.ok(error instanceof api.ApiHttpError)
      assert.equal(error.status, 503)
      assert.equal(error.responseKind, 'empty')
      return true
    })
  })
})

describe('API request failures and bodies', () => {
  it('distinguishes a network failure from an aborted request', async (t) => {
    const api = await loadClient(t)
    mockFetch(t, async () => {
      throw new TypeError('network unavailable')
    })

    await assert.rejects(api.request('/resource'), api.ApiNetworkError)
  })

  it('preserves cancellation as a distinct typed error', async (t) => {
    const api = await loadClient(t)
    mockFetch(t, async () => {
      throw new DOMException('aborted', 'AbortError')
    })

    await assert.rejects(api.request('/resource'), api.ApiAbortError)
  })

  it('does not issue a request for an already-aborted signal', async (t) => {
    const api = await loadClient(t)
    const controller = new AbortController()
    controller.abort()
    let fetchCalled = false
    mockFetch(t, async () => {
      fetchCalled = true
      return jsonResponse({})
    })

    await assert.rejects(
      api.request('/resource', { signal: controller.signal }),
      api.ApiAbortError,
    )
    assert.equal(fetchCalled, false)
  })

  it('serializes JSON request bodies with the correct method and content type', async (t) => {
    const api = await loadClient(t)
    let capturedRequest
    mockFetch(t, async (url, init) => {
      capturedRequest = { url: String(url), ...init }
      return jsonResponse({ accepted: true })
    })

    await api.request('/resource', { method: 'POST', body: { value: 3 } })

    assert.equal(capturedRequest.method, 'POST')
    assert.equal(capturedRequest.headers.get('content-type'), 'application/json')
    assert.equal(capturedRequest.headers.get('accept'), 'application/json')
    assert.equal(capturedRequest.body, '{"value":3}')
  })

  it('rejects non-serializable JSON request bodies', async (t) => {
    const api = await loadClient(t)
    const body = {}
    body.self = body

    await assert.rejects(
      api.request('/resource', { method: 'POST', body }),
      api.ApiConfigurationError,
    )
  })
})

describe('CareLoop endpoint functions', () => {
  it('calls health and care journey with GET at the specified paths', async (t) => {
    const api = await loadCareLoopApi(t)
    const calls = []
    mockFetch(t, async (url, init) => {
      calls.push({ url: String(url), method: init.method })
      return jsonResponse({})
    })

    await api.getHealth()
    await api.getPatientCareJourney('patient-id')

    assert.deepEqual(calls, [
      { url: 'http://localhost:8000/api/health', method: 'GET' },
      { url: 'http://localhost:8000/api/patients/patient-id/care-journey', method: 'GET' },
    ])
  })

  it('serializes supported exception filters as GET query parameters', async (t) => {
    const api = await loadCareLoopApi(t)
    let requestedUrl
    let requestedMethod
    mockFetch(t, async (url, init) => {
      requestedUrl = String(url)
      requestedMethod = init.method
      return jsonResponse({ items: [], next_cursor: null })
    })

    await api.getExceptions({
      status: 'OPEN',
      assigned_role: 'CARE_COORDINATOR',
      limit: 20,
      cursor: 'next-page',
    })

    assert.equal(requestedUrl, 'http://localhost:8000/api/exceptions?status=OPEN&assigned_role=CARE_COORDINATOR&limit=20&cursor=next-page')
    assert.equal(requestedMethod, 'GET')
  })

  it('serializes audit entity query parameters using GET', async (t) => {
    const api = await loadCareLoopApi(t)
    let requestedUrl
    let requestedMethod
    mockFetch(t, async (url, init) => {
      requestedUrl = String(url)
      requestedMethod = init.method
      return jsonResponse([])
    })

    await api.getAudit({ entity_type: 'handoff', entity_id: 'entity-id' })

    assert.equal(requestedUrl, 'http://localhost:8000/api/audit?entity_type=handoff&entity_id=entity-id')
    assert.equal(requestedMethod, 'GET')
  })

  it('requests an unfiltered audit list when no filter is supplied', async (t) => {
    const api = await loadCareLoopApi(t)
    let requestedUrl
    mockFetch(t, async (url) => {
      requestedUrl = String(url)
      return jsonResponse({ items: [] })
    })

    await api.getAudit()

    assert.equal(requestedUrl, 'http://localhost:8000/api/audit')
  })

  it('posts the contract acknowledgment fields to the handoff acknowledgment path', async (t) => {
    const api = await loadCareLoopApi(t)
    let capturedRequest
    mockFetch(t, async (url, init) => {
      capturedRequest = { url: String(url), ...init }
      return jsonResponse({})
    })

    const body = {
      event_id: 'event-id',
      actor: { id: 'actor-id', role: 'CARE_COORDINATOR' },
      occurred_at: '2026-10-13T08:15:00Z',
      payload: { receipt_reference: 'receipt-reference' },
    }
    await api.acknowledgeHandoff('handoff-id', body)

    assert.equal(capturedRequest.url, 'http://localhost:8000/api/handoffs/handoff-id/acknowledge')
    assert.equal(capturedRequest.method, 'POST')
    assert.equal(capturedRequest.headers.get('content-type'), 'application/json')
    assert.deepEqual(JSON.parse(capturedRequest.body), body)
  })
})

describe('coordinator dashboard API states', () => {
  it('starts with loading states and marks an absent patient as not configured', async (t) => {
    const dashboardApi = await loadDashboardApi(t)
    const state = dashboardApi.createInitialCoordinatorDashboardState('')

    assert.equal(state.health.status, 'loading')
    assert.equal(state.exceptions.status, 'loading')
    assert.equal(state.journey.status, 'not-configured')
    assert.match(state.journey.message, /VITE_PATIENT_ID/)
  })

  it('loads journey, open exceptions, and health successfully', async (t) => {
    const dashboardApi = await loadDashboardApi(t)
    const journey = {
      patient: { id: 'patient-id', display_name: 'Test patient' },
      care_plan: { id: 'plan-id', status: 'APPROVED', version: 1 },
      actions: [],
      open_exception_count: 0,
    }
    const exception = {
      id: 'exception-id',
      exception_type: 'MISSING_HANDOFF',
      status: 'OPEN',
      assigned_role: 'CARE_COORDINATOR',
      reason: 'Test-only API response',
      action_id: 'action-id',
      handoff_id: 'handoff-id',
      created_at: '2026-10-13T08:15:00Z',
    }
    const exceptions = { items: [exception], next_cursor: null }
    const calls = []
    const state = await dashboardApi.loadCoordinatorDashboard(
      'patient-id',
      {},
      {
        getHealth: async () => {
          calls.push('health')
          return {}
        },
        getPatientCareJourney: async (id) => {
          calls.push(`journey:${id}`)
          return journey
        },
        getExceptions: async (query) => {
          calls.push(`exceptions:${query.status}`)
          return exceptions
        },
        getAudit: async () => ({ items: [] }),
      },
    )

    assert.equal(state.health.status, 'connected')
    assert.deepEqual(state.journey, { status: 'success', data: journey })
    assert.deepEqual(state.exceptions, { status: 'success', data: exceptions })
    assert.deepEqual(calls.sort(), ['exceptions:OPEN', 'health', 'journey:patient-id'])
  })

  it('represents successful empty API results explicitly', async (t) => {
    const dashboardApi = await loadDashboardApi(t)
    const state = await dashboardApi.loadCoordinatorDashboard(
      'patient-id',
      {},
      {
        getHealth: async () => undefined,
        getPatientCareJourney: async () => undefined,
        getExceptions: async () => undefined,
        getAudit: async () => undefined,
      },
    )

    assert.equal(state.health.status, 'connected')
    assert.equal(state.journey.status, 'empty')
    assert.equal(state.exceptions.status, 'empty')
  })

  it('does not request a journey without a configured patient ID', async (t) => {
    const dashboardApi = await loadDashboardApi(t)
    let journeyRequested = false
    const state = await dashboardApi.loadCoordinatorDashboard(
      '',
      {},
      {
        getHealth: async () => ({}),
        getPatientCareJourney: async () => {
          journeyRequested = true
          return undefined
        },
        getExceptions: async () => ({ items: [], next_cursor: null }),
        getAudit: async () => ({ items: [] }),
      },
    )

    assert.equal(state.journey.status, 'not-configured')
    assert.equal(journeyRequested, false)
  })

  it('exposes request failures as per-resource error states', async (t) => {
    const dashboardApi = await loadDashboardApi(t)
    const state = await dashboardApi.loadCoordinatorDashboard(
      'patient-id',
      {},
      {
        getHealth: async () => { throw new Error('health failure') },
        getPatientCareJourney: async () => { throw new Error('journey failure') },
        getExceptions: async () => { throw new Error('exception failure') },
        getAudit: async () => { throw new Error('audit failure') },
      },
    )

    assert.deepEqual(state.health, { status: 'error', message: 'The dashboard data request failed.' })
    assert.deepEqual(state.journey, { status: 'error', message: 'The dashboard data request failed.' })
    assert.deepEqual(state.exceptions, { status: 'error', message: 'The dashboard data request failed.' })
    assert.deepEqual(state.audit, { status: 'error', message: 'The dashboard data request failed.' })
  })

  it('returns typed audit entries when the unfiltered request has records', async (t) => {
    const dashboardApi = await loadDashboardApi(t)
    const audit = {
      items: [{
        id: 'audit-id',
        event_id: null,
        entity_type: 'care_action',
        entity_id: 'action-id',
        operation: 'STATUS_CHANGED',
        actor_id: 'coordinator',
        actor_role: 'CARE_COORDINATOR',
        before_state: { status: 'PENDING' },
        after_state: { status: 'READY' },
        created_at: '2026-10-13T08:15:00Z',
      }],
    }
    const state = await dashboardApi.loadCoordinatorDashboard(
      '',
      {},
      {
        getHealth: async () => undefined,
        getPatientCareJourney: async () => undefined,
        getExceptions: async () => ({ items: [], next_cursor: null }),
        getAudit: async (query) => {
          assert.deepEqual(query, {})
          return audit
        },
      },
    )

    assert.deepEqual(state.audit, { status: 'success', data: audit })
  })

  it('publishes journey success even when the audit request fails slowly', async (t) => {
    const dashboardApi = await loadDashboardApi(t)
    let finishAudit
    const pendingAudit = new Promise((resolve) => {
      finishAudit = resolve
    })
    const journey = {
      patient: { id: 'patient-id', display_name: 'Test patient' },
      care_plan: { id: 'plan-id', status: 'APPROVED', version: 1 },
      actions: [],
      handoffs: [],
      active_exceptions: [],
      open_exception_count: 0,
    }
    const published = []
    const loaded = dashboardApi.loadCoordinatorDashboard(
      'patient-id',
      {},
      {
        getHealth: async () => undefined,
        getPatientCareJourney: async () => journey,
        getExceptions: async () => ({ items: [], next_cursor: null }),
        getAudit: async () => pendingAudit,
      },
      (state) => published.push(state),
    )

    await new Promise((resolve) => setImmediate(resolve))
    assert.ok(published.some((state) => state.journey.status === 'success'))
    assert.ok(published.every((state) => state.audit.status === 'loading'))

    finishAudit(new Error('audit unavailable'))
    const finalState = await loaded
    assert.deepEqual(finalState.audit, {
      status: 'error',
      message: 'The dashboard data request failed.',
    })
  })

  it('does not publish updates after its request signal is aborted', async (t) => {
    const dashboardApi = await loadDashboardApi(t)
    const controller = new AbortController()
    const updates = []
    const loaded = dashboardApi.loadCoordinatorDashboard(
      '',
      { signal: controller.signal },
      {
        getHealth: async () => undefined,
        getPatientCareJourney: async () => undefined,
        getExceptions: async () => ({ items: [], next_cursor: null }),
        getAudit: async () => ({ items: [] }),
      },
      (state) => updates.push(state),
    )
    controller.abort()

    await loaded

    assert.deepEqual(updates, [])
  })
})
