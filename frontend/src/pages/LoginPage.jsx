import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'

export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(username, password)
      navigate('/')
    } catch (e) {
      setError(e.message)
      setLoading(false)
    }
  }

  return (
    <div className="screen">
      <form className="card" onSubmit={handleSubmit}>
        <p className="title">로그인</p>
        <p className="subtitle">rush-ticketing 계정으로 로그인하세요</p>

        {error && <div className="error-banner">{error}</div>}

        <input
          className="input-text"
          placeholder="아이디"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
        />
        <input
          className="input-text"
          placeholder="비밀번호"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />

        <button className="button-primary" type="submit" disabled={loading}>
          {loading ? '로그인하는 중...' : '로그인'}
        </button>

        <p style={{ textAlign: 'center', marginTop: 16, fontSize: 14, color: 'var(--color-text-secondary)' }}>
          계정이 없으신가요?{' '}
          <Link to="/signup" style={{ color: 'var(--color-primary)', fontWeight: 600 }}>
            회원가입
          </Link>
        </p>
      </form>
    </div>
  )
}