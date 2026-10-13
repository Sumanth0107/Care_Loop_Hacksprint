import {
  ApiAbortError,
  ApiConfigurationError,
  ApiEnvelopeError,
  ApiHttpError,
  ApiInvalidJsonError,
  ApiNetworkError,
} from './errors'

export type ApiHttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE' | 'HEAD'

export interface ApiRequestOptions<TBody = unknown> {
  method?: ApiHttpMethod
  body?: TBody
  headers?: HeadersInit
  signal?: AbortSignal
}

interface ApiEnvelopeMeta {
  request_id: string
}

interface ApiEnvelopeFailure {
  code: string
  message: string
  details?: Record<string, unknown>
}

type ApiEnvelope =
  | {
      success: true
      data: unknown
      meta: ApiEnvelopeMeta
      error: null
    }
  | {
      success: false
      data: null
      meta: ApiEnvelopeMeta
      error: ApiEnvelopeFailure
    }

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim()

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function isApiEnvelope(value: unknown): value is ApiEnvelope {
  if (!isRecord(value) || !Object.hasOwn(value, 'success') || !Object.hasOwn(value, 'data')) {
    return false
  }

  if (!Object.hasOwn(value, 'meta') || !Object.hasOwn(value, 'error')) {
    return false
  }

  if (typeof value.success !== 'boolean' || !isRecord(value.meta)) {
    return false
  }

  const requestId = value.meta.request_id
  if (typeof requestId !== 'string' || requestId.length === 0) {
    return false
  }

  if (value.success) {
    return value.error === null
  }

  return (
    value.data === null &&
    isRecord(value.error) &&
    typeof value.error.code === 'string' &&
    typeof value.error.message === 'string' &&
    (value.error.details === undefined || isRecord(value.error.details))
  )
}

function looksLikeApiEnvelope(value: unknown): boolean {
  if (!isRecord(value)) {
    return false
  }

  const indicators = ['success', 'data', 'meta', 'error']
  const presentIndicators = indicators.filter((key) => Object.hasOwn(value, key)).length
  return Object.hasOwn(value, 'success') || presentIndicators >= 3
}

function getRequestUrl(path: string): string {
  if (!apiBaseUrl) {
    throw new ApiConfigurationError(
      'VITE_API_BASE_URL is not configured. Set it to the FastAPI base URL before making API requests.',
    )
  }

  try {
    const baseUrl = new URL(apiBaseUrl)
    if (baseUrl.protocol !== 'http:' && baseUrl.protocol !== 'https:') {
      throw new TypeError('The configured API base URL must use HTTP or HTTPS.')
    }

    if (
      path.length === 0 ||
      path.startsWith('//') ||
      path.includes('\\') ||
      /^[a-z][a-z\d+.-]*:/i.test(path)
    ) {
      throw new TypeError('The request path must be relative to the configured API base URL.')
    }

    const requestUrl = new URL(path, baseUrl)
    if (requestUrl.origin !== baseUrl.origin) {
      throw new TypeError('The request path must use the configured API origin.')
    }

    return requestUrl.toString()
  } catch (cause) {
    throw new ApiConfigurationError('VITE_API_BASE_URL or the request path is not a valid URL.', { cause })
  }
}

function isAbortError(error: unknown): boolean {
  return typeof error === 'object' && error !== null && 'name' in error && error.name === 'AbortError'
}

function createAbortError(cause?: unknown): ApiAbortError {
  return new ApiAbortError('The API request was cancelled.', cause === undefined ? undefined : { cause })
}

function throwEnvelopeError(
  responseData: Extract<ApiEnvelope, { success: false }>,
  status: number,
): never {
  throw new ApiEnvelopeError(
    'The API reported an application-level error.',
    responseData.error.code,
    responseData.error.details,
    responseData.meta.request_id,
    status,
  )
}

export async function request<TResponse, TBody = unknown>(
  path: string,
  options: ApiRequestOptions<TBody> = {},
): Promise<TResponse | undefined> {
  const url = getRequestUrl(path)
  const method = options.method ?? 'GET'
  const headers = new Headers(options.headers)
  headers.set('Accept', 'application/json')

  let body: string | undefined
  if (options.body !== undefined) {
    if (method === 'GET' || method === 'HEAD') {
      throw new ApiConfigurationError(`${method} requests cannot include a body.`)
    }

    try {
      body = JSON.stringify(options.body)
    } catch (cause) {
      throw new ApiConfigurationError('The request body could not be serialized as JSON.', { cause })
    }

    if (body === undefined) {
      throw new ApiConfigurationError('The request body must be JSON serializable.')
    }

    headers.set('Content-Type', 'application/json')
  }

  if (options.signal?.aborted) {
    throw createAbortError(options.signal.reason)
  }

  let response: Response
  try {
    response = await fetch(url, {
      method,
      headers,
      body,
      signal: options.signal,
    })
  } catch (cause) {
    if (options.signal?.aborted || isAbortError(cause)) {
      throw createAbortError(cause)
    }
    throw new ApiNetworkError('The API request could not reach the server.', { cause })
  }

  let responseText: string
  try {
    responseText = await response.text()
  } catch (cause) {
    if (options.signal?.aborted || isAbortError(cause)) {
      throw createAbortError(cause)
    }
    if (!response.ok) {
      throw new ApiHttpError(
        `The API request failed with HTTP ${response.status}.`,
        response.status,
        response.statusText,
        'unreadable',
        { cause },
      )
    }
    throw new ApiNetworkError('The API response could not be read.', { cause })
  }

  if (responseText.length === 0) {
    if (!response.ok) {
      throw new ApiHttpError(
        `The API request failed with HTTP ${response.status}.`,
        response.status,
        response.statusText,
        'empty',
      )
    }
    return undefined
  }

  let responseData: unknown
  try {
    responseData = JSON.parse(responseText) as unknown
  } catch (cause) {
    if (!response.ok) {
      throw new ApiHttpError(
        `The API request failed with HTTP ${response.status}.`,
        response.status,
        response.statusText,
        'invalid-json',
        { cause },
      )
    }
    throw new ApiInvalidJsonError('The API response was not valid JSON.', { cause })
  }

  if (!response.ok) {
    if (isApiEnvelope(responseData) && !responseData.success) {
      throwEnvelopeError(responseData, response.status)
    }

    throw new ApiHttpError(
      `The API request failed with HTTP ${response.status}.`,
      response.status,
      response.statusText,
      'json',
    )
  }

  if (isApiEnvelope(responseData)) {
    if (!responseData.success) {
      throwEnvelopeError(responseData, response.status)
    }
    return responseData.data as TResponse
  }

  if (looksLikeApiEnvelope(responseData)) {
    throw new ApiEnvelopeError(
      'The API returned an invalid response envelope.',
      'INVALID_ENVELOPE',
      undefined,
      undefined,
      response.status,
    )
  }

  return responseData as TResponse
}

export {
  ApiAbortError,
  ApiClientError,
  ApiConfigurationError,
  ApiEnvelopeError,
  ApiHttpError,
  ApiInvalidJsonError,
  ApiNetworkError,
} from './errors'
