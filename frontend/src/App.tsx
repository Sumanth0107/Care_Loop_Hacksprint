import { useEffect, useState, type ReactNode } from 'react'
import {
  createInitialCoordinatorDashboardState,
  getJourneyHandoffsState,
  loadCoordinatorDashboard,
  type CoordinatorDashboardState,
} from './api/coordinatorDashboard'
import type { CareActionStatus, CareJourneyDependency } from './api/types'
import './App.css'

type IconName = 'overview' | 'journey' | 'exceptions' | 'activity' | 'user' | 'link' | 'clock' | 'check' | 'alert'

type StateKind = 'loading' | 'empty' | 'success' | 'error'

const iconPaths: Record<IconName, ReactNode> = {
  overview: <><rect x="3.5" y="3.5" width="7" height="7" rx="1.5" /><rect x="13.5" y="3.5" width="7" height="4" rx="1.5" /><rect x="13.5" y="9.5" width="7" height="11" rx="1.5" /><rect x="3.5" y="13.5" width="7" height="7" rx="1.5" /></>,
  journey: <><circle cx="5" cy="5" r="2" /><circle cx="19" cy="19" r="2" /><path d="M7 5h4a4 4 0 0 1 4 4v6a4 4 0 0 0 4 4" /><path d="M5 7v10" /></>,
  exceptions: <><path d="M12 3.5 21 20H3L12 3.5Z" /><path d="M12 9v4.5" /><circle cx="12" cy="17" r=".7" fill="currentColor" stroke="none" /></>,
  activity: <><path d="M3 12h4l2.2-6 4.4 12 2.2-6H21" /></>,
  user: <><circle cx="12" cy="8" r="3.5" /><path d="M5 20a7 7 0 0 1 14 0" /></>,
  link: <><path d="M10 13.5 8.5 15a3.5 3.5 0 0 1-5-5l3-3a3.5 3.5 0 0 1 5 0" /><path d="m14 10.5 1.5-1.5a3.5 3.5 0 0 1 5 5l-3 3a3.5 3.5 0 0 1-5 0" /><path d="m9 15 6-6" /></>,
  clock: <><circle cx="12" cy="12" r="8.5" /><path d="M12 7v5l3 2" /></>,
  check: <path d="m5 12 4.5 4.5L19 7" />,
  alert: <><circle cx="12" cy="12" r="8.5" /><path d="M12 8v4.5" /><circle cx="12" cy="16" r=".7" fill="currentColor" stroke="none" /></>,
}

function Icon({ name, className = '' }: { name: IconName; className?: string }) {
  return (
    <svg
      aria-hidden="true"
      className={className}
      fill="none"
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth="1.7"
      viewBox="0 0 24 24"
    >
      {iconPaths[name]}
    </svg>
  )
}

function StateNotice({
  kind,
  title,
  description,
  compact = false,
}: {
  kind: StateKind
  title: string
  description: string
  compact?: boolean
}) {
  const iconName: IconName =
    kind === 'loading' ? 'clock' : kind === 'success' ? 'check' : kind === 'error' ? 'alert' : 'activity'

  return (
    <div
      className={`state-notice state-notice--${kind}${compact ? ' state-notice--compact' : ''}`}
      role={kind === 'error' ? 'alert' : 'status'}
      aria-live={kind === 'error' ? 'assertive' : 'polite'}
    >
      <span className={`state-notice__icon${kind === 'loading' ? ' is-spinning' : ''}`}>
        <Icon name={iconName} />
      </span>
      <span className="state-notice__copy">
        <strong>{title}</strong>
        <span>{description}</span>
      </span>
    </div>
  )
}

function BrandMark() {
  return (
    <span className="brand-mark" aria-hidden="true">
      <svg viewBox="0 0 32 32" fill="none">
        <path d="M16 4.5c-6.35 0-11.5 5.15-11.5 11.5S9.65 27.5 16 27.5 27.5 22.35 27.5 16" />
        <path d="M16 10v12M10 16h12M20.5 5.5l6 6" />
      </svg>
    </span>
  )
}

function StatusBadge({ children, tone = 'neutral' }: { children: ReactNode; tone?: 'neutral' | 'warning' | 'success' }) {
  return <span className={`status-badge status-badge--${tone}`}>{children}</span>
}

function SectionHeading({
  eyebrow,
  title,
  description,
  action,
}: {
  eyebrow?: string
  title: string
  description?: string
  action?: ReactNode
}) {
  return (
    <div className="section-heading">
      <div>
        {eyebrow && <p className="eyebrow">{eyebrow}</p>}
        <h2>{title}</h2>
        {description && <p className="section-heading__description">{description}</p>}
      </div>
      {action}
    </div>
  )
}

function MetricCard({
  label,
  detail,
  icon,
  value,
}: {
  label: string
  detail: string
  icon: IconName
  value: number | undefined
}) {
  return (
    <article className="metric-card">
      <div className="metric-card__top">
        <span className="metric-card__icon"><Icon name={icon} /></span>
        <span className="metric-card__label">{label}</span>
      </div>
      <div className="metric-card__value" aria-label={`${label}: ${value ?? 'unavailable'}`}>
        {value ?? '—'}
      </div>
      <p className="metric-card__detail">{detail}</p>
    </article>
  )
}

function actionStatusTone(status: CareActionStatus): 'neutral' | 'warning' | 'success' {
  if (status === 'VERIFIED_COMPLETE') return 'success'
  if (status === 'BLOCKED') return 'warning'
  return 'neutral'
}

function formatDependency(dependency: CareJourneyDependency): string {
  return `${dependency.requirement_type} · ${dependency.satisfied ? 'Satisfied' : 'Not satisfied'}`
}

function formatTimestamp(value: string | null | undefined): string {
  if (!value) return 'Not recorded'
  const date = new Date(value)
  return Number.isNaN(date.getTime())
    ? value
    : new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(date)
}

function formatJsonState(value: Record<string, unknown> | null): string {
  return value === null ? 'Not recorded' : JSON.stringify(value, null, 2)
}

const patientId = import.meta.env.VITE_PATIENT_ID?.trim() ?? ''

const navigationItems = [
  { label: 'Overview', href: '#overview', icon: 'overview' },
  { label: 'Care journey', href: '#journey', icon: 'journey' },
  { label: 'Exceptions', href: '#exceptions', icon: 'exceptions' },
  { label: 'Activity', href: '#activity', icon: 'activity' },
] as const

type SectionHref = (typeof navigationItems)[number]['href']

function getActiveSection(): SectionHref {
  return navigationItems.find((item) => item.href === window.location.hash)?.href ?? '#overview'
}

function App() {
  const [activeSection, setActiveSection] = useState<SectionHref>(getActiveSection)
  const [dashboard, setDashboard] = useState<CoordinatorDashboardState>(
    () => createInitialCoordinatorDashboardState(patientId),
  )

  useEffect(() => {
    const updateActiveSection = () => setActiveSection(getActiveSection())
    window.addEventListener('hashchange', updateActiveSection)
    return () => window.removeEventListener('hashchange', updateActiveSection)
  }, [])

  useEffect(() => {
    const controller = new AbortController()
    void loadCoordinatorDashboard(
      patientId,
      { signal: controller.signal },
      undefined,
      (state) => setDashboard(state),
    )
    return () => controller.abort()
  }, [])

  const activeNavigationItem = navigationItems.find((item) => item.href === activeSection) ?? navigationItems[0]
  const journey = dashboard.journey.status === 'success' ? dashboard.journey.data : undefined
  const handoffs = journey?.handoffs
  const handoffsState = getJourneyHandoffsState(handoffs)
  const exceptions = dashboard.exceptions.status === 'success' ? dashboard.exceptions.data.items : []
  const healthMessage =
    dashboard.health.status === 'connected'
      ? 'Backend API connected'
      : dashboard.health.status === 'error'
        ? 'Backend API connection failed'
        : 'Checking backend API connection'

  return (
    <div className="app-shell">
      <aside className="sidebar" aria-label="Main navigation">
        <a className="brand" href="#overview" aria-label="CareLoop Coordinator home">
          <BrandMark />
          <span className="brand__name">CareLoop Coordinator</span>
        </a>

        <div className="sidebar__workspace">
          <span className="sidebar__caption">COORDINATOR</span>
          <span className="sidebar__workspace-name">Care operations</span>
        </div>

        <nav className="primary-nav" aria-label="Dashboard sections">
          {navigationItems.map((item) => (
            <a
              aria-label={item.label}
              aria-current={item.href === activeSection ? 'page' : undefined}
              className={`primary-nav__link${item.href === activeSection ? ' is-active' : ''}`}
              href={item.href}
              key={item.href}
            >
              <Icon name={item.icon} />
              <span>{item.label}</span>
              {item.label === 'Exceptions' && (
                <span
                  className="nav-indicator"
                  aria-label={
                    dashboard.exceptions.status === 'success'
                      ? `${exceptions.length} open exceptions returned`
                      : dashboard.exceptions.status === 'empty'
                        ? 'No open exceptions'
                        : 'Open exception count unavailable'
                  }
                >
                  {dashboard.exceptions.status === 'success'
                    ? exceptions.length
                    : dashboard.exceptions.status === 'empty'
                      ? 0
                      : '—'}
                </span>
              )}
            </a>
          ))}
        </nav>

        <div className="sidebar__footer">
          <span className="sidebar__footer-icon"><Icon name="link" /></span>
          <div>
            <strong>Data connection</strong>
            <span>{healthMessage}</span>
          </div>
          <span className="connection-dot" aria-hidden="true" />
        </div>
      </aside>

      <main className="main-content" id="overview">
        <header className="topbar">
          <div className="breadcrumb"><span>Care operations</span><span aria-hidden="true">/</span><strong>{activeNavigationItem.label}</strong></div>
          <div
            className={`topbar__status topbar__status--${dashboard.health.status}`}
            role="status"
            aria-live="polite"
          >
            <span className="connection-dot" aria-hidden="true" /> {healthMessage}
          </div>
        </header>

        <div className="dashboard-content">
          <section className="page-intro" aria-labelledby="page-title">
            <div>
              <p className="eyebrow">COORDINATOR WORKSPACE</p>
              <h1 id="page-title">Care coordination</h1>
              <p className="page-intro__description">A clear view of patient plans, handoffs, and follow-up.</p>
            </div>
            <div className="coordinator-chip">
              <span className="coordinator-chip__avatar"><Icon name="user" /></span>
              <span><strong>Coordinator</strong><small>Care team</small></span>
            </div>
          </section>

          <section className="panel patient-panel" aria-labelledby="patient-heading">
            <div className="patient-panel__heading">
              <div className="patient-avatar"><Icon name="user" /></div>
              <div>
                <p className="eyebrow">PATIENT SUMMARY</p>
                <h2 id="patient-heading">Patient record</h2>
              </div>
              {journey && <StatusBadge>{journey.care_plan.status}</StatusBadge>}
            </div>
            {dashboard.journey.status === 'loading' && (
              <StateNotice kind="loading" title="Loading patient journey" description="Requesting the configured patient's care journey." />
            )}
            {dashboard.journey.status === 'not-configured' && (
              <StateNotice kind="empty" title="Patient not configured" description={dashboard.journey.message} />
            )}
            {dashboard.journey.status === 'empty' && (
              <StateNotice kind="empty" title="No patient journey returned" description="The API returned no care journey for the configured patient." />
            )}
            {dashboard.journey.status === 'error' && (
              <StateNotice kind="error" title="Patient journey unavailable" description={dashboard.journey.message} />
            )}
            {journey && (
              <>
                <div className="patient-details">
                  <div className="patient-detail">
                    <span>Display name</span>
                    <strong>{journey.patient.display_name}</strong>
                  </div>
                  <div className="patient-detail">
                    <span>Patient identifier</span>
                    <strong>{journey.patient.id}</strong>
                  </div>
                  <div className="patient-detail">
                    <span>Care-plan status</span>
                    <strong className="patient-detail__status"><span className="status-dot" />{journey.care_plan.status}</strong>
                  </div>
                </div>
                <div className="plan-metadata" aria-label="Care-plan details">
                  <span>Care-plan ID: <strong>{journey.care_plan.id}</strong></span>
                  <span>Version: <strong>{journey.care_plan.version}</strong></span>
                </div>
              </>
            )}
          </section>

          <section className="metrics-grid" aria-label="Care overview metrics">
            <MetricCard
              detail="Action count from the selected patient's care journey."
              icon="journey"
              label="Care actions"
              value={journey?.actions.length}
            />
            <MetricCard
              detail="Backend open_exception_count includes OPEN and IN_PROGRESS."
              icon="exceptions"
              label="Journey exception count"
              value={journey?.open_exception_count}
            />
          </section>

          <section className="panel journey-panel" id="journey" aria-labelledby="journey-heading">
            <SectionHeading
              description="Track each care action, its owner, and any required handoffs."
              eyebrow="PLAN PROGRESS"
              title="Care journey"
              action={<StatusBadge>{journey?.care_plan.status ?? (dashboard.journey.status === 'loading' ? 'Loading' : 'Unavailable')}</StatusBadge>}
            />
            {dashboard.journey.status === 'loading' && (
              <StateNotice compact kind="loading" title="Loading care actions" description="Care journey details are being requested." />
            )}
            {dashboard.journey.status === 'not-configured' && (
              <StateNotice compact kind="empty" title="Patient not configured" description="Set VITE_PATIENT_ID to request a care journey." />
            )}
            {dashboard.journey.status === 'empty' && (
              <StateNotice compact kind="empty" title="No care journey returned" description="The API returned an empty response." />
            )}
            {dashboard.journey.status === 'error' && (
              <StateNotice compact kind="error" title="Care journey request failed" description={dashboard.journey.message} />
            )}
            {journey && journey.actions.length === 0 && (
              <StateNotice compact kind="empty" title="No care actions" description="The returned care journey contains no actions." />
            )}
            {journey && journey.actions.length > 0 && (
              <div className="journey-table-wrap">
                <table className="journey-table">
                  <thead>
                    <tr>
                      <th scope="col">Care action</th>
                      <th scope="col">Status</th>
                      <th scope="col">Responsible role</th>
                      <th scope="col">Schedule and timestamps</th>
                      <th scope="col">Dependencies</th>
                    </tr>
                  </thead>
                  <tbody>
                    {journey.actions.map((action) => (
                      <tr key={action.id}>
                        <td>
                          <span className="journey-action-title">{action.title}</span>
                          <span className="journey-record-id">ID: {action.id}</span>
                        </td>
                        <td><StatusBadge tone={actionStatusTone(action.status)}>{action.status}</StatusBadge></td>
                        <td>{action.responsible_role}</td>
                        <td>
                          <dl className="record-timestamps">
                            <div><dt>Due</dt><dd>{action.due_at ? formatTimestamp(action.due_at) : 'Not scheduled'}</dd></div>
                            {action.created_at && <div><dt>Created</dt><dd>{formatTimestamp(action.created_at)}</dd></div>}
                            {action.updated_at && <div><dt>Updated</dt><dd>{formatTimestamp(action.updated_at)}</dd></div>}
                            {action.completion_reported_at && <div><dt>Completion reported</dt><dd>{formatTimestamp(action.completion_reported_at)}</dd></div>}
                            {action.verified_at && <div><dt>Verified</dt><dd>{formatTimestamp(action.verified_at)}</dd></div>}
                            {action.verified_by && <div><dt>Verified by</dt><dd>{action.verified_by}</dd></div>}
                          </dl>
                        </td>
                        <td>{action.dependencies.length > 0 ? action.dependencies.map(formatDependency).join(', ') : 'None'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            {journey && (
              <div className="journey-subsection">
                <div className="journey-subsection__heading">
                  <h3>Handoffs</h3>
                  <span>From this care journey</span>
                </div>
                {handoffsState === 'not-provided' && (
                  <StateNotice compact kind="empty" title="Handoff data not provided" description="The care-journey response did not include a handoffs field." />
                )}
                {handoffsState === 'empty' && (
                  <StateNotice compact kind="empty" title="No handoffs returned" description="The API returned no handoffs for this care journey." />
                )}
                {handoffsState === 'available' && handoffs && (
                  <div className="handoff-list">
                    {handoffs.map((handoff) => (
                      <article className="handoff-card" key={handoff.id}>
                        <div className="handoff-card__heading">
                          <div>
                            <strong>Handoff ID: {handoff.id}</strong>
                            <span>Related action ID: {handoff.action_id}</span>
                          </div>
                          <StatusBadge>{handoff.status}</StatusBadge>
                        </div>
                        <dl className="handoff-details">
                          <div><dt>Recipient role</dt><dd>{handoff.recipient_role ?? 'Not specified'}</dd></div>
                          <div><dt>Recipient ID</dt><dd>{handoff.recipient_id ?? 'Not specified'}</dd></div>
                          <div><dt>Deadline</dt><dd>{handoff.deadline_at ? formatTimestamp(handoff.deadline_at) : 'Not scheduled'}</dd></div>
                          {handoff.sent_at && <div><dt>Sent</dt><dd>{formatTimestamp(handoff.sent_at)}</dd></div>}
                          {handoff.acknowledged_at && <div><dt>Acknowledged</dt><dd>{formatTimestamp(handoff.acknowledged_at)}</dd></div>}
                          {handoff.acknowledged_by && <div><dt>Acknowledged by</dt><dd>{handoff.acknowledged_by}</dd></div>}
                          {handoff.created_at && <div><dt>Created</dt><dd>{formatTimestamp(handoff.created_at)}</dd></div>}
                          {handoff.updated_at && <div><dt>Updated</dt><dd>{formatTimestamp(handoff.updated_at)}</dd></div>}
                        </dl>
                      </article>
                    ))}
                  </div>
                )}
              </div>
            )}
          </section>

          <div className="lower-grid">
            <section className="panel exception-panel" id="exceptions" aria-labelledby="exceptions-heading">
              <SectionHeading
                description="Exceptions returned by the OPEN status filter."
                eyebrow="NEEDS ATTENTION"
                title="Exception queue"
                action={
                  <StatusBadge tone={dashboard.exceptions.status === 'success' ? 'warning' : 'neutral'}>
                    {dashboard.exceptions.status === 'success'
                      ? `${exceptions.length} returned`
                      : dashboard.exceptions.status === 'empty'
                        ? 'No open exceptions'
                        : dashboard.exceptions.status === 'loading'
                          ? 'Loading'
                          : 'Unavailable'}
                  </StatusBadge>
                }
              />
              {dashboard.exceptions.status === 'loading' && (
                <StateNotice kind="loading" title="Loading open exceptions" description="Requesting open exceptions from the API." />
              )}
              {dashboard.exceptions.status === 'empty' && (
                <StateNotice kind="empty" title="No open exceptions" description="The API returned no open exceptions." />
              )}
              {dashboard.exceptions.status === 'error' && (
                <StateNotice kind="error" title="Exception request failed" description={dashboard.exceptions.message} />
              )}
              {dashboard.exceptions.status === 'success' && exceptions.map((exception) => (
                <article className="exception-placeholder exception-record" key={exception.id}>
                  <div className="exception-placeholder__title">
                    <span className="exception-icon"><Icon name="exceptions" /></span>
                    <div>
                      <strong>{exception.exception_type}</strong>
                      <span>{exception.status}</span>
                    </div>
                  </div>
                  <dl className="exception-fields">
                    <div><dt>Exception ID</dt><dd>{exception.id}</dd></div>
                    <div><dt>Reason</dt><dd>{exception.reason}</dd></div>
                    <div><dt>Assigned role</dt><dd>{exception.assigned_role}</dd></div>
                    <div><dt>Action ID</dt><dd>{exception.action_id ?? 'Not linked'}</dd></div>
                    <div><dt>Handoff ID</dt><dd>{exception.handoff_id ?? 'Not linked'}</dd></div>
                    <div><dt>Created</dt><dd>{formatTimestamp(exception.created_at)}</dd></div>
                    {exception.resolved_at && <div><dt>Resolved</dt><dd>{formatTimestamp(exception.resolved_at)}</dd></div>}
                  </dl>
                </article>
              ))}
            </section>

            <section className="panel acknowledgment-panel" aria-labelledby="acknowledgment-heading">
              <div className="acknowledgment-panel__icon"><Icon name="check" /></div>
              <p className="eyebrow">COORDINATOR ACTION</p>
              <h2 id="acknowledgment-heading">Acknowledge exception</h2>
              <p className="acknowledgment-panel__description">
                Acknowledgment is disabled in this read-only integration.
              </p>
              <button className="acknowledge-button" type="button" disabled>
                <Icon name="check" />
                Acknowledge
              </button>
              <span className="button-hint">No workflow changes are submitted.</span>
            </section>
          </div>

          <section className="panel activity-panel" id="activity" aria-labelledby="activity-heading">
            <SectionHeading
              description="A traceable record of updates across the care journey."
              eyebrow="RECENT UPDATES"
              title="Activity & audit"
              action={<span className="activity-scope"><Icon name="clock" /> All activity</span>}
            />
            {dashboard.audit.status === 'loading' && (
              <StateNotice compact kind="loading" title="Loading audit history" description="Requesting the unfiltered audit history." />
            )}
            {dashboard.audit.status === 'empty' && (
              <StateNotice compact kind="empty" title="No audit entries" description="The API returned no audit history." />
            )}
            {dashboard.audit.status === 'error' && (
              <StateNotice compact kind="error" title="Audit history unavailable" description={dashboard.audit.message} />
            )}
            {dashboard.audit.status === 'success' && (
              <div className="audit-list">
                {dashboard.audit.data.items.map((entry) => (
                  <article className="audit-entry" key={entry.id}>
                    <div className="audit-entry__heading">
                      <strong>{entry.operation}</strong>
                      <time dateTime={entry.created_at}>{formatTimestamp(entry.created_at)}</time>
                    </div>
                    <dl className="audit-entry__metadata">
                      <div><dt>Entity</dt><dd>{entry.entity_type} · {entry.entity_id}</dd></div>
                      <div><dt>Actor</dt><dd>{entry.actor_id ?? 'Not identified'} · {entry.actor_role}</dd></div>
                      {entry.event_id && <div><dt>Event ID</dt><dd>{entry.event_id}</dd></div>}
                    </dl>
                    <div className="audit-entry__states">
                      <div>
                        <h3>Before state</h3>
                        <pre>{formatJsonState(entry.before_state)}</pre>
                      </div>
                      <div>
                        <h3>After state</h3>
                        <pre>{formatJsonState(entry.after_state)}</pre>
                      </div>
                    </div>
                  </article>
                ))}
              </div>
            )}
          </section>

          <footer className="dashboard-footer">
            <span>CareLoop Coordinator</span>
            <span>Read-only API integration</span>
          </footer>
        </div>
      </main>
    </div>
  )
}

export default App
