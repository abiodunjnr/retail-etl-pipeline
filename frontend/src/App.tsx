
import { useEffect, useState } from 'react'
import {
  fetchPipelineRuns,
  fetchPipelineRunDetails,
  fetchPipelineQuality,
  type PipelineRun,
  type PipelineRunDetails,
  type PipelineQualityResponse,
} from './services/api'
import './App.css'

const PAGE_SIZE = 7

function formatDuration(value: number | null) {
  return value === null ? '—' : `${value.toFixed(2)}s`
}

function formatDate(value: string) {
  return new Date(value).toLocaleString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

function Status({ value }: { value: string }) {
  return (
    <span className={`status status-${value.toLowerCase()}`}>
      <span className="status-dot" />
      {value}
    </span>
  )
}

function App() {
  const [runs, setRuns] = useState<PipelineRun[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [connected, setConnected] = useState(false)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)

  const [selectedRunId, setSelectedRunId] = useState<number | null>(null)
  const [runDetails, setRunDetails] = useState<PipelineRunDetails | null>(null)
  const [quality, setQuality] = useState<PipelineQualityResponse | null>(null)
  const [detailsError, setDetailsError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'stages' | 'quality'>('stages')
  const [page, setPage] = useState(1)
  const [autoRefresh, setAutoRefresh] = useState(true)

  useEffect(() => {
    let active = true
    let inFlight = false

    async function loadRuns() {
      if (inFlight) return
      inFlight = true

      try {
        const data = await fetchPipelineRuns()
        if (!active) return

        setRuns(data.runs)
        setConnected(true)
        setError(null)
        setLastUpdated(new Date())
        setSelectedRunId((previous) =>
          previous ?? data.runs[0]?.run_id ?? null
        )
      } catch (err) {
        if (!active) return
        setConnected(false)
        setError(err instanceof Error ? err.message : 'Connection failed')
      } finally {
        inFlight = false
        if (active) setLoading(false)
      }
    }

    void loadRuns()

    const interval = window.setInterval(() => {
      if (autoRefresh) void loadRuns()
    }, 1000)

    return () => {
      active = false
      window.clearInterval(interval)
    }
  }, [autoRefresh])

  useEffect(() => {
    if (selectedRunId === null) return

    let active = true
    let inFlight = false

    async function loadDetails() {
      if (inFlight) return
      inFlight = true

      try {
        const [details, qualityResult] = await Promise.all([
          fetchPipelineRunDetails(selectedRunId!),
          fetchPipelineQuality(selectedRunId!),
        ])

        if (!active) return
        setRunDetails(details)
        setQuality(qualityResult)
        setDetailsError(null)
      } catch (err) {
        if (!active) return
        setDetailsError(
          err instanceof Error ? err.message : 'Failed to load run details'
        )
      } finally {
        inFlight = false
      }
    }

    // Schedule the initial fetch after the effect setup.
    const timeoutId = window.setTimeout(() => {
      void loadDetails()
    }, 0)

    const interval = window.setInterval(() => {
      if (autoRefresh) void loadDetails()
    }, 1000)

    return () => {
      active = false
      window.clearTimeout(timeoutId)
      window.clearInterval(interval)
    }
  }, [selectedRunId, autoRefresh])

  const latestRun = runs[0]
  const successfulRuns = runs.filter((run) => run.status === 'SUCCESS').length
  const successRate = runs.length
    ? (successfulRuns / runs.length) * 100
    : 0

  const totalPages = Math.max(1, Math.ceil(runs.length / PAGE_SIZE))
  const visibleRuns = runs.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)

  const metrics = quality?.quality_metrics ?? []
  const sourceTotal = metrics.reduce((sum, item) => sum + item.source_count, 0)
  const acceptedTotal = metrics.reduce((sum, item) => sum + item.accepted_count, 0)
  const rejectedTotal = metrics.reduce((sum, item) => sum + item.rejected_count, 0)
  const acceptanceRate = sourceTotal ? (acceptedTotal / sourceTotal) * 100 : 0

  function selectRun(runId: number) {
    setSelectedRunId(runId)
    setRunDetails(null)
    setQuality(null)
    setDetailsError(null)
    setActiveTab('stages')
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">▤</div>
          <div>
            <strong>Retail ETL</strong>
            <span>Platform</span>
          </div>
        </div>

        <nav className="navigation" aria-label="Main navigation">
          <a className="nav-item active" href="#overview">
            <span>◫</span> Monitoring
          </a>
          <a className="nav-item" href="#history">
            <span>▤</span> Pipeline Runs
          </a>
          <a className="nav-item" href="#quality">
            <span>◇</span> Data Quality
          </a>
          <a className="nav-item" href="#analytics">
            <span>▥</span> Analytics
          </a>
        </nav>

        <div className="sidebar-bottom">
          <div className="system-health">
            <span className={`health-dot ${connected ? 'online' : 'offline'}`} />
            <div>
              <small>Pipeline Monitoring API</small>
              <strong>{connected ? 'Connected' : 'Disconnected'}</strong>
            </div>
          </div>
          <div className="sidebar-version">Retail ETL Platform · v1.0</div>
        </div>
      </aside>

      <main className="workspace" id="overview">
        <header className="page-header">
          <div>
            <p className="eyebrow">DATA ENGINEERING / OPERATIONS</p>
            <h1>Retail ETL Monitoring Platform</h1>
            <p className="subtitle">
              Pipeline execution, data quality and operational monitoring
            </p>
          </div>

          <div className="header-actions">
            <span className="updated">
              ↻ {lastUpdated
                ? `Updated ${lastUpdated.toLocaleTimeString('en-GB')}`
                : 'Awaiting update'}
            </span>
            <label className="refresh-toggle">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(event) => setAutoRefresh(event.target.checked)}
              />
              Auto refresh
            </label>
            <span className={`connection ${connected ? 'online' : 'offline'}`}>
              ● {connected ? 'API Live' : 'API Offline'}
            </span>
          </div>
        </header>

        {error && <div className="error-banner" role="alert">{error}</div>}
        {loading && <p>Connecting to monitoring service...</p>}

        <section className="metrics" aria-label="Pipeline metrics">
          <article className="metric-card blue">
            <div className="metric-icon">▤</div>
            <div>
              <h3>Total Runs</h3>
              <strong>{runs.length}</strong>
              <p>Recorded executions</p>
            </div>
          </article>

          <article className="metric-card green">
            <div className="metric-icon">✓</div>
            <div>
              <h3>Successful Runs</h3>
              <strong>{successfulRuns}</strong>
              <p>{successRate.toFixed(1)}% success rate</p>
            </div>
          </article>

          <article className="metric-card blue">
            <div className="metric-icon">◷</div>
            <div>
              <h3>Latest Duration</h3>
              <strong>{formatDuration(latestRun?.duration_seconds ?? null)}</strong>
              <p>Run #{latestRun?.run_id ?? '—'}</p>
            </div>
          </article>

          <article className="metric-card green">
            <div className="metric-icon">◇</div>
            <div>
              <h3>Data Acceptance (Selected)</h3>
              <strong>{sourceTotal ? `${acceptanceRate.toFixed(2)}%` : '—'}</strong>
              <p>{acceptedTotal.toLocaleString()} of {sourceTotal.toLocaleString()} records</p>
            </div>
          </article>
        </section>

        <div className="content-grid">
          <section className="panel history-panel" id="history">
            <div className="panel-heading">
              <div className="heading-icon">▤</div>
              <div>
                <h2>Pipeline Execution History</h2>
                <p>Recent executions and operational status</p>
              </div>
            </div>

            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>Run ID</th>
                    <th>Status</th>
                    <th>Started At</th>
                    <th>Duration</th>
                  </tr>
                </thead>
                <tbody>
                  {visibleRuns.map((run) => (
                    <tr
                      key={run.run_id}
                      className={selectedRunId === run.run_id ? 'selected-run' : ''}
                    >
                      <td>
                        <button
                          className="run-link"
                          onClick={() => selectRun(run.run_id)}
                          aria-pressed={selectedRunId === run.run_id}
                        >
                          #{run.run_id}
                        </button>
                      </td>
                      <td><Status value={run.status} /></td>
                      <td>{formatDate(run.started_at)}</td>
                      <td>{formatDuration(run.duration_seconds)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="pagination">
              <span>
                {runs.length
                  ? `Showing ${(page - 1) * PAGE_SIZE + 1}–${Math.min(page * PAGE_SIZE, runs.length)} of ${runs.length} runs`
                  : 'No runs recorded'}
              </span>
              <div className="pagination-controls">
                <button disabled={page === 1} onClick={() => setPage(page - 1)}>
                  ‹
                </button>
                <span>Page {page} / {totalPages}</span>
                <button disabled={page === totalPages} onClick={() => setPage(page + 1)}>
                  ›
                </button>
              </div>
            </div>
          </section>

          <div className="right-column">
            <section className="panel details-panel">
              <div className="panel-heading details-heading">
                <div className="heading-icon">▧</div>
                <div>
                  <h2>Pipeline Run #{selectedRunId ?? '—'}</h2>
                  <p>
                    {runDetails
                      ? `Started ${formatDate(runDetails.run.started_at)} · ${formatDuration(runDetails.run.duration_seconds)}`
                      : 'Select a run to inspect its execution'}
                  </p>
                </div>
                {runDetails && <Status value={runDetails.run.status} />}
              </div>

              <div className="tabs" role="group" aria-label="Run details view">
                <button
                  className={activeTab === 'stages' ? 'active' : ''}
                  onClick={() => setActiveTab('stages')}
                >
                  Execution Stages
                </button>
                <button
                  className={activeTab === 'quality' ? 'active' : ''}
                  onClick={() => setActiveTab('quality')}
                >
                  Data Quality
                </button>
              </div>

              {detailsError && (
                <div className="error-banner" role="alert">{detailsError}</div>
              )}

              {activeTab === 'stages' && (
                <div className="detail-content">
                  <h3>Stage Execution</h3>
                  <p>Individual ETL processing stages and diagnostics</p>

                  <div className="table-scroll">
                    <table className="stage-table">
                      <thead>
                        <tr>
                          <th>Stage</th>
                          <th>Status</th>
                          <th>Duration</th>
                          <th>Error</th>
                        </tr>
                      </thead>
                      <tbody>
                        {runDetails?.stages.map((stage) => (
                          <tr key={stage.stage_id}>
                            <td className="stage-name">{stage.stage_name}</td>
                            <td><Status value={stage.status} /></td>
                            <td>{formatDuration(stage.duration_seconds)}</td>
                            <td title={stage.error_message ?? ''}>
                              {stage.error_message ?? '—'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {activeTab === 'quality' && (
                <div className="detail-content">
                  <h3>Dataset Validation</h3>
                  <p>Source, accepted and quarantined record counts</p>

                  <div className="table-scroll">
                    <table>
                      <thead>
                        <tr>
                          <th>Dataset</th>
                          <th>Source</th>
                          <th>Accepted</th>
                          <th>Rejected</th>
                        </tr>
                      </thead>
                      <tbody>
                        {metrics.map((metric) => (
                          <tr key={metric.dataset_name}>
                            <td>{metric.dataset_name}</td>
                            <td>{metric.source_count.toLocaleString()}</td>
                            <td>{metric.accepted_count.toLocaleString()}</td>
                            <td>{metric.rejected_count.toLocaleString()}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </section>

            <section className="panel quality-panel" id="quality">
              <div className="panel-heading quality-heading">
                <div className="heading-icon">◇</div>
                <div>
                  <h2>Data Quality</h2>
                  <p>Validation and quarantine monitoring</p>
                </div>
                <span className="quality-summary">
                  {sourceTotal ? `${acceptanceRate.toFixed(2)}% accepted` : 'No metrics'}
                </span>
              </div>

              <div className="quality-list">
                {metrics.map((metric) => {
                  const rate = metric.source_count
                    ? (metric.accepted_count / metric.source_count) * 100
                    : 0

                  return (
                    <div className="quality-row" key={metric.dataset_name}>
                      <div className="quality-label">
                        <strong>{metric.dataset_name}</strong>
                        <span>
                          {metric.accepted_count.toLocaleString()} / {metric.source_count.toLocaleString()} accepted
                        </span>
                      </div>
                      <div
                        className="progress-track"
                        role="progressbar"
                        aria-label={`${metric.dataset_name} acceptance`}
                        aria-valuenow={rate}
                        aria-valuemin={0}
                        aria-valuemax={100}
                      >
                        <div className="progress-fill" style={{ width: `${rate}%` }} />
                      </div>
                      <strong className="quality-percent">{rate.toFixed(2)}%</strong>
                    </div>
                  )
                })}
                {!metrics.length && <p>No quality metrics for this run.</p>}
              </div>

              <div className="quality-totals">
                <div><strong>{sourceTotal.toLocaleString()}</strong><span>Source Records</span></div>
                <div><strong>{acceptedTotal.toLocaleString()}</strong><span>Accepted Records</span></div>
                <div><strong>{rejectedTotal.toLocaleString()}</strong><span>Quarantined Records</span></div>
              </div>
            </section>
          </div>
        </div>

        <footer id="analytics">
          Retail ETL Platform · Engineering Observability · Python / FastAPI / React
        </footer>
      </main>
    </div>
  )
}

export default App
