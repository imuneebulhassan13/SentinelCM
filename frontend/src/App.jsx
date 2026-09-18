import { useEffect, useState } from 'react'
import './App.css'
import Login from './login.jsx'

const API_URL = 'http://127.0.0.1:8000'

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [authChecking, setAuthChecking] = useState(true)

  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  const [activePage, setActivePage] = useState('dashboard')

  const [logs, setLogs] = useState([])
  const [logsLoading, setLogsLoading] = useState(false)
  const [logsError, setLogsError] = useState(null)

  const [logSearch, setLogSearch] = useState('')
  const [logLevel, setLogLevel] = useState('all')
  const [logSource, setLogSource] = useState('all')

  const [alerts, setAlerts] = useState([])
const [alertsLoading, setAlertsLoading] = useState(false)
const [alertsError, setAlertsError] = useState(null)

  /*
   * Central API helper
   *
   * Automatically:
   * - adds JWT token
   * - detects 401
   * - removes expired/invalid token
   * - logs user out
   */
  const apiFetch = async (url, options = {}) => {
    const token = localStorage.getItem('token')

    const response = await fetch(url, {
      ...options,
      headers: {
        ...options.headers,
        Authorization: `Bearer ${token}`,
      },
    })

    if (response.status === 401) {
      localStorage.removeItem('token')
      setIsAuthenticated(false)
      setData(null)
      setError(null)

      throw new Error('Session expired. Please login again.')
    }

    return response
  }

  /*
   * Check saved session when application starts/reloads
   */
  useEffect(() => {
    const token = localStorage.getItem('token')

    if (!token) {
      setIsAuthenticated(false)
      setAuthChecking(false)
      return
    }

    fetch(`${API_URL}/auth/me`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
      .then(async (response) => {
        if (response.status === 401) {
          localStorage.removeItem('token')
          setIsAuthenticated(false)
          return
        }

        if (!response.ok) {
          throw new Error('Authentication check failed')
        }

        setIsAuthenticated(true)
      })
      .catch(() => {
        localStorage.removeItem('token')
        setIsAuthenticated(false)
      })
      .finally(() => {
        setAuthChecking(false)
      })
  }, [])

  /*
   * Load dashboard data
   */
  useEffect(() => {
    if (!isAuthenticated) return

    setError(null)

    apiFetch(`${API_URL}/dashboard/summary`)
      .then((response) => {
        if (!response.ok) {
          throw new Error(`API Error: ${response.status}`)
        }

        return response.json()
      })
      .then((result) => {
        setData(result)
      })
      .catch((err) => {
        if (err.message !== 'Session expired. Please login again.') {
          setError(err.message)
        }
      })
  }, [isAuthenticated])

  /*
   * Load Live Logs
   */
  useEffect(() => {
    if (!isAuthenticated) return
    if (activePage !== 'logs') return

    const fetchLogs = async () => {
      setLogsLoading(true)
      setLogsError(null)

      try {
        const params = new URLSearchParams()

        if (logSearch.trim()) {
          params.append('search', logSearch.trim())
        }

        if (logLevel !== 'all') {
          params.append('level', logLevel)
        }

        if (logSource !== 'all') {
          params.append('source', logSource)
        }

        const queryString = params.toString()

        const response = await apiFetch(
          `${API_URL}/logs/${queryString ? `?${queryString}` : ''}`
        )

        if (!response.ok) {
          throw new Error(`API Error: ${response.status}`)
        }

        const result = await response.json()

        setLogs(result.logs || [])
      } catch (err) {
        if (err.message === 'Session expired. Please login again.') {
          setLogsError(null)
        } else {
          setLogsError(err.message)
        }
      } finally {
        setLogsLoading(false)
      }
    }

    fetchLogs()
  }, [
    isAuthenticated,
    activePage,
    logSearch,
    logLevel,
    logSource,
  ])

/*
 * Load Alerts
 */
useEffect(() => {
  if (!isAuthenticated) return
  if (activePage !== 'alerts') return

  const fetchAlerts = async () => {
    setAlertsLoading(true)
    setAlertsError(null)

    try {
      const response = await apiFetch(`${API_URL}/alerts/`)

      if (!response.ok) {
        throw new Error(`API Error: ${response.status}`)
      }

      const result = await response.json()

      setAlerts(result.alerts || [])
    } catch (err) {
      if (err.message === 'Session expired. Please login again.') {
        setAlertsError(null)
      } else {
        setAlertsError(err.message)
      }
    } finally {
      setAlertsLoading(false)
    }
  }

  fetchAlerts()
}, [isAuthenticated, activePage])


  /*
   * Authentication check screen
   */
  if (authChecking) {
    return (
      <div className="loading">
        <h2>SentinelCM</h2>
        <p>Checking session...</p>
      </div>
    )
  }

  /*
   * Login screen
   */
  if (!isAuthenticated) {
    return (
      <Login
        onLogin={() => {
          setIsAuthenticated(true)
          setData(null)
          setError(null)
        }}
      />
    )
  }

  /*
   * Dashboard error
   */
  if (error) {
    return (
      <div className="error">
        <h2>SentinelCM</h2>
        <p>Failed to load dashboard: {error}</p>
      </div>
    )
  }

  /*
   * Dashboard loading
   */
  if (!data) {
    return (
      <div className="loading">
        <h2>SentinelCM</h2>
        <p>Loading dashboard...</p>
      </div>
    )
  }

  return (
    <div className="app-layout">

      {/* Sidebar */}
      <aside className="sidebar">

        <div className="sidebar-brand">
          <div className="brand-icon">SC</div>

          <div>
            <h1>SentinelCM</h1>
            <span>SIEM Platform</span>
          </div>
        </div>

        <nav className="sidebar-nav">

          <div className="nav-section">
            <span className="nav-label">MONITORING</span>

            <button
              className={`nav-item ${
                activePage === 'dashboard' ? 'active' : ''
              }`}
              onClick={() => setActivePage('dashboard')}
            >
              <span className="nav-icon">⌂</span>
              Dashboard
            </button>

            <button
              className={`nav-item ${
                activePage === 'logs' ? 'active' : ''
              }`}
              onClick={() => setActivePage('logs')}
            >
              <span className="nav-icon">≡</span>
              Live Logs
            </button>

            <button
              className={`nav-item ${
                activePage === 'alerts' ? 'active' : ''
              }`}
              onClick={() => setActivePage('alerts')}
              >
              <span className="nav-icon">!</span>
              Alerts
            </button>
          </div>

          <div className="nav-section">
            <span className="nav-label">ASSETS</span>

            <button className="nav-item">
              <span className="nav-icon">▣</span>
              Agents
            </button>

            <button className="nav-item">
              <span className="nav-icon">◈</span>
              Configuration
            </button>
          </div>

          <div className="nav-section">
            <span className="nav-label">SYSTEM</span>

            <button className="nav-item">
              <span className="nav-icon">⚙</span>
              Settings
            </button>
          </div>

        </nav>

        <div className="sidebar-footer">

          <div className="user-card">
            <div className="user-avatar">A</div>

            <div className="user-info">
              <strong>Administrator</strong>
              <span>Admin</span>
            </div>
          </div>

          <button
            className="logout-button"
            onClick={() => {
              localStorage.removeItem('token')
              setIsAuthenticated(false)
              setData(null)
              setError(null)
              setLogs([])
              setLogsError(null)
            }}
          >
            Logout
          </button>

        </div>

      </aside>

      {/* Main Area */}
      <div className="main-area">

        <header className="topbar">

          <div>
            <h2>
              {activePage === 'dashboard'
                ? 'Security Overview'
                : 'Live Logs'}
            </h2>

            <p>
              {activePage === 'dashboard'
                ? 'Centralized monitoring status and system activity'
                : 'Centralized security events collected from monitored agents'}
            </p>
          </div>

          <div className="system-status">
            <span className="status-dot"></span>
            System Online
          </div>

        </header>

        <main className="dashboard-main">

          {/* =========================
              DASHBOARD PAGE
          ========================= */}

          {activePage === 'dashboard' && (
            <>
              <section className="stats-grid">

                <div className="card">
                  <span>Total Agents</span>
                  <strong>{data.agents.total}</strong>
                </div>

                <div className="card">
                  <span>Online Agents</span>
                  <strong>{data.agents.online}</strong>
                </div>

                <div className="card">
                  <span>Offline Agents</span>
                  <strong>{data.agents.offline}</strong>
                </div>

                <div className="card">
                  <span>Total Logs</span>
                  <strong>{data.logs.total}</strong>
                </div>

                <div className="card">
                  <span>Error Logs</span>
                  <strong>{data.logs.error}</strong>
                </div>

                <div className="card">
                  <span>Warning Logs</span>
                  <strong>{data.logs.warning}</strong>
                </div>

                <div className="card">
                  <span>Information Logs</span>
                  <strong>{data.logs.information}</strong>
                </div>

              </section>

              <section className="dashboard-grid">

                <div className="panel">

                  <div className="panel-header">
                    <div>
                      <h3>System Overview</h3>
                      <p>Current SentinelCM system health</p>
                    </div>
                  </div>

                  <div className="health-list">

                    <div className="health-item">
                      <span>Backend API</span>
                      <strong>Online</strong>
                    </div>

                    <div className="health-item">
                      <span>MongoDB</span>
                      <strong>Connected</strong>
                    </div>

                    <div className="health-item">
                      <span>Log Collection</span>
                      <strong>Active</strong>
                    </div>

                    <div className="health-item">
                      <span>Agent Monitoring</span>
                      <strong>
                        {data.agents.total > 0 ? 'Active' : 'Waiting'}
                      </strong>
                    </div>

                  </div>

                </div>

                <div className="panel">

                  <div className="panel-header">
                    <div>
                      <h3>Log Status</h3>
                      <p>Collected security events</p>
                    </div>
                  </div>

                  <div className="health-list">

                    <div className="health-item">
                      <span>Errors</span>
                      <strong>{data.logs.error}</strong>
                    </div>

                    <div className="health-item">
                      <span>Warnings</span>
                      <strong>{data.logs.warning}</strong>
                    </div>

                    <div className="health-item">
                      <span>Information</span>
                      <strong>{data.logs.information}</strong>
                    </div>

                  </div>

                </div>

              </section>
            </>
          )}

          {/* =========================
              LIVE LOGS PAGE
          ========================= */}

          {activePage === 'logs' && (
            <section className="logs-page">

              <div className="page-header">
                <div>
                  <h2>Live Logs</h2>
                  <p>
                    Centralized security events collected from monitored agents
                  </p>
                </div>
              </div>

              {/* Search and Filters */}

              <div className="logs-toolbar">

                <input
                  type="text"
                  placeholder="Search logs..."
                  className="logs-search"
                  value={logSearch}
                  onChange={(e) => setLogSearch(e.target.value)}
                />

                <select
                  className="logs-filter"
                  value={logLevel}
                  onChange={(e) => setLogLevel(e.target.value)}
                >
                  <option value="all">All Levels</option>
                  <option value="Information">Information</option>
                  <option value="Warning">Warning</option>
                  <option value="Error">Error</option>
                </select>

                <select
                  className="logs-filter"
                  value={logSource}
                  onChange={(e) => setLogSource(e.target.value)}
                >
                  <option value="all">All Sources</option>
                  <option value="Windows">Windows</option>
                  <option value="Linux">Linux</option>
                  <option value="Network">Network</option>
                </select>

              </div>

              {/* Logs Table */}

              <div className="logs-panel">

                <div className="logs-table">

                  <div className="logs-table-header">
                    <span>Timestamp</span>
                    <span>Level</span>
                    <span>Source</span>
                    <span>Event</span>
                    <span>Agent</span>
                  </div>

                  {logsLoading ? (
                    <div className="logs-empty">
                      <strong>Loading logs...</strong>
                      <span>
                        Fetching security events from SentinelCM backend.
                      </span>
                    </div>
                  ) : logsError ? (
                    <div className="logs-empty">
                      <strong>Failed to load logs</strong>
                      <span>{logsError}</span>
                    </div>
                  ) : logs.length === 0 ? (
                    <div className="logs-empty">
                      <strong>No logs to display</strong>
                      <span>
                        No security events match the current filters.
                      </span>
                    </div>
                  ) : (
                    <div className="logs-table-body">

                      {logs.map((log) => (

                        <div
                          className="logs-table-row"
                          key={log._id}
                        >

                          <span className="log-timestamp">
                            {new Date(log.timestamp).toLocaleString()}
                          </span>

                          <span>
                            <strong
                              className={`level-badge level-${log.level.toLowerCase()}`}
                            >
                              {log.level}
                            </strong>
                          </span>

                          <span className="log-source">
                            {log.source}
                          </span>

                          <span className="log-event">

                            <strong>{log.log_name}</strong>

                            <small title={log.message}>
                              {log.message}
                            </small>

                          </span>

                          <span
                            className="log-agent"
                            title={log.agent_id}
                          >
                            {log.agent_id
                              ? `${log.agent_id.slice(0, 8)}...`
                              : 'N/A'}
                          </span>

                        </div>

                      ))}

                    </div>
                  )}

                </div>

              </div>

            </section>
          )}

          {activePage === 'alerts' && (
                  <div className="content-area">
                    <div className="page-header">
                      <div>
                        <h2>Security Alerts</h2>
                        <p className="subtitle">Real-time threat and log event alerts</p>
                      </div>
                    </div>

                    {/* Loading & Error States */}
                    {alertsLoading && <div className="state-message">Loading alerts...</div>}
                    {alertsError && <div className="state-message error">{alertsError}</div>}

                    {/* Empty State */}
                    {!alertsLoading && !alertsError && alerts.length === 0 && (
                      <div className="state-message">No alerts recorded yet.</div>
                    )}

                    {/* Alerts List */}
                    {!alertsLoading && !alertsError && alerts.length > 0 && (
                      <div className="alerts-container">
                        {alerts.map((alert, index) => {
                          const isHigh = alert.severity === 'High'
                          return (
                            <div 
                              key={alert._id || index} 
                              className={`card alert-card ${isHigh ? 'high-severity' : 'medium-severity'} ${alert.acknowledged ? 'is-resolved' : ''}`}
                            >
                              <div className="alert-header">
                                <div className="alert-tags">
                                  <span className={`severity-tag ${isHigh ? 'high' : 'medium'}`}>
                                    {alert.severity}
                                  </span>
                                  <span className="badge">{alert.source}</span>
                                  {alert.event_id && <span className="event-id-tag">Event ID: {alert.event_id}</span>}
                                  {alert.acknowledged && (
                                    <span className="status-resolved">✓ Resolved</span>
                                  )}
                                </div>
                                <span className="alert-time">
                                  {new Date(alert.timestamp).toLocaleString()}
                                </span>
                              </div>

                              <h4 style={{ margin: '0 0 4px 0' }}>{alert.title}</h4>
                              <p style={{ margin: 0, color: '#4b5563', fontSize: '14px' }}>{alert.message}</p>
                              
                              <div className="alert-footer">
                                <span className="agent-id-text">
                                  Agent: {alert.agent_id}
                                </span>

                                {!alert.acknowledged && (
                                  <button
                                    className="btn-resolve"
                                    onClick={async () => {
                                      try {
                                        const res = await apiFetch(`${API_URL}/alerts/${alert._id}/acknowledge`, {
                                          method: 'PATCH'
                                        })
                                        if (res.ok) {
                                          setAlerts(prev => prev.map(a => a._id === alert._id ? { ...a, acknowledged: true } : a))
                                        }
                                      } catch (err) {
                                        console.error("Failed to acknowledge alert", err)
                                      }
                                    }}
                                  >
                                    Mark as Resolved
                                  </button>
                                )}
                              </div>
                            </div>
                          )
                        })}
                      </div>
                    )}
                  </div>
                )}

        </main>

      </div>

    </div>
  )
}

export default App