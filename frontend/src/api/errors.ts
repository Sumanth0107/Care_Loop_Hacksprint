export class ApiClientError extends Error {
  constructor(message: string, options?: ErrorOptions) {
    super(message, options)
    this.name = new.target.name
  }
}

export class ApiConfigurationError extends ApiClientError {}

export class ApiNetworkError extends ApiClientError {}

export class ApiAbortError extends ApiClientError {}

export class ApiInvalidJsonError extends ApiClientError {}

export class ApiHttpError extends ApiClientError {
  readonly status: number
  readonly statusText: string
  readonly responseKind: 'json' | 'empty' | 'invalid-json' | 'unreadable'

  constructor(
    message: string,
    status: number,
    statusText: string,
    responseKind: 'json' | 'empty' | 'invalid-json' | 'unreadable',
    options?: ErrorOptions,
  ) {
    super(message, options)
    this.status = status
    this.statusText = statusText
    this.responseKind = responseKind
  }
}

export class ApiEnvelopeError extends ApiClientError {
  readonly code: string
  readonly details: Record<string, unknown> | undefined
  readonly requestId: string | undefined
  readonly status: number

  constructor(
    message: string,
    code: string,
    details: Record<string, unknown> | undefined,
    requestId: string | undefined,
    status: number,
  ) {
    super(message)
    this.code = code
    this.details = details
    this.requestId = requestId
    this.status = status
  }
}
