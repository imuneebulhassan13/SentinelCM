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

  const [agents, setAgents] = useState([])
  const [agentsLoading, setAgentsLoading] = useState(false)
  const [agentsError, setAgentsError] = useState(null)

  const [baselines, setBaselines] = useState([])
  const [baselinesLoading, setBaselinesLoading] = useState(false)
  const [baselinesError, setBaselinesError] = useState(null)

  /*
   * Central API helper
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
   * Real-Time WebSocket Connection
   */
  useEffect(() => {
    if (!isAuthenticated) return

    const socket = new WebSocket('ws://127.0.0.1:8000/ws/events')

    socket.onopen = () => {
      console.log('[WebSocket] Connected to SentinelCM Live Stream')
    }

    socket.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data)

        if (payload.event_type === 'NEW_LOG') {
          const newEvent = payload.data

          // Prepend new log to Live Logs state
          setLogs((prevLogs) => [newEvent, ...prevLogs])

          // Prepend to Alerts state if Error/Critical/High level
          if (['Error', 'Critical', 'High'].includes(newEvent.level)) {
            setAlerts((prevAlerts) => [newEvent, ...prevAlerts])
          }
        }
      } catch (err) {
        console.error('[WebSocket Parse Error]', err)
      }
    }

    socket.onerror = (error) => {
      console.error('[WebSocket Error]', error)
    }

    socket.onclose = () => {
      console.log('[WebSocket] Disconnected from Live Stream')
    }

    return () => {
      socket.close()
    }
  }, [isAuthenticated])

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
   * Load Agents (with 5s live heartbeat polling)
   */
  useEffect(() => {
    if (!isAuthenticated) return
    if (activePage !== 'agents') return

    const fetchAgents = async () => {
      try {
        const response = await apiFetch(`${API_URL}/agents/`)

        if (!response.ok) {
          throw new Error(`API Error: ${response.status}`)
        }

        const result = await response.json()
        setAgents(result.agents || result || [])
      } catch (err) {
        if (err.message !== 'Session expired. Please login again.') {
          setAgentsError(err.message)
        }
      } finally {
        setAgentsLoading(false)
      }
    }

    setAgentsLoading(true)
    fetchAgents()

    const interval = setInterval(() => {
      fetchAgents()
    }, 5000)

    return () => clearInterval(interval)
  }, [isAuthenticated, activePage])

  /*
   * Load Configuration Baselines
   */
  useEffect(() => {
    if (!isAuthenticated) return
    if (activePage !== 'configuration') return

    const fetchBaselines = async () => {
      setBaselinesLoading(true)
      setBaselinesError(null)

      try {
        const response = await apiFetch(`${API_URL}/fim/baselines`)

        if (!response.ok) {
          throw new Error(`API Error: ${response.status}`)
        }

        const result = await response.json()
        setBaselines(result.baselines || result || [])
      } catch (err) {
        if (err.message !== 'Session expired. Please login again.') {
          setBaselinesError(err.message)
        }
      } finally {
        setBaselinesLoading(false)
      }
    }

    fetchBaselines()
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

            <button
              className={`nav-item ${
                activePage === 'agents' ? 'active' : ''
              }`}
              onClick={() => setActivePage('agents')}
            >
              <span className="nav-icon">▣</span>
              Agents
            </button>

            <button
              className={`nav-item ${
                activePage === 'configuration' ? 'active' : ''
              }`}
              onClick={() => setActivePage('configuration')}
            >
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
              setAgents([])
              setBaselines([])
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
                : activePage === 'logs'
                ? 'Live Logs'
                : activePage === 'alerts'
                ? 'Security Alerts'
                : activePage === 'agents'
                ? 'Monitored Agents'
                : activePage === 'configuration'
                ? 'Configuration Integrity (FIM)'
                : 'SentinelCM Platform'}
            </h2>

            <p>
              {activePage === 'dashboard'
                ? 'Centralized monitoring status and system activity'
                : activePage === 'logs'
                ? 'Centralized security events collected from monitored agents'
                : activePage === 'alerts'
                ? 'Real-time threat and log event alerts'
                : activePage === 'agents'
                ? 'Real-time endpoint agent status, operating systems, and heartbeats'
                : activePage === 'configuration'
                ? 'Monitored baseline files, SHA-256 hashes, and version history'
                : ''}
            </p>
          </div>

          <div className="system-status">
            <span className="status-dot"></span>
            System Online
          </div>
        </header>

        <main className="dashboard-main">
          {/* DASHBOARD PAGE */}
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

          {/* LIVE LOGS PAGE */}
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

              {/* Toolbar Filters */}
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
                      {logs.map((log, idx) => (
                        <div
                          className="logs-table-row"
                          key={log._id || idx}
                        >
                          <span className="log-timestamp">
                            {new Date(log.timestamp).toLocaleString()}
                          </span>

                          <span>
                            <strong
                              className={`level-badge level-${(
                                log.level || 'info'
                              ).toLowerCase()}`}
                            >
                              {log.level}
                            </strong>
                          </span>

                          <span className="log-source">{log.source}</span>

                          <span className="log-event">
                            <strong>{log.log_name}</strong>
                            <small title={log.message}>{log.message}</small>
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

          {/* ALERTS PAGE */}
          {activePage === 'alerts' && (
            <div className="content-area">
              <div className="page-header">
                <div>
                  <h2>Security Alerts</h2>
                  <p className="subtitle">
                    Real-time threat and log event alerts
                  </p>
                </div>
              </div>

              {alertsLoading && (
                <div className="state-message">Loading alerts...</div>
              )}
              {alertsError && (
                <div className="state-message error">{alertsError}</div>
              )}

              {!alertsLoading && !alertsError && alerts.length === 0 && (
                <div className="state-message">No alerts recorded yet.</div>
              )}

              {!alertsLoading && !alertsError && alerts.length > 0 && (
                <div className="alerts-container">
                  {alerts.map((alert, index) => {
                    const isHigh = alert.severity === 'High'
                    return (
                      <div
                        key={alert._id || index}
                        className={`card alert-card ${
                          isHigh ? 'high-severity' : 'medium-severity'
                        } ${alert.acknowledged ? 'is-resolved' : ''}`}
                      >
                        <div className="alert-header">
                          <div className="alert-tags">
                            <span
                              className={`severity-tag ${
                                isHigh ? 'high' : 'medium'
                              }`}
                            >
                              {alert.severity}
                            </span>
                            <span className="badge">{alert.source}</span>
                            {alert.event_id && (
                              <span className="event-id-tag">
                                Event ID: {alert.event_id}
                              </span>
                            )}
                            {alert.acknowledged && (
                              <span className="status-resolved">
                                ✓ Resolved
                              </span>
                            )}
                          </div>
                          <span className="alert-time">
                            {new Date(alert.timestamp).toLocaleString()}
                          </span>
                        </div>

                        <h4 style={{ margin: '0 0 4px 0' }}>{alert.title}</h4>
                        <p
                          style={{
                            margin: 0,
                            color: '#4b5563',
                            fontSize: '14px',
                          }}
                        >
                          {alert.message}
                        </p>

                        <div className="alert-footer">
                          <span className="agent-id-text">
                            Agent: {alert.agent_id}
                          </span>

                          {!alert.acknowledged && (
                            <button
                              className="btn-resolve"
                              onClick={async () => {
                                try {
                                  const res = await apiFetch(
                                    `${API_URL}/alerts/${alert._id}/acknowledge`,
                                    {
                                      method: 'PATCH',
                                    }
                                  )
                                  if (res.ok) {
                                    setAlerts((prev) =>
                                      prev.map((a) =>
                                        a._id === alert._id
                                          ? { ...a, acknowledged: true }
                                          : a
                                      )
                                    )
                                  }
                                } catch (err) {
                                  console.error(
                                    'Failed to acknowledge alert',
                                    err
                                  )
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

          {/* AGENTS PAGE */}
          {activePage === 'agents' && (
            <section className="logs-page">
              <div className="page-header">
                <div>
                  <h2>Monitored Agents</h2>
                  <p>
                    Real-time endpoint agent status, operating systems, and heartbeats
                  </p>
                </div>
              </div>

              <div className="logs-panel">
                <div className="logs-table">
                  <div
                    className="logs-table-header"
                    style={{
                      display: 'grid',
                      gridTemplateColumns: '1.2fr 1.5fr 1.2fr 1fr 1fr 1.5fr',
                      gap: '10px',
                    }}
                  >
                    <span>Agent ID</span>
                    <span>Hostname</span>
                    <span>IP Address</span>
                    <span>OS</span>
                    <span>Status</span>
                    <span>Last Heartbeat</span>
                  </div>

                  {agentsLoading ? (
                    <div className="logs-empty">
                      <strong>Loading agents...</strong>
                    </div>
                  ) : agentsError ? (
                    <div className="logs-empty">
                      <strong>Failed to load agents</strong>
                      <span>{agentsError}</span>
                    </div>
                  ) : agents.length === 0 ? (
                    <div className="logs-empty">
                      <strong>No agents registered</strong>
                      <span>Run the python agent script to register endpoints.</span>
                    </div>
                  ) : (
                    <div className="logs-table-body">
                      {agents.map((ag, idx) => (
                        <div
                          className="logs-table-row"
                          key={ag._id || ag.agent_id || idx}
                          style={{
                            display: 'grid',
                            gridTemplateColumns: '1.2fr 1.5fr 1.2fr 1fr 1fr 1.5fr',
                            gap: '10px',
                          }}
                        >
                          <span className="log-agent" title={ag.agent_id}>
                            {ag.agent_id ? `${ag.agent_id.slice(0, 8)}...` : 'N/A'}
                          </span>

                          <span>
                            <strong>{ag.hostname || 'Unknown'}</strong>
                          </span>

                          <span>{ag.ip_address || ag.ip || '127.0.0.1'}</span>

                          <span>{ag.os || 'Windows'}</span>

                          <span>
                            <strong
                              className={`level-badge level-${
                                ag.status === 'online' ? 'information' : 'error'
                              }`}
                            >
                              {ag.status || 'offline'}
                            </strong>
                          </span>

                          <span className="log-timestamp">
                            {ag.last_heartbeat || ag.last_seen || ag.timestamp
                              ? new Date(
                                  ag.last_heartbeat || ag.last_seen || ag.timestamp
                                ).toLocaleString()
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

          {/* CONFIGURATION PAGE */}
          {activePage === 'configuration' && (
            <section className="logs-page">
              <div className="page-header">
                <div>
                  <h2>Configuration Integrity (FIM)</h2>
                  <p>
                    Monitored baseline files, SHA-256 hashes, and version history
                  </p>
                </div>
              </div>

              <div className="logs-panel">
                <div className="logs-table">
                  <div
                    className="logs-table-header"
                    style={{
                      display: 'grid',
                      gridTemplateColumns: '1.5fr 1fr 2.5fr 1fr 1.5fr',
                      gap: '10px',
                    }}
                  >
                    <span>File Path</span>
                    <span>Version</span>
                    <span>SHA-256 Hash</span>
                    <span>Status</span>
                    <span>Timestamp</span>
                  </div>

                  {baselinesLoading ? (
                    <div className="logs-empty">
                      <strong>Loading baseline configurations...</strong>
                    </div>
                  ) : baselinesError ? (
                    <div className="logs-empty">
                      <strong>Failed to load baselines</strong>
                      <span>{baselinesError}</span>
                    </div>
                  ) : baselines.length === 0 ? (
                    <div className="logs-empty">
                      <strong>No configuration baselines recorded</strong>
                      <span>Agent will push baselines upon initialization.</span>
                    </div>
                  ) : (
                    <div className="logs-table-body">
                      {baselines.map((base, idx) => (
                        <div
                          className="logs-table-row"
                          key={base._id || idx}
                          style={{
                            display: 'grid',
                            gridTemplateColumns: '1.5fr 1fr 2.5fr 1fr 1.5fr',
                            gap: '10px',
                          }}
                        >
                          <span>
                            <strong>
                              {base.file_path || base.filename || 'config.json'}
                            </strong>
                          </span>

                          <span>
                            <strong className="badge">
                              v{base.version || '1'}
                            </strong>
                          </span>

                          <span className="log-agent" title={base.hash}>
                            {base.hash ? `${base.hash.slice(0, 24)}...` : 'N/A'}
                          </span>

                          <span>
                            <strong
                              className={`level-badge level-${
                                base.drift ? 'error' : 'information'
                              }`}
                            >
                              {base.drift ? 'Drift Detected' : 'In Sync'}
                            </strong>
                          </span>

                          <span className="log-timestamp">
                            {base.created_at || base.timestamp
                              ? new Date(
                                  base.created_at || base.timestamp
                                ).toLocaleString()
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
        </main>
      </div>
    </div>
  )
}

export default App