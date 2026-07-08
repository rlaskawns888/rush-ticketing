import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { getMyReservation } from '../api/client'

export default function HomePage() {
  const { name, logout } = useAuth()
  const navigate = useNavigate()

  const [checking, setChecking] = useState(false)
  const [message, setMessage] = useState('')

  async function handleBookClick() {
    setChecking(true)
    setMessage('')
    try {
      const data = await getMyReservation()
      if (data.has_reservation) {
        setMessage('이미 진행 중인 예약이 있어요. 예약확인에서 확인해주세요.')
        setChecking(false)
        return
      }
      navigate('/waiting')
    } catch (e) {
      setMessage(e.message)
      setChecking(false)
    }
  }

  function handleLogout() {
    logout()
    navigate('/login')
  }

  return (
    <div className="screen">
      <div className="card">
        <p className="title">{name}님, 안녕하세요</p>
        <p className="subtitle">무엇을 하시겠어요?</p>

        {message && <div className="error-banner">{message}</div>}

        <button
          className="button-primary"
          onClick={handleBookClick}
          disabled={checking}
          style={{ marginBottom: 12 }}
        >
          {checking ? '확인하는 중...' : '예약하기'}
        </button>

        <button
          className="button-primary"
          onClick={() => navigate('/my-reservation')}
          style={{
            background: 'var(--color-surface)',
            color: 'var(--color-primary)',
            border: '1.5px solid var(--color-primary)',
            marginBottom: 24,
          }}
        >
          예약확인
        </button>

        <button
          onClick={handleLogout}
          style={{
            border: 'none',
            background: 'none',
            color: 'var(--color-text-secondary)',
            fontSize: 14,
            cursor: 'pointer',
            fontFamily: 'inherit',
            width: '100%',
          }}
        >
          로그아웃
        </button>
      </div>
    </div>
  )
}