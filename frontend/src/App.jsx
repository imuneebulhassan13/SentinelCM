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
      <div className="dashboard">
        <h1>SentinelCM</h1>
        <div className="error">
          Failed to load dashboard: {error}
        </div>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="dashboard">
        <h1>SentinelCM</h1>
        <p>Loading dashboard...</p>
      </div>
    )
  }

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div>
          <h1>SentinelCM</h1>
          <p>Security Information & Configuration Monitoring</p>
        </div>

        <div className="status">
          ● System Online
        </div>
      </header>

      <main>
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

        <section className="overview">
          <h2>System Overview</h2>
          <p>
            SentinelCM is monitoring connected systems and collecting
            security events from registered agents.
          </p>
        </section>
      </main>
    </div>
  )
}

export default App