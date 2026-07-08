import { useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { cancelSeat, TRAIN_ID } from '../api/client'

export default function ConfirmationPage() {
  const { name } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const { trainName, seatNumber, confirmedAt, holdToken } = location.state || {}

  const [cancelling, setCancelling] = useState(false)
  const [cancelled, setCancelled] = useState(false)
  const [error, setError] = useState('')

  if (!seatNumber) {
    navigate('/')
    return null
  }

  const confirmedTimeText = confirmedAt
    ? new Date(confirmedAt).toLocaleString('ko-KR', {
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    : ''

  async function handleCancel() {
    if (!window.confirm('예약을 취소하시겠어요?')) return
    setCancelling(true)
    setError('')
    try {
      await cancelSeat(TRAIN_ID, seatNumber, holdToken)
      setCancelled(true)
    } catch (e) {
      setError(e.message)
      setCancelling(false)
    }
  }

if (cancelled) {
    return (
      <div className="screen">
        <div className="card" style={{ textAlign: 'center' }}>
          <p className="title">예약이 취소됐어요</p>
          <p className="subtitle">{seatNumber} 좌석이 다시 예매 가능한 상태가 됐어요</p>
          <button className="button-primary" onClick={() => navigate('/')} style={{ marginTop: 8 }}>
            처음으로
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="screen">
      <div className="card" style={{ textAlign: 'center' }}>
        <div
          style={{
            width: 56,
            height: 56,
            borderRadius: '50%',
            background: 'var(--color-success-light)',
            color: 'var(--color-success)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 28,
            margin: '0 auto 16px',
          }}
        >
          ✓
        </div>
        <p className="title">예약이 완료됐어요</p>
        <p className="subtitle">{name}님, 즐거운 여행 되세요</p>

        {error && <div className="error-banner">{error}</div>}

        <div
          style={{
            background: 'var(--color-bg)',
            borderRadius: 'var(--radius-md)',
            padding: '20px',
            marginBottom: 16,
            textAlign: 'left',
          }}
        >
          <Row label="열차" value={trainName} />
          <Row label="좌석" value={seatNumber} />
          <Row label="예매자" value={name} />
          <Row label="예약 확정" value={confirmedTimeText} />
        </div>

        <button className="button-primary" onClick={() => navigate('/')} style={{ marginBottom: 12 }}>
          처음으로
        </button>

        <button
          onClick={handleCancel}
          disabled={cancelling}
          style={{
            border: 'none',
            background: 'none',
            color: 'var(--color-danger)',
            fontSize: 14,
            cursor: 'pointer',
            fontFamily: 'inherit',
          }}
        >
          {cancelling ? '취소하는 중...' : '예약 취소'}
        </button>
      </div>
    </div>
  )
}

function Row({ label, value }) {
  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'space-between',
        padding: '6px 0',
        fontSize: 14,
        color: 'var(--color-text-secondary)',
      }}
    >
      <span>{label}</span>
      <span style={{ color: 'var(--color-text)', fontWeight: 600 }}>{value}</span>
    </div>
  )
}