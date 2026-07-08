import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { joinQueue, getQueueStatus, TRAIN_ID } from '../api/client'

const POLL_INTERVAL_MS = 1500

export default function WaitingPage() {
  const { name } = useAuth()
  const navigate = useNavigate()
  const [token, setToken] = useState(null)
  const [status, setStatus] = useState(null)
  const [error, setError] = useState('')
  const [joining, setJoining] = useState(false)
  const pollTimerRef = useRef(null)

  async function handleJoin() {
    setError('')
    setJoining(true)
    try {
      const { token: newToken } = await joinQueue(TRAIN_ID)
      setToken(newToken)
    } catch (e) {
      setError(e.message)
      setJoining(false)
    }
  }

  useEffect(() => {
    if (!token) return

    async function poll() {
      try {
        const data = await getQueueStatus(TRAIN_ID, token)
        if (data.state === 'ADMITTED') {
          clearInterval(pollTimerRef.current)
          navigate('/seats', { state: { admitToken: token } })
          return
        }
        setStatus(data)
      } catch (e) {
        setError(e.message)
        clearInterval(pollTimerRef.current)
      }
    }

    poll()
    pollTimerRef.current = setInterval(poll, POLL_INTERVAL_MS)
    return () => clearInterval(pollTimerRef.current)
  }, [token])

  if (!token) {
    return (
      <div className="screen">
        <div className="card">
          <p className="title">티켓 예매를 시작할게요</p>
          <p className="subtitle">{name}님, 순서대로 안전하게 안내해드릴게요</p>
          {error && <div className="error-banner">{error}</div>}
          <button className="button-primary" onClick={handleJoin} disabled={joining}>
            {joining ? '접속하는 중...' : '대기열 참여하기'}
          </button>
        </div>
      </div>
    )
  }

  const progress =
    status && status.total_waiting > 0
      ? Math.min(100, Math.round(((status.total_waiting - status.ahead_of_me) / status.total_waiting) * 100))
      : 0

  return (
    <div className="screen">
      <div className="card">
        <p className="subtitle" style={{ marginBottom: 4 }}>
          {name}님, 순서대로 안내해드리고 있어요
        </p>
        <div
          className="tabular-nums"
          style={{ fontSize: 56, fontWeight: 800, color: 'var(--color-primary)', margin: '16px 0 8px' }}
        >
          {status ? status.rank.toLocaleString() : '-'}
          <span style={{ fontSize: 20, fontWeight: 600, color: 'var(--color-text-secondary)' }}>번째</span>
        </div>
        <p className="subtitle">
          내 앞에{' '}
          <strong className="tabular-nums" style={{ color: 'var(--color-text)' }}>
            {status ? status.ahead_of_me.toLocaleString() : '-'}명
          </strong>
          이 대기하고 있어요
        </p>
        <div
          style={{
            width: '100%',
            height: 8,
            borderRadius: 999,
            background: 'var(--color-bg)',
            overflow: 'hidden',
            marginBottom: 8,
          }}
        >
          <div
            style={{
              width: `${progress}%`,
              height: '100%',
              background: 'var(--color-primary)',
              transition: 'width 0.6s ease',
              borderRadius: 999,
            }}
          />
        </div>
        <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', textAlign: 'center' }}>
          화면을 꺼두지 말고 잠시만 기다려주세요
        </p>
        {error && <div className="error-banner" style={{ marginTop: 16 }}>{error}</div>}
      </div>
    </div>
  )
}