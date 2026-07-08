import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'

export default function SignupPage() {
  const { signup } = useAuth()
  const navigate = useNavigate()

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await signup(username, password, name)
      navigate('/')
    } catch (e) {
      setError(e.message)
      setLoading(false)
    }
  }

  return (
    <div className="screen">
      <form className="card" onSubmit={handleSubmit}>
        <p className="title">회원가입</p>
        <p className="subtitle">아이디, 비밀번호, 이름을 입력해주세요</p>

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
        <input
          className="input-text"
          placeholder="이름"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />

        <button className="button-primary" type="submit" disabled={loading}>
          {loading ? '가입하는 중...' : '회원가입'}
        </button>

        <p style={{ textAlign: 'center', marginTop: 16, fontSize: 14, color: 'var(--color-text-secondary)' }}>
          이미 계정이 있으신가요?{' '}
          <Link to="/login" style={{ color: 'var(--color-primary)', fontWeight: 600 }}>
            로그인
          </Link>
        </p>
      </form>
    </div>
  )
}