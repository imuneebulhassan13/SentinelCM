import { useState } from 'react'

function Login({ onLogin }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleLogin = async (e) => {
    e.preventDefault()

    setLoading(true)
    setError('')

    try {
      const formData = new URLSearchParams()

      formData.append('username', username)
      formData.append('password', password)

      const response = await fetch(
        'http://127.0.0.1:8000/auth/login',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
          body: formData,
        }
      )

      const result = await response.json()

      if (!response.ok) {
        throw new Error(
          result.detail || `Login failed: ${response.status}`
        )
      }

      localStorage.setItem('token', result.access_token)

      onLogin()
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-page">
      <div className="login-card">

        <div className="login-brand">
          <div className="brand-icon">SC</div>
          <h1>SentinelCM</h1>
          <p>SIEM Platform</p>
        </div>

        <form onSubmit={handleLogin}>

          <label>Username</label>
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="Enter username"
            required
          />

          <label>Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Enter password"
            required
          />

          {error && (
            <div className="login-error">
              {error}
            </div>
          )}

          <button type="submit" disabled={loading}>
            {loading ? 'Signing in...' : 'Sign In'}
          </button>

        </form>

      </div>
    </div>
  )
}

export default Login