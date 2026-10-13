import { useEffect, useState, type ReactNode } from 'react'
import {
  createInitialCoordinatorDashboardState,
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
    void loadCoordinatorDashboard(patientId, { signal: controller.signal }).then((data) => {
      if (!controller.signal.aborted) {
        setDashboard(data)
      }
    })
    return () => controller.abort()
  }, [])

  const activeNavigationItem = navigationItems.find((item) => item.href === activeSection) ?? navigationItems[0]
  const journey = dashboard.journey.status === 'success' ? dashboard.journey.data : undefined
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
                      : 'Open exception count unavailable'
                  }
                >
                  {dashboard.exceptions.status === 'success' ? exceptions.length : '—'}
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
                <p className="panel-footnote">Care plan version {journey.care_plan.version}</p>
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
              detail="Open exception total reported by the care journey."
              icon="exceptions"
              label="Open exceptions"
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
                      <th scope="col">Dependencies</th>
                    </tr>
                  </thead>
                  <tbody>
                    {journey.actions.map((action) => (
                      <tr key={action.id}>
                        <td>{action.title}</td>
                        <td><StatusBadge tone={actionStatusTone(action.status)}>{action.status}</StatusBadge></td>
                        <td>{action.responsible_role}</td>
                        <td>{action.dependencies.length > 0 ? action.dependencies.map(formatDependency).join(', ') : 'None'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          <div className="lower-grid">
            <section className="panel exception-panel" id="exceptions" aria-labelledby="exceptions-heading">
              <SectionHeading
                description="Review open care coordination exceptions returned by the API."
                eyebrow="NEEDS ATTENTION"
                title="Exception queue"
                action={<StatusBadge tone="warning">{dashboard.exceptions.status === 'success' ? `${exceptions.length} returned` : dashboard.exceptions.status === 'loading' ? 'Loading' : 'Unavailable'}</StatusBadge>}
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
                      <span>{exception.status} · {exception.created_at}</span>
                    </div>
                  </div>
                  <dl className="exception-fields">
                    <div><dt>Reason</dt><dd>{exception.reason}</dd></div>
                    <div><dt>Assigned role</dt><dd>{exception.assigned_role}</dd></div>
                    <div><dt>Action ID</dt><dd>{exception.action_id}</dd></div>
                    <div><dt>Handoff ID</dt><dd>{exception.handoff_id}</dd></div>
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
            <StateNotice
              compact
              kind="empty"
              title="Audit unavailable"
              description="Waiting for backend confirmation of audit entity types and response structure."
            />
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
