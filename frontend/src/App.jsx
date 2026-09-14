import { useEffect, useState } from 'react'
import './App.css'

function App() {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch('http://127.0.0.1:8000/dashboard/summary', {
      headers: {
        Authorization: `Bearer ${localStorage.getItem('token')}`,
      },
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`API Error: ${response.status}`)
        }
        return response.json()
      })
      .then((result) => setData(result))
      .catch((err) => setError(err.message))
  }, [])

  if (error) {
    return (
      <div className="error">
        <h2>SentinelCM</h2>
        <p>Failed to load dashboard: {error}</p>
      </div>
    )
  }

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

            <button className="nav-item active">
              <span className="nav-icon">⌂</span>
              Dashboard
            </button>

            <button className="nav-item">
              <span className="nav-icon">≡</span>
              Live Logs
            </button>

            <button className="nav-item">
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

          <button className="logout-button">
            Logout
          </button>

        </div>

      </aside>

      {/* Main Area */}
      <div className="main-area">

        <header className="topbar">

          <div>
            <h2>Security Overview</h2>
            <p>Centralized monitoring status and system activity</p>
          </div>

          <div className="system-status">
            <span className="status-dot"></span>
            System Online
          </div>

        </header>

        <main className="dashboard-main">

          {/* Statistics */}

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

          {/* Dashboard Panels */}

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

        </main>

      </div>

    </div>
  )
}

export default App